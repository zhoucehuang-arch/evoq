from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class GoalCreate(BaseModel):
    title: str
    description: str
    mission_domain: str = "governance"
    success_metrics: dict[str, Any] = Field(default_factory=dict)
    failure_metrics: dict[str, Any] = Field(default_factory=dict)
    budget_scope: dict[str, Any] = Field(default_factory=dict)
    time_horizon: str | None = None
    created_by: str = "operator"
    origin_type: str = "discord"
    origin_id: str | None = None
    status: str = "proposed"


class GoalSummary(BaseModel):
    id: str
    title: str
    description: str
    mission_domain: str
    status: str
    created_by: str
    created_at: datetime


class IncidentCreate(BaseModel):
    title: str
    summary: str
    severity: str = "SEV-3"
    created_by: str = "system"
    origin_type: str = "system"
    origin_id: str | None = None
    status: str = "open"
    related_workflow_run_id: str | None = None


class IncidentSummary(BaseModel):
    id: str
    title: str
    summary: str
    severity: str
    status: str
    created_at: datetime


class ApprovalRequestCreate(BaseModel):
    approval_type: str
    subject_type: str
    subject_id: str
    requested_by: str
    risk_level: str = "R2"
    rationale: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    deadline: datetime | None = None
    created_by: str = "system"
    origin_type: str = "system"
    origin_id: str | None = None
    status: str = "pending"


class ApprovalRequestSummary(BaseModel):
    id: str
    approval_type: str
    subject_type: str
    subject_id: str
    requested_by: str
    risk_level: str
    decision_status: str
    created_at: datetime


class ApprovalDecisionCreate(BaseModel):
    decision: Literal["approved", "rejected"]
    decided_by: str
    reason: str | None = None


class ApprovalDecisionSummary(BaseModel):
    id: str
    approval_request_id: str
    decision: str
    decided_by: str
    decided_at: datetime
    approval_request_status: str
    effect_summary: str | None = None


class OperatorOverrideCreate(BaseModel):
    scope: str
    action: str
    reason: str
    activated_by: str
    expires_at: datetime | None = None
    created_by: str = "operator"
    origin_type: str = "discord"
    origin_id: str | None = None
    status: str = "active"


class OperatorOverrideSummary(BaseModel):
    id: str
    scope: str
    action: str
    reason: str
    activated_by: str
    is_active: bool
    created_at: datetime


class WorkflowRunSummary(BaseModel):
    id: str
    workflow_code: str
    workflow_name: str
    workflow_family: str
    owner_role: str
    status: str
    started_at: datetime
    ended_at: datetime | None = None
    latest_event_type: str | None = None
    latest_event_summary: str | None = None


class EvolutionImprovementProposalCreate(BaseModel):
    goal_id: str | None = None
    workflow_run_id: str | None = None
    codex_run_id: str | None = None
    title: str
    summary: str
    target_surface: str = "system"
    proposal_kind: str = "process_improvement"
    change_scope: list[str] = Field(default_factory=list)
    expected_benefit: dict[str, Any] = Field(default_factory=dict)
    evaluation_summary: dict[str, Any] = Field(default_factory=dict)
    risk_summary: str | None = None
    canary_plan: dict[str, Any] = Field(default_factory=dict)
    rollback_plan: dict[str, Any] = Field(default_factory=dict)
    objective_drift_checks: list[str] = Field(default_factory=list)
    proposal_state: str = "candidate"
    created_by: str = "operator"
    origin_type: str = "manual"
    origin_id: str | None = None
    status: str = "active"


class EvolutionImprovementProposalSummary(BaseModel):
    id: str
    goal_id: str | None = None
    workflow_run_id: str | None = None
    codex_run_id: str | None = None
    title: str
    summary: str
    target_surface: str
    proposal_kind: str
    change_scope: list[str]
    expected_benefit: dict[str, Any]
    evaluation_summary: dict[str, Any]
    risk_summary: str | None = None
    canary_plan: dict[str, Any]
    rollback_plan: dict[str, Any]
    objective_drift_checks: list[str]
    proposal_state: str
    status: str
    created_at: datetime


