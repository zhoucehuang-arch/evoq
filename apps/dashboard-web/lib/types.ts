export type FreshnessState = "fresh" | "lagging" | "stale" | "broken";

export interface FreshnessPayload {
  state: FreshnessState;
  age_seconds: number;
  generated_at: string;
  note?: string | null;
}

export type DashboardFrontendErrorKind = "auth" | "unavailable" | "server" | "http" | "network" | "unknown";

export interface DashboardFrontendStatus {
  degraded: boolean;
  error_kind: DashboardFrontendErrorKind;
  detail: string;
  operator_action: string;
  status_code?: number | null;
}

export interface SummaryCard {
  label: string;
  value: string;
  tone: string;
  hint?: string | null;
}

export interface StrategySummary {
  candidates: number;
  staging: number;
  production: number;
  active_production: boolean;
}

export interface LearningSummary {
  principles: number;
  causal_cases: number;
  occupied_feature_cells: number;
  feature_coverage_pct: number;
  total_generations: number;
}

export interface SystemSummary {
  mode: string;
  risk_state: string;
  codex_queue_depth: number;
  active_goals: number;
  open_incidents: number;
  pending_approvals: number;
  active_overrides: number;
  repo_root: string;
}

export interface DashboardOverview {
  generated_at: string;
  freshness: FreshnessPayload;
  frontend_status?: DashboardFrontendStatus;
  headline: string;
  summary_cards: SummaryCard[];
  highlights: string[];
  strategy: StrategySummary;
  learning: LearningSummary;
  system: SystemSummary;
}

export interface DomainControlState {
  domain: string;
  is_paused: boolean;
  pending_approval_count: number;
  override_count: number;
  latest_reason?: string | null;
}

export interface ApprovalCard {
  id: string;
  approval_type: string;
  subject_id: string;
  requested_by: string;
  risk_level: string;
  decision_status: string;
  created_at: string;
}

export interface WorkflowRunCard {
  id: string;
  workflow_code: string;
  workflow_name: string;
  workflow_family: string;
  owner_role: string;
  status: string;
  started_at: string;
  ended_at?: string | null;
  latest_event_summary?: string | null;
}

export interface CodexRunCard {
  id: string;
  status: string;
  worker_class: string;
  execution_mode: string;
  strategy_mode: string;
  objective: string;
  current_attempt: number;
  max_iterations: number;
  queued_at: string;
  completed_at?: string | null;
  last_error?: string | null;
}

export interface SourceHealthCard {
  source_key: string;
  source_type: string;
  health_status: string;
  trust_score: number;
  freshness_score: number;
  last_validated_at?: string | null;
  notes?: string | null;
}

export interface LearningDocumentCard {
  id: string;
  codex_run_id?: string | null;
  workflow_run_id?: string | null;
  source_key: string;
  title: string;
  summary: string;
  status: string;
  source_type: string;
  supervisor_loop_key?: string | null;
  citation_count: number;
  evidence_count: number;
  confidence?: number | null;
  created_at: string;
}

export interface LearningInsightCard {
  id: string;
  document_id: string;
  codex_run_id?: string | null;
  workflow_run_id?: string | null;
  supervisor_loop_key?: string | null;
  topic_key: string;
  title: string;
  summary: string;
  status: string;
  promotion_state: string;
  evidence_count: number;
  citation_count: number;
  confidence?: number | null;
  quarantine_reason?: string | null;
  created_at: string;
}

export interface ProviderProfileCard {
  provider_key: string;
  display_name: string;
  health_status: string;
  api_style: string;
  is_primary: boolean;
  base_url?: string | null;
}

export interface SupervisorLoopCard {
  loop_key: string;
  workflow_code: string;
  domain: string;
  display_name: string;
  execution_mode: string;
  is_enabled: boolean;
  cadence_seconds: number;
  next_due_at?: string | null;
  last_completed_at?: string | null;
  last_status: string;
  failure_streak: number;
  last_error?: string | null;
}

export interface IncidentCard {
  id: string;
  title: string;
  summary: string;
  severity: string;
  status: string;
  created_at: string;
}

export interface OwnerPreferenceCard {
  preference_key: string;
  display_name: string;
  scope: string;
  updated_by: string;
  updated_at: string;
  value_preview: string;
  preview_lines: string[];
  contains_sensitive_fields: boolean;
}

export interface RuntimeConfigCard {
  target_type: string;
  target_key: string;
  display_name: string;
  category: string;
  risk_level: string;
  is_mutable: boolean;
  requires_restart: boolean;
  updated_at: string;
  updated_by?: string | null;
  value_preview: string;
  preview_lines: string[];
  contains_sensitive_fields: boolean;
}

export interface RuntimeConfigProposalCard {
  id: string;
  target_type: string;
  target_key: string;
  display_name: string;
  category: string;
  requested_by: string;
  change_summary: string;
  risk_level: string;
  requires_approval: boolean;
  approval_request_id?: string | null;
  status: string;
  created_at: string;
}

