from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class FreshnessState(str, Enum):
    FRESH = "fresh"
    LAGGING = "lagging"
    STALE = "stale"
    BROKEN = "broken"


class FreshnessPayload(BaseModel):
    state: FreshnessState
    age_seconds: int
    generated_at: datetime
    note: str | None = None


class SummaryCard(BaseModel):
    label: str
    value: str
    tone: str = "neutral"
    hint: str | None = None


class StrategySummary(BaseModel):
    candidates: int
    staging: int
    production: int
    active_production: bool


class LearningSummary(BaseModel):
    principles: int
    causal_cases: int
    occupied_feature_cells: int
    feature_coverage_pct: float
    total_generations: int


class SystemSummary(BaseModel):
    mode: str
    risk_state: str
    codex_queue_depth: int
    active_goals: int
    open_incidents: int
    pending_approvals: int
    active_overrides: int
    repo_root: str


class DashboardOverview(BaseModel):
    generated_at: datetime
    freshness: FreshnessPayload
    headline: str
    summary_cards: list[SummaryCard]
    highlights: list[str]
    strategy: StrategySummary
    learning: LearningSummary
    system: SystemSummary


class DomainControlState(BaseModel):
    domain: str
    is_paused: bool
    pending_approval_count: int
    override_count: int
    latest_reason: str | None = None


class ApprovalCard(BaseModel):
    id: str
    approval_type: str
    subject_id: str
    requested_by: str
    risk_level: str
    decision_status: str
    created_at: datetime


class WorkflowRunCard(BaseModel):
    id: str
    workflow_code: str
    workflow_name: str
    workflow_family: str
    owner_role: str
    status: str
    started_at: datetime
    ended_at: datetime | None = None
    latest_event_summary: str | None = None


class CodexRunCard(BaseModel):
    id: str
    status: str
    worker_class: str
    execution_mode: str
    strategy_mode: str
    objective: str
    current_attempt: int
    max_iterations: int
    queued_at: datetime
    completed_at: datetime | None = None
    last_error: str | None = None


class SourceHealthCard(BaseModel):
    source_key: str
    source_type: str
    health_status: str
    trust_score: float
    freshness_score: float
    last_validated_at: datetime | None = None
    notes: str | None = None


class LearningDocumentCard(BaseModel):
    id: str
    codex_run_id: str | None = None
    workflow_run_id: str | None = None
    source_key: str
    title: str
    summary: str
    status: str
    source_type: str
    supervisor_loop_key: str | None = None
    citation_count: int
    evidence_count: int
    confidence: float | None = None
    created_at: datetime


class LearningInsightCard(BaseModel):
    id: str
    document_id: str
    codex_run_id: str | None = None
    workflow_run_id: str | None = None
    supervisor_loop_key: str | None = None
    topic_key: str
    title: str
    summary: str
    status: str
    promotion_state: str
    evidence_count: int
    citation_count: int
    confidence: float | None = None
    quarantine_reason: str | None = None
    created_at: datetime


class ProviderProfileCard(BaseModel):
    provider_key: str
    display_name: str
    health_status: str
    api_style: str
    is_primary: bool
    base_url: str | None = None


class SupervisorLoopCard(BaseModel):
    loop_key: str
    workflow_code: str
    domain: str
    display_name: str
    execution_mode: str
    is_enabled: bool
    cadence_seconds: int
    next_due_at: datetime | None = None
    last_completed_at: datetime | None = None
    last_status: str
    failure_streak: int
    last_error: str | None = None


class IncidentCard(BaseModel):
    id: str
    title: str
    summary: str
    severity: str
    status: str
    created_at: datetime


class OwnerPreferenceCard(BaseModel):
    preference_key: str
    display_name: str
    scope: str
    updated_by: str
    updated_at: datetime
    value_preview: str
    preview_lines: list[str] = Field(default_factory=list)
    contains_sensitive_fields: bool = False


class RuntimeConfigCard(BaseModel):
    target_type: str
    target_key: str
    display_name: str
    category: str
    risk_level: str
    is_mutable: bool
    requires_restart: bool
    updated_at: datetime
    updated_by: str | None = None
    value_preview: str
    preview_lines: list[str] = Field(default_factory=list)
    contains_sensitive_fields: bool = False


class RuntimeConfigProposalCard(BaseModel):
    id: str
    target_type: str
    target_key: str
    display_name: str
    category: str
    requested_by: str
    change_summary: str
    risk_level: str
    requires_approval: bool
    approval_request_id: str | None = None
    status: str
    created_at: datetime


class RuntimeConfigRevisionCard(BaseModel):
    id: str
    target_type: str
    target_key: str
    display_name: str
    change_summary: str
    applied_by: str
    applied_at: datetime


class StrategyLabMetrics(BaseModel):
    hypothesis_count: int
    spec_count: int
    paper_candidate_count: int
    paper_running_count: int
    live_candidate_count: int
    production_count: int