class EvolutionCanaryRunCreate(BaseModel):
    proposal_id: str
    lane_type: Literal["shadow", "canary"]
    environment: str = "paper"
    traffic_pct: float = 0.0
    success_metrics: dict[str, Any] = Field(default_factory=dict)
    objective_drift_score: float | None = None
    objective_drift_summary: str | None = None
    rollback_ready: bool = False
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_by: str = "operator"
    origin_type: str = "manual"
    origin_id: str | None = None
    status: str = "scheduled"


class EvolutionCanaryRunSummary(BaseModel):
    id: str
    proposal_id: str
    lane_type: str
    environment: str
    traffic_pct: float
    success_metrics: dict[str, Any]
    objective_drift_score: float | None = None
    objective_drift_summary: str | None = None
    rollback_ready: bool
    status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime


class EvolutionPromotionDecisionCreate(BaseModel):
    proposal_id: str
    decision: Literal["approved", "rejected", "shadow_approved", "canary_approved", "promoted", "rolled_back"]
    rationale: str
    decided_by: str
    decision_payload: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    origin_type: str = "manual"
    origin_id: str | None = None
    status: str = "recorded"


class EvolutionPromotionDecisionSummary(BaseModel):
    id: str
    proposal_id: str
    decision: str
    rationale: str
    decided_by: str
    decision_payload: dict[str, Any]
    status: str
    decided_at: datetime
    created_at: datetime


class ProviderProfileSummary(BaseModel):
    provider_key: str
    display_name: str
    health_status: str
    api_style: str
    is_primary: bool
    base_url: str | None = None
    capability_snapshot: dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime


class SourceHealthSummary(BaseModel):
    source_key: str
    source_type: str
    health_status: str
    trust_score: float
    freshness_score: float
    last_validated_at: datetime | None = None
    notes: str | None = None
    updated_at: datetime


class LearningDocumentSummary(BaseModel):
    id: str
    codex_run_id: str | None = None
    workflow_run_id: str | None = None
    supervisor_loop_key: str | None = None
    source_key: str
    source_type: str
    title: str
    summary: str
    status: str
    citation_count: int
    evidence_count: int
    confidence: float | None = None
    created_at: datetime


class LearningInsightSummary(BaseModel):
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


class StrategyHypothesisCreate(BaseModel):
    source_insight_id: str | None = None
    title: str
    thesis: str
    target_market: str
    mechanism: str
    risk_hypothesis: str | None = None
    evaluation_plan: list[str] = Field(default_factory=list)
    invalidation_conditions: list[str] = Field(default_factory=list)
    created_by: str = "operator"
    origin_type: str = "manual"
    origin_id: str | None = None
    status: str = "active"


class StrategyHypothesisSummary(BaseModel):
    id: str
    source_insight_id: str | None = None
    title: str
    thesis: str
    target_market: str
    current_stage: str
    status: str
    created_at: datetime


class StrategySpecCreate(BaseModel):
    hypothesis_id: str
    spec_code: str
    version_label: str = "v1"
    title: str
    target_market: str
    signal_logic: str
    risk_rules: dict[str, Any] = Field(default_factory=dict)
    data_requirements: list[str] = Field(default_factory=list)
    invalidation_conditions: list[str] = Field(default_factory=list)
    execution_constraints: dict[str, Any] = Field(default_factory=dict)
    created_by: str = "operator"
    origin_type: str = "manual"
    origin_id: str | None = None
    status: str = "active"


class StrategySpecSummary(BaseModel):
    id: str
    hypothesis_id: str
    spec_code: str
    version_label: str
    title: str
    target_market: str
    current_stage: str
    latest_backtest_gate: str | None = None
    latest_paper_gate: str | None = None
    status: str
    created_at: datetime


