from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Callable, Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from quant_evo_nextgen.config import Settings
from quant_evo_nextgen.contracts.state import (
    ApprovalDecisionCreate,
    ApprovalDecisionSummary,
    ApprovalRequestCreate,
    ApprovalRequestSummary,
    GoalCreate,
    GoalSummary,
    IncidentCreate,
    IncidentSummary,
    OperatorOverrideCreate,
    OperatorOverrideSummary,
    OwnerPreferenceSummary,
    OwnerPreferenceUpsert,
    ProviderProfileSummary,
    RuntimeConfigEntrySummary,
    RuntimeConfigProposalCreate,
    RuntimeConfigProposalSummary,
    RuntimeConfigRevisionSummary,
    SourceHealthSummary,
    SupervisorLoopSummary,
    WorkflowRunSummary,
)
from quant_evo_nextgen.db.models import (
    AllocationPolicyModel,
    ApprovalDecisionModel,
    ApprovalRequestModel,
    AutonomyModeModel,
    BrokerCapabilityModel,
    CodexRunModel,
    GoalModel,
    HeartbeatModel,
    IncidentModel,
    OwnerPreferenceModel,
    OperatorOverrideModel,
    ProviderProfileModel,
    RuntimeConfigProposalModel,
    RuntimeConfigRevisionModel,
    SourceHealthModel,
    SupervisorLoopModel,
    SystemPolicyModel,
    WorkflowDefinitionModel,
    WorkflowEventModel,
    WorkflowRunModel,
)
from quant_evo_nextgen.services.broker import broker_capability_defaults


@dataclass(slots=True)
class RuntimeSnapshot:
    active_goals: int
    open_incidents: int
    pending_approvals: int
    active_overrides: int
    active_codex_runs: int
    last_heartbeat_at: datetime | None


WORKFLOW_BOOTSTRAP: tuple[dict[str, Any], ...] = (
    {
        "workflow_code": "WF-GOV-001",
        "family": "governance",
        "name": "Goal Admission",
        "description": "Admit new goals into durable runtime tracking.",
        "risk_tier": "R2",
        "approval_required": False,
    },
    {
        "workflow_code": "WF-GOV-002",
        "family": "governance",
        "name": "Governance Heartbeat",
        "description": "Persist recurring heartbeat and control-plane health state.",
        "risk_tier": "R1",
        "approval_required": False,
    },
    {
        "workflow_code": "WF-GOV-003",
        "family": "governance",
        "name": "Pause Domain By Approval",
        "description": "Apply an approved pause to a governed runtime domain.",
        "risk_tier": "R4",
        "approval_required": True,
    },
    {
        "workflow_code": "WF-GOV-004",
        "family": "governance",
        "name": "Resume Domain By Approval",
        "description": "Lift an approved pause from a governed runtime domain.",
        "risk_tier": "R3",
        "approval_required": True,
    },
    {
        "workflow_code": "WF-GOV-005",
        "family": "governance",
        "name": "Owner Absence Safe-Mode Escalation",
        "description": "Escalate into safe mode during prolonged owner absence.",
        "risk_tier": "R4",
        "approval_required": True,
    },
    {
        "workflow_code": "WF-GOV-006",
        "family": "governance",
        "name": "Runtime Config Change Management",
        "description": "Create, approve, apply, and audit durable runtime configuration changes.",
        "risk_tier": "R2",
        "approval_required": False,
    },
    {
        "workflow_code": "WF-LRN-002",
        "family": "learning",
        "name": "Research Intake Sweep",
        "description": "Collect fresh external material into the bounded learning inbox.",
        "risk_tier": "R2",
        "approval_required": False,
    },
    {
        "workflow_code": "WF-LRN-003",
        "family": "learning",
        "name": "Research Distillation",
        "description": "Distill completed research runs into durable documents and evidence items.",
        "risk_tier": "R2",
        "approval_required": False,
    },
    {
        "workflow_code": "WF-LRN-004",
        "family": "learning",
        "name": "Insight Synthesis and Quarantine",
        "description": "Synthesize durable insight candidates from ingested evidence while quarantining unsafe learning items.",
        "risk_tier": "R2",
        "approval_required": False,
    },
    {
        "workflow_code": "WF-LRN-005",
        "family": "learning",
        "name": "Source Revalidation and Trust Decay",
        "description": "Revalidate knowledge sources and decay stale trust.",
        "risk_tier": "R2",
        "approval_required": False,
    },
    {
        "workflow_code": "WF-EXE-004",
        "family": "execution",
        "name": "Market Calendar and Session Guard",
        "description": "Gate capital-facing actions with market session state.",
        "risk_tier": "R4",
        "approval_required": False,
    },
    {
        "workflow_code": "WF-EXE-005",
        "family": "execution",
        "name": "Broker Outage Degradation",
        "description": "Degrade safely when broker health is compromised.",
        "risk_tier": "R4",
        "approval_required": False,
    },
    {
        "workflow_code": "WF-EXE-006",
        "family": "execution",
        "name": "Broker Truth Sync",
        "description": "Synchronize durable trading state from the configured external broker.",
        "risk_tier": "R4",
        "approval_required": False,
    },
    {
        "workflow_code": "WF-EVO-003",
        "family": "evolution",
        "name": "Codex Build Cycle",
        "description": "Execute Codex-backed implementation and review tasks.",
        "risk_tier": "R3",
        "approval_required": False,
    },
    {
        "workflow_code": "WF-EVO-004",
        "family": "evolution",
        "name": "Council Reflection Cycle",
        "description": "Run a bounded multi-agent reflection cycle before promoting change.",
        "risk_tier": "R2",
        "approval_required": False,
    },
    {
        "workflow_code": "WF-EVO-005",
        "family": "evolution",
        "name": "Objective Drift Review",
        "description": "Review self-improvement proposals against the core mission.",
        "risk_tier": "R3",
        "approval_required": True,
    },
    {
        "workflow_code": "WF-EVO-006",
        "family": "evolution",
        "name": "Capability Scorecard And Anti-Stall Review",
        "description": "Score autonomous capability health, detect stalls, and queue bounded replanning when needed.",
        "risk_tier": "R2",
        "approval_required": False,
    },
    {
        "workflow_code": "WF-STR-001",
        "family": "strategy",
        "name": "Hypothesis Generation",
        "description": "Create durable strategy hypotheses from learning and market observations.",
        "risk_tier": "R2",
        "approval_required": False,
    },
    {
        "workflow_code": "WF-STR-002",
        "family": "strategy",
        "name": "Strategy Evaluation Cycle",
        "description": "Evaluate candidate strategies before paper or live promotion.",
        "risk_tier": "R3",
        "approval_required": False,
    },
    {
        "workflow_code": "WF-STR-003",
        "family": "strategy",
        "name": "Backtest Validation",
        "description": "Run backtests and gate candidate strategies before paper trading.",
        "risk_tier": "R3",
        "approval_required": False,
    },
    {
        "workflow_code": "WF-STR-004",
        "family": "strategy",
        "name": "Paper Promotion and Monitoring",
        "description": "Promote strategies into paper trading and monitor paper performance.",
        "risk_tier": "R3",
        "approval_required": False,
    },
    {
        "workflow_code": "WF-STR-005",
        "family": "strategy",
        "name": "Live Promotion Review",
        "description": "Review paper-validated strategies before limited-live or production promotion.",
        "risk_tier": "R4",
        "approval_required": True,
    },
    {
        "workflow_code": "WF-STR-006",
        "family": "strategy",
        "name": "Strategy Withdrawal",
        "description": "Withdraw degraded strategies with durable evidence and replacement references.",
        "risk_tier": "R3",
        "approval_required": True,
    },
    {
        "workflow_code": "WF-INC-003",
        "family": "incident",
        "name": "Provider or Relay Outage Response",
        "description": "Persist provider incidents and fail safely on relay degradation.",
        "risk_tier": "R4",
        "approval_required": False,
    },
    {
        "workflow_code": "WF-INC-004",
        "family": "incident",
        "name": "Credential or Bot Token Compromise Response",
        "description": "Handle Discord, dashboard, or provider credential compromise.",
        "risk_tier": "R4",
        "approval_required": True,
    },
    {
        "workflow_code": "WF-OPS-001",
        "family": "operations",
        "name": "Disaster Recovery Drill",
        "description": "Run and record disaster recovery drills.",
        "risk_tier": "R3",
        "approval_required": True,
    },
)


