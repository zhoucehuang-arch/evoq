from __future__ import annotations

from contextlib import asynccontextmanager
import secrets

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from quant_evo_nextgen.config import Settings, get_settings
from quant_evo_nextgen.contracts.codex import (
    CodexArtifactSummary,
    CodexAttemptSummary,
    CodexRunRequest,
    CodexRunSummary,
)
from quant_evo_nextgen.contracts.dashboard import (
    DashboardEvolution,
    DashboardIncidents,
    DashboardLearning,
    DashboardOverview,
    DashboardSystem,
    DashboardTrading,
)
from quant_evo_nextgen.contracts.state import (
    AllocationPolicySummary,
    AllocationPolicyUpsert,
    ApprovalDecisionCreate,
    ApprovalDecisionSummary,
    ApprovalRequestCreate,
    ApprovalRequestSummary,
    BacktestRunCreate,
    BacktestRunSummary,
    BrokerAccountSnapshotCreate,
    BrokerAccountSnapshotSummary,
    BrokerCapabilitySummary,
    BrokerCapabilityUpsert,
    BrokerSyncRunCreate,
    BrokerSyncRunSummary,
    ExecutionReadinessSummary,
    EvolutionCanaryRunCreate,
    EvolutionCanaryRunSummary,
    EvolutionImprovementProposalCreate,
    EvolutionImprovementProposalSummary,
    EvolutionPromotionDecisionCreate,
    EvolutionPromotionDecisionSummary,
    GoalCreate,
    GoalSummary,
    IncidentCreate,
    IncidentSummary,
    InstrumentDefinitionSummary,
    InstrumentDefinitionUpsert,
    LearningDocumentSummary,
    LearningInsightSummary,
    MarketSessionStateCreate,
    MarketSessionStateSummary,
    OperatorOverrideCreate,
    OperatorOverrideSummary,
    OrderCancelCreate,
    OrderIntentCreate,
    OrderIntentSummary,
    OptionLifecycleEventCreate,
    OptionLifecycleEventSummary,
    OrderReplaceCreate,
    OrderRecordSummary,
    OwnerPreferenceSummary,
    OwnerPreferenceUpsert,
    PaperRunCreate,
    PaperRunSummary,
    PositionRecordSummary,
    PromotionDecisionCreate,
    PromotionDecisionSummary,
    ProviderIncidentCreate,
    ProviderIncidentResolve,
    ProviderIncidentSummary,
    ProviderProfileSummary,
    ReconciliationRunCreate,
    ReconciliationRunSummary,
    RuntimeConfigEntrySummary,
    RuntimeConfigProposalCreate,
    RuntimeConfigProposalSummary,
    RuntimeConfigRevisionSummary,
    RuntimeConfigRollbackRequest,
    SourceHealthSummary,
    StrategyHypothesisCreate,
    StrategyHypothesisSummary,
    StrategySpecCreate,
    StrategySpecSummary,
    SupervisorLoopSummary,
    WithdrawalDecisionCreate,
    WithdrawalDecisionSummary,
    WorkflowRunSummary,
)
from quant_evo_nextgen.db.session import Database
from quant_evo_nextgen.services.codex_fabric import CodexFabricService
from quant_evo_nextgen.services.dashboard import DashboardService
from quant_evo_nextgen.services.doctor import DoctorService
from quant_evo_nextgen.services.evolution import EvolutionService
from quant_evo_nextgen.services.execution import ExecutionService
from quant_evo_nextgen.services.learning import LearningService
from quant_evo_nextgen.services.repo_state import RepoStateService
from quant_evo_nextgen.services.state_store import StateStore
from quant_evo_nextgen.services.strategy_lab import StrategyLabService