class BacktestRunCreate(BaseModel):
    strategy_spec_id: str
    dataset_range: str | None = None
    sample_size: int = 0
    metrics_json: dict[str, Any] = Field(default_factory=dict)
    artifact_path: str | None = None
    created_by: str = "operator"
    origin_type: str = "manual"
    origin_id: str | None = None
    status: str = "recorded"


class BacktestRunSummary(BaseModel):
    id: str
    strategy_spec_id: str
    dataset_range: str | None = None
    sample_size: int
    gate_result: str
    gate_notes: list[str]
    metrics_json: dict[str, Any]
    artifact_path: str | None = None
    created_at: datetime


class PaperRunCreate(BaseModel):
    strategy_spec_id: str
    deployment_label: str
    monitoring_days: int = 0
    metrics_json: dict[str, Any] = Field(default_factory=dict)
    capital_allocated: float | None = None
    created_by: str = "operator"
    origin_type: str = "manual"
    origin_id: str | None = None
    status: str = "paper_running"


class PaperRunSummary(BaseModel):
    id: str
    strategy_spec_id: str
    deployment_label: str
    monitoring_days: int
    gate_result: str
    gate_notes: list[str]
    metrics_json: dict[str, Any]
    capital_allocated: float | None = None
    status: str
    created_at: datetime


class PromotionDecisionCreate(BaseModel):
    strategy_spec_id: str
    target_stage: str
    decision: str
    rationale: str
    evidence_refs: list[dict[str, Any]] = Field(default_factory=list)
    decided_by: str
    paper_run_id: str | None = None
    created_by: str | None = None
    origin_type: str = "manual"
    origin_id: str | None = None
    status: str | None = None


class PromotionDecisionSummary(BaseModel):
    id: str
    strategy_spec_id: str
    paper_run_id: str | None = None
    target_stage: str
    decision: str
    rationale: str
    decided_by: str
    decided_at: datetime
    created_at: datetime


class WithdrawalDecisionCreate(BaseModel):
    strategy_spec_id: str
    reason: str
    evidence_refs: list[dict[str, Any]] = Field(default_factory=list)
    decided_by: str
    replacement_strategy_spec_id: str | None = None
    created_by: str | None = None
    origin_type: str = "manual"
    origin_id: str | None = None
    status: str | None = None


class WithdrawalDecisionSummary(BaseModel):
    id: str
    strategy_spec_id: str
    replacement_strategy_spec_id: str | None = None
    reason: str
    decided_by: str
    decided_at: datetime
    created_at: datetime


class MarketSessionStateCreate(BaseModel):
    market_calendar: str
    market_timezone: str
    session_label: str
    is_market_open: bool
    trading_allowed: bool
    next_open_at: datetime | None = None
    next_close_at: datetime | None = None
    created_by: str = "system"
    origin_type: str = "system"
    origin_id: str | None = None
    status: str = "observed"


class MarketSessionStateSummary(BaseModel):
    id: str
    market_calendar: str
    market_timezone: str
    session_label: str
    is_market_open: bool
    trading_allowed: bool
    next_open_at: datetime | None = None
    next_close_at: datetime | None = None
    created_at: datetime


class BrokerAccountSnapshotCreate(BaseModel):
    provider_key: str
    account_ref: str
    environment: str = "paper"
    equity: float = 0.0
    cash: float = 0.0
    buying_power: float = 0.0
    gross_exposure: float = 0.0
    net_exposure: float = 0.0
    positions_count: int = 0
    open_orders_count: int = 0
    source_captured_at: datetime | None = None
    source_age_seconds: int = 0
    payload: dict[str, Any] = Field(default_factory=dict)
    created_by: str = "system"
    origin_type: str = "system"
    origin_id: str | None = None
    status: str = "captured"