export interface RuntimeConfigRevisionCard {
  id: string;
  target_type: string;
  target_key: string;
  display_name: string;
  change_summary: string;
  applied_by: string;
  applied_at: string;
}

export interface StrategyLabMetrics {
  hypothesis_count: number;
  spec_count: number;
  paper_candidate_count: number;
  paper_running_count: number;
  live_candidate_count: number;
  production_count: number;
}

export interface StrategySpecCard {
  id: string;
  spec_code: string;
  title: string;
  target_market: string;
  current_stage: string;
  latest_backtest_gate?: string | null;
  latest_paper_gate?: string | null;
  created_at: string;
}

export interface BacktestRunCard {
  id: string;
  strategy_spec_id: string;
  dataset_range?: string | null;
  sample_size: number;
  gate_result: string;
  total_return_pct?: number | null;
  sharpe_ratio?: number | null;
  max_drawdown_pct?: number | null;
  created_at: string;
}

export interface PaperRunCard {
  id: string;
  strategy_spec_id: string;
  deployment_label: string;
  monitoring_days: number;
  gate_result: string;
  net_pnl_pct?: number | null;
  profit_factor?: number | null;
  max_drawdown_pct?: number | null;
  created_at: string;
}

export interface ExecutionReadinessCard {
  status: string;
  trading_allowed: boolean;
  market_calendar: string;
  market_session_label?: string | null;
  market_open: boolean;
  active_production_strategies: number;
  active_trading_overrides: number;
  open_provider_incidents: number;
  latest_provider_health?: string | null;
  broker_snapshot_age_seconds?: number | null;
  reconciliation_status?: string | null;
  reconciliation_halt_triggered: boolean;
  blocked_reasons: string[];
  warnings: string[];
}

export interface MarketSessionCard {
  id: string;
  market_calendar: string;
  market_timezone: string;
  session_label: string;
  is_market_open: boolean;
  trading_allowed: boolean;
  next_open_at?: string | null;
  next_close_at?: string | null;
  created_at: string;
}

export interface BrokerAccountSnapshotCard {
  id: string;
  provider_key: string;
  account_ref: string;
  environment: string;
  equity: number;
  cash: number;
  buying_power: number;
  gross_exposure: number;
  net_exposure: number;
  positions_count: number;
  open_orders_count: number;
  source_captured_at: string;
  source_age_seconds: number;
  created_at: string;
}

export interface ReconciliationRunCard {
  id: string;
  provider_key: string;
  account_ref: string;
  environment: string;
  equity_delta_abs: number;
  equity_delta_pct: number;
  position_delta_count: number;
  order_delta_count: number;
  blocking_reason?: string | null;
  halt_triggered: boolean;
  status: string;
  checked_at: string;
  created_at: string;
}

export interface BrokerSyncRunCard {
  id: string;
  provider_key: string;
  account_ref: string;
  environment: string;
  broker_adapter: string;
  sync_scope: string;
  synced_orders_count: number;
  synced_positions_count: number;
  unmanaged_orders_count: number;
  unmanaged_positions_count: number;
  missing_internal_orders_count: number;
  missing_internal_positions_count: number;
  status: string;
  completed_at?: string | null;
  created_at: string;
}

export interface ProviderIncidentCard {
  id: string;
  provider_key: string;
  title: string;
  severity: string;
  status: string;
  detected_at: string;
  resolved_at?: string | null;
}

export interface AllocationPolicyCard {
  policy_key: string;
  environment: string;
  scope: string;
  max_strategy_notional_pct: number;
  max_gross_exposure_pct: number;
  max_open_positions: number;
  max_open_orders: number;
  allow_short: boolean;
  allow_fractional: boolean;
  updated_at: string;
}

export interface OrderIntentCard {
  id: string;
  strategy_spec_id: string;
  provider_key: string;
  symbol: string;
  asset_type: string;
  instrument_key?: string | null;
  position_effect: string;
  side: string;
  quantity: number;
  reference_price: number;
  requested_notional: number;
  leg_count: number;
  broker_adapter: string;
  status: string;
  decision_reason?: string | null;
  created_at: string;
}

export interface OrderRecordCard {
  id: string;
  order_intent_id: string;
  broker_order_id: string;
  client_order_id?: string | null;
  parent_order_record_id?: string | null;
  symbol: string;
  asset_type: string;
  instrument_key?: string | null;
  position_effect: string;
  side: string;
  quantity: number;
  filled_quantity: number;
  avg_fill_price?: number | null;
  leg_count: number;
  status: string;
  submitted_at: string;
  broker_updated_at?: string | null;
  created_at: string;
}

export interface PositionCard {
  id: string;
  strategy_spec_id: string;
  symbol: string;
  underlying_symbol?: string | null;
  asset_type: string;
  instrument_key?: string | null;
  direction: string;
  quantity: number;
  avg_entry_price: number;
  market_price?: number | null;
  notional_value: number;
  realized_pnl: number;
  unrealized_pnl: number;
  status: string;
  last_synced_at: string;
  created_at: string;
}

