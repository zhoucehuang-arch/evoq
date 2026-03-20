from __future__ import annotations

from datetime import UTC, datetime

from quant_evo_nextgen.contracts.dashboard import (
    AllocationPolicyCard,
    ApprovalCard,
    BacktestRunCard,
    BrokerAccountSnapshotCard,
    BrokerSyncRunCard,
    CapabilityGapCard,
    CapabilityScorecardCard,
    CodexRunCard,
    DashboardEvolution,
    DashboardIncidents,
    DashboardLearning,
    DashboardOverview,
    DashboardSystem,
    DashboardTrading,
    DomainControlState,
    EvolutionCanaryRunCard,
    EvolutionGovernanceMetrics,
    EvolutionPromotionDecisionCard,
    EvolutionProposalCard,
    ExecutionReadinessCard,
    FreshnessPayload,
    FreshnessState,
    IncidentCard,
    LearningDocumentCard,
    LearningGateMetrics,
    LearningInsightCard,
    LearningSummary,
    MarketSessionCard,
    OptionLifecycleEventCard,
    OrderIntentCard,
    OrderRecordCard,
    OwnerPreferenceCard,
    PaperRunCard,
    PositionCard,
    ProviderIncidentCard,
    ProviderProfileCard,
    ReconciliationRunCard,
    RuntimeConfigCard,
    RuntimeConfigProposalCard,
    RuntimeConfigRevisionCard,
    SourceHealthCard,
    ExpiringOptionPositionCard,
    StrategyLabMetrics as DashboardStrategyLabMetrics,
    StrategySpecCard,
    StrategySummary,
    SummaryCard,
    SupervisorLoopCard,
    SystemSummary,
    WorkflowRunCard,
)
from quant_evo_nextgen.services.codex_fabric import CodexFabricService
from quant_evo_nextgen.services.evolution import EvolutionService
from quant_evo_nextgen.services.evolution_capability import EvolutionCapabilityService
from quant_evo_nextgen.services.execution import ExecutionService
from quant_evo_nextgen.services.learning import LearningService
from quant_evo_nextgen.services.repo_state import RepoStateService
from quant_evo_nextgen.services.state_store import RuntimeSnapshot, StateStore
from quant_evo_nextgen.services.strategy_lab import StrategyLabService