class BrokerAccountSnapshotSummary(BaseModel):
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
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ReconciliationRunCreate(BaseModel):
    provider_key: str
    account_ref: str
    account_snapshot_id: str | None = None
    environment: str = "paper"
    internal_equity: float = 0.0
    broker_equity: float | None = None
    internal_positions_count: int = 0
    broker_positions_count: int | None = None
    internal_open_orders_count: int = 0
    broker_open_orders_count: int | None = None
    equity_warning_pct: float = 0.5
    equity_block_pct: float = 2.0
    notes: list[str] = Field(default_factory=list)
    checked_at: datetime | None = None
    trigger_halt_on_blocked: bool = True
    created_by: str = "system"
    origin_type: str = "system"
    origin_id: str | None = None
    status: str = "recorded"


class ReconciliationRunSummary(BaseModel):
    id: str
    provider_key: str
    account_ref: str
    account_snapshot_id: str | None = None
    environment: str
    internal_equity: float
    broker_equity: float
    equity_delta_abs: float
    equity_delta_pct: float
    internal_positions_count: int
    broker_positions_count: int
    internal_open_orders_count: int
    broker_open_orders_count: int
    position_delta_count: int
    order_delta_count: int
    blocking_reason: str | None = None
    notes: list[str]
    halt_triggered: bool
    status: str
    checked_at: datetime
    created_at: datetime


class BrokerSyncRunCreate(BaseModel):
    provider_key: str
    account_ref: str
    broker_adapter: str | None = None
    environment: str = "paper"
    full_sync: bool = True
    created_by: str = "system"
    origin_type: str = "system"
    origin_id: str | None = None
    status: str = "requested"


class BrokerSyncRunSummary(BaseModel):
    id: str
    provider_key: str
    account_ref: str
    environment: str
    broker_adapter: str
    sync_scope: str
    account_snapshot_id: str | None = None
    synced_orders_count: int
    synced_positions_count: int
    unmanaged_orders_count: int
    unmanaged_positions_count: int
    missing_internal_orders_count: int
    missing_internal_positions_count: int
    notes: list[str]
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    created_at: datetime


class ProviderIncidentCreate(BaseModel):
    provider_key: str
    title: str
    summary: str
    severity: str = "SEV-2"
    health_status: str = "degraded"
    created_by: str = "system"
    origin_type: str = "system"
    origin_id: str | None = None
    status: str = "open"


class ProviderIncidentResolve(BaseModel):
    resolved_by: str
    resolution_note: str | None = None
    health_status: str = "healthy"


class ProviderIncidentSummary(BaseModel):
    id: str
    provider_key: str
    title: str
    summary: str
    severity: str
    status: str
    detected_at: datetime
    resolved_at: datetime | None = None
    created_at: datetime


class ExecutionReadinessSummary(BaseModel):
    status: str
    trading_allowed: bool
    market_calendar: str
    market_session_label: str | None = None
    market_open: bool
    active_production_strategies: int
    blocked_reasons: list[str]
    warnings: list[str]
    active_trading_overrides: int
    open_provider_incidents: int
    latest_provider_health: str | None = None
    latest_market_state_at: datetime | None = None
    latest_account_snapshot_at: datetime | None = None
    latest_reconciliation_at: datetime | None = None
    broker_snapshot_age_seconds: int | None = None
    reconciliation_status: str | None = None
    reconciliation_halt_triggered: bool = False


class InstrumentDefinitionUpsert(BaseModel):
    instrument_key: str | None = None
    symbol: str
    display_symbol: str | None = None
    instrument_type: Literal["equity", "etf", "option", "leveraged_etf", "inverse_etf", "crypto", "custom"] = "equity"
    venue: str | None = None
    currency: str = "USD"
    underlying_symbol: str | None = None
    option_right: Literal["call", "put"] | None = None
    option_style: Literal["american", "european"] | None = None
    expiration_date: date | None = None
    strike_price: float | None = None
    contract_multiplier: float = 1.0
    leverage_ratio: float = 1.0
    inverse_exposure: bool = False
    is_marginable: bool = True
    is_shortable: bool = False
    metadata_payload: dict[str, Any] = Field(default_factory=dict)
    created_by: str = "operator"
    origin_type: str = "manual"
    origin_id: str | None = None
    status: str = "active"

    @model_validator(mode="after")
    def validate_option_fields(self) -> "InstrumentDefinitionUpsert":
        if self.instrument_type == "option":
            missing = []
            if not self.underlying_symbol:
                missing.append("underlying_symbol")
            if not self.option_right:
                missing.append("option_right")
            if self.expiration_date is None:
                missing.append("expiration_date")
            if self.strike_price is None:
                missing.append("strike_price")
            if missing:
                raise ValueError(f"Option instruments require: {', '.join(missing)}")
        return self


