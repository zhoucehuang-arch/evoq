from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Callable, Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from quant_evo_nextgen.contracts.state import (
    EvolutionCanaryRunCreate,
    EvolutionCanaryRunSummary,
    EvolutionImprovementProposalCreate,
    EvolutionImprovementProposalSummary,
    EvolutionPromotionDecisionCreate,
    EvolutionPromotionDecisionSummary,
)
from quant_evo_nextgen.db.models import (
    EvolutionCanaryRunModel,
    EvolutionImprovementProposalModel,
    EvolutionPromotionDecisionModel,
)
from quant_evo_nextgen.services.state_store import StateStore


@dataclass(slots=True)
class EvolutionMetrics:
    proposal_count: int
    ready_for_review_count: int
    active_canary_count: int
    promoted_count: int
    rolled_back_count: int


@dataclass(slots=True)
class EvolutionGovernanceTickResult:
    processed_proposal_ids: list[str]
    created_canary_ids: list[str]
    created_decision_ids: list[str]
    rollback_incident_ids: list[str]
    paused_domains: list[str]
    skipped_proposal_ids: list[str]


class EvolutionService:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self.session_factory = session_factory

    def create_improvement_proposal(
        self,
        payload: EvolutionImprovementProposalCreate | dict[str, Any],
    ) -> EvolutionImprovementProposalSummary:
        request = EvolutionImprovementProposalCreate.model_validate(payload)
        with self.session_factory() as session:
            proposal = EvolutionImprovementProposalModel(
                goal_id=request.goal_id,
                workflow_run_id=request.workflow_run_id,
                codex_run_id=request.codex_run_id,
                title=request.title,
                summary=request.summary,
                target_surface=request.target_surface,
                proposal_kind=request.proposal_kind,
                change_scope=list(request.change_scope),
                expected_benefit=dict(request.expected_benefit),
                evaluation_summary=dict(request.evaluation_summary),
                risk_summary=request.risk_summary,
                canary_plan=dict(request.canary_plan),
                rollback_plan=dict(request.rollback_plan),
                objective_drift_checks=list(request.objective_drift_checks),
                proposal_state=request.proposal_state,
                created_by=request.created_by,
                origin_type=request.origin_type,
                origin_id=request.origin_id,
                status=request.status,
            )
            session.add(proposal)
            session.commit()
            session.refresh(proposal)
            return self._proposal_summary(proposal)

    def list_improvement_proposals(
        self,
        *,
        limit: int = 20,
        proposal_states: Sequence[str] | None = None,
    ) -> list[EvolutionImprovementProposalSummary]:
        with self.session_factory() as session:
            query = select(EvolutionImprovementProposalModel).order_by(
                EvolutionImprovementProposalModel.created_at.desc()
            )
            if proposal_states:
                query = query.where(EvolutionImprovementProposalModel.proposal_state.in_(list(proposal_states)))
            proposals = session.scalars(query.limit(limit)).all()
            return [self._proposal_summary(proposal) for proposal in proposals]

    def find_proposal_by_codex_run_id(self, codex_run_id: str) -> EvolutionImprovementProposalSummary | None:
        with self.session_factory() as session:
            proposal = session.scalar(
                select(EvolutionImprovementProposalModel).where(
                    EvolutionImprovementProposalModel.codex_run_id == codex_run_id
                )
            )
            return self._proposal_summary(proposal) if proposal is not None else None

    def record_canary_run(
        self,
        payload: EvolutionCanaryRunCreate | dict[str, Any],
    ) -> EvolutionCanaryRunSummary:
        request = EvolutionCanaryRunCreate.model_validate(payload)
        with self.session_factory() as session:
            proposal = session.get(EvolutionImprovementProposalModel, request.proposal_id)
            if proposal is None:
                raise ValueError(f"Evolution proposal not found: {request.proposal_id}")
            canary = EvolutionCanaryRunModel(
                proposal_id=request.proposal_id,
                lane_type=request.lane_type,
                environment=request.environment,
                traffic_pct=request.traffic_pct,
                success_metrics=dict(request.success_metrics),
                objective_drift_score=request.objective_drift_score,
                objective_drift_summary=request.objective_drift_summary,
                rollback_ready=request.rollback_ready,
                started_at=request.started_at,
                completed_at=request.completed_at,
                created_by=request.created_by,
                origin_type=request.origin_type,
                origin_id=request.origin_id,
                status=request.status,
            )
            proposal.proposal_state = self._proposal_state_from_canary(request)
            session.add(canary)
            session.commit()
            session.refresh(canary)
            return self._canary_summary(canary)

    def list_canary_runs(
        self,
        *,
        limit: int = 20,
        proposal_id: str | None = None,
    ) -> list[EvolutionCanaryRunSummary]:
        with self.session_factory() as session:
            query = select(EvolutionCanaryRunModel).order_by(EvolutionCanaryRunModel.created_at.desc())
            if proposal_id:
                query = query.where(EvolutionCanaryRunModel.proposal_id == proposal_id)
            runs = session.scalars(query.limit(limit)).all()
            return [self._canary_summary(run) for run in runs]

    def record_promotion_decision(
        self,
        payload: EvolutionPromotionDecisionCreate | dict[str, Any],
    ) -> EvolutionPromotionDecisionSummary:
        request = EvolutionPromotionDecisionCreate.model_validate(payload)
        with self.session_factory() as session:
            proposal = session.get(EvolutionImprovementProposalModel, request.proposal_id)
            if proposal is None:
                raise ValueError(f"Evolution proposal not found: {request.proposal_id}")
            decision = EvolutionPromotionDecisionModel(
                proposal_id=request.proposal_id,
                decision=request.decision,
                rationale=request.rationale,
                decided_by=request.decided_by,
                decision_payload=dict(request.decision_payload),
                created_by=request.created_by or request.decided_by,
                origin_type=request.origin_type,
                origin_id=request.origin_id,
                status=request.status,
            )
            proposal.proposal_state = self._proposal_state_from_decision(request.decision)
            session.add(decision)
            session.commit()
            session.refresh(decision)
            return self._promotion_summary(decision)

    def list_promotion_decisions(
        self,
        *,
        limit: int = 20,
        proposal_id: str | None = None,
    ) -> list[EvolutionPromotionDecisionSummary]:
        with self.session_factory() as session:
            query = select(EvolutionPromotionDecisionModel).order_by(
                EvolutionPromotionDecisionModel.decided_at.desc()
            )
            if proposal_id:
                query = query.where(EvolutionPromotionDecisionModel.proposal_id == proposal_id)
            decisions = session.scalars(query.limit(limit)).all()
            return [self._promotion_summary(decision) for decision in decisions]

    def get_metrics(self) -> EvolutionMetrics:
        with self.session_factory() as session:
            proposal_count = int(
                session.scalar(select(func.count()).select_from(EvolutionImprovementProposalModel)) or 0
            )
            ready_for_review_count = int(
                session.scalar(
                    select(func.count())
                    .select_from(EvolutionImprovementProposalModel)
                    .where(EvolutionImprovementProposalModel.proposal_state == "ready_for_review")
                )
                or 0
            )
            active_canary_count = int(
                session.scalar(
                    select(func.count())
                    .select_from(EvolutionCanaryRunModel)
                    .where(EvolutionCanaryRunModel.status.in_(["scheduled", "running"]))
                )
                or 0
            )
            promoted_count = int(
                session.scalar(
                    select(func.count())
                    .select_from(EvolutionImprovementProposalModel)
                    .where(EvolutionImprovementProposalModel.proposal_state == "promoted")
                )
                or 0
            )
            rolled_back_count = int(
                session.scalar(
                    select(func.count())
                    .select_from(EvolutionImprovementProposalModel)
                    .where(EvolutionImprovementProposalModel.proposal_state == "rolled_back")
                )
                or 0
            )
        return EvolutionMetrics(
            proposal_count=proposal_count,
            ready_for_review_count=ready_for_review_count,
            active_canary_count=active_canary_count,
            promoted_count=promoted_count,
            rolled_back_count=rolled_back_count,
        )

    def run_governance_tick(
        self,
        *,
        state_store: StateStore | None = None,
        max_proposals: int = 5,
        created_by: str = "supervisor",
        origin_type: str = "supervisor-loop",
        origin_id: str | None = None,
    ) -> EvolutionGovernanceTickResult:
        processed_proposal_ids: list[str] = []
        created_canary_ids: list[str] = []
        created_decision_ids: list[str] = []
        skipped_proposal_ids: list[str] = []
        rollback_queue: list[EvolutionImprovementProposalSummary] = []

        with self.session_factory() as session:
            proposals = session.scalars(
                select(EvolutionImprovementProposalModel)
                .where(
                    EvolutionImprovementProposalModel.proposal_state.in_(
                        [
                            "ready_for_review",
                            "shadow_passed",
                            "canary_passed",
                            "blocked",
                        ]
                    )
                )
                .order_by(EvolutionImprovementProposalModel.created_at.asc())
                .limit(max_proposals)
            ).all()

            for proposal in proposals:
                processed_proposal_ids.append(proposal.id)
                latest_canary = self._latest_canary_run(session, proposal.id)
                latest_decision = self._latest_promotion_decision(session, proposal.id)

                if proposal.proposal_state == "ready_for_review":
                    if latest_canary is not None:
                        skipped_proposal_ids.append(proposal.id)
                        continue
                    canary = self._create_auto_canary_run(
                        session,
                        proposal=proposal,
                        lane_type=self._initial_lane_type(proposal),
                        created_by=created_by,
                        origin_type=origin_type,
                        origin_id=origin_id,
                    )
                    created_canary_ids.append(canary.id)
                    continue

                if proposal.proposal_state == "shadow_passed":
                    follow_on_lane = self._follow_on_lane_type(proposal)
                    if follow_on_lane == "canary":
                        if self._has_lane_run(session, proposal.id, "canary"):
                            skipped_proposal_ids.append(proposal.id)
                            continue
                        canary = self._create_auto_canary_run(
                            session,
                            proposal=proposal,
                            lane_type="canary",
                            created_by=created_by,
                            origin_type=origin_type,
                            origin_id=origin_id,
                        )
                        created_canary_ids.append(canary.id)
                        continue
                    if latest_decision is None or latest_decision.decision != "shadow_approved":
                        decision = self._record_auto_promotion_decision(
                            session,
                            proposal=proposal,
                            decision="shadow_approved",
                            rationale="Auto-governance approved the shadow lane and found no need for a follow-on canary lane.",
                            decision_payload={"automation": "evolution-governance-tick", "lane_type": "shadow"},
                            created_by=created_by,
                            origin_type=origin_type,
                            origin_id=origin_id,
                        )
                        created_decision_ids.append(decision.id)
                        continue
                    skipped_proposal_ids.append(proposal.id)
                    continue

                if proposal.proposal_state == "canary_passed":
                    if latest_decision is None or latest_decision.decision != "promoted":
                        decision = self._record_auto_promotion_decision(
                            session,
                            proposal=proposal,
                            decision="promoted",
                            rationale="Auto-governance promoted the proposal after a passed canary lane and acceptable objective-drift score.",
                            decision_payload={"automation": "evolution-governance-tick", "lane_type": "canary"},
                            created_by=created_by,
                            origin_type=origin_type,
                            origin_id=origin_id,
                        )
                        created_decision_ids.append(decision.id)
                        continue
                    skipped_proposal_ids.append(proposal.id)
                    continue

                if proposal.proposal_state == "blocked":
                    if latest_canary is None or latest_canary.status not in {"failed", "rolled_back"}:
                        skipped_proposal_ids.append(proposal.id)
                        continue
                    if latest_decision is not None and latest_decision.decision == "rolled_back":
                        skipped_proposal_ids.append(proposal.id)
                        continue
                    decision = self._record_auto_promotion_decision(
                        session,
                        proposal=proposal,
                        decision="rolled_back",
                        rationale=(
                            "Auto-governance rolled back the proposal because the canary lane failed "
                            "or breached the objective-drift threshold."
                        ),
                        decision_payload={
                            "automation": "evolution-governance-tick",
                            "latest_canary_status": latest_canary.status,
                            "latest_canary_id": latest_canary.id,
                        },
                        created_by=created_by,
                        origin_type=origin_type,
                        origin_id=origin_id,
                    )
                    created_decision_ids.append(decision.id)
                    rollback_queue.append(self._proposal_summary(proposal))
                    continue

            session.commit()

        rollback_incident_ids: list[str] = []
        paused_domains: list[str] = []
        if state_store is not None:
            for proposal in rollback_queue:
                actuation = self._actuate_rollback(
                    state_store,
                    proposal=proposal,
                    created_by=created_by,
                    origin_type=origin_type,
                    origin_id=origin_id,
                )
                rollback_incident_ids.extend(actuation["incident_ids"])
                paused_domains.extend(actuation["paused_domains"])

        return EvolutionGovernanceTickResult(
            processed_proposal_ids=processed_proposal_ids,
            created_canary_ids=created_canary_ids,
            created_decision_ids=created_decision_ids,
            rollback_incident_ids=rollback_incident_ids,
            paused_domains=list(dict.fromkeys(paused_domains)),
            skipped_proposal_ids=skipped_proposal_ids,
        )

    def _proposal_summary(
        self,
        proposal: EvolutionImprovementProposalModel,
    ) -> EvolutionImprovementProposalSummary:
        return EvolutionImprovementProposalSummary(
            id=proposal.id,
            goal_id=proposal.goal_id,
            workflow_run_id=proposal.workflow_run_id,
            codex_run_id=proposal.codex_run_id,
            title=proposal.title,
            summary=proposal.summary,
            target_surface=proposal.target_surface,
            proposal_kind=proposal.proposal_kind,
            change_scope=list(proposal.change_scope or []),
            expected_benefit=dict(proposal.expected_benefit or {}),
            evaluation_summary=dict(proposal.evaluation_summary or {}),
            risk_summary=proposal.risk_summary,
            canary_plan=dict(proposal.canary_plan or {}),
            rollback_plan=dict(proposal.rollback_plan or {}),
            objective_drift_checks=list(proposal.objective_drift_checks or []),
            proposal_state=proposal.proposal_state,
            status=proposal.status,
            created_at=proposal.created_at,
        )

    def _canary_summary(self, run: EvolutionCanaryRunModel) -> EvolutionCanaryRunSummary:
        return EvolutionCanaryRunSummary(
            id=run.id,
            proposal_id=run.proposal_id,
            lane_type=run.lane_type,
            environment=run.environment,
            traffic_pct=run.traffic_pct,
            success_metrics=dict(run.success_metrics or {}),
            objective_drift_score=run.objective_drift_score,
            objective_drift_summary=run.objective_drift_summary,
            rollback_ready=run.rollback_ready,
            status=run.status,
            started_at=run.started_at,
            completed_at=run.completed_at,
            created_at=run.created_at,
        )

    def _promotion_summary(
        self,
        decision: EvolutionPromotionDecisionModel,
    ) -> EvolutionPromotionDecisionSummary:
        return EvolutionPromotionDecisionSummary(
            id=decision.id,
            proposal_id=decision.proposal_id,
            decision=decision.decision,
            rationale=decision.rationale,
            decided_by=decision.decided_by,
            decision_payload=dict(decision.decision_payload or {}),
            status=decision.status,
            decided_at=decision.decided_at,
            created_at=decision.created_at,
        )

    def _latest_canary_run(
        self,
        session: Session,
        proposal_id: str,
    ) -> EvolutionCanaryRunModel | None:
        return session.scalar(
            select(EvolutionCanaryRunModel)
            .where(EvolutionCanaryRunModel.proposal_id == proposal_id)
            .order_by(EvolutionCanaryRunModel.created_at.desc())
            .limit(1)
        )

    def _latest_promotion_decision(
        self,
        session: Session,
        proposal_id: str,
    ) -> EvolutionPromotionDecisionModel | None:
        return session.scalar(
            select(EvolutionPromotionDecisionModel)
            .where(EvolutionPromotionDecisionModel.proposal_id == proposal_id)
            .order_by(EvolutionPromotionDecisionModel.created_at.desc())
            .limit(1)
        )

    def _has_lane_run(
        self,
        session: Session,
        proposal_id: str,
        lane_type: str,
    ) -> bool:
        return bool(
            session.scalar(
                select(func.count())
                .select_from(EvolutionCanaryRunModel)
                .where(
                    EvolutionCanaryRunModel.proposal_id == proposal_id,
                    EvolutionCanaryRunModel.lane_type == lane_type,
                )
            )
            or 0
        )

    def _create_auto_canary_run(
        self,
        session: Session,
        *,
        proposal: EvolutionImprovementProposalModel,
        lane_type: str,
        created_by: str,
        origin_type: str,
        origin_id: str | None,
    ) -> EvolutionCanaryRunModel:
        evaluation = self._auto_canary_evaluation(proposal, lane_type=lane_type)
        current_time = datetime.now(tz=UTC)
        canary = EvolutionCanaryRunModel(
            proposal_id=proposal.id,
            lane_type=lane_type,
            environment=str(proposal.canary_plan.get("environment") or "paper"),
            traffic_pct=int(evaluation["traffic_pct"]),
            success_metrics=dict(evaluation["success_metrics"]),
            objective_drift_score=float(evaluation["objective_drift_score"]),
            objective_drift_summary=str(evaluation["objective_drift_summary"]),
            rollback_ready=bool(evaluation["rollback_ready"]),
            started_at=current_time,
            completed_at=current_time,
            created_by=created_by,
            origin_type=origin_type,
            origin_id=origin_id,
            status=str(evaluation["status"]),
        )
        proposal.proposal_state = self._proposal_state_from_canary_status(canary.status, lane_type)
        session.add(canary)
        session.flush()
        return canary

    def _record_auto_promotion_decision(
        self,
        session: Session,
        *,
        proposal: EvolutionImprovementProposalModel,
        decision: str,
        rationale: str,
        decision_payload: dict[str, Any],
        created_by: str,
        origin_type: str,
        origin_id: str | None,
    ) -> EvolutionPromotionDecisionModel:
        record = EvolutionPromotionDecisionModel(
            proposal_id=proposal.id,
            decision=decision,
            rationale=rationale,
            decided_by=created_by,
            decision_payload=decision_payload,
            created_by=created_by,
            origin_type=origin_type,
            origin_id=origin_id,
            status="recorded",
        )
        proposal.proposal_state = self._proposal_state_from_decision(decision)
        session.add(record)
        session.flush()
        return record

    def _initial_lane_type(self, proposal: EvolutionImprovementProposalModel) -> str:
        lane_type = str(proposal.canary_plan.get("lane_type") or "shadow").strip().lower()
        return lane_type if lane_type in {"shadow", "canary"} else "shadow"

    def _follow_on_lane_type(self, proposal: EvolutionImprovementProposalModel) -> str | None:
        configured = str(proposal.canary_plan.get("follow_on_lane_type") or "").strip().lower()
        if configured in {"shadow", "canary"}:
            return configured
        if self._initial_lane_type(proposal) == "shadow":
            return "canary"
        return None

    def _auto_canary_evaluation(
        self,
        proposal: EvolutionImprovementProposalModel,
        *,
        lane_type: str,
    ) -> dict[str, Any]:
        confidence = self._coerce_float(
            proposal.expected_benefit.get("confidence")
            or proposal.evaluation_summary.get("confidence")
        ) or 0.0
        objective_drift_score = self._objective_drift_score(proposal, lane_type=lane_type)
        max_objective_drift_score = self._coerce_float(
            proposal.canary_plan.get("max_objective_drift_score")
        ) or (0.12 if lane_type == "canary" else 0.18)
        min_confidence = self._coerce_float(proposal.canary_plan.get("min_confidence")) or (
            0.75 if lane_type == "canary" else 0.65
        )
        test_results = [str(item).strip().lower() for item in proposal.evaluation_summary.get("test_results", [])]
        failed_tests = [
            result for result in test_results if any(token in result for token in ("fail", "error", "timeout"))
        ]
        rollback_ready = bool(proposal.rollback_plan)
        traffic_pct = int(
            proposal.canary_plan.get(
                "canary_traffic_pct" if lane_type == "canary" else "traffic_pct",
                10 if lane_type == "canary" else 5,
            )
        )

        status = "passed"
        summary = f"{lane_type.title()} lane stayed within the current automated governance thresholds."
        if not rollback_ready:
            status = "failed"
            summary = "Rollback plan is missing, so the proposal cannot advance through unattended canary governance."
        elif failed_tests:
            status = "failed"
            summary = "Recorded evaluation results include failing checks, so the proposal cannot pass unattended canary governance."
        elif confidence < min_confidence:
            status = "failed"
            summary = "Recorded confidence is below the automated promotion floor for this lane."
        elif objective_drift_score > max_objective_drift_score:
            status = "failed"
            summary = "Objective-drift enforcement blocked the proposal because the inferred drift score exceeded the configured threshold."

        return {
            "status": status,
            "traffic_pct": max(1, traffic_pct),
            "rollback_ready": rollback_ready,
            "objective_drift_score": round(objective_drift_score, 4),
            "objective_drift_summary": summary,
            "success_metrics": {
                "confidence": round(confidence, 4),
                "failed_test_count": len(failed_tests),
                "citations": int(proposal.expected_benefit.get("citations", 0) or 0),
                "lane_type": lane_type,
            },
        }

    def _objective_drift_score(
        self,
        proposal: EvolutionImprovementProposalModel,
        *,
        lane_type: str,
    ) -> float:
        explicit_score = self._coerce_float(
            proposal.canary_plan.get("objective_drift_score")
            or proposal.evaluation_summary.get("objective_drift_score")
        )
        declared_checks = {str(item).strip().lower() for item in proposal.objective_drift_checks if str(item).strip()}
        required_checks = {"system survivability", "capital protection", "governance continuity"}
        missing_required = sum(1 for check in required_checks if check not in declared_checks)
        combined_text = " ".join(
            [
                proposal.summary or "",
                proposal.risk_summary or "",
                " ".join(str(item) for item in proposal.evaluation_summary.get("followup_tasks", [])),
            ]
        ).lower()
        risk_penalty = 0.0
        for keyword in (
            "mission drift",
            "objective drift",
            "owner alignment",
            "proxy metric",
            "unbounded autonomy",
            "regression risk",
        ):
            if keyword in combined_text:
                risk_penalty += 0.06
        base_score = (explicit_score if explicit_score is not None else 0.04 if lane_type == "shadow" else 0.06)
        return min(1.0, round(base_score + (missing_required * 0.08) + risk_penalty, 4))

    def _actuate_rollback(
        self,
        state_store: StateStore,
        *,
        proposal: EvolutionImprovementProposalSummary,
        created_by: str,
        origin_type: str,
        origin_id: str | None,
    ) -> dict[str, list[str]]:
        paused_domains: list[str] = []
        incident_ids: list[str] = []
        pause_domain = "trading" if proposal.target_surface in {"strategy", "trading"} else "evolution"
        active_overrides = state_store.list_operator_overrides(active_only=True)
        if not any(override.scope == pause_domain and override.action == "pause" for override in active_overrides):
            state_store.create_operator_override(
                {
                    "scope": pause_domain,
                    "action": "pause",
                    "reason": f"Auto rollback executed for evolution proposal `{proposal.id}`.",
                    "activated_by": created_by,
                    "created_by": created_by,
                    "origin_type": origin_type,
                    "origin_id": origin_id or proposal.id,
                }
            )
            paused_domains.append(pause_domain)

        title = f"Evolution rollback executed: {proposal.title[:96]}"
        open_incidents = state_store.list_incidents(open_only=True, limit=50)
        if not any(incident.title == title for incident in open_incidents):
            incident = state_store.create_incident(
                {
                    "title": title,
                    "summary": (
                        "An automated evolution rollback was executed because a governed shadow/canary lane "
                        "failed or exceeded the objective-drift threshold."
                    ),
                    "severity": "SEV-2",
                    "created_by": created_by,
                    "origin_type": origin_type,
                    "origin_id": origin_id or proposal.id,
                }
            )
            incident_ids.append(incident.id)

        return {"incident_ids": incident_ids, "paused_domains": paused_domains}

    def _coerce_float(self, value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _proposal_state_from_canary_status(self, status: str, lane_type: str) -> str:
        if status == "rolled_back":
            return "rolled_back"
        if status == "failed":
            return "blocked"
        if status == "passed":
            return f"{lane_type}_passed"
        return "shadowing" if lane_type == "shadow" else "canarying"

    def _proposal_state_from_canary(self, request: EvolutionCanaryRunCreate) -> str:
        return self._proposal_state_from_canary_status(request.status, request.lane_type)

    def _proposal_state_from_decision(self, decision: str) -> str:
        return {
            "approved": "approved",
            "rejected": "rejected",
            "shadow_approved": "shadow_approved",
            "canary_approved": "canary_approved",
            "promoted": "promoted",
            "rolled_back": "rolled_back",
        }[decision]