class DashboardService:
    def __init__(
        self,
        repo_state_service: RepoStateService,
        state_store: StateStore | None = None,
        codex_fabric_service: CodexFabricService | None = None,
        learning_service: LearningService | None = None,
        strategy_service: StrategyLabService | None = None,
        execution_service: ExecutionService | None = None,
        evolution_service: EvolutionService | None = None,
    ) -> None:
        self.repo_state_service = repo_state_service
        self.state_store = state_store
        self.codex_fabric_service = codex_fabric_service
        self.learning_service = learning_service
        self.strategy_service = strategy_service
        self.execution_service = execution_service
        self.evolution_service = evolution_service

    def build_overview(self) -> DashboardOverview:
        snapshot = self.repo_state_service.collect()
        runtime = self.state_store.get_runtime_snapshot() if self.state_store is not None else _empty_runtime_snapshot()
        strategy_metrics = self.strategy_service.get_metrics() if self.strategy_service is not None else None

        candidate_count = snapshot.candidates
        staging_count = snapshot.staging
        production_count = snapshot.production
        if strategy_metrics is not None:
            candidate_count = max(
                candidate_count,
                strategy_metrics.paper_candidate_count + strategy_metrics.live_candidate_count,
            )
            staging_count = max(staging_count, strategy_metrics.paper_running_count)
            production_count = max(production_count, strategy_metrics.production_count)

        production_ready = production_count > 0
        mode = "paper_only" if not production_ready else "limited_live_ready"
        risk_state = "halted" if runtime.active_overrides > 0 else ("observe" if not production_ready else "normal")
        freshness_state, freshness_note = _compute_freshness(runtime)

        if runtime.active_overrides > 0:
            headline = "The system is operating under active manual governance. Review overrides and risk state first."
        elif not production_ready:
            headline = (
                "The core runtime is online, but capital-facing autonomy remains gated until governance and "
                "validation are stronger."
            )
        else:
            headline = "A governed production-ready strategy is present and the runtime is operating within control limits."

        highlights = [
            (
                f"Candidate strategies {candidate_count}, staging strategies {staging_count}, "
                f"production strategies {production_count}."
            ),
            f"Long-term principles {snapshot.principles}, causal memory records {snapshot.causal_cases}.",
            (
                f"Feature map cells occupied {snapshot.occupied_feature_cells}, "
                f"coverage {snapshot.feature_coverage_pct:.4f}%."
            ),
            (
                f"Active goals {runtime.active_goals}, open incidents {runtime.open_incidents}, "
                f"pending approvals {runtime.pending_approvals}."
            ),
        ]

        return DashboardOverview(
            generated_at=snapshot.generated_at,
            freshness=FreshnessPayload(
                state=freshness_state,
                age_seconds=_freshness_age_seconds(runtime),
                generated_at=snapshot.generated_at,
                note=freshness_note,
            ),
            headline=headline,
            summary_cards=[
                SummaryCard(
                    label="Production strategies",
                    value=str(production_count),
                    tone="good" if production_ready else "warn",
                    hint="Governed strategies currently marked production-ready.",
                ),
                SummaryCard(
                    label="Pending approvals",
                    value=str(runtime.pending_approvals),
                    tone="warn" if runtime.pending_approvals else "neutral",
                    hint="Owner confirmations still waiting in the control plane.",
                ),
                SummaryCard(
                    label="Principle memory",
                    value=str(snapshot.principles),
                    tone="neutral",
                    hint="Promoted long-term principle records.",
                ),
                SummaryCard(
                    label="Active overrides",
                    value=str(runtime.active_overrides),
                    tone="warn" if runtime.active_overrides else "good",
                    hint="Manual or approval-backed control overrides.",
                ),
            ],
            highlights=highlights,
            strategy=StrategySummary(
                candidates=candidate_count,
                staging=staging_count,
                production=production_count,
                active_production=production_ready,
            ),
            learning=LearningSummary(
                principles=snapshot.principles,
                causal_cases=snapshot.causal_cases,
                occupied_feature_cells=snapshot.occupied_feature_cells,
                feature_coverage_pct=snapshot.feature_coverage_pct,
                total_generations=snapshot.total_generations,
            ),
            system=SystemSummary(
                mode=mode,
                risk_state=risk_state,
                codex_queue_depth=runtime.active_codex_runs,
                active_goals=runtime.active_goals,
                open_incidents=runtime.open_incidents,
                pending_approvals=runtime.pending_approvals,
                active_overrides=runtime.active_overrides,
                repo_root=str(snapshot.repo_root),
            ),
        )

    def build_trading_view(self) -> DashboardTrading:
        overview = self.build_overview()
        approvals = self.state_store.list_approval_requests(pending_only=True) if self.state_store else []
        overrides = self.state_store.list_operator_overrides(active_only=True) if self.state_store else []
        domain_states = _build_domain_states(overrides=overrides, approvals=approvals, domains=("trading", "evolution"))
        strategy_metrics = self.strategy_service.get_metrics() if self.strategy_service else None
        recent_specs = self.strategy_service.list_strategy_specs(limit=6) if self.strategy_service else []
        recent_backtests = self.strategy_service.list_backtests(limit=6) if self.strategy_service else []
        recent_paper_runs = self.strategy_service.list_paper_runs(limit=6) if self.strategy_service else []
        execution_readiness = (
            self.execution_service.get_execution_readiness()
            if self.execution_service is not None
            else _empty_execution_readiness()
        )
        recent_market_sessions = (
            self.execution_service.list_market_session_states(limit=6)
            if self.execution_service is not None
            else []
        )
        recent_snapshots = (
            self.execution_service.list_broker_account_snapshots(limit=1)
            if self.execution_service is not None
            else []
        )
        recent_reconciliations = (
            self.execution_service.list_reconciliation_runs(limit=1)
            if self.execution_service is not None
            else []
        )
        recent_broker_syncs = (
            self.execution_service.list_broker_sync_runs(limit=1)
            if self.execution_service is not None
            else []
        )
        active_provider_incidents = (
            self.execution_service.list_provider_incidents(limit=6, open_only=True)
            if self.execution_service is not None
            else []
        )
        allocation_policies = (
            self.execution_service.list_allocation_policies(limit=1)
            if self.execution_service is not None
            else []
        )
        recent_order_intents = (
            self.execution_service.list_order_intents(limit=6)
            if self.execution_service is not None
            else []
        )
        recent_order_records = (
            self.execution_service.list_order_records(limit=6)
            if self.execution_service is not None
            else []
        )
        active_positions = (
            self.execution_service.list_positions(limit=6, active_only=True)
            if self.execution_service is not None
            else []
        )
        recent_option_events = (
            self.execution_service.list_option_lifecycle_events(limit=6)
            if self.execution_service is not None
            else []
        )
        expiring_option_positions = []
        if self.execution_service is not None:
            active_positions_all = self.execution_service.list_positions(limit=50, active_only=True)
            option_instruments = {
                instrument.instrument_key: instrument
                for instrument in self.execution_service.list_instrument_definitions(limit=200, instrument_type="option")
            }
            current_date = overview.generated_at.date()
            for position in active_positions_all:
                if position.asset_type != "option" or not position.instrument_key:
                    continue
                instrument = option_instruments.get(position.instrument_key)
                if instrument is None or instrument.expiration_date is None:
                    continue
                days_to_expiry = (instrument.expiration_date - current_date).days
                if days_to_expiry < 0 or days_to_expiry > 14:
                    continue
                expiring_option_positions.append(
                    ExpiringOptionPositionCard(
                        id=position.id,
                        strategy_spec_id=position.strategy_spec_id,
                        symbol=position.symbol,
                        underlying_symbol=position.underlying_symbol,
                        instrument_key=position.instrument_key,
                        quantity=position.quantity,
                        direction=position.direction,
                        expiration_date=instrument.expiration_date,
                        days_to_expiry=days_to_expiry,
                        market_price=position.market_price,
                        unrealized_pnl=position.unrealized_pnl,
                    )
                )
            expiring_option_positions.sort(key=lambda item: (item.days_to_expiry, item.symbol))
            expiring_option_positions = expiring_option_positions[:6]
        production_count = strategy_metrics.production_count if strategy_metrics is not None else overview.strategy.production

        strategy_highlight = (
            (
                f"Durable strategy lab: specs {strategy_metrics.spec_count}, paper-running "
                f"{strategy_metrics.paper_running_count}, live-candidate {strategy_metrics.live_candidate_count}."
            )
            if strategy_metrics is not None
            else "Durable strategy lifecycle data is not configured on this node yet."
        )
        readiness_highlight = (
            f"Execution is blocked: {execution_readiness.blocked_reasons[0]}"
            if execution_readiness.blocked_reasons
            else (
                f"Execution is degraded: {execution_readiness.warnings[0]}"
                if execution_readiness.warnings
                else "Execution readiness is clear across session, provider, and reconciliation gates."
            )
        )
        option_highlight = (
            f"{len(expiring_option_positions)} option positions expire within 14 days."
            if expiring_option_positions
            else (
                f"{sum(1 for event in recent_option_events if event.review_required)} option lifecycle events need review."
                if recent_option_events
                else "No near-dated option expiry pressure or recent option lifecycle events are visible right now."
            )
        )

        return DashboardTrading(
            generated_at=overview.generated_at,
            freshness=overview.freshness,
            strategy_lab=DashboardStrategyLabMetrics(
                hypothesis_count=strategy_metrics.hypothesis_count if strategy_metrics is not None else 0,
                spec_count=strategy_metrics.spec_count if strategy_metrics is not None else 0,
                paper_candidate_count=strategy_metrics.paper_candidate_count if strategy_metrics is not None else 0,
                paper_running_count=strategy_metrics.paper_running_count if strategy_metrics is not None else 0,
                live_candidate_count=strategy_metrics.live_candidate_count if strategy_metrics is not None else 0,
                production_count=production_count,
            ),
            execution_readiness=_execution_readiness_card(execution_readiness),
            summary_cards=[
                SummaryCard(
                    label="Execution readiness",
                    value=execution_readiness.status,
                    tone="good" if execution_readiness.status == "ready" else "warn",
                ),
                SummaryCard(
                    label="Trading allowed",
                    value="yes" if execution_readiness.trading_allowed else "no",
                    tone="good" if execution_readiness.trading_allowed else "warn",
                ),
                SummaryCard(
                    label="Active positions",
                    value=str(len(active_positions)),
                    tone="good" if active_positions else "neutral",
                ),
                SummaryCard(
                    label="Recent orders",
                    value=str(len(recent_order_records)),
                    tone="good" if recent_order_records else "neutral",
                ),
            ],
            highlights=[
                "Trading view prioritizes governed execution readiness over vanity PnL presentation.",
                readiness_highlight,
                strategy_highlight,
                option_highlight,
            ],
            allocation_policy=(
                _allocation_policy_card(allocation_policies[0]) if allocation_policies else None
            ),
            domain_states=domain_states,
            latest_account_snapshot=(
                _account_snapshot_card(recent_snapshots[0]) if recent_snapshots else None
            ),
            latest_reconciliation=(
                _reconciliation_card(recent_reconciliations[0]) if recent_reconciliations else None
            ),
            latest_broker_sync=(
                _broker_sync_card(recent_broker_syncs[0]) if recent_broker_syncs else None
            ),
            recent_market_sessions=[_market_session_card(session_state) for session_state in recent_market_sessions],
            active_provider_incidents=[
                _provider_incident_card(provider_incident) for provider_incident in active_provider_incidents
            ],
            recent_order_intents=[_order_intent_card(order_intent) for order_intent in recent_order_intents],
            recent_order_records=[_order_record_card(order_record) for order_record in recent_order_records],
            active_positions=[_position_card(position) for position in active_positions],
            expiring_option_positions=expiring_option_positions,
            recent_option_events=[
                _option_lifecycle_event_card(option_event) for option_event in recent_option_events
            ],
            recent_specs=[_strategy_spec_card(spec) for spec in recent_specs],
            recent_backtests=[_backtest_run_card(backtest) for backtest in recent_backtests],
            recent_paper_runs=[_paper_run_card(paper_run) for paper_run in recent_paper_runs],
        )

    def build_learning_view(self) -> DashboardLearning:
        overview = self.build_overview()
        sources = self.state_store.list_source_health() if self.state_store else []
        loops = self.state_store.list_supervisor_loops() if self.state_store else []
        documents = self.learning_service.list_documents(limit=6) if self.learning_service else []
        insights = self.learning_service.list_insights(limit=6) if self.learning_service else []
        metrics = self.learning_service.get_learning_metrics() if self.learning_service else None
        learning_loops = [loop for loop in loops if loop.domain == "learning"]
        ready_insight_count = metrics.ready_insight_count if metrics is not None else 0
        quarantined_insight_count = metrics.quarantined_insight_count if metrics is not None else 0
        insight_count = metrics.insight_count if metrics is not None else len(insights)

        return DashboardLearning(
            generated_at=overview.generated_at,
            freshness=overview.freshness,
            metrics=LearningGateMetrics(
                document_count=metrics.document_count if metrics is not None else len(documents),
                insight_count=insight_count,
                ready_insight_count=ready_insight_count,
                quarantined_insight_count=quarantined_insight_count,
            ),
            summary_cards=[
                SummaryCard(label="Principle memory", value=str(overview.learning.principles), tone="neutral"),
                SummaryCard(
                    label="Research documents",
                    value=str(metrics.document_count if metrics is not None else len(documents)),
                    tone="good" if documents else "warn",
                ),
                SummaryCard(
                    label="Insight candidates",
                    value=str(insight_count),
                    tone="good" if insight_count else "warn",
                ),
                SummaryCard(
                    label="Quarantined insights",
                    value=str(quarantined_insight_count),
                    tone="warn" if quarantined_insight_count else "good",
                ),
            ],
            highlights=[
                "Learning runs through quarantine, synthesis, and promotion gates before long-term memory is touched.",
                "When source freshness decays, trust is reduced before the system treats new material as actionable.",
                (
                    f"{ready_insight_count} insight candidates are ready for review."
                    if ready_insight_count
                    else "No insight candidates are ready for review yet."
                ),
                (
                    f"{quarantined_insight_count} insight candidates are currently quarantined."
                    if quarantined_insight_count
                    else "No insight candidates are quarantined right now."
                ),
            ],
            sources=[_source_card(source) for source in sources],
            recent_documents=[_learning_document_card(document) for document in documents],
            recent_insights=[_learning_insight_card(insight) for insight in insights],
            supervisor_loops=[_loop_card(loop) for loop in learning_loops],
        )

    def build_evolution_view(self) -> DashboardEvolution:
        overview = self.build_overview()
        loops = self.state_store.list_supervisor_loops() if self.state_store else []
        recent_workflows = self.state_store.list_workflow_runs(limit=8, families=("evolution", "strategy")) if self.state_store else []
        codex_runs = self.codex_fabric_service.list_runs(limit=8) if self.codex_fabric_service else []
        evolution_metrics = self.evolution_service.get_metrics() if self.evolution_service is not None else None
        recent_proposals = self.evolution_service.list_improvement_proposals(limit=6) if self.evolution_service else []
        recent_canary_runs = self.evolution_service.list_canary_runs(limit=6) if self.evolution_service else []
        recent_promotion_decisions = (
            self.evolution_service.list_promotion_decisions(limit=6) if self.evolution_service else []
        )
        evolution_loops = [loop for loop in loops if loop.domain in {"evolution", "strategy"}]
        capability_review = (
            EvolutionCapabilityService(
                state_store=self.state_store,
                learning_service=self.learning_service,
                strategy_service=self.strategy_service,
                execution_service=self.execution_service,
                evolution_service=self.evolution_service,
                codex_fabric_service=self.codex_fabric_service,
            ).build_review()
            if self.state_store is not None
            else None
        )

        return DashboardEvolution(
            generated_at=overview.generated_at,
            freshness=overview.freshness,
            metrics=EvolutionGovernanceMetrics(
                proposal_count=evolution_metrics.proposal_count if evolution_metrics is not None else 0,
                ready_for_review_count=evolution_metrics.ready_for_review_count if evolution_metrics is not None else 0,
                active_canary_count=evolution_metrics.active_canary_count if evolution_metrics is not None else 0,
                promoted_count=evolution_metrics.promoted_count if evolution_metrics is not None else 0,
                rolled_back_count=evolution_metrics.rolled_back_count if evolution_metrics is not None else 0,
            ),
            summary_cards=[
                SummaryCard(label="Codex queue", value=str(overview.system.codex_queue_depth), tone="neutral"),
                SummaryCard(
                    label="Pending changes",
                    value=str(overview.system.pending_approvals),
                    tone="warn" if overview.system.pending_approvals else "neutral",
                ),
                SummaryCard(
                    label="Active loops",
                    value=str(
                        sum(
                            1
                            for loop in evolution_loops
                            if loop.is_enabled and loop.execution_mode == "active"
                        )
                    ),
                    tone="good" if evolution_loops else "warn",
                ),
                SummaryCard(
                    label="Production strategies",
                    value=str(overview.strategy.production),
                    tone="good" if overview.strategy.production else "warn",
                ),
                SummaryCard(
                    label="Capability score",
                    value=str(capability_review.overall_score_pct if capability_review is not None else 0),
                    tone=(
                        "good"
                        if capability_review is not None and capability_review.status == "ok"
                        else "warn"
                    ),
                ),
            ],
            highlights=[
                "Evolution must flow through workflow, review, and evaluation gates before higher-authority environments are touched.",
                "Multi-agent debate belongs inside bounded council loops with explicit budget and exit criteria.",
                (
                    f"Improvement proposals {evolution_metrics.proposal_count}, active canary lanes "
                    f"{evolution_metrics.active_canary_count}, promoted changes {evolution_metrics.promoted_count}."
                    if evolution_metrics is not None
                    else "Evolution governance records are not available on this node yet."
                ),
                (
                    capability_review.stall_summary
                    if capability_review is not None and capability_review.stall_summary
                    else "Capability scorecards track where self-improvement is strong, weak, or stalled."
                ),
            ],
            capability_scorecards=[
                _capability_scorecard_card(item)
                for item in (capability_review.scorecards if capability_review is not None else [])
            ],
            capability_gaps=[
                _capability_gap_card(item)
                for item in (capability_review.capability_gaps if capability_review is not None else [])
            ],
            stall_state=capability_review.stall_state if capability_review is not None else "healthy",
            stall_summary=capability_review.stall_summary if capability_review is not None else None,
            recent_proposals=[_evolution_proposal_card(item) for item in recent_proposals],
            recent_canary_runs=[_evolution_canary_run_card(item) for item in recent_canary_runs],
            recent_promotion_decisions=[
                _evolution_promotion_decision_card(item) for item in recent_promotion_decisions
            ],
            recent_workflows=[_workflow_card(run) for run in recent_workflows],
            recent_codex_runs=[_codex_run_card(run) for run in codex_runs],
            supervisor_loops=[_loop_card(loop) for loop in evolution_loops],
        )

    def build_system_view(self) -> DashboardSystem:
        overview = self.build_overview()
        providers = self.state_store.list_provider_profiles() if self.state_store else []
        loops = self.state_store.list_supervisor_loops() if self.state_store else []
        recent_workflows = self.state_store.list_workflow_runs(limit=10) if self.state_store else []
        codex_runs = self.codex_fabric_service.list_runs(limit=10) if self.codex_fabric_service else []
        runtime_config = self.state_store.list_runtime_config_entries(limit=10) if self.state_store else []
        config_proposals = (
            self.state_store.list_runtime_config_proposals(statuses=("proposed", "awaiting_approval"), limit=8)
            if self.state_store
            else []
        )
        config_revisions = self.state_store.list_runtime_config_revisions(limit=8) if self.state_store else []
        owner_preferences = self.state_store.list_owner_preferences(limit=6) if self.state_store else []

        return DashboardSystem(
            generated_at=overview.generated_at,
            freshness=overview.freshness,
            summary_cards=[
                SummaryCard(
                    label="Freshness",
                    value=overview.freshness.state.value,
                    tone="good" if overview.freshness.state == FreshnessState.FRESH else "warn",
                ),
                SummaryCard(
                    label="Active loops",
                    value=str(sum(1 for loop in loops if loop.is_enabled and loop.execution_mode == "active")),
                    tone="good" if loops else "warn",
                ),
                SummaryCard(
                    label="Providers",
                    value=str(len(providers)),
                    tone="good" if providers else "warn",
                ),
                SummaryCard(
                    label="Config proposals",
                    value=str(len(config_proposals)),
                    tone="warn" if config_proposals else "good",
                ),
                SummaryCard(
                    label="Open incidents",
                    value=str(overview.system.open_incidents),
                    tone="warn" if overview.system.open_incidents else "good",
                ),
            ],
            highlights=[
                "System view exposes authority-core observability instead of raw worker chatter.",
                "If freshness is not fresh, the dashboard should show that risk directly instead of pretending the state is real-time.",
                "Runtime config is durable, proposal-driven, and approval-backed for risky changes.",
            ],
            providers=[_provider_card(provider) for provider in providers],
            supervisor_loops=[_loop_card(loop) for loop in loops],
            recent_workflows=[_workflow_card(run) for run in recent_workflows],
            recent_codex_runs=[_codex_run_card(run) for run in codex_runs],
            runtime_config=[_runtime_config_card(entry) for entry in runtime_config],
            pending_config_proposals=[_runtime_config_proposal_card(proposal) for proposal in config_proposals],
            recent_config_revisions=[_runtime_config_revision_card(revision) for revision in config_revisions],
            owner_preferences=[_owner_preference_card(preference) for preference in owner_preferences],
        )

    def build_incidents_view(self) -> DashboardIncidents:
        overview = self.build_overview()
        active_incidents = self.state_store.list_incidents(open_only=True, limit=10) if self.state_store else []
        recent_incidents = self.state_store.list_incidents(limit=10) if self.state_store else []
        approvals = self.state_store.list_approval_requests(pending_only=True, limit=10) if self.state_store else []

        return DashboardIncidents(
            generated_at=overview.generated_at,
            freshness=overview.freshness,
            summary_cards=[
                SummaryCard(
                    label="Open incidents",
                    value=str(len(active_incidents)),
                    tone="warn" if active_incidents else "good",
                ),
                SummaryCard(
                    label="Pending approvals",
                    value=str(len(approvals)),
                    tone="warn" if approvals else "neutral",
                ),
                SummaryCard(
                    label="Risk state",
                    value=overview.system.risk_state,
                    tone="warn" if overview.system.risk_state != "normal" else "good",
                ),
                SummaryCard(
                    label="Active overrides",
                    value=str(overview.system.active_overrides),
                    tone="warn" if overview.system.active_overrides else "good",
                ),
            ],
            highlights=[
                "Incident view helps the owner decide whether intervention is needed, not just count alarms.",
                "Approval backlog is itself a governance signal and should be reviewed alongside incidents.",
            ],
            active_incidents=[_incident_card(incident) for incident in active_incidents],
            recent_incidents=[_incident_card(incident) for incident in recent_incidents],
            pending_approvals=[_approval_card(approval) for approval in approvals],
        )