SUPERVISOR_LOOP_BOOTSTRAP: tuple[dict[str, Any], ...] = (
    {
        "loop_key": "governance-heartbeat",
        "workflow_code": "WF-GOV-002",
        "domain": "governance",
        "display_name": "Governance heartbeat",
        "handler_key": "governance_heartbeat",
        "cadence_seconds": 60,
        "priority": 10,
        "execution_mode": "active",
        "is_enabled": True,
        "budget_scope": {"max_runs_per_tick": 1, "max_duration_seconds": 15},
        "stop_conditions": {"max_failure_streak": 5},
    },
    {
        "loop_key": "source-revalidation",
        "workflow_code": "WF-LRN-005",
        "domain": "learning",
        "display_name": "Source revalidation",
        "handler_key": "source_revalidation",
        "cadence_seconds": 900,
        "priority": 20,
        "execution_mode": "active",
        "is_enabled": True,
        "budget_scope": {"max_runs_per_tick": 1, "max_duration_seconds": 60},
        "stop_conditions": {"max_failure_streak": 3},
    },
    {
        "loop_key": "research-intake",
        "workflow_code": "WF-LRN-002",
        "domain": "learning",
        "display_name": "Research intake sweep",
        "handler_key": "research_intake",
        "cadence_seconds": 1800,
        "priority": 40,
        "execution_mode": "active",
        "is_enabled": True,
        "budget_scope": {
            "max_runs_per_tick": 1,
            "max_duration_seconds": 300,
            "max_iterations": 3,
            "max_token_budget": 90000,
            "max_system_codex_runs": 3,
        },
        "stop_conditions": {"max_failure_streak": 3},
    },
    {
        "loop_key": "research-distillation",
        "workflow_code": "WF-LRN-003",
        "domain": "learning",
        "display_name": "Research distillation",
        "handler_key": "research_distillation",
        "cadence_seconds": 900,
        "priority": 45,
        "execution_mode": "active",
        "is_enabled": True,
        "budget_scope": {"max_runs_per_tick": 1, "max_documents_per_tick": 3},
        "stop_conditions": {"max_failure_streak": 3},
    },
    {
        "loop_key": "learning-synthesis",
        "workflow_code": "WF-LRN-004",
        "domain": "learning",
        "display_name": "Insight synthesis and quarantine",
        "handler_key": "learning_synthesis",
        "cadence_seconds": 1200,
        "priority": 47,
        "execution_mode": "active",
        "is_enabled": True,
        "budget_scope": {"max_runs_per_tick": 1, "max_insights_per_tick": 3},
        "stop_conditions": {"max_failure_streak": 3},
    },
    {
        "loop_key": "market-session-guard",
        "workflow_code": "WF-EXE-004",
        "domain": "trading",
        "display_name": "Market session guard",
        "handler_key": "market_session_guard",
        "cadence_seconds": 300,
        "priority": 48,
        "execution_mode": "active",
        "is_enabled": True,
        "budget_scope": {"max_runs_per_tick": 1, "max_duration_seconds": 15},
        "stop_conditions": {"max_failure_streak": 4},
    },
    {
        "loop_key": "broker-state-sync",
        "workflow_code": "WF-EXE-006",
        "domain": "trading",
        "display_name": "Broker state sync",
        "handler_key": "broker_state_sync",
        "cadence_seconds": 300,
        "priority": 49,
        "execution_mode": "active",
        "is_enabled": True,
        "budget_scope": {"max_runs_per_tick": 1, "full_sync": True},
        "stop_conditions": {"max_failure_streak": 4},
    },
    {
        "loop_key": "strategy-evaluation",
        "workflow_code": "WF-STR-002",
        "domain": "strategy",
        "display_name": "Strategy evaluation",
        "handler_key": "strategy_evaluation",
        "cadence_seconds": 1800,
        "priority": 50,
        "execution_mode": "active",
        "is_enabled": True,
        "budget_scope": {
            "max_runs_per_tick": 1,
            "max_duration_seconds": 300,
            "max_iterations": 2,
            "max_token_budget": 50000,
            "max_system_codex_runs": 2,
        },
        "stop_conditions": {"max_failure_streak": 3},
    },
    {
        "loop_key": "evolution-governance-sync",
        "workflow_code": "WF-EVO-005",
        "domain": "evolution",
        "display_name": "Evolution governance sync",
        "handler_key": "evolution_governance_sync",
        "cadence_seconds": 900,
        "priority": 55,
        "execution_mode": "active",
        "is_enabled": True,
        "budget_scope": {"max_runs_per_tick": 1, "max_completed_codex_runs": 3},
        "stop_conditions": {"max_failure_streak": 3},
    },
    {
        "loop_key": "capability-review",
        "workflow_code": "WF-EVO-006",
        "domain": "evolution",
        "display_name": "Capability scorecard and anti-stall review",
        "handler_key": "capability_review",
        "cadence_seconds": 3600,
        "priority": 57,
        "execution_mode": "active",
        "is_enabled": True,
        "budget_scope": {
            "max_runs_per_tick": 1,
            "max_duration_seconds": 480,
            "max_iterations": 2,
            "max_token_budget": 45000,
            "max_system_codex_runs": 1,
        },
        "stop_conditions": {"max_failure_streak": 3},
    },
    {
        "loop_key": "council-reflection",
        "workflow_code": "WF-EVO-004",
        "domain": "evolution",
        "display_name": "Council reflection cycle",
        "handler_key": "council_reflection",
        "cadence_seconds": 3600,
        "priority": 60,
        "execution_mode": "planned",
        "is_enabled": False,
        "budget_scope": {"max_runs_per_tick": 1, "max_duration_seconds": 900},
        "stop_conditions": {"max_failure_streak": 3},
    },
    {
        "loop_key": "owner-absence-safe-mode",
        "workflow_code": "WF-GOV-005",
        "domain": "governance",
        "display_name": "Owner absence safe mode",
        "handler_key": "owner_absence_watch",
        "cadence_seconds": 3600,
        "priority": 70,
        "execution_mode": "planned",
        "is_enabled": False,
        "budget_scope": {"max_runs_per_tick": 1, "max_duration_seconds": 120},
        "stop_conditions": {"max_failure_streak": 2},
    },
)


MISSION_PRIORITY_ORDER = [
    "system survivability",
    "auditability and recoverability",
    "capital protection",
    "governance continuity",
    "learning and capability growth",
    "return optimization after the above remain intact",
]


SYSTEM_POLICY_METADATA: dict[str, dict[str, Any]] = {
    "mission_priority_order": {
        "category": "governance",
        "risk_level": "R4",
        "is_mutable": False,
        "requires_restart": False,
    },
    "deployment_topology": {
        "category": "operations",
        "risk_level": "R3",
        "is_mutable": True,
        "requires_restart": True,
    },
    "owner_language": {
        "category": "owner-experience",
        "risk_level": "R1",
        "is_mutable": True,
        "requires_restart": False,
    },
    "heartbeat_runtime": {
        "category": "governance",
        "risk_level": "R1",
        "is_mutable": True,
        "requires_restart": False,
    },
    "codex_runtime": {
        "category": "evolution",
        "risk_level": "R2",
        "is_mutable": True,
        "requires_restart": True,
    },
}


OWNER_PREFERENCE_METADATA: dict[str, dict[str, Any]] = {
    "interaction_language": {
        "category": "owner-experience",
        "risk_level": "R1",
        "is_mutable": True,
        "requires_restart": False,
    },
    "discord_channels": {
        "category": "owner-experience",
        "risk_level": "R2",
        "is_mutable": True,
        "requires_restart": True,
    },
}