class StrategySpecCard(BaseModel):
    id: str
    spec_code: str
    title: str
    target_market: str
    current_stage: str
    latest_backtest_gate: str | None = None
    latest_paper_gate: str | None = None
    created_at: datetime


class BacktestRunCard(BaseModel):
    id: str
    strategy_spec_id: str
    dataset_range: str | None = None
    sample_size: int
    gate_result: str
    total_return_pct: float | None = None
    sharpe_ratio: float | None = None
    max_drawdown_pct: float | None = None
    created_at: datetime


class PaperRunCard(BaseModel):
    id: str
    strategy_spec_id: str
    deployment_label: str
    monitoring_days: int
    gate_result: str
    net_pnl_pct: float | None = None
    profit_factor: float | None = None
    max_drawdown_pct: float | None = None
    created_at: datetime


class ExecutionReadinessCard(BaseModel):
    status: str
    trading_allowed: bool
    market_calendar: str
    market_session_label: str | None = None
    market_open: bool
    active_production_strategies: int
    active_trading_overrides: int
    open_provider_incidents: int
    latest_provider_health: str | None = None
    broker_snapshot_age_seconds: int | None = None
    reconciliation_status: str | None = None
    reconciliation_halt_triggered: bool = False
    blocked_reasons: list[str]
    warnings: list[str]


class MarketSessionCard(BaseModel):
    id: str
    market_calendar: str
    market_timezone: str
    session_label: str
    is_market_open: bool
    trading_allowed: bool
    next_open_at: datetime | None = None
    next_close_at: datetime | None = None
    created_at: datetime


class BrokerAccountSnapshotCard(BaseModel):
    id: str
    provider_key: str
    account_ref: str
    environment: str
    equity: float
    cash: float
    buying_power: float
    gross_exposure: float
    net_exposure: float
    positions_count: int
    open_orders_count: int
    source_captured_at: datetime
    source_age_seconds: int
    created_at: datetime


class ReconciliationRunCard(BaseModel):
    id: str
    provider_key: str
    account_ref: str
    environment: str
    equity_delta_abs: float
    equity_delta_pct: float
    position_delta_count: int
    order_delta_count: int
    blocking_reason: str | None = None
    halt_triggered: bool
    status: str
    checked_at: datetime
    created_at: datetime


class BrokerSyncRunCard(BaseModel):
    id: str
    provider_key: str
    account_ref: str
    environment: str
    broker_adapter: str
    sync_scope: str
    synced_orders_count: int
    synced_positions_count: int
    unmanaged_orders_count: int
    unmanaged_positions_count: int
    missing_internal_orders_count: int
    missing_internal_positions_count: int
    status: str
    completed_at: datetime | None = None
    created_at: datetime


class ProviderIncidentCard(BaseModel):
    id: str
    provider_key: str
    title: str
    severity: str
    status: str
    detected_at: datetime
    resolved_at: datetime | None = None


class AllocationPolicyCard(BaseModel):
    policy_key: str
    environment: str
    scope: str
    max_strategy_notional_pct: float
    max_gross_exposure_pct: float
    max_open_positions: int
    max_open_orders: int
    allow_short: bool
    allow_fractional: bool
    updated_at: datetime


class OrderIntentCard(BaseModel):
    id: str
    strategy_spec_id: str
    provider_key: str
    symbol: str
    asset_type: str
    instrument_key: str | None = None
    position_effect: str
    side: str
    quantity: float
    reference_price: float
    requested_notional: float
    leg_count: int = 0
    broker_adapter: str
    status: str
    decision_reason: str | None = None
    created_at: datetime


class OrderRecordCard(BaseModel):
    id: str
    order_intent_id: str
    broker_order_id: str
    client_order_id: str | None = None
    parent_order_record_id: str | None = None
    symbol: str
    asset_type: str
    instrument_key: str | None = None
    position_effect: str
    side: str
    quantity: float
    filled_quantity: float
    avg_fill_price: float | None = None
    leg_count: int = 0
    status: str
    submitted_at: datetime
    broker_updated_at: datetime | None = None
    created_at: datetime


class PositionCard(BaseModel):
    id: str
    strategy_spec_id: str
    symbol: str
    underlying_symbol: str | None = None
    asset_type: str
    instrument_key: str | None = None
    direction: str
    quantity: float
    avg_entry_price: float
    market_price: float | None = None
    notional_value: float
    realized_pnl: float
    unrealized_pnl: float
    status: str
    last_synced_at: datetime
    created_at: datetime


class OptionLifecycleEventCard(BaseModel):
    id: str
    event_type: str
    symbol: str
    underlying_symbol: str | None = None
    quantity: float
    event_price: float | None = None
    cash_flow: float | None = None
    state_applied: bool
    review_required: bool
    status: str
    occurred_at: datetime
    notes: str | None = None