def _empty_runtime_snapshot() -> RuntimeSnapshot:
    return RuntimeSnapshot(
        active_goals=0,
        open_incidents=0,
        pending_approvals=0,
        active_overrides=0,
        active_codex_runs=0,
        last_heartbeat_at=None,
    )


def _compute_freshness(runtime: RuntimeSnapshot) -> tuple[FreshnessState, str]:
    if runtime.last_heartbeat_at is None:
        return (
            FreshnessState.LAGGING,
            "Database state is available, but no persisted heartbeat has been recorded yet.",
        )

    age_seconds = _freshness_age_seconds(runtime)
    if age_seconds <= 180:
        return (FreshnessState.FRESH, "Payload combines repository bootstrap state with live database counts.")
    if age_seconds <= 900:
        return (FreshnessState.LAGGING, "Database heartbeat is delayed; check supervisor runner health.")
    return (FreshnessState.STALE, "Database heartbeat is stale; treat control-plane status cautiously.")


def _freshness_age_seconds(runtime: RuntimeSnapshot) -> int:
    if runtime.last_heartbeat_at is None:
        return 0
    heartbeat_at = runtime.last_heartbeat_at
    if heartbeat_at.tzinfo is None:
        heartbeat_at = heartbeat_at.replace(tzinfo=UTC)
    return int((snapshot_now() - heartbeat_at).total_seconds())