class InstrumentDefinitionSummary(BaseModel):
    id: str
    instrument_key: str
    symbol: str
    display_symbol: str
    instrument_type: str
    venue: str | None = None
    currency: str
    underlying_symbol: str | None = None
    option_right: str | None = None
    option_style: str | None = None
    expiration_date: date | None = None
    strike_price: float | None = None
    contract_multiplier: float
    leverage_ratio: float
    inverse_exposure: bool
    is_marginable: bool
    is_shortable: bool
    metadata_payload: dict[str, Any] = Field(default_factory=dict)
    status: str
    updated_at: datetime


class BrokerCapabilityUpsert(BaseModel):
    capability_key: str
    provider_key: str
    broker_adapter: str
    account_ref: str | None = None
    environment: str = "paper"
    account_mode: str = "cash"
    supports_equities: bool = True
    supports_etfs: bool = True
    supports_fractional: bool = True
    supports_short: bool = False
    supports_margin: bool = False
    supports_options: bool = False
    supports_multi_leg_options: bool = False
    supports_option_exercise: bool = False
    supports_option_assignment_events: bool = False
    supports_live_trading: bool = False
    supports_paper_trading: bool = True
    notes: str | None = None
    created_by: str = "operator"
    origin_type: str = "manual"
    origin_id: str | None = None
    status: str = "active"


class BrokerCapabilitySummary(BaseModel):
    id: str
    capability_key: str
    provider_key: str
    broker_adapter: str
    account_ref: str | None = None
    environment: str
    account_mode: str
    supports_equities: bool
    supports_etfs: bool
    supports_fractional: bool
    supports_short: bool
    supports_margin: bool
    supports_options: bool
    supports_multi_leg_options: bool
    supports_option_exercise: bool
    supports_option_assignment_events: bool
    supports_live_trading: bool
    supports_paper_trading: bool
    notes: str | None = None
    status: str
    updated_at: datetime


class AllocationPolicyUpsert(BaseModel):
    policy_key: str
    environment: str = "paper"
    scope: str = "global"
    strategy_spec_id: str | None = None
    provider_key: str | None = None
    account_ref: str | None = None
    max_strategy_notional_pct: float = 0.05
    max_gross_exposure_pct: float = 0.8
    max_open_positions: int = 8
    max_open_orders: int = 8
    allow_short: bool = False
    allow_fractional: bool = True
    notes: str | None = None
    created_by: str = "operator"
    origin_type: str = "manual"
    origin_id: str | None = None
    status: str = "active"


class AllocationPolicySummary(BaseModel):
    id: str
    policy_key: str
    environment: str
    scope: str
    strategy_spec_id: str | None = None
    provider_key: str | None = None
    account_ref: str | None = None
    max_strategy_notional_pct: float
    max_gross_exposure_pct: float
    max_open_positions: int
    max_open_orders: int
    allow_short: bool
    allow_fractional: bool
    notes: str | None = None
    status: str
    updated_at: datetime


class OrderLegCreate(BaseModel):
    symbol: str
    instrument_id: str | None = None
    instrument_key: str | None = None
    asset_type: str = "option"
    side: Literal["buy", "sell"]
    position_effect: Literal["auto", "open", "close", "reduce", "increase"] = "auto"
    quantity: float
    reference_price: float
    ratio_quantity: float = 1.0


class OrderLegSummary(BaseModel):
    id: str
    order_intent_id: str | None = None
    order_record_id: str | None = None
    leg_index: int
    symbol: str
    instrument_id: str | None = None
    instrument_key: str | None = None
    underlying_symbol: str | None = None
    asset_type: str
    side: str
    position_effect: str
    quantity: float
    ratio_quantity: float
    reference_price: float
    requested_notional: float
    status: str
    created_at: datetime