class ExpiringOptionPositionCard(BaseModel):
    id: str
    strategy_spec_id: str
    symbol: str
    underlying_symbol: str | None = None
    instrument_key: str | None = None
    quantity: float
    direction: str
    expiration_date: date
    days_to_expiry: int
    market_price: float | None = None
    unrealized_pnl: float


class DashboardTrading(BaseModel):
    generated_at: datetime
    freshness: FreshnessPayload
    strategy_lab: StrategyLabMetrics
    execution_readiness: ExecutionReadinessCard
    allocation_policy: AllocationPolicyCard | None = None
    summary_cards: list[SummaryCard]
    highlights: list[str]
    domain_states: list[DomainControlState]
    latest_account_snapshot: BrokerAccountSnapshotCard | None = None
    latest_reconciliation: ReconciliationRunCard | None = None
    latest_broker_sync: BrokerSyncRunCard | None = None
    recent_market_sessions: list[MarketSessionCard]
    active_provider_incidents: list[ProviderIncidentCard]
    recent_order_intents: list[OrderIntentCard]
    recent_order_records: list[OrderRecordCard]
    active_positions: list[PositionCard]
    expiring_option_positions: list[ExpiringOptionPositionCard]
    recent_option_events: list[OptionLifecycleEventCard]
    recent_specs: list[StrategySpecCard]
    recent_backtests: list[BacktestRunCard]
    recent_paper_runs: list[PaperRunCard]


class LearningGateMetrics(BaseModel):
    document_count: int
    insight_count: int
    ready_insight_count: int
    quarantined_insight_count: int


class DashboardLearning(BaseModel):
    generated_at: datetime
    freshness: FreshnessPayload
    metrics: LearningGateMetrics
    summary_cards: list[SummaryCard]
    highlights: list[str]
    sources: list[SourceHealthCard]
    recent_documents: list[LearningDocumentCard]
    recent_insights: list[LearningInsightCard]
    supervisor_loops: list[SupervisorLoopCard]


class EvolutionGovernanceMetrics(BaseModel):
    proposal_count: int
    ready_for_review_count: int
    active_canary_count: int
    promoted_count: int
    rolled_back_count: int


class CapabilityScorecardCard(BaseModel):
    capability_key: str
    label: str
    score_pct: int
    status: str
    evidence_count: int
    summary: str
    gaps: list[str]


class CapabilityGapCard(BaseModel):
    gap_key: str
    label: str
    severity: str
    summary: str
    recommended_action: str


class EvolutionProposalCard(BaseModel):
    id: str
    title: str
    target_surface: str
    proposal_kind: str
    proposal_state: str
    risk_summary: str | None = None
    codex_run_id: str | None = None
    workflow_run_id: str | None = None
    created_at: datetime


class EvolutionCanaryRunCard(BaseModel):
    id: str
    proposal_id: str
    lane_type: str
    environment: str
    traffic_pct: float
    objective_drift_score: float | None = None
    rollback_ready: bool
    status: str
    completed_at: datetime | None = None
    created_at: datetime


class EvolutionPromotionDecisionCard(BaseModel):
    id: str
    proposal_id: str
    decision: str
    decided_by: str
    rationale: str
    decided_at: datetime


class DashboardEvolution(BaseModel):
    generated_at: datetime
    freshness: FreshnessPayload
    metrics: EvolutionGovernanceMetrics
    summary_cards: list[SummaryCard]
    highlights: list[str]
    capability_scorecards: list[CapabilityScorecardCard]
    capability_gaps: list[CapabilityGapCard]
    stall_state: str
    stall_summary: str | None = None
    recent_proposals: list[EvolutionProposalCard]
    recent_canary_runs: list[EvolutionCanaryRunCard]
    recent_promotion_decisions: list[EvolutionPromotionDecisionCard]
    recent_workflows: list[WorkflowRunCard]
    recent_codex_runs: list[CodexRunCard]
    supervisor_loops: list[SupervisorLoopCard]


class DashboardSystem(BaseModel):
    generated_at: datetime
    freshness: FreshnessPayload
    summary_cards: list[SummaryCard]
    highlights: list[str]
    providers: list[ProviderProfileCard]
    supervisor_loops: list[SupervisorLoopCard]
    recent_workflows: list[WorkflowRunCard]
    recent_codex_runs: list[CodexRunCard]
    runtime_config: list[RuntimeConfigCard]
    pending_config_proposals: list[RuntimeConfigProposalCard]
    recent_config_revisions: list[RuntimeConfigRevisionCard]
    owner_preferences: list[OwnerPreferenceCard]


class DashboardIncidents(BaseModel):
    generated_at: datetime
    freshness: FreshnessPayload
    summary_cards: list[SummaryCard]
    highlights: list[str]
    active_incidents: list[IncidentCard]
    recent_incidents: list[IncidentCard]
    pending_approvals: list[ApprovalCard]