def _build_domain_states(*, overrides, approvals, domains: tuple[str, ...]) -> list[DomainControlState]:
    states: list[DomainControlState] = []
    for domain in domains:
        domain_overrides = [override for override in overrides if override.scope == domain and override.is_active]
        domain_approvals = [approval for approval in approvals if approval.subject_id == domain]
        states.append(
            DomainControlState(
                domain=domain,
                is_paused=any(override.action == "pause" for override in domain_overrides),
                pending_approval_count=len(domain_approvals),
                override_count=len(domain_overrides),
                latest_reason=domain_overrides[0].reason if domain_overrides else None,
            )
        )
    return states


def _approval_card(approval) -> ApprovalCard:
    return ApprovalCard(
        id=approval.id,
        approval_type=approval.approval_type,
        subject_id=approval.subject_id,
        requested_by=approval.requested_by,
        risk_level=approval.risk_level,
        decision_status=approval.decision_status,
        created_at=approval.created_at,
    )


def _workflow_card(run) -> WorkflowRunCard:
    return WorkflowRunCard(
        id=run.id,
        workflow_code=run.workflow_code,
        workflow_name=run.workflow_name,
        workflow_family=run.workflow_family,
        owner_role=run.owner_role,
        status=run.status,
        started_at=run.started_at,
        ended_at=run.ended_at,
        latest_event_summary=run.latest_event_summary,
    )