class OrderIntentCreate(BaseModel):
    strategy_spec_id: str
    symbol: str
    side: Literal["buy", "sell"]
    quantity: float
    reference_price: float
    instrument_id: str | None = None
    instrument_key: str | None = None
    asset_type: str = "equity"
    position_effect: Literal["auto", "open", "close", "reduce", "increase"] = "auto"
    order_type: str = "market"
    time_in_force: str = "day"
    provider_key: str | None = None
    account_ref: str | None = None
    environment: str = "paper"
    broker_adapter: str | None = None
    allocation_policy_key: str | None = None
    limit_price: float | None = None
    stop_price: float | None = None
    rationale: str | None = None
    legs: list[OrderLegCreate] = Field(default_factory=list)
    signal_payload: dict[str, Any] = Field(default_factory=dict)
    created_by: str = "system"
    origin_type: str = "system"
    origin_id: str | None = None
    status: str = "requested"


class OrderIntentSummary(BaseModel):
    id: str
    strategy_spec_id: str
    allocation_policy_id: str | None = None
    provider_key: str
    account_ref: str
    environment: str
    broker_adapter: str
    symbol: str
    instrument_id: str | None = None
    instrument_key: str | None = None
    underlying_symbol: str | None = None
    asset_type: str
    position_effect: str
    side: str
    order_type: str
    time_in_force: str
    quantity: float
    reference_price: float
    requested_notional: float
    decision_reason: str | None = None
    rationale: str | None = None
    leg_count: int = 0
    legs: list[OrderLegSummary] = Field(default_factory=list)
    status: str
    created_at: datetime


class OrderCancelCreate(BaseModel):
    reason: str
    created_by: str = "operator"
    origin_type: str = "manual"
    origin_id: str | None = None


class OrderReplaceCreate(BaseModel):
    quantity: float
    reference_price: float
    order_type: str | None = None
    time_in_force: str | None = None
    limit_price: float | None = None
    stop_price: float | None = None
    rationale: str | None = None
    created_by: str = "operator"
    origin_type: str = "manual"
    origin_id: str | None = None


class OrderRecordSummary(BaseModel):
    id: str
    order_intent_id: str
    strategy_spec_id: str
    provider_key: str
    account_ref: str
    environment: str
    broker_order_id: str
    client_order_id: str | None = None
    parent_order_record_id: str | None = None
    last_sync_run_id: str | None = None
    symbol: str
    instrument_id: str | None = None
    instrument_key: str | None = None
    underlying_symbol: str | None = None
    asset_type: str
    position_effect: str
    side: str
    order_type: str
    time_in_force: str
    quantity: float
    filled_quantity: float
    requested_notional: float
    avg_fill_price: float | None = None
    leg_count: int = 0
    legs: list[OrderLegSummary] = Field(default_factory=list)
    status: str
    submitted_at: datetime
    broker_updated_at: datetime | None = None
    created_at: datetime


class PositionRecordSummary(BaseModel):
    id: str
    strategy_spec_id: str
    provider_key: str
    account_ref: str
    environment: str
    symbol: str
    instrument_id: str | None = None
    instrument_key: str | None = None
    underlying_symbol: str | None = None
    asset_type: str
    direction: str
    quantity: float
    avg_entry_price: float
    market_price: float | None = None
    notional_value: float
    realized_pnl: float
    unrealized_pnl: float
    status: str
    opened_at: datetime
    closed_at: datetime | None = None
    last_synced_at: datetime
    last_sync_run_id: str | None = None
    created_at: datetime


