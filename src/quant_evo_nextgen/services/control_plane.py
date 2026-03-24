from __future__ import annotations

from dataclasses import dataclass

from quant_evo_nextgen.contracts.intents import IntentClassification, IntentType
from quant_evo_nextgen.contracts.state import ApprovalDecisionCreate, RuntimeConfigProposalSummary
from quant_evo_nextgen.services.owner_onboarding import OwnerOnboardingService
from quant_evo_nextgen.services.state_store import StateStore


@dataclass(slots=True)
class ControlPlaneResult:
    created_record_id: str | None
    response_text: str


class ControlPlaneService:
    def __init__(
        self,
        state_store: StateStore,
        onboarding_service: OwnerOnboardingService | None = None,
    ) -> None:
        self.state_store = state_store
        self.onboarding_service = onboarding_service

    def handle_control_intent(
        self,
        *,
        intent: IntentClassification,
        actor: str,
        source_channel: str,
        raw_message: str,
    ) -> ControlPlaneResult:
        message_summary = intent.sanitized_message_summary or raw_message
        self.state_store.touch_owner_presence(
            actor=actor,
            source_channel=source_channel,
            message_summary=message_summary,
        )

        try:
            if intent.intent_type in {
                IntentType.PAUSE_TRADING,
                IntentType.PAUSE_EVOLUTION,
                IntentType.RESUME_DOMAIN,
            }:
                return self._create_approval_for_intent(intent, actor, source_channel, message_summary)

            if intent.intent_type is IntentType.LIST_APPROVALS:
                return self._render_pending_approvals()

            if intent.intent_type is IntentType.LIST_RUNTIME_CONFIG:
                return self._render_runtime_config_overview()

            if intent.intent_type is IntentType.PROPOSE_CONFIG_CHANGE:
                return self._propose_runtime_config_change(intent, actor, source_channel, message_summary)

            if intent.intent_type is IntentType.ROLLBACK_RUNTIME_CONFIG:
                return self._propose_runtime_config_rollback(intent, actor, source_channel, message_summary)

            if intent.intent_type is IntentType.APPROVE_REQUEST:
                return self._resolve_approval(
                    approval_id=intent.reference_id,
                    actor=actor,
                    source_channel=source_channel,
                    decision="approved",
                    raw_message=message_summary,
                )

            if intent.intent_type is IntentType.REJECT_REQUEST:
                return self._resolve_approval(
                    approval_id=intent.reference_id,
                    actor=actor,
                    source_channel=source_channel,
                    decision="rejected",
                    raw_message=message_summary,
                )

            if intent.intent_type is IntentType.DEPLOY_BOOTSTRAP:
                return self._bootstrap_deploy_role(intent, actor, source_channel)

            if intent.intent_type is IntentType.DEPLOY_STATUS:
                return self._render_deploy_status(intent)

            if intent.intent_type is IntentType.DEPLOY_SET:
                return self._set_deploy_field(intent, actor, source_channel)
        except ValueError as exc:
            return ControlPlaneResult(
                created_record_id=None,
                response_text=f"Control plane could not execute this request: {exc}",
            )

        return ControlPlaneResult(
            created_record_id=None,
            response_text="This message does not require a control-plane write.",
        )

    def _create_approval_for_intent(
        self,
        intent: IntentClassification,
        actor: str,
        source_channel: str,
        raw_message: str,
    ) -> ControlPlaneResult:
        approval_type, target_domain = _approval_spec_from_intent(intent)
        approval = self.state_store.create_approval_request(
            {
                "approval_type": approval_type,
                "subject_type": "domain",
                "subject_id": target_domain,
                "requested_by": actor,
                "risk_level": intent.risk_tier,
                "rationale": raw_message,
                "payload": {
                    "target_domain": target_domain,
                    "source_channel": source_channel,
                    "intent": intent.intent_type.value,
                },
                "created_by": actor,
                "origin_type": "discord",
                "origin_id": source_channel,
                "status": "pending",
            }
        )

        action_label = {
            "pause_trading": "pause auto-trading",
            "pause_evolution": "pause auto-evolution",
            "resume_domain": f"resume `{target_domain}`",
        }[approval_type]
        return ControlPlaneResult(
            created_record_id=approval.id,
            response_text=(
                f"Created approval request for `{action_label}` as `{approval.id}`.\n"
                "The system will wait for owner approval before changing state, and both the approval and follow-up action are written to durable state."
            ),
        )

    def _render_pending_approvals(self) -> ControlPlaneResult:
        approvals = self.state_store.list_approval_requests(pending_only=True, limit=5)
        if not approvals:
            return ControlPlaneResult(
                created_record_id=None,
                response_text="There are no pending approval requests right now.",
            )

        lines = ["Pending approvals:"]
        for approval in approvals:
            lines.append(
                f"- `{approval.id}` | {approval.approval_type} | domain `{approval.subject_id}` | risk {approval.risk_level}"
            )
        lines.append("Reply with `approve <id>` or `reject <id>`.")
        return ControlPlaneResult(created_record_id=None, response_text="\n".join(lines))

    def _render_runtime_config_overview(self) -> ControlPlaneResult:
        entries = self.state_store.list_runtime_config_entries(limit=8)
        proposals = self.state_store.list_runtime_config_proposals(
            statuses=("proposed", "awaiting_approval"),
            limit=5,
        )
        revisions = self.state_store.list_runtime_config_revisions(limit=3)

        lines = ["Current runtime configuration summary:"]
        for entry in entries:
            lines.append(
                f"- `{entry.target_type}:{entry.target_key}` | {entry.display_name} | risk {entry.risk_level} | current value {entry.value_json}"
            )

        if proposals:
            lines.append("Pending config proposals:")
            for proposal in proposals:
                suffix = f" | approval `{proposal.approval_request_id}`" if proposal.approval_request_id else ""
                lines.append(
                    f"- `{proposal.id}` | {proposal.display_name} | {proposal.status} | {proposal.change_summary}{suffix}"
                )
        else:
            lines.append("There are no pending config proposals right now.")

        if revisions:
            lines.append("Recent config revisions:")
            for revision in revisions:
                lines.append(
                    f"- `{revision.id}` | {revision.display_name} | {revision.change_summary} | by {revision.applied_by}"
                )
            lines.append("To roll back, send `rollback config <revision-id>`.")

        return ControlPlaneResult(created_record_id=None, response_text="\n".join(lines))

    def _propose_runtime_config_change(
        self,
        intent: IntentClassification,
        actor: str,
        source_channel: str,
        raw_message: str,
    ) -> ControlPlaneResult:
        if not intent.config_target_type or not intent.config_target_key or not intent.config_patch:
            return ControlPlaneResult(
                created_record_id=None,
                response_text=(
                    "I understood that you want to change runtime config, but I still could not determine the target field and value. "
                    "Try something like `set heartbeat interval to 120 seconds`."
                ),
            )

        proposal = self.state_store.create_runtime_config_proposal(
            {
                "target_type": intent.config_target_type,
                "target_key": intent.config_target_key,
                "requested_by": actor,
                "rationale": raw_message,
                "proposed_value_json": intent.config_patch,
                "change_summary": intent.config_change_summary,
                "created_by": actor,
                "origin_type": "discord",
                "origin_id": source_channel,
            }
        )
        return self._finalize_runtime_config_proposal(
            proposal=proposal,
            actor=actor,
            source_channel=source_channel,
            create_prefix="Created runtime config proposal",
            apply_prefix="Applied runtime config proposal",
        )

    def _propose_runtime_config_rollback(
        self,
        intent: IntentClassification,
        actor: str,
        source_channel: str,
        raw_message: str,
    ) -> ControlPlaneResult:
        if not intent.reference_id:
            return ControlPlaneResult(
                created_record_id=None,
                response_text="I could not determine which config revision to roll back. Try `rollback config <revision-id>`.",
            )

        proposal = self.state_store.create_runtime_config_rollback_proposal(
            intent.reference_id,
            requested_by=actor,
            rationale=raw_message,
        )
        return self._finalize_runtime_config_proposal(
            proposal=proposal,
            actor=actor,
            source_channel=source_channel,
            create_prefix="Created config rollback proposal",
            apply_prefix="Applied config rollback proposal",
        )

    def _finalize_runtime_config_proposal(
        self,
        *,
        proposal: RuntimeConfigProposalSummary,
        actor: str,
        source_channel: str,
        create_prefix: str,
        apply_prefix: str,
    ) -> ControlPlaneResult:
        if proposal.requires_approval:
            return ControlPlaneResult(
                created_record_id=proposal.id,
                response_text=(
                    f"{create_prefix} `{proposal.id}`: {proposal.change_summary}\n"
                    f"This change is rated {proposal.risk_level} and opened approval `{proposal.approval_request_id}`. "
                    "Reply with `approve <approval-id>` to continue."
                ),
            )

        revision = self.state_store.apply_runtime_config_proposal(proposal.id, applied_by=actor)
        run = self.state_store.start_workflow_run(
            workflow_code="WF-GOV-006",
            owner_role="owner",
            summary=f"Applying runtime config change for {proposal.display_name}.",
            input_payload={
                "proposal_id": proposal.id,
                "target_type": proposal.target_type,
                "target_key": proposal.target_key,
                "source_channel": source_channel,
            },
            created_by=actor,
        )
        self.state_store.append_workflow_event(
            run.id,
            event_type="workflow.runtime_config_applied",
            summary=proposal.change_summary,
            payload={"proposal_id": proposal.id, "revision_id": revision.id},
            created_by=actor,
        )
        self.state_store.complete_workflow_run(
            run.id,
            result_payload={"proposal_id": proposal.id, "revision_id": revision.id},
            created_by=actor,
        )
        return ControlPlaneResult(
            created_record_id=proposal.id,
            response_text=(
                f"{apply_prefix} `{proposal.id}`: {proposal.change_summary}\n"
                f"New revision id: `{revision.id}`."
            ),
        )

    def _resolve_approval(
        self,
        *,
        approval_id: str | None,
        actor: str,
        source_channel: str,
        decision: str,
        raw_message: str,
    ) -> ControlPlaneResult:
        if not approval_id:
            return ControlPlaneResult(
                created_record_id=None,
                response_text="I could not determine the approval id. Reply with `approve <id>` or `reject <id>`.",
            )

        approval = self.state_store.get_approval_request(approval_id)
        decision_summary = self.state_store.decide_approval_request(
            approval_id,
            ApprovalDecisionCreate(
                decision="approved" if decision == "approved" else "rejected",
                decided_by=actor,
                reason=raw_message,
            ),
        )

        if decision == "approved":
            workflow_code = {
                "resume_domain": "WF-GOV-004",
                "runtime_config_change": "WF-GOV-006",
            }.get(approval.approval_type, "WF-GOV-003")
            run = self.state_store.start_workflow_run(
                workflow_code=workflow_code,
                owner_role="owner",
                summary=f"Applying approved control action for {approval.approval_type}.",
                input_payload={
                    "approval_id": approval.id,
                    "approval_type": approval.approval_type,
                    "subject_id": approval.subject_id,
                    "actor": actor,
                    "source_channel": source_channel,
                },
                created_by=actor,
            )
            self.state_store.append_workflow_event(
                run.id,
                event_type="workflow.control_action_applied",
                summary=decision_summary.effect_summary or "Control action applied.",
                payload={"approval_id": approval.id, "decision": decision},
                created_by=actor,
            )
            self.state_store.complete_workflow_run(
                run.id,
                result_payload={
                    "approval_id": approval.id,
                    "decision": decision,
                    "effect_summary": decision_summary.effect_summary,
                },
                created_by=actor,
            )

        verb = "Approved approval request" if decision == "approved" else "Rejected approval request"
        return ControlPlaneResult(
            created_record_id=decision_summary.id,
            response_text=(
                f"{verb} `{approval.id}`, type `{approval.approval_type}`.\n"
                f"{decision_summary.effect_summary or 'The approval decision has been recorded.'}"
            ),
        )

    def _bootstrap_deploy_role(
        self,
        intent: IntentClassification,
        actor: str,
        source_channel: str,
    ) -> ControlPlaneResult:
        onboarding = self._require_onboarding_service()
        role = intent.deploy_role or "core"
        result = onboarding.bootstrap_role(role)
        workflow = self.state_store.start_workflow_run(
            workflow_code="WF-OPS-001",
            owner_role="owner",
            summary=f"Bootstrap deployment draft for {result.role}.",
            input_payload={"role": result.role, "source_channel": source_channel},
            created_by=actor,
        )
        self.state_store.append_workflow_event(
            workflow.id,
            event_type="workflow.deploy_draft_bootstrapped",
            summary=f"Deployment draft prepared for {result.role}.",
            payload={"role": result.role, "env_path": result.env_path, "preflight_status": result.preflight_status},
            created_by=actor,
        )
        self.state_store.complete_workflow_run(
            workflow.id,
            result_payload={"role": result.role, "env_path": result.env_path, "preflight_status": result.preflight_status},
            created_by=actor,
        )
        return ControlPlaneResult(created_record_id=workflow.id, response_text=result.summary_text)

    def _render_deploy_status(self, intent: IntentClassification) -> ControlPlaneResult:
        onboarding = self._require_onboarding_service()
        result = onboarding.status(intent.deploy_role or "core")
        return ControlPlaneResult(created_record_id=None, response_text=result.summary_text)

    def _set_deploy_field(
        self,
        intent: IntentClassification,
        actor: str,
        source_channel: str,
    ) -> ControlPlaneResult:
        onboarding = self._require_onboarding_service()
        role = intent.deploy_role or "core"
        field_alias = intent.deploy_field_alias or ""
        if not field_alias or intent.deploy_value is None:
            raise ValueError("I could not determine the deployment field and value to update.")
        result = onboarding.set_field(role=role, field_alias=field_alias, value=intent.deploy_value)
        workflow = self.state_store.start_workflow_run(
            workflow_code="WF-OPS-001",
            owner_role="owner",
            summary=f"Update deployment draft field for {result.role}.",
            input_payload={
                "role": result.role,
                "field_alias": field_alias,
                "changed_keys": result.changed_keys,
                "masked_value": result.masked_value,
                "sensitive": result.sensitive,
                "source_channel": source_channel,
            },
            created_by=actor,
        )
        self.state_store.append_workflow_event(
            workflow.id,
            event_type="workflow.deploy_draft_updated",
            summary=f"Updated deployment draft field `{field_alias}` for `{result.role}`.",
            payload={
                "role": result.role,
                "field_alias": field_alias,
                "changed_keys": result.changed_keys,
                "masked_value": result.masked_value,
                "preflight_status": result.preflight_status,
            },
            created_by=actor,
        )
        self.state_store.complete_workflow_run(
            workflow.id,
            result_payload={
                "role": result.role,
                "field_alias": field_alias,
                "changed_keys": result.changed_keys,
                "preflight_status": result.preflight_status,
            },
            created_by=actor,
        )
        return ControlPlaneResult(created_record_id=workflow.id, response_text=result.summary_text)

    def _require_onboarding_service(self) -> OwnerOnboardingService:
        if self.onboarding_service is None:
            raise ValueError("Deployment onboarding service is not configured for this control plane.")
        return self.onboarding_service


def _approval_spec_from_intent(intent: IntentClassification) -> tuple[str, str]:
    if intent.intent_type is IntentType.PAUSE_TRADING:
        return ("pause_trading", "trading")
    if intent.intent_type is IntentType.PAUSE_EVOLUTION:
        return ("pause_evolution", "evolution")
    if intent.intent_type is IntentType.RESUME_DOMAIN:
        return ("resume_domain", intent.target_domain or "governance")
    raise ValueError(f"Unsupported control intent: {intent.intent_type}")