def _codex_run_card(run) -> CodexRunCard:
    return CodexRunCard(
        id=run.id,
        status=run.status,
        worker_class=run.worker_class,
        execution_mode=run.execution_mode,
        strategy_mode=run.strategy_mode,
        objective=run.objective,
        current_attempt=run.current_attempt,
        max_iterations=run.max_iterations,
        queued_at=run.queued_at,
        completed_at=run.completed_at,
        last_error=run.last_error,
    )


def _source_card(source) -> SourceHealthCard:
    return SourceHealthCard(
        source_key=source.source_key,
        source_type=source.source_type,
        health_status=source.health_status,
        trust_score=source.trust_score,
        freshness_score=source.freshness_score,
        last_validated_at=source.last_validated_at,
        notes=source.notes,
    )


def _learning_document_card(document) -> LearningDocumentCard:
    return LearningDocumentCard(
        id=document.id,
        codex_run_id=document.codex_run_id,
        workflow_run_id=document.workflow_run_id,
        source_key=document.source_key,
        title=document.title,
        summary=document.summary,
        status=document.status,
        source_type=document.source_type,
        supervisor_loop_key=document.supervisor_loop_key,
        citation_count=document.citation_count,
        evidence_count=document.evidence_count,
        confidence=document.confidence,
        created_at=document.created_at,
    )