def create_app(settings: Settings | None = None) -> FastAPI:
    runtime_settings = settings or get_settings()
    database = Database(runtime_settings.postgres_url, echo=runtime_settings.db_echo)
    repo_state_service = RepoStateService(runtime_settings.resolved_repo_root)
    state_store = StateStore(database.session_factory)
    codex_fabric_service = CodexFabricService(database.session_factory, runtime_settings)
    doctor_service = DoctorService(database.session_factory, runtime_settings)
    learning_service = LearningService(database.session_factory)
    strategy_service = StrategyLabService(database.session_factory)
    execution_service = ExecutionService(database.session_factory, runtime_settings)
    evolution_service = EvolutionService(database.session_factory)
    dashboard_service = DashboardService(
        repo_state_service,
        state_store,
        codex_fabric_service,
        learning_service,
        strategy_service,
        execution_service,
        evolution_service,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if runtime_settings.db_bootstrap_on_start:
            database.create_schema()
        state_store.bootstrap_reference_data(runtime_settings)

        app.state.settings = runtime_settings
        app.state.database = database
        app.state.repo_state_service = repo_state_service
        app.state.state_store = state_store
        app.state.codex_fabric_service = codex_fabric_service
        app.state.doctor_service = doctor_service
        app.state.learning_service = learning_service
        app.state.strategy_service = strategy_service
        app.state.execution_service = execution_service
        app.state.evolution_service = evolution_service
        app.state.dashboard_service = dashboard_service
        try:
            yield
        finally:
            database.dispose()

    app = FastAPI(
        title="EvoQ API",
        version="0.3.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=runtime_settings.cors_allow_origins_list or ["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def dashboard_surface_guard(request: Request, call_next):
        token = (runtime_settings.dashboard_api_token or "").strip()
        if not token or not _requires_dashboard_api_token(request.url.path):
            return await call_next(request)

        provided = request.headers.get("x-quant-evo-dashboard-token", "").strip()
        if not provided or not secrets.compare_digest(provided, token):
            return JSONResponse(
                status_code=401,
                content={"detail": "Dashboard API token is missing or invalid."},
            )
        return await call_next(request)

    @app.get("/healthz")
    async def healthcheck(request: Request) -> dict[str, object]:
        overview = _state_store(request).get_runtime_snapshot()
        return {
            "ok": True,
            "service": "core-api",
            "env": runtime_settings.env,
            "repo_root": str(runtime_settings.resolved_repo_root),
            "db_bootstrap_on_start": runtime_settings.db_bootstrap_on_start,
            "active_goals": overview.active_goals,
            "open_incidents": overview.open_incidents,
            "pending_approvals": overview.pending_approvals,
        }

    @app.get("/api/v1/system/status")
    async def system_status(request: Request) -> dict[str, object]:
        overview = _dashboard_service(request).build_overview()
        return {
            "headline": overview.headline,
            "mode": overview.system.mode,
            "risk_state": overview.system.risk_state,
            "production_strategies": overview.strategy.production,
            "feature_map_occupied": overview.learning.occupied_feature_cells,
            "active_goals": overview.system.active_goals,
            "open_incidents": overview.system.open_incidents,
            "pending_approvals": overview.system.pending_approvals,
            "codex_queue_depth": overview.system.codex_queue_depth,
        }

    @app.get("/api/v1/system/doctor")
    async def system_doctor(request: Request) -> dict[str, object]:
        return _doctor_service(request).run()

    @app.get("/api/v1/dashboard/overview", response_model=DashboardOverview)
    async def dashboard_overview(request: Request) -> DashboardOverview:
        return _dashboard_service(request).build_overview()

    @app.get("/api/v1/dashboard/trading", response_model=DashboardTrading)
    async def dashboard_trading(request: Request) -> DashboardTrading:
        return _dashboard_service(request).build_trading_view()

    @app.get("/api/v1/dashboard/learning", response_model=DashboardLearning)
    async def dashboard_learning(request: Request) -> DashboardLearning:
        return _dashboard_service(request).build_learning_view()

    @app.get("/api/v1/dashboard/evolution", response_model=DashboardEvolution)
    async def dashboard_evolution(request: Request) -> DashboardEvolution:
        return _dashboard_service(request).build_evolution_view()

    @app.post("/api/v1/evolution/proposals", response_model=EvolutionImprovementProposalSummary)
    async def create_evolution_proposal(
        payload: EvolutionImprovementProposalCreate,
        request: Request,
    ) -> EvolutionImprovementProposalSummary:
        return _evolution_service(request).create_improvement_proposal(payload)

    @app.get("/api/v1/evolution/proposals", response_model=list[EvolutionImprovementProposalSummary])
    async def list_evolution_proposals(request: Request) -> list[EvolutionImprovementProposalSummary]:
        return _evolution_service(request).list_improvement_proposals()

    @app.post("/api/v1/evolution/canary-runs", response_model=EvolutionCanaryRunSummary)
    async def record_evolution_canary_run(
        payload: EvolutionCanaryRunCreate,
        request: Request,
    ) -> EvolutionCanaryRunSummary:
        return _evolution_service(request).record_canary_run(payload)

    @app.get("/api/v1/evolution/canary-runs", response_model=list[EvolutionCanaryRunSummary])
    async def list_evolution_canary_runs(request: Request) -> list[EvolutionCanaryRunSummary]:
        return _evolution_service(request).list_canary_runs()

    @app.post("/api/v1/evolution/promotion-decisions", response_model=EvolutionPromotionDecisionSummary)
    async def record_evolution_promotion_decision(
        payload: EvolutionPromotionDecisionCreate,
        request: Request,
    ) -> EvolutionPromotionDecisionSummary:
        return _evolution_service(request).record_promotion_decision(payload)

    @app.get("/api/v1/evolution/promotion-decisions", response_model=list[EvolutionPromotionDecisionSummary])
    async def list_evolution_promotion_decisions(request: Request) -> list[EvolutionPromotionDecisionSummary]:
        return _evolution_service(request).list_promotion_decisions()

    @app.get("/api/v1/dashboard/system", response_model=DashboardSystem)
    async def dashboard_system(request: Request) -> DashboardSystem:
        return _dashboard_service(request).build_system_view()

    @app.get("/api/v1/dashboard/incidents", response_model=DashboardIncidents)
    async def dashboard_incidents(request: Request) -> DashboardIncidents:
        return _dashboard_service(request).build_incidents_view()

    @app.post("/api/v1/goals", response_model=GoalSummary)
    async def create_goal(payload: GoalCreate, request: Request) -> GoalSummary:
        return _state_store(request).create_goal(payload)

    @app.get("/api/v1/goals", response_model=list[GoalSummary])
    async def list_goals(request: Request) -> list[GoalSummary]:
        return _state_store(request).list_goals()

    @app.post("/api/v1/incidents", response_model=IncidentSummary)
    async def create_incident(payload: IncidentCreate, request: Request) -> IncidentSummary:
        return _state_store(request).create_incident(payload)

    @app.get("/api/v1/incidents", response_model=list[IncidentSummary])
    async def list_incidents(request: Request) -> list[IncidentSummary]:
        return _state_store(request).list_incidents()

    @app.post("/api/v1/approvals", response_model=ApprovalRequestSummary)
    async def create_approval_request(
        payload: ApprovalRequestCreate,
        request: Request,
    ) -> ApprovalRequestSummary:
        return _state_store(request).create_approval_request(payload)

    @app.get("/api/v1/approvals", response_model=list[ApprovalRequestSummary])
    async def list_approvals(request: Request) -> list[ApprovalRequestSummary]:
        return _state_store(request).list_approval_requests()

    @app.post("/api/v1/approvals/{approval_id}/decision", response_model=ApprovalDecisionSummary)
    async def decide_approval(
        approval_id: str,
        payload: ApprovalDecisionCreate,
        request: Request,
    ) -> ApprovalDecisionSummary:
        return _state_store(request).decide_approval_request(approval_id, payload)

    @app.post("/api/v1/operator-overrides", response_model=OperatorOverrideSummary)
    async def create_operator_override(
        payload: OperatorOverrideCreate,
        request: Request,
    ) -> OperatorOverrideSummary:
        return _state_store(request).create_operator_override(payload)

    @app.get("/api/v1/operator-overrides", response_model=list[OperatorOverrideSummary])
    async def list_operator_overrides(request: Request) -> list[OperatorOverrideSummary]:
        return _state_store(request).list_operator_overrides()

    @app.get("/api/v1/workflows/runs", response_model=list[WorkflowRunSummary])
    async def list_workflow_runs(request: Request) -> list[WorkflowRunSummary]:
        return _state_store(request).list_workflow_runs()

    @app.post("/api/v1/codex/runs", response_model=CodexRunSummary)
    async def queue_codex_run(payload: CodexRunRequest, request: Request) -> CodexRunSummary:
        return _codex_fabric_service(request).queue_run(payload)

    @app.get("/api/v1/codex/runs", response_model=list[CodexRunSummary])
    async def list_codex_runs(request: Request) -> list[CodexRunSummary]:
        return _codex_fabric_service(request).list_runs()

    @app.get("/api/v1/codex/runs/{run_id}/attempts", response_model=list[CodexAttemptSummary])
    async def list_codex_attempts(run_id: str, request: Request) -> list[CodexAttemptSummary]:
        return _codex_fabric_service(request).list_attempts(run_id)

    @app.get("/api/v1/codex/runs/{run_id}/artifacts", response_model=list[CodexArtifactSummary])
    async def list_codex_artifacts(run_id: str, request: Request) -> list[CodexArtifactSummary]:
        return _codex_fabric_service(request).list_artifacts(run_id)

    @app.get("/api/v1/providers", response_model=list[ProviderProfileSummary])
    async def list_providers(request: Request) -> list[ProviderProfileSummary]:
        return _state_store(request).list_provider_profiles()

    @app.get("/api/v1/source-health", response_model=list[SourceHealthSummary])
    async def list_source_health(request: Request) -> list[SourceHealthSummary]:
        return _state_store(request).list_source_health()

    @app.get("/api/v1/learning/documents", response_model=list[LearningDocumentSummary])
    async def list_learning_documents(request: Request) -> list[LearningDocumentSummary]:
        return _learning_service(request).list_documents()

    @app.get("/api/v1/learning/insights", response_model=list[LearningInsightSummary])
    async def list_learning_insights(request: Request) -> list[LearningInsightSummary]:
        return _learning_service(request).list_insights()

    @app.post("/api/v1/execution/market-sessions", response_model=MarketSessionStateSummary)
    async def record_market_session_state(
        payload: MarketSessionStateCreate,
        request: Request,
    ) -> MarketSessionStateSummary:
        return _execution_service(request).record_market_session_state(payload)

    @app.get("/api/v1/execution/market-sessions", response_model=list[MarketSessionStateSummary])
    async def list_market_session_states(request: Request) -> list[MarketSessionStateSummary]:
        return _execution_service(request).list_market_session_states()

    @app.post("/api/v1/execution/account-snapshots", response_model=BrokerAccountSnapshotSummary)
    async def record_broker_account_snapshot(
        payload: BrokerAccountSnapshotCreate,
        request: Request,
    ) -> BrokerAccountSnapshotSummary:
        return _execution_service(request).record_broker_account_snapshot(payload)

    @app.get("/api/v1/execution/account-snapshots", response_model=list[BrokerAccountSnapshotSummary])
    async def list_broker_account_snapshots(request: Request) -> list[BrokerAccountSnapshotSummary]:
        return _execution_service(request).list_broker_account_snapshots()

    @app.post("/api/v1/execution/reconciliation-runs", response_model=ReconciliationRunSummary)
    async def record_reconciliation_run(
        payload: ReconciliationRunCreate,
        request: Request,
    ) -> ReconciliationRunSummary:
        return _execution_service(request).record_reconciliation_run(payload)

    @app.get("/api/v1/execution/reconciliation-runs", response_model=list[ReconciliationRunSummary])
    async def list_reconciliation_runs(request: Request) -> list[ReconciliationRunSummary]:
        return _execution_service(request).list_reconciliation_runs()

    @app.post("/api/v1/execution/broker-sync-runs", response_model=BrokerSyncRunSummary)
    async def sync_broker_state(
        payload: BrokerSyncRunCreate,
        request: Request,
    ) -> BrokerSyncRunSummary:
        return _execution_service(request).sync_broker_state(payload)

    @app.get("/api/v1/execution/broker-sync-runs", response_model=list[BrokerSyncRunSummary])
    async def list_broker_sync_runs(request: Request) -> list[BrokerSyncRunSummary]:
        return _execution_service(request).list_broker_sync_runs()

    @app.get("/api/v1/execution/readiness", response_model=ExecutionReadinessSummary)
    async def get_execution_readiness(request: Request) -> ExecutionReadinessSummary:
        return _execution_service(request).get_execution_readiness()

    @app.post("/api/v1/execution/instruments", response_model=InstrumentDefinitionSummary)
    async def upsert_instrument_definition(
        payload: InstrumentDefinitionUpsert,
        request: Request,
    ) -> InstrumentDefinitionSummary:
        return _execution_service(request).upsert_instrument_definition(payload)

    @app.get("/api/v1/execution/instruments", response_model=list[InstrumentDefinitionSummary])
    async def list_instrument_definitions(request: Request) -> list[InstrumentDefinitionSummary]:
        return _execution_service(request).list_instrument_definitions()

    @app.post("/api/v1/execution/broker-capabilities", response_model=BrokerCapabilitySummary)
    async def upsert_broker_capability(
        payload: BrokerCapabilityUpsert,
        request: Request,
    ) -> BrokerCapabilitySummary:
        return _execution_service(request).upsert_broker_capability(payload)

    @app.get("/api/v1/execution/broker-capabilities", response_model=list[BrokerCapabilitySummary])
    async def list_broker_capabilities(request: Request) -> list[BrokerCapabilitySummary]:
        return _execution_service(request).list_broker_capabilities()

    @app.post("/api/v1/execution/allocation-policies", response_model=AllocationPolicySummary)
    async def upsert_allocation_policy(
        payload: AllocationPolicyUpsert,
        request: Request,
    ) -> AllocationPolicySummary:
        return _execution_service(request).upsert_allocation_policy(payload)

    @app.get("/api/v1/execution/allocation-policies", response_model=list[AllocationPolicySummary])
    async def list_allocation_policies(request: Request) -> list[AllocationPolicySummary]:
        return _execution_service(request).list_allocation_policies()

    @app.post("/api/v1/execution/order-intents", response_model=OrderIntentSummary)
    async def submit_order_intent(
        payload: OrderIntentCreate,
        request: Request,
    ) -> OrderIntentSummary:
        return _execution_service(request).submit_order_intent(payload)

    @app.get("/api/v1/execution/order-intents", response_model=list[OrderIntentSummary])
    async def list_order_intents(request: Request) -> list[OrderIntentSummary]:
        return _execution_service(request).list_order_intents()

    @app.get("/api/v1/execution/order-records", response_model=list[OrderRecordSummary])
    async def list_order_records(request: Request) -> list[OrderRecordSummary]:
        return _execution_service(request).list_order_records()

    @app.post("/api/v1/execution/order-records/{order_record_id}/cancel", response_model=OrderRecordSummary)
    async def cancel_order_record(
        order_record_id: str,
        payload: OrderCancelCreate,
        request: Request,
    ) -> OrderRecordSummary:
        return _execution_service(request).cancel_order(order_record_id, payload)

    @app.post("/api/v1/execution/order-records/{order_record_id}/replace", response_model=OrderRecordSummary)
    async def replace_order_record(
        order_record_id: str,
        payload: OrderReplaceCreate,
        request: Request,
    ) -> OrderRecordSummary:
        return _execution_service(request).replace_order(order_record_id, payload)

    @app.get("/api/v1/execution/positions", response_model=list[PositionRecordSummary])
    async def list_positions(request: Request) -> list[PositionRecordSummary]:
        return _execution_service(request).list_positions()

    @app.post("/api/v1/execution/option-events", response_model=OptionLifecycleEventSummary)
    async def record_option_lifecycle_event(
        payload: OptionLifecycleEventCreate,
        request: Request,
    ) -> OptionLifecycleEventSummary:
        return _execution_service(request).record_option_lifecycle_event(payload)

    @app.get("/api/v1/execution/option-events", response_model=list[OptionLifecycleEventSummary])
    async def list_option_lifecycle_events(request: Request) -> list[OptionLifecycleEventSummary]:
        return _execution_service(request).list_option_lifecycle_events()

    @app.post("/api/v1/providers/incidents", response_model=ProviderIncidentSummary)
    async def create_provider_incident(
        payload: ProviderIncidentCreate,
        request: Request,
    ) -> ProviderIncidentSummary:
        return _execution_service(request).create_provider_incident(payload)

    @app.get("/api/v1/providers/incidents", response_model=list[ProviderIncidentSummary])
    async def list_provider_incidents(request: Request) -> list[ProviderIncidentSummary]:
        return _execution_service(request).list_provider_incidents()

    @app.post("/api/v1/providers/incidents/{incident_id}/resolve", response_model=ProviderIncidentSummary)
    async def resolve_provider_incident(
        incident_id: str,
        payload: ProviderIncidentResolve,
        request: Request,
    ) -> ProviderIncidentSummary:
        return _execution_service(request).resolve_provider_incident(incident_id, payload)

    @app.post("/api/v1/strategy/hypotheses", response_model=StrategyHypothesisSummary)
    async def create_strategy_hypothesis(
        payload: StrategyHypothesisCreate,
        request: Request,
    ) -> StrategyHypothesisSummary:
        return _strategy_service(request).create_hypothesis(payload)

    @app.get("/api/v1/strategy/hypotheses", response_model=list[StrategyHypothesisSummary])
    async def list_strategy_hypotheses(request: Request) -> list[StrategyHypothesisSummary]:
        return _strategy_service(request).list_hypotheses()

    @app.post("/api/v1/strategy/specs", response_model=StrategySpecSummary)
    async def create_strategy_spec(payload: StrategySpecCreate, request: Request) -> StrategySpecSummary:
        return _strategy_service(request).create_strategy_spec(payload)

    @app.get("/api/v1/strategy/specs", response_model=list[StrategySpecSummary])
    async def list_strategy_specs(request: Request) -> list[StrategySpecSummary]:
        return _strategy_service(request).list_strategy_specs()

    @app.post("/api/v1/strategy/backtests", response_model=BacktestRunSummary)
    async def record_strategy_backtest(payload: BacktestRunCreate, request: Request) -> BacktestRunSummary:
        return _strategy_service(request).record_backtest(payload)

    @app.get("/api/v1/strategy/backtests", response_model=list[BacktestRunSummary])
    async def list_strategy_backtests(request: Request) -> list[BacktestRunSummary]:
        return _strategy_service(request).list_backtests()

    @app.post("/api/v1/strategy/paper-runs", response_model=PaperRunSummary)
    async def record_strategy_paper_run(payload: PaperRunCreate, request: Request) -> PaperRunSummary:
        return _strategy_service(request).record_paper_run(payload)

    @app.get("/api/v1/strategy/paper-runs", response_model=list[PaperRunSummary])
    async def list_strategy_paper_runs(request: Request) -> list[PaperRunSummary]:
        return _strategy_service(request).list_paper_runs()

    @app.post("/api/v1/strategy/promotion-decisions", response_model=PromotionDecisionSummary)
    async def record_promotion_decision(
        payload: PromotionDecisionCreate,
        request: Request,
    ) -> PromotionDecisionSummary:
        return _strategy_service(request).record_promotion_decision(payload)

    @app.get("/api/v1/strategy/promotion-decisions", response_model=list[PromotionDecisionSummary])
    async def list_promotion_decisions(request: Request) -> list[PromotionDecisionSummary]:
        return _strategy_service(request).list_promotion_decisions()

    @app.post("/api/v1/strategy/withdrawal-decisions", response_model=WithdrawalDecisionSummary)
    async def record_withdrawal_decision(
        payload: WithdrawalDecisionCreate,
        request: Request,
    ) -> WithdrawalDecisionSummary:
        return _strategy_service(request).record_withdrawal_decision(payload)

    @app.get("/api/v1/strategy/withdrawal-decisions", response_model=list[WithdrawalDecisionSummary])
    async def list_withdrawal_decisions(request: Request) -> list[WithdrawalDecisionSummary]:
        return _strategy_service(request).list_withdrawal_decisions()

    @app.get("/api/v1/supervisor/loops", response_model=list[SupervisorLoopSummary])
    async def list_supervisor_loops(request: Request) -> list[SupervisorLoopSummary]:
        return _state_store(request).list_supervisor_loops()

    @app.get("/api/v1/runtime-config", response_model=list[RuntimeConfigEntrySummary])
    async def list_runtime_config(request: Request) -> list[RuntimeConfigEntrySummary]:
        return _state_store(request).list_runtime_config_entries()

    @app.post("/api/v1/runtime-config/proposals", response_model=RuntimeConfigProposalSummary)
    async def create_runtime_config_proposal(
        payload: RuntimeConfigProposalCreate,
        request: Request,
    ) -> RuntimeConfigProposalSummary:
        return _state_store(request).create_runtime_config_proposal(payload)

    @app.get("/api/v1/runtime-config/proposals", response_model=list[RuntimeConfigProposalSummary])
    async def list_runtime_config_proposals(request: Request) -> list[RuntimeConfigProposalSummary]:
        return _state_store(request).list_runtime_config_proposals()

    @app.post("/api/v1/runtime-config/proposals/{proposal_id}/apply", response_model=RuntimeConfigRevisionSummary)
    async def apply_runtime_config_proposal(
        proposal_id: str,
        request: Request,
    ) -> RuntimeConfigRevisionSummary:
        return _state_store(request).apply_runtime_config_proposal(proposal_id, applied_by="api")

    @app.get("/api/v1/runtime-config/revisions", response_model=list[RuntimeConfigRevisionSummary])
    async def list_runtime_config_revisions(request: Request) -> list[RuntimeConfigRevisionSummary]:
        return _state_store(request).list_runtime_config_revisions()

    @app.post(
        "/api/v1/runtime-config/revisions/{revision_id}/rollback-proposal",
        response_model=RuntimeConfigProposalSummary,
    )
    async def rollback_runtime_config_revision(
        revision_id: str,
        payload: RuntimeConfigRollbackRequest,
        request: Request,
    ) -> RuntimeConfigProposalSummary:
        return _state_store(request).create_runtime_config_rollback_proposal(
            revision_id,
            requested_by=payload.requested_by,
            rationale=payload.rationale,
        )

    @app.post("/api/v1/owner-preferences", response_model=OwnerPreferenceSummary)
    async def upsert_owner_preference(
        payload: OwnerPreferenceUpsert,
        request: Request,
    ) -> OwnerPreferenceSummary:
        return _state_store(request).upsert_owner_preference(payload)

    @app.get("/api/v1/owner-preferences", response_model=list[OwnerPreferenceSummary])
    async def list_owner_preferences(request: Request) -> list[OwnerPreferenceSummary]:
        return _state_store(request).list_owner_preferences()

    return app


def _dashboard_service(request: Request) -> DashboardService:
    return request.app.state.dashboard_service


def _state_store(request: Request) -> StateStore:
    return request.app.state.state_store


def _codex_fabric_service(request: Request) -> CodexFabricService:
    return request.app.state.codex_fabric_service


def _doctor_service(request: Request) -> DoctorService:
    return request.app.state.doctor_service


def _learning_service(request: Request) -> LearningService:
    return request.app.state.learning_service


def _execution_service(request: Request) -> ExecutionService:
    return request.app.state.execution_service


def _strategy_service(request: Request) -> StrategyLabService:
    return request.app.state.strategy_service


def _evolution_service(request: Request) -> EvolutionService:
    return request.app.state.evolution_service


app = create_app()


def _requires_dashboard_api_token(path: str) -> bool:
    return path.startswith("/api/v1/dashboard/") or path in {
        "/api/v1/system/status",
        "/api/v1/system/doctor",
    }