class OptionLifecycleEventCreate(BaseModel):
    event_type: Literal["expiration", "exercise", "assignment"]
    provider_key: str
    account_ref: str
    environment: str = "paper"
    symbol: str
    position_id: str | None = None
    strategy_spec_id: str | None = None
    instrument_id: str | None = None
    instrument_key: str | None = None
    quantity: float | None = None
    event_price: float | None = None
    cash_flow: float | None = None
    notes: str | None = None
    metadata_payload: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime | None = None
    created_by: str = "system"
    origin_type: str = "system"
    origin_id: str | None = None
    status: str = "recorded"

    @model_validator(mode="after")
    def validate_locator(self) -> "OptionLifecycleEventCreate":
        if not self.position_id and not self.instrument_id and not self.instrument_key:
            raise ValueError("Option lifecycle events require position_id, instrument_id, or instrument_key.")
        return self


class OptionLifecycleEventSummary(BaseModel):
    id: str
    event_type: str
    provider_key: str
    account_ref: str
    environment: str
    symbol: str
    underlying_symbol: str | None = None
    position_id: str | None = None
    strategy_spec_id: str | None = None
    instrument_id: str | None = None
    instrument_key: str | None = None
    quantity: float
    event_price: float | None = None
    cash_flow: float | None = None
    state_applied: bool
    review_required: bool
    applied_position_id: str | None = None
    resulting_symbol: str | None = None
    resulting_instrument_key: str | None = None
    notes: str | None = None
    metadata_payload: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime
    status: str
    created_at: datetime


class RuntimeConfigEntrySummary(BaseModel):
    target_type: str
    target_key: str
    display_name: str
    category: str
    risk_level: str
    is_mutable: bool
    requires_restart: bool
    value_json: dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime
    updated_by: str | None = None


class RuntimeConfigProposalCreate(BaseModel):
    target_type: Literal["system_policy", "owner_preference", "supervisor_loop"]
    target_key: str
    requested_by: str = "operator"
    rationale: str | None = None
    proposed_value_json: dict[str, Any] = Field(default_factory=dict)
    change_summary: str | None = None
    created_by: str | None = None
    origin_type: str = "manual"
    origin_id: str | None = None
    status: str = "proposed"


class RuntimeConfigProposalSummary(BaseModel):
    id: str
    target_type: str
    target_key: str
    display_name: str
    category: str
    requested_by: str
    rationale: str | None = None
    change_summary: str
    risk_level: str
    requires_approval: bool
    approval_request_id: str | None = None
    current_value_json: dict[str, Any] = Field(default_factory=dict)
    proposed_value_json: dict[str, Any] = Field(default_factory=dict)
    status: str
    created_at: datetime


class RuntimeConfigRevisionSummary(BaseModel):
    id: str
    proposal_id: str | None = None
    target_type: str
    target_key: str
    display_name: str
    change_summary: str
    previous_value_json: dict[str, Any] = Field(default_factory=dict)
    applied_value_json: dict[str, Any] = Field(default_factory=dict)
    applied_by: str
    applied_at: datetime


class RuntimeConfigRollbackRequest(BaseModel):
    requested_by: str = "operator"
    rationale: str | None = None


class OwnerPreferenceUpsert(BaseModel):
    preference_key: str
    display_name: str
    value_json: dict[str, Any] = Field(default_factory=dict)
    scope: str = "owner"
    updated_by: str = "operator"
    notes: str | None = None
    status: str = "active"


class OwnerPreferenceSummary(BaseModel):
    id: str
    preference_key: str
    display_name: str
    scope: str
    value_json: dict[str, Any]
    updated_by: str
    updated_at: datetime
    notes: str | None = None


class SupervisorLoopSummary(BaseModel):
    id: str
    loop_key: str
    workflow_code: str
    domain: str
    display_name: str
    handler_key: str
    cadence_seconds: int
    priority: int
    execution_mode: str
    is_enabled: bool
    next_due_at: datetime | None = None
    last_started_at: datetime | None = None
    last_completed_at: datetime | None = None
    last_status: str
    last_error: str | None = None
    failure_streak: int
    max_failure_streak: int
    budget_scope: dict[str, Any] = Field(default_factory=dict)
    stop_conditions: dict[str, Any] = Field(default_factory=dict)