def _learning_insight_card(insight) -> LearningInsightCard:
    return LearningInsightCard(
        id=insight.id,
        document_id=insight.document_id,
        codex_run_id=insight.codex_run_id,
        workflow_run_id=insight.workflow_run_id,
        supervisor_loop_key=insight.supervisor_loop_key,
        topic_key=insight.topic_key,
        title=insight.title,
        summary=insight.summary,
        status=insight.status,
        promotion_state=insight.promotion_state,
        evidence_count=insight.evidence_count,
        citation_count=insight.citation_count,
        confidence=insight.confidence,
        quarantine_reason=insight.quarantine_reason,
        created_at=insight.created_at,
    )


def _provider_card(provider) -> ProviderProfileCard:
    return ProviderProfileCard(
        provider_key=provider.provider_key,
        display_name=provider.display_name,
        health_status=provider.health_status,
        api_style=provider.api_style,
        is_primary=provider.is_primary,
        base_url=provider.base_url,
    )


def _loop_card(loop) -> SupervisorLoopCard:
    return SupervisorLoopCard(
        loop_key=loop.loop_key,
        workflow_code=loop.workflow_code,
        domain=loop.domain,
        display_name=loop.display_name,
        execution_mode=loop.execution_mode,
        is_enabled=loop.is_enabled,
        cadence_seconds=loop.cadence_seconds,
        next_due_at=loop.next_due_at,
        last_completed_at=loop.last_completed_at,
        last_status=loop.last_status,
        failure_streak=loop.failure_streak,
        last_error=loop.last_error,
    )


def _incident_card(incident) -> IncidentCard:
    return IncidentCard(
        id=incident.id,
        title=incident.title,
        summary=incident.summary,
        severity=incident.severity,
        status=incident.status,
        created_at=incident.created_at,
    )


def _owner_preference_card(preference) -> OwnerPreferenceCard:
    return OwnerPreferenceCard(
        preference_key=preference.preference_key,
        display_name=preference.display_name,
        scope=preference.scope,
        updated_by=preference.updated_by,
        updated_at=preference.updated_at,
        value_json=preference.value_json,
    )


def _runtime_config_card(entry) -> RuntimeConfigCard:
    return RuntimeConfigCard(
        target_type=entry.target_type,
        target_key=entry.target_key,
        display_name=entry.display_name,
        category=entry.category,
        risk_level=entry.risk_level,
        is_mutable=entry.is_mutable,
        requires_restart=entry.requires_restart,
        updated_at=entry.updated_at,
        updated_by=entry.updated_by,
        value_json=entry.value_json,
    )


def _runtime_config_proposal_card(proposal) -> RuntimeConfigProposalCard:
    return RuntimeConfigProposalCard(
        id=proposal.id,
        target_type=proposal.target_type,
        target_key=proposal.target_key,
        display_name=proposal.display_name,
        category=proposal.category,
        requested_by=proposal.requested_by,
        change_summary=proposal.change_summary,
        risk_level=proposal.risk_level,
        requires_approval=proposal.requires_approval,
        approval_request_id=proposal.approval_request_id,
        status=proposal.status,
        created_at=proposal.created_at,
    )


def _runtime_config_revision_card(revision) -> RuntimeConfigRevisionCard:
    return RuntimeConfigRevisionCard(
        id=revision.id,
        target_type=revision.target_type,
        target_key=revision.target_key,
        display_name=revision.display_name,
        change_summary=revision.change_summary,
        applied_by=revision.applied_by,
        applied_at=revision.applied_at,
    )


def _evolution_proposal_card(proposal) -> EvolutionProposalCard:
    return EvolutionProposalCard(
        id=proposal.id,
        title=proposal.title,
        target_surface=proposal.target_surface,
        proposal_kind=proposal.proposal_kind,
        proposal_state=proposal.proposal_state,
        risk_summary=proposal.risk_summary,
        codex_run_id=proposal.codex_run_id,
        workflow_run_id=proposal.workflow_run_id,
        created_at=proposal.created_at,
    )


