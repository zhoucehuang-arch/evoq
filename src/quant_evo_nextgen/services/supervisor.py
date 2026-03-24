from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Callable
from uuid import uuid4

from sqlalchemy import select

from quant_evo_nextgen.config import Settings
from quant_evo_nextgen.contracts.state import SupervisorLoopSummary, WorkflowRunSummary
from quant_evo_nextgen.db.models import CodexRunModel
from quant_evo_nextgen.services.acquisition import AcquisitionStackService
from quant_evo_nextgen.services.codex_fabric import CodexFabricService
from quant_evo_nextgen.services.dashboard import DashboardService
from quant_evo_nextgen.services.evolution import EvolutionService
from quant_evo_nextgen.services.evolution_capability import EvolutionCapabilityService
from quant_evo_nextgen.services.execution import ExecutionService
from quant_evo_nextgen.services.learning import LearningService
from quant_evo_nextgen.services.state_store import StateStore
from quant_evo_nextgen.services.strategy_lab import StrategyLabService


logger = logging.getLogger("quant_evo_nextgen.supervisor")


@dataclass(slots=True)
class LoopExecutionResult:
    loop_key: str
    status: str
    workflow_run_id: str | None
    payload: dict[str, Any]


class SupervisorService:
    def __init__(
        self,
        *,
        state_store: StateStore,
        dashboard_service: DashboardService,
        settings: Settings,
        codex_fabric_service: CodexFabricService | None = None,
        learning_service: LearningService | None = None,
        strategy_service: StrategyLabService | None = None,
        execution_service: ExecutionService | None = None,
        evolution_service: EvolutionService | None = None,
    ) -> None:
        self.state_store = state_store
        self.dashboard_service = dashboard_service
        self.settings = settings
        self.codex_fabric_service = codex_fabric_service
        self.learning_service = learning_service
        self.strategy_service = strategy_service
        self.execution_service = execution_service
        self.evolution_service = evolution_service
        self.handlers: dict[str, Callable[[SupervisorLoopSummary, WorkflowRunSummary], dict[str, Any]]] = {
            "governance_heartbeat": self._governance_heartbeat,
            "source_revalidation": self._source_revalidation,
            "research_intake": self._research_intake,
            "research_distillation": self._research_distillation,
            "learning_synthesis": self._learning_synthesis,
            "market_session_guard": self._market_session_guard,
            "broker_state_sync": self._broker_state_sync,
            "strategy_evaluation": self._strategy_evaluation,
            "evolution_governance_sync": self._evolution_governance_sync,
            "capability_review": self._capability_review,
            "council_reflection": self._council_reflection,
            "owner_absence_watch": self._owner_absence_watch,
        }

    def _deployment_market_context(self) -> tuple[str, list[str]]:
        market_mode = (self.settings.deployment_market_mode or "us").strip().lower() or "us"
        if market_mode == "cn":
            return ("cn", ["cn_equities"])
        if market_mode == "us":
            return ("us", ["us_equities", "us_options"])
        return (market_mode, [])

    def run_due_loops(self, *, max_loops: int = 3) -> list[LoopExecutionResult]:
        results: list[LoopExecutionResult] = []
        loops = self.state_store.claim_due_supervisor_loops(limit=max_loops)
        for loop in loops:
            workflow_run_id: str | None = None
            try:
                run = self.state_store.start_workflow_run(
                    workflow_code=loop.workflow_code,
                    owner_role="supervisor",
                    summary=f"Running supervisor loop `{loop.loop_key}`.",
                    input_payload={
                        "loop_key": loop.loop_key,
                        "handler_key": loop.handler_key,
                        "domain": loop.domain,
                        "execution_mode": loop.execution_mode,
                    },
                    created_by="supervisor",
                )
                workflow_run_id = run.id
                handler = self.handlers.get(loop.handler_key)
                if handler is None:
                    payload = {
                        "loop_key": loop.loop_key,
                        "status": "skipped",
                        "reason": f"No handler registered for `{loop.handler_key}`.",
                    }
                    self.state_store.append_workflow_event(
                        run.id,
                        event_type="workflow.supervisor_skipped",
                        summary=payload["reason"],
                        payload=payload,
                        created_by="supervisor",
                    )
                    self.state_store.complete_workflow_run(
                        run.id,
                        result_payload=payload,
                        status="completed",
                        created_by="supervisor",
                    )
                    self.state_store.complete_supervisor_loop(loop.loop_key, status="completed")
                    results.append(
                        LoopExecutionResult(
                            loop_key=loop.loop_key,
                            status="skipped",
                            workflow_run_id=run.id,
                            payload=payload,
                        )
                    )
                    continue

                payload = handler(loop, run)
                self.state_store.append_workflow_event(
                    run.id,
                    event_type="workflow.supervisor_completed",
                    summary=f"Supervisor loop `{loop.loop_key}` finished successfully.",
                    payload=payload,
                    created_by="supervisor",
                )
                self.state_store.complete_workflow_run(
                    run.id,
                    result_payload=payload,
                    status="completed",
                    created_by="supervisor",
                )
                self.state_store.complete_supervisor_loop(loop.loop_key, status="completed")
                results.append(
                    LoopExecutionResult(
                        loop_key=loop.loop_key,
                        status="completed",
                        workflow_run_id=run.id,
                        payload=payload,
                    )
                )
            except Exception as exc:
                logger.exception("supervisor loop failed: %s", loop.loop_key)
                error_payload = {"loop_key": loop.loop_key, "error": str(exc)}
                if workflow_run_id is not None:
                    self.state_store.append_workflow_event(
                        workflow_run_id,
                        event_type="workflow.supervisor_failed",
                        summary=str(exc),
                        payload=error_payload,
                        created_by="supervisor",
                    )
                    self.state_store.complete_workflow_run(
                        workflow_run_id,
                        result_payload=error_payload,
                        status="failed",
                        created_by="supervisor",
                    )
                self.state_store.fail_supervisor_loop(loop.loop_key, error=str(exc))
                results.append(
                    LoopExecutionResult(
                        loop_key=loop.loop_key,
                        status="failed",
                        workflow_run_id=workflow_run_id,
                        payload=error_payload,
                    )
                )
        return results

    def _governance_heartbeat(
        self,
        _loop: SupervisorLoopSummary,
        _workflow_run: WorkflowRunSummary,
    ) -> dict[str, Any]:
        overview = self.dashboard_service.build_overview()
        payload = {
            "mode": overview.system.mode,
            "risk_state": overview.system.risk_state,
            "production_strategies": overview.strategy.production,
            "candidate_strategies": overview.strategy.candidates,
            "active_goals": overview.system.active_goals,
            "open_incidents": overview.system.open_incidents,
            "pending_approvals": overview.system.pending_approvals,
        }
        self.state_store.record_heartbeat(
            node_role=self.settings.node_role,
            deployment_topology=self.settings.deployment_topology,
            mode=overview.system.mode,
            risk_state=overview.system.risk_state,
            summary_payload=payload,
        )
        return payload

    def _source_revalidation(
        self,
        _loop: SupervisorLoopSummary,
        _workflow_run: WorkflowRunSummary,
    ) -> dict[str, Any]:
        sources = self.state_store.decay_stale_sources()
        status_counts: dict[str, int] = {}
        for source in sources:
            status_counts[source.health_status] = status_counts.get(source.health_status, 0) + 1
        return {
            "sources_checked": len(sources),
            "status_counts": status_counts,
        }

    def _research_intake(
        self,
        loop: SupervisorLoopSummary,
        workflow_run: WorkflowRunSummary,
    ) -> dict[str, Any]:
        overview = self.dashboard_service.build_overview()
        sources = self.state_store.list_source_health()
        healthy_sources = sum(1 for source in sources if source.health_status in {"healthy", "unknown"})
        acquisition_guidance = AcquisitionStackService(self.settings).prompt_guidance()
        market_mode, active_sleeves = self._deployment_market_context()
        sleeve_text = ", ".join(active_sleeves) if active_sleeves else "unconfigured"
        return self._queue_loop_codex_run(
            loop=loop,
            workflow_run=workflow_run,
            worker_class="analysis_worker",
            objective="Run a bounded research intake sweep and produce cited learning follow-ups for the autonomous investment system.",
            context_summary=(
                f"System mode={overview.system.mode}, risk_state={overview.system.risk_state}, "
                f"production_strategies={overview.strategy.production}, active_goals={overview.system.active_goals}, "
                f"healthy_or_unknown_sources={healthy_sources}/{len(sources)}, "
                f"deployment_market_mode={market_mode}, active_sleeves={sleeve_text}, "
                f"market_calendar={self.settings.market_calendar}, market_timezone={self.settings.market_timezone}."
            ),
            write_scope=["knowledge/", "memory/", "docs/next-gen/"],
            allowed_tools=["shell", "web"],
            search_enabled=True,
            risk_tier="R2",
            review_required=False,
            eval_required=True,
            acceptance_criteria=[
                "Use bounded web research with explicit citations.",
                "Identify learning items relevant to strategy, governance, relay/provider stability, or system operations.",
                "Do not modify production trading logic or governance controls.",
                "Leave clear follow-up tasks and risks if promotion should not happen yet.",
            ],
            prompt_appendix=(
                "Work as the research intake loop. Favor fresh, high-signal material over volume. "
                "Explicitly distinguish confirmed evidence from inference. "
                "If repository edits are unnecessary, keep the workspace read-light and return structured findings. "
                f"Current deployment target is `{market_mode}` with sleeves `{sleeve_text}`. "
                "Do not suggest instruments, brokers, or execution paths outside that deployment scope. "
                f"{acquisition_guidance}"
            ),
            citation_requirements=[
                "Cite every external claim that affects trading, system design, provider risk, or governance.",
            ],
        )

    def _market_session_guard(
        self,
        _loop: SupervisorLoopSummary,
        workflow_run: WorkflowRunSummary,
    ) -> dict[str, Any]:
        if self.execution_service is None:
            return {
                "status": "skipped",
                "reason": "Execution service is not configured on this supervisor node.",
                "workflow_run_id": workflow_run.id,
            }
        market_state = self.execution_service.synthesize_market_session_state(origin_id=workflow_run.id)
        return {
            "status": "completed",
            "workflow_run_id": workflow_run.id,
            "market_calendar": market_state.market_calendar,
            "session_label": market_state.session_label,
            "is_market_open": market_state.is_market_open,
            "trading_allowed": market_state.trading_allowed,
        }

    def _broker_state_sync(
        self,
        loop: SupervisorLoopSummary,
        workflow_run: WorkflowRunSummary,
    ) -> dict[str, Any]:
        if self.execution_service is None:
            return {
                "status": "skipped",
                "reason": "Execution service is not configured on this supervisor node.",
                "workflow_run_id": workflow_run.id,
            }
        if self.settings.default_broker_adapter == "paper_sim":
            return {
                "status": "skipped",
                "reason": "Default broker adapter is paper_sim, so external broker sync is not needed.",
                "workflow_run_id": workflow_run.id,
            }

        sync_run = self.execution_service.sync_broker_state(
            {
                "provider_key": self.settings.default_broker_provider_key,
                "account_ref": self.settings.default_broker_account_ref,
                "environment": self.settings.default_broker_environment,
                "broker_adapter": self.settings.default_broker_adapter,
                "full_sync": bool(loop.budget_scope.get("full_sync", True)),
                "created_by": "supervisor",
                "origin_type": "workflow",
                "origin_id": workflow_run.id,
            }
        )
        return {
            "status": "completed",
            "workflow_run_id": workflow_run.id,
            "sync_run_id": sync_run.id,
            "broker_adapter": sync_run.broker_adapter,
            "provider_key": sync_run.provider_key,
            "synced_orders_count": sync_run.synced_orders_count,
            "synced_positions_count": sync_run.synced_positions_count,
            "unmanaged_orders_count": sync_run.unmanaged_orders_count,
            "unmanaged_positions_count": sync_run.unmanaged_positions_count,
            "sync_status": sync_run.status,
        }

    def _strategy_evaluation(
        self,
        loop: SupervisorLoopSummary,
        workflow_run: WorkflowRunSummary,
    ) -> dict[str, Any]:
        overview = self.dashboard_service.build_overview()
        strategy_metrics = self.strategy_service.get_metrics() if self.strategy_service is not None else None
        market_mode, active_sleeves = self._deployment_market_context()
        sleeve_text = ", ".join(active_sleeves) if active_sleeves else "unconfigured"
        context_summary = (
            (
                f"Hypotheses={strategy_metrics.hypothesis_count}, specs={strategy_metrics.spec_count}, "
                f"paper_candidates={strategy_metrics.paper_candidate_count}, "
                f"paper_running={strategy_metrics.paper_running_count}, "
                f"live_candidates={strategy_metrics.live_candidate_count}, "
                f"production={strategy_metrics.production_count}, risk_state={overview.system.risk_state}, "
                f"codex_queue_depth={overview.system.codex_queue_depth}, "
                f"deployment_market_mode={market_mode}, active_sleeves={sleeve_text}, "
                f"market_calendar={self.settings.market_calendar}."
            )
            if strategy_metrics is not None
            else (
                f"Candidates={overview.strategy.candidates}, staging={overview.strategy.staging}, "
                f"production={overview.strategy.production}, risk_state={overview.system.risk_state}, "
                f"codex_queue_depth={overview.system.codex_queue_depth}, "
                f"deployment_market_mode={market_mode}, active_sleeves={sleeve_text}, "
                f"market_calendar={self.settings.market_calendar}."
            )
        )
        return self._queue_loop_codex_run(
            loop=loop,
            workflow_run=workflow_run,
            worker_class="strategy_worker",
            objective="Run a bounded strategy evaluation cycle and recommend the next governed research or validation actions.",
            context_summary=context_summary,
            write_scope=["strategies/", "trading/", "docs/next-gen/", "memory/"],
            allowed_tools=["shell"],
            search_enabled=False,
            risk_tier="R3",
            review_required=True,
            eval_required=True,
            acceptance_criteria=[
                "Do not change live trading authority or broker-facing paths.",
                "Evaluate strategy readiness, testing gaps, and promotion blockers.",
                "Reference durable hypothesis, spec, backtest, and paper-trading lifecycle state when available.",
                "Surface regression risk and explicit next actions for paper or further validation.",
                "Keep all recommendations governed and auditable.",
            ],
            prompt_appendix=(
                "This is a strategy evaluation loop, not a live-promotion path. "
                "Prefer objective readiness analysis, missing-test detection, and bounded improvement planning. "
                f"Current deployment target is `{market_mode}` with sleeves `{sleeve_text}`. "
                "Do not recommend instruments, broker paths, or promotions that fall outside that deployment scope."
            ),
        )

    def _research_distillation(
        self,
        loop: SupervisorLoopSummary,
        workflow_run: WorkflowRunSummary,
    ) -> dict[str, Any]:
        if self.learning_service is None:
            return {
                "status": "skipped",
                "reason": "Learning service is not configured on this supervisor node.",
                "workflow_run_id": workflow_run.id,
            }
        results = self.learning_service.ingest_completed_research_runs(
            limit=int(loop.budget_scope.get("max_documents_per_tick", 3))
        )
        ingested = [result for result in results if result.status == "ingested"]
        skipped = [result for result in results if result.status != "ingested"]
        if ingested:
            self.state_store.append_workflow_event(
                workflow_run.id,
                event_type="workflow.learning_ingested",
                summary=f"Ingested {len(ingested)} research document(s) into durable learning state.",
                payload={
                    "document_ids": [result.document_id for result in ingested if result.document_id],
                    "codex_run_ids": [result.codex_run_id for result in ingested],
                },
                created_by="supervisor",
            )
        return {
            "status": "completed",
            "workflow_run_id": workflow_run.id,
            "ingested_count": len(ingested),
            "skipped_count": len(skipped),
            "document_ids": [result.document_id for result in ingested if result.document_id],
        }

    def _learning_synthesis(
        self,
        loop: SupervisorLoopSummary,
        workflow_run: WorkflowRunSummary,
    ) -> dict[str, Any]:
        if self.learning_service is None:
            return {
                "status": "skipped",
                "reason": "Learning service is not configured on this supervisor node.",
                "workflow_run_id": workflow_run.id,
            }
        results = self.learning_service.synthesize_pending_insights(
            limit=int(loop.budget_scope.get("max_insights_per_tick", 3))
        )
        synthesized = [result for result in results if result.status == "synthesized"]
        quarantined = [result for result in results if result.status == "quarantined"]
        if synthesized or quarantined:
            self.state_store.append_workflow_event(
                workflow_run.id,
                event_type="workflow.learning_synthesized",
                summary=(
                    f"Synthesized {len(synthesized)} insight(s) and quarantined {len(quarantined)} insight(s)."
                ),
                payload={
                    "insight_ids": [result.insight_id for result in results if result.insight_id],
                    "quarantined_document_ids": [
                        result.document_id for result in quarantined if result.document_id
                    ],
                },
                created_by="supervisor",
            )
        return {
            "status": "completed",
            "workflow_run_id": workflow_run.id,
            "synthesized_count": len(synthesized),
            "quarantined_count": len(quarantined),
            "insight_ids": [result.insight_id for result in results if result.insight_id],
        }

    def _council_reflection(
        self,
        loop: SupervisorLoopSummary,
        workflow_run: WorkflowRunSummary,
    ) -> dict[str, Any]:
        overview = self.dashboard_service.build_overview()
        recent_workflows = self.state_store.list_workflow_runs(limit=6, families=("evolution", "strategy", "learning"))
        capability_review = EvolutionCapabilityService(
            state_store=self.state_store,
            learning_service=self.learning_service,
            strategy_service=self.strategy_service,
            execution_service=self.execution_service,
            evolution_service=self.evolution_service,
            codex_fabric_service=self.codex_fabric_service,
        ).build_review()
        return self._queue_loop_codex_run(
            loop=loop,
            workflow_run=workflow_run,
            worker_class="analysis_worker",
            objective="Run a bounded council reflection cycle and identify the highest-value next self-improvement action without changing the mission.",
            context_summary=(
                f"Mode={overview.system.mode}, risk_state={overview.system.risk_state}, "
                f"pending_approvals={overview.system.pending_approvals}, active_goals={overview.system.active_goals}, "
                f"recent_relevant_workflows={len(recent_workflows)}, "
                f"capability_score={capability_review.overall_score_pct}, stall_state={capability_review.stall_state}."
            ),
            write_scope=["docs/next-gen/", "memory/", "knowledge/"],
            allowed_tools=["shell", "web"],
            search_enabled=True,
            risk_tier="R2",
            review_required=True,
            eval_required=True,
            acceptance_criteria=[
                "Represent planner, skeptic, builder, guardian, and judge perspectives explicitly in the reasoning.",
                "Do not propose mission drift or uncontrolled autonomy expansion.",
                "Produce a bounded next action with clear risks, confidence, and follow-up tasks.",
                "Use citations for any external claims that materially shape the recommendation.",
            ],
            prompt_appendix=(
                "Simulate a governed council: include distinct planner, skeptic, builder, guardian, and judge viewpoints "
                "before reaching a final recommendation. Keep the loop bounded and efficiency-aware. "
                f"Prioritize these current gaps when relevant: {[gap.summary for gap in capability_review.capability_gaps[:4]]}"
            ),
            citation_requirements=[
                "Cite external evidence for any recommendation involving provider behavior, market structure, or external tooling.",
            ],
        )

    def _capability_review(
        self,
        loop: SupervisorLoopSummary,
        workflow_run: WorkflowRunSummary,
    ) -> dict[str, Any]:
        review = EvolutionCapabilityService(
            state_store=self.state_store,
            learning_service=self.learning_service,
            strategy_service=self.strategy_service,
            execution_service=self.execution_service,
            evolution_service=self.evolution_service,
            codex_fabric_service=self.codex_fabric_service,
        ).build_review()

        created_goal_id: str | None = None
        created_incident_id: str | None = None
        existing_recovery_goal = next(
            (
                goal
                for goal in self.state_store.list_goals(statuses=("active", "proposed"))
                if goal.title == "Evolution anti-stall recovery"
            ),
            None,
        )
        if review.stall_state in {"warning", "critical"} and existing_recovery_goal is None:
            goal = self.state_store.create_goal(
                {
                    "title": "Evolution anti-stall recovery",
                    "description": (
                        review.stall_summary
                        or "Capability review detected stalled self-improvement progress that needs bounded replanning."
                    ),
                    "mission_domain": "evolution",
                    "success_metrics": {
                        "target_stall_state": "healthy",
                        "target_capability_score": max(70, review.overall_score_pct + 10),
                    },
                    "failure_metrics": {"stall_state": review.stall_state},
                    "budget_scope": {"source_loop": "capability-review"},
                    "time_horizon": "72h",
                    "created_by": "supervisor",
                    "origin_type": "workflow",
                    "origin_id": workflow_run.id,
                    "status": "active",
                }
            )
            created_goal_id = goal.id

        if review.stall_state == "critical":
            existing_incident = next(
                (
                    incident
                    for incident in self.state_store.list_incidents(open_only=True, limit=20)
                    if incident.title == "Evolution anti-stall escalation"
                ),
                None,
            )
            if existing_incident is None:
                incident = self.state_store.create_incident(
                    {
                        "title": "Evolution anti-stall escalation",
                        "summary": review.stall_summary
                        or "Capability review detected repeated stalled or blocked self-improvement behavior.",
                        "severity": "SEV-2",
                        "created_by": "supervisor",
                        "origin_type": "workflow",
                        "origin_id": workflow_run.id,
                        "related_workflow_run_id": workflow_run.id,
                    }
                )
                created_incident_id = incident.id

        queue_result: dict[str, Any] | None = None
        if review.should_queue_replan:
            queue_result = self._queue_loop_codex_run(
                loop=loop,
                workflow_run=workflow_run,
                worker_class="analysis_worker",
                objective="Run a bounded Ralph-style anti-stall replanning cycle and produce the next governed recovery plan for the autonomous investment system.",
                context_summary=(
                    f"Capability_score={review.overall_score_pct}, stall_state={review.stall_state}, "
                    f"top_gaps={[gap.summary for gap in review.capability_gaps[:3]]}."
                ),
                write_scope=["docs/next-gen/", "memory/", "knowledge/"],
                allowed_tools=["shell", "web"],
                search_enabled=True,
                risk_tier="R2",
                review_required=True,
                eval_required=True,
                acceptance_criteria=[
                    "Use the mission priority order as a hard constraint.",
                    "Rank the top recovery actions by marginal utility, cost, and regression risk.",
                    "Do not propose uncontrolled autonomy expansion.",
                    "Leave a bounded recovery plan with explicit stop conditions and follow-up tasks.",
                ],
                prompt_appendix=(
                    "This is an anti-stall replanning run. Work in Ralph-style bounded outer-loop mode. "
                    f"Current capability gaps: {[gap.summary for gap in review.capability_gaps[:5]]}"
                ),
                citation_requirements=[
                    "Cite any external claim that materially changes the recovery plan.",
                ],
            )

        return {
            "status": "completed",
            "workflow_run_id": workflow_run.id,
            "overall_score_pct": review.overall_score_pct,
            "review_status": review.status,
            "stall_state": review.stall_state,
            "stall_summary": review.stall_summary,
            "capability_gaps": [gap.summary for gap in review.capability_gaps[:5]],
            "created_goal_id": created_goal_id,
            "created_incident_id": created_incident_id,
            "queued_replan": queue_result,
        }

    def _evolution_governance_sync(
        self,
        loop: SupervisorLoopSummary,
        workflow_run: WorkflowRunSummary,
    ) -> dict[str, Any]:
        if self.evolution_service is None:
            return {
                "status": "skipped",
                "reason": "Evolution service is not configured on this supervisor node.",
                "workflow_run_id": workflow_run.id,
            }

        with self.state_store.session_factory() as session:
            candidate_runs = session.scalars(
                select(CodexRunModel)
                .where(
                    CodexRunModel.status == "completed",
                    CodexRunModel.supervisor_loop_key.in_(["strategy-evaluation", "council-reflection"]),
                )
                .order_by(CodexRunModel.completed_at.desc(), CodexRunModel.queued_at.desc())
                .limit(int(loop.budget_scope.get("max_completed_codex_runs", 3)))
            ).all()

        created_proposals: list[str] = []
        skipped_runs: list[str] = []
        for run in candidate_runs:
            if self.evolution_service.find_proposal_by_codex_run_id(run.id) is not None:
                skipped_runs.append(run.id)
                continue

            structured = (run.result_payload or {}).get("structured_output") or {}
            if structured.get("outcome") != "completed":
                skipped_runs.append(run.id)
                continue

            proposal = self.evolution_service.create_improvement_proposal(
                self._proposal_payload_from_codex_run(run=run, structured=structured)
            )
            created_proposals.append(proposal.id)

        if created_proposals:
            self.state_store.append_workflow_event(
                workflow_run.id,
                event_type="workflow.evolution_proposals_created",
                summary=f"Created {len(created_proposals)} evolution proposal(s) from completed Codex runs.",
                payload={"proposal_ids": created_proposals},
                created_by="supervisor",
            )

        governance_tick = self.evolution_service.run_governance_tick(
            state_store=self.state_store,
            max_proposals=int(loop.budget_scope.get("max_governance_transitions", 5)),
            created_by="supervisor",
            origin_type="workflow",
            origin_id=workflow_run.id,
        )
        if governance_tick.created_canary_ids or governance_tick.created_decision_ids:
            self.state_store.append_workflow_event(
                workflow_run.id,
                event_type="workflow.evolution_governance_progressed",
                summary=(
                    "Auto-governance advanced evolution proposals through "
                    f"{len(governance_tick.created_canary_ids)} canary lane(s) and "
                    f"{len(governance_tick.created_decision_ids)} promotion decision(s)."
                ),
                payload={
                    "created_canary_ids": governance_tick.created_canary_ids,
                    "created_decision_ids": governance_tick.created_decision_ids,
                    "rollback_incident_ids": governance_tick.rollback_incident_ids,
                    "paused_domains": governance_tick.paused_domains,
                },
                created_by="supervisor",
            )

        return {
            "status": "completed",
            "workflow_run_id": workflow_run.id,
            "created_proposal_ids": created_proposals,
            "created_count": len(created_proposals),
            "skipped_run_ids": skipped_runs,
            "auto_canary_ids": governance_tick.created_canary_ids,
            "auto_decision_ids": governance_tick.created_decision_ids,
            "rollback_incident_ids": governance_tick.rollback_incident_ids,
            "paused_domains": governance_tick.paused_domains,
        }

    def _owner_absence_watch(
        self,
        _loop: SupervisorLoopSummary,
        workflow_run: WorkflowRunSummary,
    ) -> dict[str, Any]:
        preference = self.state_store.get_owner_preference("last_owner_interaction")
        now = datetime.now(tz=UTC)
        if preference is None:
            return {
                "status": "no_owner_signal",
                "workflow_run_id": workflow_run.id,
                "reason": "No owner interaction has been recorded yet.",
            }

        occurred_at_raw = preference.value_json.get("occurred_at")
        if not occurred_at_raw:
            return {
                "status": "invalid_owner_signal",
                "workflow_run_id": workflow_run.id,
                "reason": "Last owner interaction record is missing `occurred_at`.",
            }

        occurred_at = datetime.fromisoformat(str(occurred_at_raw))
        if occurred_at.tzinfo is None:
            occurred_at = occurred_at.replace(tzinfo=UTC)
        hours_absent = round((now - occurred_at).total_seconds() / 3600, 2)
        if hours_absent < 72:
            return {
                "status": "healthy",
                "workflow_run_id": workflow_run.id,
                "hours_absent": hours_absent,
            }

        active_overrides = self.state_store.list_operator_overrides(active_only=True)
        governed_domains = {(override.scope, override.action) for override in active_overrides}
        paused_domains: list[str] = []
        for domain in ("evolution", "trading"):
            if (domain, "pause") in governed_domains:
                continue
            self.state_store.create_operator_override(
                {
                    "scope": domain,
                    "action": "pause",
                    "reason": f"Owner absence watch triggered after {hours_absent} hours without control interaction.",
                    "activated_by": "supervisor",
                    "created_by": "supervisor",
                    "origin_type": "workflow",
                    "origin_id": workflow_run.id,
                }
            )
            paused_domains.append(domain)

        open_incidents = self.state_store.list_incidents(open_only=True, limit=20)
        existing_incident = next(
            (incident for incident in open_incidents if incident.title == "Owner absence safe-mode escalation"),
            None,
        )
        if existing_incident is not None:
            return {
                "status": "safe_mode_active",
                "workflow_run_id": workflow_run.id,
                "incident_id": existing_incident.id,
                "hours_absent": hours_absent,
                "paused_domains": paused_domains,
            }

        incident = self.state_store.create_incident(
            {
                "title": "Owner absence safe-mode escalation",
                "summary": (
                    f"The owner has been absent for {hours_absent} hours. "
                    f"Paused domains: {', '.join(paused_domains) if paused_domains else 'none newly paused'}."
                ),
                "severity": "SEV-2",
                "created_by": "supervisor",
                "origin_type": "workflow",
                "origin_id": workflow_run.id,
                "related_workflow_run_id": workflow_run.id,
            }
        )
        return {
            "status": "safe_mode_escalated",
            "workflow_run_id": workflow_run.id,
            "incident_id": incident.id,
            "hours_absent": hours_absent,
            "paused_domains": paused_domains,
        }

    def _queue_loop_codex_run(
        self,
        *,
        loop: SupervisorLoopSummary,
        workflow_run: WorkflowRunSummary,
        worker_class: str,
        objective: str,
        context_summary: str,
        write_scope: list[str],
        allowed_tools: list[str],
        search_enabled: bool,
        risk_tier: str,
        review_required: bool,
        eval_required: bool,
        acceptance_criteria: list[str],
        prompt_appendix: str | None = None,
        citation_requirements: list[str] | None = None,
    ) -> dict[str, Any]:
        if self.codex_fabric_service is None:
            return {
                "status": "skipped",
                "reason": "Codex Fabric service is not configured on this supervisor node.",
                "workflow_run_id": workflow_run.id,
            }
        if not self.settings.openai_api_key:
            return {
                "status": "skipped",
                "reason": "Codex execution is disabled because no OpenAI-compatible API key is configured.",
                "workflow_run_id": workflow_run.id,
            }

        existing_run = self.codex_fabric_service.find_active_run(supervisor_loop_key=loop.loop_key)
        if existing_run is not None:
            self.state_store.append_workflow_event(
                workflow_run.id,
                event_type="workflow.codex_deduped",
                summary=f"Skipped duplicate Codex run for loop `{loop.loop_key}` because `{existing_run.id}` is still active.",
                payload={"existing_codex_run_id": existing_run.id, "loop_key": loop.loop_key},
                created_by="supervisor",
            )
            return {
                "status": "skipped",
                "reason": "An active Codex run for this loop is already in progress.",
                "workflow_run_id": workflow_run.id,
                "existing_codex_run_id": existing_run.id,
            }

        runtime = self.state_store.get_runtime_snapshot()
        max_system_codex_runs = int(loop.budget_scope.get("max_system_codex_runs", 4))
        if runtime.active_codex_runs >= max_system_codex_runs:
            self.state_store.append_workflow_event(
                workflow_run.id,
                event_type="workflow.codex_backpressure",
                summary=f"Deferred Codex run for loop `{loop.loop_key}` because the Codex queue is saturated.",
                payload={
                    "loop_key": loop.loop_key,
                    "active_codex_runs": runtime.active_codex_runs,
                    "max_system_codex_runs": max_system_codex_runs,
                },
                created_by="supervisor",
            )
            return {
                "status": "deferred",
                "reason": "Codex queue is saturated.",
                "workflow_run_id": workflow_run.id,
                "active_codex_runs": runtime.active_codex_runs,
                "max_system_codex_runs": max_system_codex_runs,
            }

        max_duration_sec = int(loop.budget_scope.get("max_duration_seconds", self.settings.codex_timeout_seconds))
        codex_run = self.codex_fabric_service.queue_run(
            {
                "codex_run_id": str(uuid4()),
                "workflow_run_id": workflow_run.id,
                "supervisor_loop_key": loop.loop_key,
                "worker_class": worker_class,
                "objective": objective,
                "context_summary": context_summary,
                "repo_path": self.settings.resolved_repo_root,
                "workspace_path": self.settings.resolved_repo_root,
                "write_scope": write_scope,
                "allowed_tools": allowed_tools,
                "search_enabled": search_enabled,
                "risk_tier": risk_tier,
                "max_duration_sec": max_duration_sec,
                "max_token_budget": int(loop.budget_scope.get("max_token_budget", 120000)),
                "max_iterations": int(loop.budget_scope.get("max_iterations", 3)),
                "acceptance_criteria": acceptance_criteria,
                "prompt_appendix": prompt_appendix,
                "review_required": review_required,
                "eval_required": eval_required,
                "citation_requirements": citation_requirements or [],
            }
        )
        self.state_store.append_workflow_event(
            workflow_run.id,
            event_type="workflow.codex_queued",
            summary=f"Queued Codex run `{codex_run.id}` for supervisor loop `{loop.loop_key}`.",
            payload={
                "codex_run_id": codex_run.id,
                "loop_key": loop.loop_key,
                "worker_class": worker_class,
                "risk_tier": risk_tier,
                "search_enabled": search_enabled,
            },
            created_by="supervisor",
        )
        return {
            "status": "queued",
            "workflow_run_id": workflow_run.id,
            "codex_run_id": codex_run.id,
            "loop_key": loop.loop_key,
            "worker_class": worker_class,
        }

    def _proposal_payload_from_codex_run(
        self,
        *,
        run: CodexRunModel,
        structured: dict[str, Any],
    ) -> dict[str, Any]:
        target_surface = "strategy" if run.supervisor_loop_key == "strategy-evaluation" else "system"
        proposal_kind = "strategy_improvement" if target_surface == "strategy" else "system_improvement"
        confidence = structured.get("confidence")
        proposal_state = "ready_for_review" if isinstance(confidence, (int, float)) and confidence >= 0.7 else "candidate"
        risk_items = [str(item) for item in structured.get("risks_found", []) if item]
        tests_run = [str(item) for item in structured.get("tests_run", []) if item]
        test_results = [str(item) for item in structured.get("test_results", []) if item]

        return {
            "workflow_run_id": run.workflow_run_id,
            "codex_run_id": run.id,
            "title": (
                f"Governed proposal from {run.supervisor_loop_key or run.worker_class}: "
                f"{(run.objective or '').strip()[:120]}"
            ),
            "summary": structured.get("summary") or run.objective,
            "target_surface": target_surface,
            "proposal_kind": proposal_kind,
            "change_scope": list(structured.get("files_changed", []) or run.write_scope or []),
            "expected_benefit": {
                "confidence": confidence,
                "citations": len(structured.get("citations", [])),
                "source_loop": run.supervisor_loop_key,
            },
            "evaluation_summary": {
                "tests_run": tests_run,
                "test_results": test_results,
                "followup_tasks": list(structured.get("followup_tasks", [])),
            },
            "risk_summary": "; ".join(risk_items) if risk_items else "Supervisor-generated proposal pending explicit review.",
            "canary_plan": {
                "lane_type": "shadow",
                "environment": "paper",
                "traffic_pct": 5 if target_surface == "system" else 10,
                "source_loop": run.supervisor_loop_key,
            },
            "rollback_plan": {
                "action": "revert_governed_change",
                "source_codex_run_id": run.id,
                "source_workflow_run_id": run.workflow_run_id,
            },
            "objective_drift_checks": [
                "system survivability",
                "capital protection",
                "governance continuity",
            ],
            "proposal_state": proposal_state,
            "created_by": "supervisor",
            "origin_type": "supervisor-loop",
            "origin_id": run.supervisor_loop_key or run.id,
        }