class StateStore:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self.session_factory = session_factory

    def bootstrap_reference_data(self, settings: Settings) -> None:
        with self.session_factory() as session:
            self._bootstrap_reference_data(session, settings)
            session.commit()

    def create_goal(self, payload: GoalCreate | dict[str, Any]) -> GoalSummary:
        request = GoalCreate.model_validate(payload)
        with self.session_factory() as session:
            goal = GoalModel(
                title=request.title,
                description=request.description,
                mission_domain=request.mission_domain,
                success_metrics=request.success_metrics,
                failure_metrics=request.failure_metrics,
                budget_scope=request.budget_scope,
                time_horizon=request.time_horizon,
                created_by=request.created_by,
                origin_type=request.origin_type,
                origin_id=request.origin_id,
                status=request.status,
            )
            session.add(goal)
            session.commit()
            session.refresh(goal)
            return self._goal_summary(goal)

    def list_goals(self, *, statuses: Sequence[str] | None = None) -> list[GoalSummary]:
        with self.session_factory() as session:
            query = select(GoalModel).order_by(GoalModel.created_at.desc())
            if statuses:
                query = query.where(GoalModel.status.in_(list(statuses)))
            goals = session.scalars(query).all()
            return [self._goal_summary(goal) for goal in goals]

    def create_incident(self, payload: IncidentCreate | dict[str, Any]) -> IncidentSummary:
        request = IncidentCreate.model_validate(payload)
        with self.session_factory() as session:
            incident = IncidentModel(
                title=request.title,
                summary=request.summary,
                severity=request.severity,
                created_by=request.created_by,
                origin_type=request.origin_type,
                origin_id=request.origin_id,
                status=request.status,
                related_workflow_run_id=request.related_workflow_run_id,
            )
            session.add(incident)
            session.commit()
            session.refresh(incident)
            return self._incident_summary(incident)

    def list_incidents(
        self,
        *,
        open_only: bool = False,
        limit: int | None = None,
    ) -> list[IncidentSummary]:
        with self.session_factory() as session:
            query = select(IncidentModel).order_by(IncidentModel.created_at.desc())
            if open_only:
                query = query.where(IncidentModel.status.in_(["open", "investigating", "mitigated"]))
            if limit is not None:
                query = query.limit(limit)
            incidents = session.scalars(query).all()
            return [self._incident_summary(incident) for incident in incidents]

    def create_approval_request(
        self,
        payload: ApprovalRequestCreate | dict[str, Any],
    ) -> ApprovalRequestSummary:
        request = ApprovalRequestCreate.model_validate(payload)
        with self.session_factory() as session:
            approval = ApprovalRequestModel(
                approval_type=request.approval_type,
                subject_type=request.subject_type,
                subject_id=request.subject_id,
                requested_by=request.requested_by,
                risk_level=request.risk_level,
                rationale=request.rationale,
                payload=request.payload,
                deadline=request.deadline,
                created_by=request.created_by,
                origin_type=request.origin_type,
                origin_id=request.origin_id,
                status=request.status,
                decision_status="pending",
            )
            session.add(approval)
            session.commit()
            session.refresh(approval)
            return self._approval_summary(approval)

    def list_approval_requests(
        self,
        *,
        pending_only: bool = False,
        limit: int | None = None,
    ) -> list[ApprovalRequestSummary]:
        with self.session_factory() as session:
            query = select(ApprovalRequestModel).order_by(ApprovalRequestModel.created_at.desc())
            if pending_only:
                query = query.where(ApprovalRequestModel.decision_status == "pending")
            if limit is not None:
                query = query.limit(limit)
            approvals = session.scalars(query).all()
            return [self._approval_summary(approval) for approval in approvals]

    def get_approval_request(self, approval_request_id: str) -> ApprovalRequestSummary:
        with self.session_factory() as session:
            approval = session.get(ApprovalRequestModel, approval_request_id)
            if approval is None:
                raise ValueError(f"Approval request not found: {approval_request_id}")
            return self._approval_summary(approval)

    def decide_approval_request(
        self,
        approval_request_id: str,
        payload: ApprovalDecisionCreate | dict[str, Any],
    ) -> ApprovalDecisionSummary:
        request = ApprovalDecisionCreate.model_validate(payload)
        with self.session_factory() as session:
            approval = session.get(ApprovalRequestModel, approval_request_id)
            if approval is None:
                raise ValueError(f"Approval request not found: {approval_request_id}")
            if approval.decision_status != "pending":
                raise ValueError(f"Approval request is already resolved: {approval_request_id}")

            approval.decision_status = request.decision
            approval.status = request.decision

            effect_summary = None
            if request.decision == "approved":
                effect_summary = self._apply_approved_control_action(session, approval, request.decided_by)
            else:
                if approval.approval_type == "runtime_config_change":
                    proposal_id = str(approval.payload.get("config_proposal_id") or "")
                    if proposal_id:
                        proposal = session.get(RuntimeConfigProposalModel, proposal_id)
                        if proposal is not None and proposal.status in {"proposed", "awaiting_approval"}:
                            proposal.status = "rejected"
                effect_summary = "No runtime state change was applied."

            decision = ApprovalDecisionModel(
                approval_request_id=approval_request_id,
                decision=request.decision,
                decided_by=request.decided_by,
                reason=request.reason,
                created_by=request.decided_by,
                origin_type="approval-decision",
                origin_id=approval_request_id,
                status=request.decision,
            )
            session.add(decision)
            session.commit()
            session.refresh(decision)
            return self._approval_decision_summary(decision, approval.decision_status, effect_summary)

    def create_operator_override(
        self,
        payload: OperatorOverrideCreate | dict[str, Any],
    ) -> OperatorOverrideSummary:
        request = OperatorOverrideCreate.model_validate(payload)
        with self.session_factory() as session:
            override = OperatorOverrideModel(
                scope=request.scope,
                action=request.action,
                reason=request.reason,
                activated_by=request.activated_by,
                expires_at=request.expires_at,
                created_by=request.created_by,
                origin_type=request.origin_type,
                origin_id=request.origin_id,
                status=request.status,
                is_active=True,
            )
            session.add(override)
            session.commit()
            session.refresh(override)
            return self._override_summary(override)

    def list_operator_overrides(
        self,
        *,
        active_only: bool = False,
        limit: int | None = None,
    ) -> list[OperatorOverrideSummary]:
        with self.session_factory() as session:
            query = select(OperatorOverrideModel).order_by(OperatorOverrideModel.created_at.desc())
            if active_only:
                query = query.where(OperatorOverrideModel.is_active.is_(True))
            if limit is not None:
                query = query.limit(limit)
            overrides = session.scalars(query).all()
            return [self._override_summary(override) for override in overrides]

    def upsert_owner_preference(
        self,
        payload: OwnerPreferenceUpsert | dict[str, Any],
    ) -> OwnerPreferenceSummary:
        request = OwnerPreferenceUpsert.model_validate(payload)
        with self.session_factory() as session:
            preference = session.scalar(
                select(OwnerPreferenceModel).where(OwnerPreferenceModel.preference_key == request.preference_key)
            )
            if preference is None:
                preference = OwnerPreferenceModel(
                    preference_key=request.preference_key,
                    scope=request.scope,
                    display_name=request.display_name,
                    value_json=request.value_json,
                    updated_by=request.updated_by,
                    notes=request.notes,
                    created_by=request.updated_by,
                    origin_type="owner-preference",
                    origin_id=request.preference_key,
                    status=request.status,
                )
                session.add(preference)
            else:
                preference.scope = request.scope
                preference.display_name = request.display_name
                preference.value_json = request.value_json
                preference.updated_by = request.updated_by
                preference.notes = request.notes
                preference.status = request.status

            session.commit()
            session.refresh(preference)
            return self._owner_preference_summary(preference)

    def touch_owner_presence(
        self,
        *,
        actor: str,
        source_channel: str,
        message_summary: str,
    ) -> OwnerPreferenceSummary:
        return self.upsert_owner_preference(
            {
                "preference_key": "last_owner_interaction",
                "display_name": "Last Owner Interaction",
                "scope": "presence",
                "updated_by": actor,
                "notes": "Updated automatically from Discord control interactions.",
                "value_json": {
                    "actor": actor,
                    "source_channel": source_channel,
                    "message_summary": message_summary[:500],
                    "occurred_at": datetime.now(tz=UTC).isoformat(),
                },
            }
        )

    def list_owner_preferences(self, *, limit: int | None = None) -> list[OwnerPreferenceSummary]:
        with self.session_factory() as session:
            query = select(OwnerPreferenceModel).order_by(OwnerPreferenceModel.updated_at.desc())
            if limit is not None:
                query = query.limit(limit)
            preferences = session.scalars(query).all()
            return [self._owner_preference_summary(preference) for preference in preferences]

    def get_owner_preference(self, preference_key: str) -> OwnerPreferenceSummary | None:
        with self.session_factory() as session:
            preference = session.scalar(
                select(OwnerPreferenceModel).where(OwnerPreferenceModel.preference_key == preference_key)
            )
            return self._owner_preference_summary(preference) if preference is not None else None

    def list_runtime_config_entries(
        self,
        *,
        include_presence: bool = False,
        limit: int | None = None,
    ) -> list[RuntimeConfigEntrySummary]:
        with self.session_factory() as session:
            policies = session.scalars(
                select(SystemPolicyModel).order_by(SystemPolicyModel.policy_key.asc())
            ).all()
            preference_query = select(OwnerPreferenceModel).order_by(OwnerPreferenceModel.preference_key.asc())
            if not include_presence:
                preference_query = preference_query.where(OwnerPreferenceModel.scope != "presence")
            preferences = session.scalars(preference_query).all()
            loops = session.scalars(
                select(SupervisorLoopModel).order_by(SupervisorLoopModel.priority.asc(), SupervisorLoopModel.loop_key.asc())
            ).all()

            entries = [self._runtime_config_entry_from_policy(policy) for policy in policies]
            entries.extend(self._runtime_config_entry_from_preference(preference) for preference in preferences)
            entries.extend(self._runtime_config_entry_from_loop(loop) for loop in loops)

        entries.sort(key=lambda entry: (entry.category, entry.display_name, entry.target_key))
        if limit is not None:
            return entries[:limit]
        return entries

    def create_runtime_config_proposal(
        self,
        payload: RuntimeConfigProposalCreate | dict[str, Any],
    ) -> RuntimeConfigProposalSummary:
        request = RuntimeConfigProposalCreate.model_validate(payload)
        with self.session_factory() as session:
            proposal = self._create_runtime_config_proposal_record(session, request)
            session.commit()
            session.refresh(proposal)
            return self._runtime_config_proposal_summary(proposal)

    def get_runtime_config_proposal(self, proposal_id: str) -> RuntimeConfigProposalSummary:
        with self.session_factory() as session:
            proposal = session.get(RuntimeConfigProposalModel, proposal_id)
            if proposal is None:
                raise ValueError(f"Runtime config proposal not found: {proposal_id}")
            return self._runtime_config_proposal_summary(proposal)

    def list_runtime_config_proposals(
        self,
        *,
        statuses: Sequence[str] | None = None,
        limit: int | None = None,
    ) -> list[RuntimeConfigProposalSummary]:
        with self.session_factory() as session:
            query = select(RuntimeConfigProposalModel).order_by(RuntimeConfigProposalModel.created_at.desc())
            if statuses:
                query = query.where(RuntimeConfigProposalModel.status.in_(list(statuses)))
            if limit is not None:
                query = query.limit(limit)
            proposals = session.scalars(query).all()
            return [self._runtime_config_proposal_summary(proposal) for proposal in proposals]

    def apply_runtime_config_proposal(
        self,
        proposal_id: str,
        *,
        applied_by: str,
    ) -> RuntimeConfigRevisionSummary:
        with self.session_factory() as session:
            revision = self._apply_runtime_config_proposal(session, proposal_id, applied_by)
            session.commit()
            session.refresh(revision)
            return self._runtime_config_revision_summary(revision)

    def list_runtime_config_revisions(
        self,
        *,
        target_type: str | None = None,
        target_key: str | None = None,
        limit: int | None = None,
    ) -> list[RuntimeConfigRevisionSummary]:
        with self.session_factory() as session:
            query = select(RuntimeConfigRevisionModel).order_by(RuntimeConfigRevisionModel.applied_at.desc())
            if target_type:
                query = query.where(RuntimeConfigRevisionModel.target_type == target_type)
            if target_key:
                query = query.where(RuntimeConfigRevisionModel.target_key == target_key)
            if limit is not None:
                query = query.limit(limit)
            revisions = session.scalars(query).all()
            return [self._runtime_config_revision_summary(revision) for revision in revisions]

    def create_runtime_config_rollback_proposal(
        self,
        revision_id: str,
        *,
        requested_by: str,
        rationale: str | None = None,
    ) -> RuntimeConfigProposalSummary:
        with self.session_factory() as session:
            revision = session.get(RuntimeConfigRevisionModel, revision_id)
            if revision is None:
                raise ValueError(f"Runtime config revision not found: {revision_id}")
            proposal = self._create_runtime_config_proposal_record(
                session,
                RuntimeConfigProposalCreate(
                    target_type=revision.target_type,
                    target_key=revision.target_key,
                    requested_by=requested_by,
                    rationale=rationale or f"Rollback to revision {revision.id}.",
                    proposed_value_json=revision.previous_value_json,
                    change_summary=f"Rollback {revision.display_name} to revision {revision.id}.",
                    created_by=requested_by,
                    origin_type="runtime-config-rollback",
                    origin_id=revision.id,
                ),
            )
            session.commit()
            session.refresh(proposal)
            return self._runtime_config_proposal_summary(proposal)

    def list_provider_profiles(self) -> list[ProviderProfileSummary]:
        with self.session_factory() as session:
            providers = session.scalars(
                select(ProviderProfileModel).order_by(ProviderProfileModel.is_primary.desc(), ProviderProfileModel.updated_at.desc())
            ).all()
            return [self._provider_profile_summary(provider) for provider in providers]

    def list_source_health(self) -> list[SourceHealthSummary]:
        with self.session_factory() as session:
            sources = session.scalars(
                select(SourceHealthModel).order_by(SourceHealthModel.updated_at.desc())
            ).all()
            return [self._source_health_summary(source) for source in sources]

    def list_workflow_runs(
        self,
        *,
        limit: int = 20,
        families: Sequence[str] | None = None,
        statuses: Sequence[str] | None = None,
    ) -> list[WorkflowRunSummary]:
        with self.session_factory() as session:
            query = (
                select(WorkflowRunModel)
                .join(WorkflowDefinitionModel)
                .options(
                    selectinload(WorkflowRunModel.workflow_definition),
                    selectinload(WorkflowRunModel.events),
                )
                .order_by(WorkflowRunModel.started_at.desc())
            )
            if families:
                query = query.where(WorkflowDefinitionModel.family.in_(list(families)))
            if statuses:
                query = query.where(WorkflowRunModel.status.in_(list(statuses)))
            query = query.limit(limit)
            runs = session.scalars(query).unique().all()
            return [self._workflow_run_summary(run, run.workflow_definition.workflow_code) for run in runs]

    def list_supervisor_loops(
        self,
        *,
        enabled_only: bool = False,
        execution_modes: Sequence[str] | None = None,
    ) -> list[SupervisorLoopSummary]:
        with self.session_factory() as session:
            query = select(SupervisorLoopModel).order_by(
                SupervisorLoopModel.priority.asc(),
                SupervisorLoopModel.updated_at.desc(),
            )
            if enabled_only:
                query = query.where(SupervisorLoopModel.is_enabled.is_(True))
            if execution_modes:
                query = query.where(SupervisorLoopModel.execution_mode.in_(list(execution_modes)))
            loops = session.scalars(query).all()
            return [self._supervisor_loop_summary(loop) for loop in loops]

    def claim_due_supervisor_loops(
        self,
        *,
        limit: int = 3,
        now: datetime | None = None,
    ) -> list[SupervisorLoopSummary]:
        current_time = now or datetime.now(tz=UTC)
        with self.session_factory() as session:
            query = (
                select(SupervisorLoopModel)
                .where(
                    SupervisorLoopModel.is_enabled.is_(True),
                    SupervisorLoopModel.execution_mode == "active",
                    SupervisorLoopModel.next_due_at <= current_time,
                )
                .order_by(SupervisorLoopModel.priority.asc(), SupervisorLoopModel.next_due_at.asc())
                .limit(limit)
            )
            loops = session.scalars(query).all()
            for loop in loops:
                loop.last_status = "running"
                loop.last_started_at = current_time
                loop.last_error = None
            session.commit()
            return [self._supervisor_loop_summary(loop) for loop in loops]

    def complete_supervisor_loop(
        self,
        loop_key: str,
        *,
        status: str = "completed",
        error: str | None = None,
        now: datetime | None = None,
    ) -> SupervisorLoopSummary:
        current_time = now or datetime.now(tz=UTC)
        with self.session_factory() as session:
            loop = session.scalar(select(SupervisorLoopModel).where(SupervisorLoopModel.loop_key == loop_key))
            if loop is None:
                raise ValueError(f"Supervisor loop not found: {loop_key}")

            loop.last_status = status
            loop.last_error = error
            loop.last_completed_at = current_time
            loop.next_due_at = current_time + timedelta(seconds=loop.cadence_seconds)
            if status == "completed":
                loop.failure_streak = 0
            session.commit()
            session.refresh(loop)
            return self._supervisor_loop_summary(loop)

    def fail_supervisor_loop(
        self,
        loop_key: str,
        *,
        error: str,
        now: datetime | None = None,
    ) -> SupervisorLoopSummary:
        current_time = now or datetime.now(tz=UTC)
        with self.session_factory() as session:
            loop = session.scalar(select(SupervisorLoopModel).where(SupervisorLoopModel.loop_key == loop_key))
            if loop is None:
                raise ValueError(f"Supervisor loop not found: {loop_key}")

            loop.failure_streak += 1
            loop.last_status = "failed"
            loop.last_error = error
            loop.last_completed_at = current_time
            loop.next_due_at = current_time + timedelta(seconds=loop.cadence_seconds)
            if loop.failure_streak >= loop.max_failure_streak:
                loop.is_enabled = False
            session.commit()
            session.refresh(loop)
            return self._supervisor_loop_summary(loop)

    def decay_stale_sources(self, *, now: datetime | None = None) -> list[SourceHealthSummary]:
        current_time = now or datetime.now(tz=UTC)
        with self.session_factory() as session:
            sources = session.scalars(select(SourceHealthModel)).all()
            for source in sources:
                last_seen = source.last_validated_at or source.updated_at
                if last_seen.tzinfo is None:
                    last_seen = last_seen.replace(tzinfo=UTC)
                age_hours = max((current_time - last_seen).total_seconds() / 3600, 0)
                freshness_penalty = min(age_hours / 96, 0.5)
                trust_penalty = min(age_hours / 240, 0.2)
                source.freshness_score = max(round(source.freshness_score - freshness_penalty, 4), 0.0)
                source.trust_score = max(round(source.trust_score - trust_penalty, 4), 0.0)
                if source.freshness_score < 0.2:
                    source.health_status = "stale"
                elif source.freshness_score < 0.4:
                    source.health_status = "lagging"
                else:
                    source.health_status = "healthy"
                source.last_validated_at = current_time
            session.commit()
            return [self._source_health_summary(source) for source in sources]

    def start_workflow_run(
        self,
        *,
        workflow_code: str,
        owner_role: str,
        summary: str,
        goal_id: str | None = None,
        task_id: str | None = None,
        input_payload: dict[str, Any] | None = None,
        created_by: str = "workflow-runner",
    ) -> WorkflowRunSummary:
        with self.session_factory() as session:
            definition = self._require_workflow_definition(session, workflow_code)
            run = WorkflowRunModel(
                workflow_definition_id=definition.id,
                goal_id=goal_id,
                task_id=task_id,
                owner_role=owner_role,
                input_payload=input_payload or {},
                result_payload={},
                created_by=created_by,
                origin_type="workflow",
                origin_id=workflow_code,
                status="running",
            )
            session.add(run)
            session.flush()
            event = WorkflowEventModel(
                workflow_run_id=run.id,
                event_type="workflow.started",
                summary=summary,
                payload=input_payload or {},
                created_by=created_by,
                origin_type="workflow",
                origin_id=workflow_code,
                status="recorded",
            )
            session.add(event)
            session.commit()
            session.refresh(run)
            return self._workflow_run_summary(run, workflow_code)

    def append_workflow_event(
        self,
        workflow_run_id: str,
        *,
        event_type: str,
        summary: str,
        payload: dict[str, Any] | None = None,
        created_by: str = "workflow-runner",
    ) -> None:
        with self.session_factory() as session:
            event = WorkflowEventModel(
                workflow_run_id=workflow_run_id,
                event_type=event_type,
                summary=summary,
                payload=payload or {},
                created_by=created_by,
                origin_type="workflow-event",
                origin_id=workflow_run_id,
                status="recorded",
            )
            session.add(event)
            session.commit()

    def complete_workflow_run(
        self,
        workflow_run_id: str,
        *,
        result_payload: dict[str, Any] | None = None,
        status: str = "completed",
        created_by: str = "workflow-runner",
    ) -> None:
        with self.session_factory() as session:
            run = session.get(WorkflowRunModel, workflow_run_id)
            if run is None:
                raise ValueError(f"Workflow run not found: {workflow_run_id}")

            run.status = status
            run.result_payload = result_payload or {}
            run.ended_at = datetime.now(tz=UTC)

            event = WorkflowEventModel(
                workflow_run_id=workflow_run_id,
                event_type=f"workflow.{status}",
                summary=f"Workflow {status}.",
                payload=result_payload or {},
                created_by=created_by,
                origin_type="workflow-event",
                origin_id=workflow_run_id,
                status="recorded",
            )
            session.add(event)
            session.commit()

    def record_heartbeat(
        self,
        *,
        node_role: str,
        deployment_topology: str,
        mode: str,
        risk_state: str,
        summary_payload: dict[str, Any],
    ) -> None:
        with self.session_factory() as session:
            heartbeat = HeartbeatModel(
                node_role=node_role,
                deployment_topology=deployment_topology,
                mode=mode,
                risk_state=risk_state,
                summary_payload=summary_payload,
                created_by="workflow-runner",
                origin_type="heartbeat",
                origin_id=node_role,
                status="recorded",
            )
            session.add(heartbeat)
            session.commit()

    def get_runtime_snapshot(self) -> RuntimeSnapshot:
        with self.session_factory() as session:
            active_goals = self._scalar_count(
                session,
                select(func.count()).select_from(GoalModel).where(GoalModel.status == "active"),
            )
            open_incidents = self._scalar_count(
                session,
                select(func.count()).select_from(IncidentModel).where(
                    IncidentModel.status.in_(["open", "investigating", "mitigated"])
                ),
            )
            pending_approvals = self._scalar_count(
                session,
                select(func.count()).select_from(ApprovalRequestModel).where(
                    ApprovalRequestModel.decision_status == "pending"
                ),
            )
            active_overrides = self._scalar_count(
                session,
                select(func.count()).select_from(OperatorOverrideModel).where(OperatorOverrideModel.is_active.is_(True)),
            )
            active_codex_runs = self._scalar_count(
                session,
                select(func.count()).select_from(CodexRunModel).where(
                    CodexRunModel.status.in_(["queued", "booting", "running", "reviewing"])
                ),
            )
            last_heartbeat_at = session.scalar(
                select(func.max(HeartbeatModel.recorded_at)).select_from(HeartbeatModel)
            )

        return RuntimeSnapshot(
            active_goals=active_goals,
            open_incidents=open_incidents,
            pending_approvals=pending_approvals,
            active_overrides=active_overrides,
            active_codex_runs=active_codex_runs,
            last_heartbeat_at=last_heartbeat_at,
        )

    def _bootstrap_reference_data(self, session: Session, settings: Settings) -> None:
        current_time = datetime.now(tz=UTC)
        for policy_key, display_name, description, value_json, is_mutable in (
            (
                "mission_priority_order",
                "Mission Priority Order",
                "Canonical mission priority order for the autonomous system.",
                {"priority_order": MISSION_PRIORITY_ORDER},
                False,
            ),
            (
                "deployment_topology",
                "Deployment Topology",
                "Current configured deployment topology.",
                {
                    "node_role": settings.node_role,
                    "deployment_topology": settings.deployment_topology,
                    "operator_timezone": settings.operator_timezone,
                    "market_timezone": settings.market_timezone,
                },
                True,
            ),
            (
                "owner_language",
                "Owner Language",
                "Primary owner interaction language.",
                {"operator_language": settings.operator_language},
                True,
            ),
            (
                "heartbeat_runtime",
                "Heartbeat Runtime",
                "Heartbeat pacing and freshness expectations for the governance kernel.",
                {
                    "interval_seconds": settings.heartbeat_interval_seconds,
                    "stale_after_seconds": max(settings.heartbeat_interval_seconds * 15, 900),
                },
                True,
            ),
            (
                "codex_runtime",
                "Codex Runtime",
                "Primary Codex-compatible execution settings for autonomous implementation and review tasks.",
                {
                    "command": settings.codex_command,
                    "default_model": settings.codex_default_model,
                    "timeout_seconds": settings.codex_timeout_seconds,
                    "primary_model": settings.primary_model,
                    "fast_model": settings.fast_model,
                    "openai_base_url": settings.openai_base_url,
                    "relay_configured": bool(settings.openai_api_key),
                },
                True,
            ),
        ):
            existing = session.scalar(
                select(SystemPolicyModel).where(SystemPolicyModel.policy_key == policy_key)
            )
            if existing is None:
                session.add(
                    SystemPolicyModel(
                        policy_key=policy_key,
                        display_name=display_name,
                        description=description,
                        value_json=value_json,
                        is_mutable=is_mutable,
                        created_by="bootstrap",
                        origin_type="bootstrap",
                        origin_id=policy_key,
                        status="active",
                    )
                )

        for preference_key, display_name, scope, value_json, notes in (
            (
                "interaction_language",
                "Interaction Language",
                "owner",
                {"operator_language": settings.operator_language},
                "Primary language for owner-facing interactions.",
            ),
            (
                "discord_channels",
                "Discord Channels",
                "owner",
                {
                    "control_channel": settings.discord_control_channel,
                    "approvals_channel": settings.discord_approvals_channel,
                    "alerts_channel": settings.discord_alerts_channel,
                },
                "Bootstrap snapshot of the main Discord interaction channels.",
            ),
            (
                "discord_access",
                "Discord Access",
                "owner",
                {
                    "control_channel_id": settings.discord_control_channel_id,
                    "approvals_channel_id": settings.discord_approvals_channel_id,
                    "alerts_channel_id": settings.discord_alerts_channel_id,
                    "allowed_user_ids": settings.discord_allowed_user_ids,
                },
                "Bootstrap snapshot of Discord operator allowlists and channel IDs.",
            ),
        ):
            preference = session.scalar(
                select(OwnerPreferenceModel).where(OwnerPreferenceModel.preference_key == preference_key)
            )
            if preference is None:
                session.add(
                    OwnerPreferenceModel(
                        preference_key=preference_key,
                        scope=scope,
                        display_name=display_name,
                        value_json=value_json,
                        updated_by="bootstrap",
                        notes=notes,
                        created_by="bootstrap",
                        origin_type="bootstrap",
                        origin_id=preference_key,
                        status="active",
                    )
                )

        active_mode = session.scalar(
            select(AutonomyModeModel).where(AutonomyModeModel.is_active.is_(True))
        )
        if active_mode is None:
            session.add(
                AutonomyModeModel(
                    mode="A1",
                    rationale="Bootstrap default keeps the system in research automation until stronger controls land.",
                    activated_by="bootstrap",
                    created_by="bootstrap",
                    origin_type="bootstrap",
                    origin_id="A1",
                    status="active",
                    is_active=True,
                )
            )

        primary_provider = session.scalar(
            select(ProviderProfileModel).where(ProviderProfileModel.provider_key == "primary-relay")
        )
        if primary_provider is None:
            session.add(
                ProviderProfileModel(
                    provider_key="primary-relay",
                    display_name="Primary Relay",
                    base_url=settings.openai_base_url,
                    api_style="openai-compatible",
                    health_status="unknown",
                    is_primary=True,
                    capability_snapshot={
                        "primary_model": settings.primary_model,
                        "fast_model": settings.fast_model,
                        "codex_model": settings.codex_default_model,
                    },
                    created_by="bootstrap",
                    origin_type="bootstrap",
                    origin_id="provider-primary",
                    status="active",
                    )
                )

        allocation_policy = session.scalar(
            select(AllocationPolicyModel).where(
                AllocationPolicyModel.policy_key == settings.default_allocation_policy_key
            )
        )
        if allocation_policy is None:
            session.add(
                AllocationPolicyModel(
                    policy_key=settings.default_allocation_policy_key,
                    environment=settings.default_broker_environment,
                    scope="global",
                    provider_key=settings.default_broker_provider_key,
                    account_ref=settings.default_broker_account_ref,
                    max_strategy_notional_pct=0.05,
                    max_gross_exposure_pct=0.8,
                    max_open_positions=8,
                    max_open_orders=8,
                    allow_short=False,
                    allow_fractional=True,
                    notes="Bootstrap default allocation policy for paper trading and governed execution tests.",
                    created_by="bootstrap",
                    origin_type="bootstrap",
                    origin_id=settings.default_allocation_policy_key,
                    status="active",
                )
            )

        broker_capability = session.scalar(
            select(BrokerCapabilityModel).where(
                BrokerCapabilityModel.capability_key
                == f"{settings.default_broker_provider_key}:{settings.default_broker_adapter}:{settings.default_broker_environment}"
            )
        )
        if broker_capability is None:
            capability_defaults = broker_capability_defaults(
                settings.default_broker_adapter,
                settings.default_broker_environment,
            )
            session.add(
                BrokerCapabilityModel(
                    capability_key=f"{settings.default_broker_provider_key}:{settings.default_broker_adapter}:{settings.default_broker_environment}",
                    provider_key=settings.default_broker_provider_key,
                    broker_adapter=settings.default_broker_adapter,
                    account_ref=settings.default_broker_account_ref,
                    environment=settings.default_broker_environment,
                    account_mode=str(capability_defaults["account_mode"]),
                    supports_equities=bool(capability_defaults["supports_equities"]),
                    supports_etfs=bool(capability_defaults["supports_etfs"]),
                    supports_fractional=bool(capability_defaults["supports_fractional"]),
                    supports_short=bool(capability_defaults["supports_short"]),
                    supports_margin=bool(capability_defaults["supports_margin"]),
                    supports_options=bool(capability_defaults["supports_options"]),
                    supports_multi_leg_options=bool(capability_defaults["supports_multi_leg_options"]),
                    supports_option_exercise=bool(capability_defaults["supports_option_exercise"]),
                    supports_option_assignment_events=bool(capability_defaults["supports_option_assignment_events"]),
                    supports_live_trading=bool(capability_defaults["supports_live_trading"]),
                    supports_paper_trading=bool(capability_defaults["supports_paper_trading"]),
                    notes=str(capability_defaults["notes"]),
                    created_by="bootstrap",
                    origin_type="bootstrap",
                    origin_id=settings.default_broker_adapter,
                    status="active",
                )
            )

        for source_key, source_type in (
            ("official-docs", "official"),
            ("market-news", "news"),
            ("social-signal", "social"),
        ):
            source = session.scalar(select(SourceHealthModel).where(SourceHealthModel.source_key == source_key))
            if source is None:
                session.add(
                    SourceHealthModel(
                        source_key=source_key,
                        source_type=source_type,
                        health_status="unknown",
                        trust_score=0.5,
                        freshness_score=0.5,
                        notes="Bootstrap placeholder until learning mesh is implemented.",
                        created_by="bootstrap",
                        origin_type="bootstrap",
                        origin_id=source_key,
                        status="active",
                    )
                )

        for workflow in WORKFLOW_BOOTSTRAP:
            existing = session.scalar(
                select(WorkflowDefinitionModel).where(
                    WorkflowDefinitionModel.workflow_code == workflow["workflow_code"]
                )
            )
            if existing is None:
                session.add(
                    WorkflowDefinitionModel(
                        **workflow,
                        created_by="bootstrap",
                        origin_type="bootstrap",
                        origin_id=workflow["workflow_code"],
                        status="active",
                    )
                )

        for loop in SUPERVISOR_LOOP_BOOTSTRAP:
            existing_loop = session.scalar(
                select(SupervisorLoopModel).where(SupervisorLoopModel.loop_key == loop["loop_key"])
            )
            if existing_loop is None:
                session.add(
                    SupervisorLoopModel(
                        **loop,
                        next_due_at=current_time
                        if loop["execution_mode"] == "active" and loop["is_enabled"]
                        else current_time + timedelta(seconds=loop["cadence_seconds"]),
                        last_status="idle",
                        max_failure_streak=int(loop["stop_conditions"].get("max_failure_streak", 3)),
                        created_by="bootstrap",
                        origin_type="bootstrap",
                        origin_id=loop["loop_key"],
                        status="active",
                    )
                )

    def _require_workflow_definition(self, session: Session, workflow_code: str) -> WorkflowDefinitionModel:
        definition = session.scalar(
            select(WorkflowDefinitionModel).where(WorkflowDefinitionModel.workflow_code == workflow_code)
        )
        if definition is None:
            raise ValueError(f"Workflow definition not found: {workflow_code}")
        return definition

    def _goal_summary(self, goal: GoalModel) -> GoalSummary:
        return GoalSummary(
            id=goal.id,
            title=goal.title,
            description=goal.description,
            mission_domain=goal.mission_domain,
            status=goal.status,
            created_by=goal.created_by,
            created_at=goal.created_at,
        )

    def _incident_summary(self, incident: IncidentModel) -> IncidentSummary:
        return IncidentSummary(
            id=incident.id,
            title=incident.title,
            summary=incident.summary,
            severity=incident.severity,
            status=incident.status,
            created_at=incident.created_at,
        )

    def _approval_summary(self, approval: ApprovalRequestModel) -> ApprovalRequestSummary:
        return ApprovalRequestSummary(
            id=approval.id,
            approval_type=approval.approval_type,
            subject_type=approval.subject_type,
            subject_id=approval.subject_id,
            requested_by=approval.requested_by,
            risk_level=approval.risk_level,
            decision_status=approval.decision_status,
            created_at=approval.created_at,
        )

    def _approval_decision_summary(
        self,
        decision: ApprovalDecisionModel,
        approval_request_status: str,
        effect_summary: str | None,
    ) -> ApprovalDecisionSummary:
        return ApprovalDecisionSummary(
            id=decision.id,
            approval_request_id=decision.approval_request_id,
            decision=decision.decision,
            decided_by=decision.decided_by,
            decided_at=decision.decided_at,
            approval_request_status=approval_request_status,
            effect_summary=effect_summary,
        )

    def _override_summary(self, override: OperatorOverrideModel) -> OperatorOverrideSummary:
        return OperatorOverrideSummary(
            id=override.id,
            scope=override.scope,
            action=override.action,
            reason=override.reason,
            activated_by=override.activated_by,
            is_active=override.is_active,
            created_at=override.created_at,
        )

    def _owner_preference_summary(self, preference: OwnerPreferenceModel) -> OwnerPreferenceSummary:
        return OwnerPreferenceSummary(
            id=preference.id,
            preference_key=preference.preference_key,
            display_name=preference.display_name,
            scope=preference.scope,
            value_json=preference.value_json,
            updated_by=preference.updated_by,
            updated_at=preference.updated_at,
            notes=preference.notes,
        )

    def _runtime_config_entry_from_policy(self, policy: SystemPolicyModel) -> RuntimeConfigEntrySummary:
        metadata = SYSTEM_POLICY_METADATA.get(policy.policy_key, {})
        return RuntimeConfigEntrySummary(
            target_type="system_policy",
            target_key=policy.policy_key,
            display_name=policy.display_name,
            category=str(metadata.get("category", "system")),
            risk_level=str(metadata.get("risk_level", "R2")),
            is_mutable=bool(metadata.get("is_mutable", policy.is_mutable)),
            requires_restart=bool(metadata.get("requires_restart", False)),
            value_json=dict(policy.value_json or {}),
            updated_at=policy.updated_at,
            updated_by=policy.origin_id or policy.created_by,
        )

    def _runtime_config_entry_from_preference(self, preference: OwnerPreferenceModel) -> RuntimeConfigEntrySummary:
        metadata = OWNER_PREFERENCE_METADATA.get(preference.preference_key, {})
        return RuntimeConfigEntrySummary(
            target_type="owner_preference",
            target_key=preference.preference_key,
            display_name=preference.display_name,
            category=str(metadata.get("category", "owner-experience")),
            risk_level=str(metadata.get("risk_level", "R1")),
            is_mutable=bool(metadata.get("is_mutable", True)),
            requires_restart=bool(metadata.get("requires_restart", False)),
            value_json=dict(preference.value_json or {}),
            updated_at=preference.updated_at,
            updated_by=preference.updated_by,
        )

    def _runtime_config_entry_from_loop(self, loop: SupervisorLoopModel) -> RuntimeConfigEntrySummary:
        risk_level = "R4" if loop.domain == "trading" else ("R3" if loop.domain in {"governance", "evolution", "strategy"} else "R2")
        return RuntimeConfigEntrySummary(
            target_type="supervisor_loop",
            target_key=loop.loop_key,
            display_name=loop.display_name,
            category=loop.domain,
            risk_level=risk_level,
            is_mutable=True,
            requires_restart=False,
            value_json={
                "display_name": loop.display_name,
                "domain": loop.domain,
                "cadence_seconds": loop.cadence_seconds,
                "execution_mode": loop.execution_mode,
                "is_enabled": loop.is_enabled,
                "priority": loop.priority,
                "budget_scope": dict(loop.budget_scope or {}),
                "stop_conditions": dict(loop.stop_conditions or {}),
            },
            updated_at=loop.updated_at,
            updated_by=loop.origin_id or loop.created_by,
        )

    def _runtime_config_proposal_summary(
        self,
        proposal: RuntimeConfigProposalModel,
    ) -> RuntimeConfigProposalSummary:
        return RuntimeConfigProposalSummary(
            id=proposal.id,
            target_type=proposal.target_type,
            target_key=proposal.target_key,
            display_name=proposal.display_name,
            category=proposal.category,
            requested_by=proposal.requested_by,
            rationale=proposal.rationale,
            change_summary=proposal.change_summary,
            risk_level=proposal.risk_level,
            requires_approval=proposal.requires_approval,
            approval_request_id=proposal.approval_request_id,
            current_value_json=dict(proposal.current_value_json or {}),
            proposed_value_json=dict(proposal.proposed_value_json or {}),
            status=proposal.status,
            created_at=proposal.created_at,
        )

    def _runtime_config_revision_summary(
        self,
        revision: RuntimeConfigRevisionModel,
    ) -> RuntimeConfigRevisionSummary:
        return RuntimeConfigRevisionSummary(
            id=revision.id,
            proposal_id=revision.proposal_id,
            target_type=revision.target_type,
            target_key=revision.target_key,
            display_name=revision.display_name,
            change_summary=revision.change_summary,
            previous_value_json=dict(revision.previous_value_json or {}),
            applied_value_json=dict(revision.applied_value_json or {}),
            applied_by=revision.applied_by,
            applied_at=revision.applied_at,
        )

    def _resolve_runtime_config_target(
        self,
        session: Session,
        target_type: str,
        target_key: str,
    ) -> dict[str, Any]:
        if target_type == "system_policy":
            policy = session.scalar(
                select(SystemPolicyModel).where(SystemPolicyModel.policy_key == target_key)
            )
            if policy is None:
                raise ValueError(f"System policy not found: {target_key}")
            entry = self._runtime_config_entry_from_policy(policy)
            return {"record": policy, "entry": entry}

        if target_type == "owner_preference":
            preference = session.scalar(
                select(OwnerPreferenceModel).where(OwnerPreferenceModel.preference_key == target_key)
            )
            if preference is None:
                raise ValueError(f"Owner preference not found: {target_key}")
            entry = self._runtime_config_entry_from_preference(preference)
            return {"record": preference, "entry": entry}

        if target_type == "supervisor_loop":
            loop = session.scalar(
                select(SupervisorLoopModel).where(SupervisorLoopModel.loop_key == target_key)
            )
            if loop is None:
                raise ValueError(f"Supervisor loop not found: {target_key}")
            entry = self._runtime_config_entry_from_loop(loop)
            return {"record": loop, "entry": entry}

        raise ValueError(f"Unsupported runtime config target type: {target_type}")

    def _merge_runtime_config_value(
        self,
        current_value: dict[str, Any],
        patch_value: dict[str, Any],
    ) -> dict[str, Any]:
        merged = dict(current_value)
        for key, value in patch_value.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = {**merged[key], **value}
            else:
                merged[key] = value
        return merged

    def _evaluate_runtime_config_risk(
        self,
        *,
        target_type: str,
        target_key: str,
        category: str,
        current_value: dict[str, Any],
        proposed_value: dict[str, Any],
    ) -> tuple[str, bool]:
        if target_type == "system_policy":
            metadata = SYSTEM_POLICY_METADATA.get(target_key, {})
            risk_level = str(metadata.get("risk_level", "R2"))
            requires_approval = bool(target_key in {"deployment_topology", "codex_runtime"})
            if target_key == "heartbeat_runtime":
                interval_seconds = int(proposed_value.get("interval_seconds", current_value.get("interval_seconds", 60)))
                if interval_seconds < 15 or interval_seconds > 3600:
                    return ("R2", True)
            return (risk_level, requires_approval)

        if target_type == "owner_preference":
            metadata = OWNER_PREFERENCE_METADATA.get(target_key, {})
            risk_level = str(metadata.get("risk_level", "R1"))
            requires_approval = target_key == "discord_channels"
            return (risk_level, requires_approval)

        if target_type == "supervisor_loop":
            disable_requested = not bool(proposed_value.get("is_enabled", current_value.get("is_enabled", True)))
            cadence_changed = int(proposed_value.get("cadence_seconds", current_value.get("cadence_seconds", 0))) != int(
                current_value.get("cadence_seconds", 0)
            )
            execution_mode_changed = str(
                proposed_value.get("execution_mode", current_value.get("execution_mode", "active"))
            ) != str(current_value.get("execution_mode", "active"))

            if category == "trading":
                if disable_requested or execution_mode_changed:
                    return ("R4", True)
                if cadence_changed:
                    return ("R3", True)
                return ("R3", False)

            if category in {"governance", "evolution", "strategy"}:
                if disable_requested or execution_mode_changed:
                    return ("R3", True)
                if cadence_changed:
                    return ("R2", category == "governance")
                return ("R2", False)

            if disable_requested:
                return ("R2", False)
            return ("R1", False)

        return ("R2", False)

    def _build_runtime_config_change_summary(
        self,
        *,
        display_name: str,
        current_value: dict[str, Any],
        proposed_value: dict[str, Any],
    ) -> str:
        changed_fields = [
            key for key, value in proposed_value.items() if current_value.get(key) != value
        ]
        if not changed_fields:
            return f"Confirm {display_name} configuration."
        rendered_fields = ", ".join(changed_fields[:4])
        if len(changed_fields) > 4:
            rendered_fields = f"{rendered_fields}, ..."
        return f"Update {display_name}: {rendered_fields}."

    def _create_runtime_config_proposal_record(
        self,
        session: Session,
        request: RuntimeConfigProposalCreate,
    ) -> RuntimeConfigProposalModel:
        target = self._resolve_runtime_config_target(session, request.target_type, request.target_key)
        entry: RuntimeConfigEntrySummary = target["entry"]
        current_value = dict(entry.value_json or {})
        proposed_value = self._merge_runtime_config_value(current_value, request.proposed_value_json)
        if proposed_value == current_value:
            raise ValueError(f"Runtime config target `{request.target_key}` already matches the proposed value.")
        risk_level, requires_approval = self._evaluate_runtime_config_risk(
            target_type=request.target_type,
            target_key=request.target_key,
            category=entry.category,
            current_value=current_value,
            proposed_value=proposed_value,
        )
        proposal = RuntimeConfigProposalModel(
            target_type=request.target_type,
            target_key=request.target_key,
            display_name=entry.display_name,
            category=entry.category,
            requested_by=request.requested_by,
            rationale=request.rationale,
            change_summary=request.change_summary
            or self._build_runtime_config_change_summary(
                display_name=entry.display_name,
                current_value=current_value,
                proposed_value=proposed_value,
            ),
            risk_level=risk_level,
            requires_approval=requires_approval,
            current_value_json=current_value,
            proposed_value_json=proposed_value,
            created_by=request.created_by or request.requested_by,
            origin_type=request.origin_type,
            origin_id=request.origin_id,
            status="awaiting_approval" if requires_approval else request.status,
        )
        session.add(proposal)
        session.flush()

        if requires_approval:
            approval = ApprovalRequestModel(
                approval_type="runtime_config_change",
                subject_type="runtime_config",
                subject_id=f"{request.target_type}:{request.target_key}",
                requested_by=request.requested_by,
                risk_level=risk_level,
                rationale=request.rationale or proposal.change_summary,
                payload={
                    "config_proposal_id": proposal.id,
                    "target_type": request.target_type,
                    "target_key": request.target_key,
                    "display_name": entry.display_name,
                },
                created_by=request.created_by or request.requested_by,
                origin_type=request.origin_type,
                origin_id=request.origin_id,
                status="pending",
                decision_status="pending",
            )
            session.add(approval)
            session.flush()
            proposal.approval_request_id = approval.id

        return proposal

    def _apply_runtime_config_proposal(
        self,
        session: Session,
        proposal_id: str,
        applied_by: str,
        *,
        via_approval: bool = False,
    ) -> RuntimeConfigRevisionModel:
        proposal = session.get(RuntimeConfigProposalModel, proposal_id)
        if proposal is None:
            raise ValueError(f"Runtime config proposal not found: {proposal_id}")

        if proposal.status == "applied":
            revision = session.scalar(
                select(RuntimeConfigRevisionModel)
                .where(RuntimeConfigRevisionModel.proposal_id == proposal.id)
                .order_by(RuntimeConfigRevisionModel.applied_at.desc())
            )
            if revision is None:
                raise ValueError(f"Applied runtime config proposal is missing a revision record: {proposal_id}")
            return revision

        if proposal.requires_approval and proposal.approval_request_id and not via_approval:
            raise ValueError(f"Runtime config proposal requires approval before apply: {proposal_id}")

        if proposal.status not in {"proposed", "awaiting_approval"}:
            raise ValueError(f"Runtime config proposal is not applyable in status `{proposal.status}`.")

        target = self._resolve_runtime_config_target(session, proposal.target_type, proposal.target_key)
        entry: RuntimeConfigEntrySummary = target["entry"]
        record = target["record"]
        previous_value = dict(entry.value_json or {})
        applied_value = self._merge_runtime_config_value(previous_value, proposal.proposed_value_json)

        if proposal.target_type == "system_policy":
            record.value_json = applied_value
            record.origin_type = "runtime-config-proposal"
            record.origin_id = proposal.id
            record.status = "active"
        elif proposal.target_type == "owner_preference":
            record.value_json = applied_value
            record.updated_by = applied_by
            record.origin_type = "runtime-config-proposal"
            record.origin_id = proposal.id
            record.status = "active"
        elif proposal.target_type == "supervisor_loop":
            record.display_name = str(applied_value.get("display_name", record.display_name))
            record.cadence_seconds = int(applied_value.get("cadence_seconds", record.cadence_seconds))
            record.execution_mode = str(applied_value.get("execution_mode", record.execution_mode))
            record.is_enabled = bool(applied_value.get("is_enabled", record.is_enabled))
            record.budget_scope = dict(applied_value.get("budget_scope", record.budget_scope or {}))
            record.stop_conditions = dict(applied_value.get("stop_conditions", record.stop_conditions or {}))
            record.origin_type = "runtime-config-proposal"
            record.origin_id = proposal.id
            record.status = "active"
            if not record.is_enabled:
                record.last_status = "disabled"
                record.next_due_at = None
            elif record.next_due_at is None:
                record.next_due_at = datetime.now(tz=UTC) + timedelta(seconds=record.cadence_seconds)
        else:
            raise ValueError(f"Unsupported runtime config proposal target type: {proposal.target_type}")

        proposal.status = "applied"
        revision = RuntimeConfigRevisionModel(
            proposal_id=proposal.id,
            target_type=proposal.target_type,
            target_key=proposal.target_key,
            display_name=proposal.display_name,
            change_summary=proposal.change_summary,
            previous_value_json=previous_value,
            applied_value_json=applied_value,
            applied_by=applied_by,
            created_by=applied_by,
            origin_type="runtime-config-proposal",
            origin_id=proposal.id,
            status="applied",
        )
        session.add(revision)
        session.flush()
        return revision

    def _provider_profile_summary(self, provider: ProviderProfileModel) -> ProviderProfileSummary:
        return ProviderProfileSummary(
            provider_key=provider.provider_key,
            display_name=provider.display_name,
            health_status=provider.health_status,
            api_style=provider.api_style,
            is_primary=provider.is_primary,
            base_url=provider.base_url,
            capability_snapshot=provider.capability_snapshot,
            updated_at=provider.updated_at,
        )

    def _source_health_summary(self, source: SourceHealthModel) -> SourceHealthSummary:
        return SourceHealthSummary(
            source_key=source.source_key,
            source_type=source.source_type,
            health_status=source.health_status,
            trust_score=source.trust_score,
            freshness_score=source.freshness_score,
            last_validated_at=source.last_validated_at,
            notes=source.notes,
            updated_at=source.updated_at,
        )

    def _supervisor_loop_summary(self, loop: SupervisorLoopModel) -> SupervisorLoopSummary:
        return SupervisorLoopSummary(
            id=loop.id,
            loop_key=loop.loop_key,
            workflow_code=loop.workflow_code,
            domain=loop.domain,
            display_name=loop.display_name,
            handler_key=loop.handler_key,
            cadence_seconds=loop.cadence_seconds,
            priority=loop.priority,
            execution_mode=loop.execution_mode,
            is_enabled=loop.is_enabled,
            next_due_at=loop.next_due_at,
            last_started_at=loop.last_started_at,
            last_completed_at=loop.last_completed_at,
            last_status=loop.last_status,
            last_error=loop.last_error,
            failure_streak=loop.failure_streak,
            max_failure_streak=loop.max_failure_streak,
            budget_scope=loop.budget_scope,
            stop_conditions=loop.stop_conditions,
        )

    def _workflow_run_summary(self, run: WorkflowRunModel, workflow_code: str) -> WorkflowRunSummary:
        definition = run.workflow_definition
        latest_event = None
        if run.events:
            latest_event = max(run.events, key=lambda event: event.event_at)

        return WorkflowRunSummary(
            id=run.id,
            workflow_code=workflow_code,
            workflow_name=definition.name if definition is not None else workflow_code,
            workflow_family=definition.family if definition is not None else "unknown",
            owner_role=run.owner_role,
            status=run.status,
            started_at=run.started_at,
            ended_at=run.ended_at,
            latest_event_type=latest_event.event_type if latest_event is not None else None,
            latest_event_summary=latest_event.summary if latest_event is not None else None,
        )

    def _scalar_count(self, session: Session, query: Any) -> int:
        value = session.scalar(query)
        return int(value or 0)

    def _apply_approved_control_action(
        self,
        session: Session,
        approval: ApprovalRequestModel,
        decided_by: str,
    ) -> str:
        target_domain = str(approval.payload.get("target_domain") or approval.subject_id)

        if approval.approval_type in {"pause_trading", "pause_evolution"}:
            existing_override = session.scalar(
                select(OperatorOverrideModel).where(
                    OperatorOverrideModel.scope == target_domain,
                    OperatorOverrideModel.action == "pause",
                    OperatorOverrideModel.is_active.is_(True),
                )
            )
            if existing_override is None:
                session.add(
                    OperatorOverrideModel(
                        scope=target_domain,
                        action="pause",
                        reason=approval.rationale or f"Approved pause request for {target_domain}.",
                        activated_by=decided_by,
                        created_by=decided_by,
                        origin_type="approval",
                        origin_id=approval.id,
                        status="active",
                        is_active=True,
                    )
                )
            return f"Domain `{target_domain}` is now paused behind an active operator override."

        if approval.approval_type == "resume_domain":
            overrides = session.scalars(
                select(OperatorOverrideModel).where(
                    OperatorOverrideModel.scope == target_domain,
                    OperatorOverrideModel.is_active.is_(True),
                )
            ).all()
            for override in overrides:
                override.is_active = False
                override.status = "released"
            released_count = len(overrides)
            return (
                f"Domain `{target_domain}` resumed; released {released_count} active override(s)."
                if released_count
                else f"Domain `{target_domain}` had no active override to release."
            )

        if approval.approval_type == "runtime_config_change":
            proposal_id = str(approval.payload.get("config_proposal_id") or "")
            if not proposal_id:
                return "Runtime config approval was recorded, but no proposal id was attached."
            revision = self._apply_runtime_config_proposal(session, proposal_id, decided_by, via_approval=True)
            return (
                f"Applied runtime config change for `{revision.display_name}`."
                f" Revision `{revision.id}` is now the latest durable version."
            )

        return "Approval recorded without a runtime state mutation."