def _evolution_canary_run_card(run) -> EvolutionCanaryRunCard:
    return EvolutionCanaryRunCard(
        id=run.id,
        proposal_id=run.proposal_id,
        lane_type=run.lane_type,
        environment=run.environment,
        traffic_pct=run.traffic_pct,
        objective_drift_score=run.objective_drift_score,
        rollback_ready=run.rollback_ready,
        status=run.status,
        completed_at=run.completed_at,
        created_at=run.created_at,
    )


def _evolution_promotion_decision_card(decision) -> EvolutionPromotionDecisionCard:
    return EvolutionPromotionDecisionCard(
        id=decision.id,
        proposal_id=decision.proposal_id,
        decision=decision.decision,
        decided_by=decision.decided_by,
        rationale=decision.rationale,
        decided_at=decision.decided_at,
    )


def _capability_scorecard_card(scorecard) -> CapabilityScorecardCard:
    return CapabilityScorecardCard(
        capability_key=scorecard.capability_key,
        label=scorecard.label,
        score_pct=scorecard.score_pct,
        status=scorecard.status,
        evidence_count=scorecard.evidence_count,
        summary=scorecard.summary,
        gaps=list(scorecard.gaps),
    )


def _capability_gap_card(gap) -> CapabilityGapCard:
    return CapabilityGapCard(
        gap_key=gap.gap_key,
        label=gap.label,
        severity=gap.severity,
        summary=gap.summary,
        recommended_action=gap.recommended_action,
    )


def snapshot_now() -> datetime:
    return datetime.now(tz=UTC)


def _strategy_spec_card(spec) -> StrategySpecCard:
    return StrategySpecCard(
        id=spec.id,
        spec_code=spec.spec_code,
        title=spec.title,
        target_market=spec.target_market,
        current_stage=spec.current_stage,
        latest_backtest_gate=spec.latest_backtest_gate,
        latest_paper_gate=spec.latest_paper_gate,
        created_at=spec.created_at,
    )


def _backtest_run_card(backtest) -> BacktestRunCard:
    metrics = backtest.metrics_json
    return BacktestRunCard(
        id=backtest.id,
        strategy_spec_id=backtest.strategy_spec_id,
        dataset_range=backtest.dataset_range,
        sample_size=backtest.sample_size,
        gate_result=backtest.gate_result,
        total_return_pct=_metric_value(metrics, "total_return_pct"),
        sharpe_ratio=_metric_value(metrics, "sharpe_ratio"),
        max_drawdown_pct=_metric_value(metrics, "max_drawdown_pct"),
        created_at=backtest.created_at,
    )


def _paper_run_card(paper_run) -> PaperRunCard:
    metrics = paper_run.metrics_json
    return PaperRunCard(
        id=paper_run.id,
        strategy_spec_id=paper_run.strategy_spec_id,
        deployment_label=paper_run.deployment_label,
        monitoring_days=paper_run.monitoring_days,
        gate_result=paper_run.gate_result,
        net_pnl_pct=_metric_value(metrics, "net_pnl_pct"),
        profit_factor=_metric_value(metrics, "profit_factor"),
        max_drawdown_pct=_metric_value(metrics, "max_drawdown_pct"),
        created_at=paper_run.created_at,
    )


def _execution_readiness_card(readiness) -> ExecutionReadinessCard:
    return ExecutionReadinessCard(
        status=readiness.status,
        trading_allowed=readiness.trading_allowed,
        market_calendar=readiness.market_calendar,
        market_session_label=readiness.market_session_label,
        market_open=readiness.market_open,
        active_production_strategies=readiness.active_production_strategies,
        active_trading_overrides=readiness.active_trading_overrides,
        open_provider_incidents=readiness.open_provider_incidents,
        latest_provider_health=readiness.latest_provider_health,
        broker_snapshot_age_seconds=readiness.broker_snapshot_age_seconds,
        reconciliation_status=readiness.reconciliation_status,
        reconciliation_halt_triggered=readiness.reconciliation_halt_triggered,
        blocked_reasons=readiness.blocked_reasons,
        warnings=readiness.warnings,
    )


def _market_session_card(session_state) -> MarketSessionCard:
    return MarketSessionCard(
        id=session_state.id,
        market_calendar=session_state.market_calendar,
        market_timezone=session_state.market_timezone,
        session_label=session_state.session_label,
        is_market_open=session_state.is_market_open,
        trading_allowed=session_state.trading_allowed,
        next_open_at=session_state.next_open_at,
        next_close_at=session_state.next_close_at,
        created_at=session_state.created_at,
    )


def _account_snapshot_card(snapshot) -> BrokerAccountSnapshotCard:
    return BrokerAccountSnapshotCard(
        id=snapshot.id,
        provider_key=snapshot.provider_key,
        account_ref=snapshot.account_ref,
        environment=snapshot.environment,
        equity=snapshot.equity,
        cash=snapshot.cash,
        buying_power=snapshot.buying_power,
        gross_exposure=snapshot.gross_exposure,
        net_exposure=snapshot.net_exposure,
        positions_count=snapshot.positions_count,
        open_orders_count=snapshot.open_orders_count,
        source_captured_at=snapshot.source_captured_at,
        source_age_seconds=snapshot.source_age_seconds,
        created_at=snapshot.created_at,
    )


def _reconciliation_card(reconciliation) -> ReconciliationRunCard:
    return ReconciliationRunCard(
        id=reconciliation.id,
        provider_key=reconciliation.provider_key,
        account_ref=reconciliation.account_ref,
        environment=reconciliation.environment,
        equity_delta_abs=reconciliation.equity_delta_abs,
        equity_delta_pct=reconciliation.equity_delta_pct,
        position_delta_count=reconciliation.position_delta_count,
        order_delta_count=reconciliation.order_delta_count,
        blocking_reason=reconciliation.blocking_reason,
        halt_triggered=reconciliation.halt_triggered,
        status=reconciliation.status,
        checked_at=reconciliation.checked_at,
        created_at=reconciliation.created_at,
    )