export interface OptionLifecycleEventCard {
  id: string;
  event_type: string;
  symbol: string;
  underlying_symbol?: string | null;
  quantity: number;
  event_price?: number | null;
  cash_flow?: number | null;
  state_applied: boolean;
  review_required: boolean;
  status: string;
  occurred_at: string;
  notes?: string | null;
}

export interface ExpiringOptionPositionCard {
  id: string;
  strategy_spec_id: string;
  symbol: string;
  underlying_symbol?: string | null;
  instrument_key?: string | null;
  quantity: number;
  direction: string;
  expiration_date: string;
  days_to_expiry: number;
  market_price?: number | null;
  unrealized_pnl: number;
}

export interface DashboardTrading {
  generated_at: string;
  freshness: FreshnessPayload;
  frontend_status?: DashboardFrontendStatus;
  strategy_lab: StrategyLabMetrics;
  execution_readiness: ExecutionReadinessCard;
  allocation_policy?: AllocationPolicyCard | null;
  summary_cards: SummaryCard[];
  highlights: string[];
  domain_states: DomainControlState[];
  latest_account_snapshot?: BrokerAccountSnapshotCard | null;
  latest_reconciliation?: ReconciliationRunCard | null;
  latest_broker_sync?: BrokerSyncRunCard | null;
  recent_market_sessions: MarketSessionCard[];
  active_provider_incidents: ProviderIncidentCard[];
  recent_order_intents: OrderIntentCard[];
  recent_order_records: OrderRecordCard[];
  active_positions: PositionCard[];
  expiring_option_positions: ExpiringOptionPositionCard[];
  recent_option_events: OptionLifecycleEventCard[];
  recent_specs: StrategySpecCard[];
  recent_backtests: BacktestRunCard[];
  recent_paper_runs: PaperRunCard[];
}

export interface LearningGateMetrics {
  document_count: number;
  insight_count: number;
  ready_insight_count: number;
  quarantined_insight_count: number;
}

export interface DashboardLearning {
  generated_at: string;
  freshness: FreshnessPayload;
  frontend_status?: DashboardFrontendStatus;
  metrics: LearningGateMetrics;
  summary_cards: SummaryCard[];
  highlights: string[];
  sources: SourceHealthCard[];
  recent_documents: LearningDocumentCard[];
  recent_insights: LearningInsightCard[];
  supervisor_loops: SupervisorLoopCard[];
}

export interface EvolutionGovernanceMetrics {
  proposal_count: number;
  ready_for_review_count: number;
  active_canary_count: number;
  promoted_count: number;
  rolled_back_count: number;
}

export interface EvolutionProposalCard {
  id: string;
  title: string;
  target_surface: string;
  proposal_kind: string;
  proposal_state: string;
  risk_summary?: string | null;
  codex_run_id?: string | null;
  workflow_run_id?: string | null;
  created_at: string;
}

export interface EvolutionCanaryRunCard {
  id: string;
  proposal_id: string;
  lane_type: string;
  environment: string;
  traffic_pct: number;
  objective_drift_score?: number | null;
  rollback_ready: boolean;
  status: string;
  completed_at?: string | null;
  created_at: string;
}

export interface EvolutionPromotionDecisionCard {
  id: string;
  proposal_id: string;
  decision: string;
  decided_by: string;
  rationale: string;
  decided_at: string;
}

export interface DashboardEvolution {
  generated_at: string;
  freshness: FreshnessPayload;
  frontend_status?: DashboardFrontendStatus;
  metrics: EvolutionGovernanceMetrics;
  summary_cards: SummaryCard[];
  highlights: string[];
  recent_proposals: EvolutionProposalCard[];
  recent_canary_runs: EvolutionCanaryRunCard[];
  recent_promotion_decisions: EvolutionPromotionDecisionCard[];
  recent_workflows: WorkflowRunCard[];
  recent_codex_runs: CodexRunCard[];
  supervisor_loops: SupervisorLoopCard[];
}

export interface DashboardSystem {
  generated_at: string;
  freshness: FreshnessPayload;
  frontend_status?: DashboardFrontendStatus;
  summary_cards: SummaryCard[];
  highlights: string[];
  providers: ProviderProfileCard[];
  supervisor_loops: SupervisorLoopCard[];
  recent_workflows: WorkflowRunCard[];
  recent_codex_runs: CodexRunCard[];
  runtime_config: RuntimeConfigCard[];
  pending_config_proposals: RuntimeConfigProposalCard[];
  recent_config_revisions: RuntimeConfigRevisionCard[];
  owner_preferences: OwnerPreferenceCard[];
}

export interface DashboardIncidents {
  generated_at: string;
  freshness: FreshnessPayload;
  frontend_status?: DashboardFrontendStatus;
  summary_cards: SummaryCard[];
  highlights: string[];
  active_incidents: IncidentCard[];
  recent_incidents: IncidentCard[];
  pending_approvals: ApprovalCard[];
}