def _broker_sync_card(sync_run) -> BrokerSyncRunCard:
    return BrokerSyncRunCard(
        id=sync_run.id,
        provider_key=sync_run.provider_key,
        account_ref=sync_run.account_ref,
        environment=sync_run.environment,
        broker_adapter=sync_run.broker_adapter,
        sync_scope=sync_run.sync_scope,
        synced_orders_count=sync_run.synced_orders_count,
        synced_positions_count=sync_run.synced_positions_count,
        unmanaged_orders_count=sync_run.unmanaged_orders_count,
        unmanaged_positions_count=sync_run.unmanaged_positions_count,
        missing_internal_orders_count=sync_run.missing_internal_orders_count,
        missing_internal_positions_count=sync_run.missing_internal_positions_count,
        status=sync_run.status,
        completed_at=sync_run.completed_at,
        created_at=sync_run.created_at,
    )


def _provider_incident_card(provider_incident) -> ProviderIncidentCard:
    return ProviderIncidentCard(
        id=provider_incident.id,
        provider_key=provider_incident.provider_key,
        title=provider_incident.title,
        severity=provider_incident.severity,
        status=provider_incident.status,
        detected_at=provider_incident.detected_at,
        resolved_at=provider_incident.resolved_at,
    )


def _allocation_policy_card(policy) -> AllocationPolicyCard:
    return AllocationPolicyCard(
        policy_key=policy.policy_key,
        environment=policy.environment,
        scope=policy.scope,
        max_strategy_notional_pct=policy.max_strategy_notional_pct,
        max_gross_exposure_pct=policy.max_gross_exposure_pct,
        max_open_positions=policy.max_open_positions,
        max_open_orders=policy.max_open_orders,
        allow_short=policy.allow_short,
        allow_fractional=policy.allow_fractional,
        updated_at=policy.updated_at,
    )


def _order_intent_card(order_intent) -> OrderIntentCard:
    return OrderIntentCard(
        id=order_intent.id,
        strategy_spec_id=order_intent.strategy_spec_id,
        provider_key=order_intent.provider_key,
        symbol=order_intent.symbol,
        asset_type=order_intent.asset_type,
        instrument_key=order_intent.instrument_key,
        position_effect=order_intent.position_effect,
        side=order_intent.side,
        quantity=order_intent.quantity,
        reference_price=order_intent.reference_price,
        requested_notional=order_intent.requested_notional,
        leg_count=order_intent.leg_count,
        broker_adapter=order_intent.broker_adapter,
        status=order_intent.status,
        decision_reason=order_intent.decision_reason,
        created_at=order_intent.created_at,
    )


def _order_record_card(order_record) -> OrderRecordCard:
    return OrderRecordCard(
        id=order_record.id,
        order_intent_id=order_record.order_intent_id,
        broker_order_id=order_record.broker_order_id,
        client_order_id=order_record.client_order_id,
        parent_order_record_id=order_record.parent_order_record_id,
        symbol=order_record.symbol,
        asset_type=order_record.asset_type,
        instrument_key=order_record.instrument_key,
        position_effect=order_record.position_effect,
        side=order_record.side,
        quantity=order_record.quantity,
        filled_quantity=order_record.filled_quantity,
        avg_fill_price=order_record.avg_fill_price,
        leg_count=order_record.leg_count,
        status=order_record.status,
        submitted_at=order_record.submitted_at,
        broker_updated_at=order_record.broker_updated_at,
        created_at=order_record.created_at,
    )


def _position_card(position) -> PositionCard:
    return PositionCard(
        id=position.id,
        strategy_spec_id=position.strategy_spec_id,
        symbol=position.symbol,
        underlying_symbol=position.underlying_symbol,
        asset_type=position.asset_type,
        instrument_key=position.instrument_key,
        direction=position.direction,
        quantity=position.quantity,
        avg_entry_price=position.avg_entry_price,
        market_price=position.market_price,
        notional_value=position.notional_value,
        realized_pnl=position.realized_pnl,
        unrealized_pnl=position.unrealized_pnl,
        status=position.status,
        last_synced_at=position.last_synced_at,
        created_at=position.created_at,
    )


def _option_lifecycle_event_card(option_event) -> OptionLifecycleEventCard:
    return OptionLifecycleEventCard(
        id=option_event.id,
        event_type=option_event.event_type,
        symbol=option_event.symbol,
        underlying_symbol=option_event.underlying_symbol,
        quantity=option_event.quantity,
        event_price=option_event.event_price,
        cash_flow=option_event.cash_flow,
        state_applied=option_event.state_applied,
        review_required=option_event.review_required,
        status=option_event.status,
        occurred_at=option_event.occurred_at,
        notes=option_event.notes,
    )


def _metric_value(metrics: dict[str, object], key: str) -> float | None:
    value = metrics.get(key)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _empty_execution_readiness() -> ExecutionReadinessCard:
    return ExecutionReadinessCard(
        status="blocked",
        trading_allowed=False,
        market_calendar="unconfigured",
        market_session_label=None,
        market_open=False,
        active_production_strategies=0,
        active_trading_overrides=0,
        open_provider_incidents=0,
        latest_provider_health=None,
        broker_snapshot_age_seconds=None,
        reconciliation_status=None,
        reconciliation_halt_triggered=False,
        blocked_reasons=["Execution service is not configured on this node."],
        warnings=[],
    )
