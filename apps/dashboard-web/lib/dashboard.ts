import "server-only";

import {
  DashboardEvolution,
  DashboardIncidents,
  DashboardLearning,
  DashboardOverview,
  DashboardSystem,
  DashboardTrading,
  FreshnessPayload,
} from "@/lib/types";

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");
const DASHBOARD_API_TOKEN = (process.env.QE_DASHBOARD_API_TOKEN ?? "").trim();

export async function fetchOverview(): Promise<DashboardOverview> {
  return fetchJson("/api/v1/dashboard/overview", buildFallbackOverview);
}

export async function fetchTrading(): Promise<DashboardTrading> {
  return fetchJson("/api/v1/dashboard/trading", buildFallbackTrading);
}

export async function fetchLearning(): Promise<DashboardLearning> {
  return fetchJson("/api/v1/dashboard/learning", buildFallbackLearning);
}

export async function fetchEvolution(): Promise<DashboardEvolution> {
  return fetchJson("/api/v1/dashboard/evolution", buildFallbackEvolution);
}

export async function fetchSystem(): Promise<DashboardSystem> {
  return fetchJson("/api/v1/dashboard/system", buildFallbackSystem);
}

export async function fetchIncidents(): Promise<DashboardIncidents> {
  return fetchJson("/api/v1/dashboard/incidents", buildFallbackIncidents);
}

async function fetchJson<T>(path: string, fallback: (reason: string) => T): Promise<T> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      cache: "no-store",
      headers: DASHBOARD_API_TOKEN ? { "X-Quant-Evo-Dashboard-Token": DASHBOARD_API_TOKEN } : undefined,
    });

    if (!response.ok) {
      throw new Error(`API returned ${response.status}`);
    }

    return (await response.json()) as T;
  } catch (error) {
    return fallback(error instanceof Error ? error.message : "Dashboard API unavailable");
  }
}

function buildFallbackOverview(reason: string): DashboardOverview {
  const generatedAt = new Date().toISOString();
  return {
    generated_at: generatedAt,
    freshness: buildBrokenFreshness(generatedAt, reason),
    headline: "Dashboard API is unavailable, so the frontend is showing a degraded fallback view.",
    summary_cards: [
      { label: "Production strategies", value: "0", tone: "warn", hint: "Waiting for API" },
      { label: "Pending approvals", value: "0", tone: "neutral", hint: "Waiting for API" },
      { label: "Principle memory", value: "0", tone: "neutral", hint: "Waiting for API" },
      { label: "Active overrides", value: "0", tone: "warn", hint: "Waiting for API" },
    ],
    highlights: [
      "The frontend is running, but the backend aggregation API could not be reached.",
      "Check that core-api is online and that NEXT_PUBLIC_API_BASE_URL points to the right host.",
      "Broken freshness means the UI should not pretend to have live control-plane data.",
    ],
    strategy: {
      candidates: 0,
      staging: 0,
      production: 0,
      active_production: false,
    },
    learning: {
      principles: 0,
      causal_cases: 0,
      occupied_feature_cells: 0,
      feature_coverage_pct: 0,
      total_generations: 0,
    },
    system: {
      mode: "degraded",
      risk_state: "observe",
      codex_queue_depth: 0,
      active_goals: 0,
      open_incidents: 0,
      pending_approvals: 0,
      active_overrides: 0,
      repo_root: "unavailable",
    },
  };
}

function buildFallbackTrading(reason: string): DashboardTrading {
  const generatedAt = new Date().toISOString();
  return {
    generated_at: generatedAt,
    freshness: buildBrokenFreshness(generatedAt, reason),
    strategy_lab: {
      hypothesis_count: 0,
      spec_count: 0,
      paper_candidate_count: 0,
      paper_running_count: 0,
      live_candidate_count: 0,
      production_count: 0,
    },
    execution_readiness: {
      status: "blocked",
      trading_allowed: false,
      market_calendar: "unconfigured",
      market_session_label: null,
      market_open: false,
      active_production_strategies: 0,
      active_trading_overrides: 0,
      open_provider_incidents: 0,
      latest_provider_health: null,
      broker_snapshot_age_seconds: null,
      reconciliation_status: null,
      reconciliation_halt_triggered: false,
      blocked_reasons: ["Trading API is unavailable."],
      warnings: [],
    },
    allocation_policy: null,
    summary_cards: [],
    highlights: ["Trading view is waiting for backend strategy lifecycle data."],
    domain_states: [],
    latest_account_snapshot: null,
    latest_reconciliation: null,
    latest_broker_sync: null,
    recent_market_sessions: [],
    active_provider_incidents: [],
    recent_order_intents: [],
    recent_order_records: [],
    active_positions: [],
    expiring_option_positions: [],
    recent_option_events: [],
    recent_specs: [],
    recent_backtests: [],
    recent_paper_runs: [],
  };
}

function buildFallbackLearning(reason: string): DashboardLearning {
  const generatedAt = new Date().toISOString();
  return {
    generated_at: generatedAt,
    freshness: buildBrokenFreshness(generatedAt, reason),
    metrics: {
      document_count: 0,
      insight_count: 0,
      ready_insight_count: 0,
      quarantined_insight_count: 0,
    },
    summary_cards: [],
    highlights: ["Learning view is waiting for backend learning state."],
    sources: [],
    recent_documents: [],
    recent_insights: [],
    supervisor_loops: [],
  };
}

function buildFallbackEvolution(reason: string): DashboardEvolution {
  const generatedAt = new Date().toISOString();
  return {
    generated_at: generatedAt,
    freshness: buildBrokenFreshness(generatedAt, reason),
    metrics: {
      proposal_count: 0,
      ready_for_review_count: 0,
      active_canary_count: 0,
      promoted_count: 0,
      rolled_back_count: 0,
    },
    summary_cards: [],
    highlights: ["Evolution view is waiting for backend workflow state."],
    recent_proposals: [],
    recent_canary_runs: [],
    recent_promotion_decisions: [],
    recent_workflows: [],
    recent_codex_runs: [],
    supervisor_loops: [],
  };
}

function buildFallbackSystem(reason: string): DashboardSystem {
  const generatedAt = new Date().toISOString();
  return {
    generated_at: generatedAt,
    freshness: buildBrokenFreshness(generatedAt, reason),
    summary_cards: [],
    highlights: ["System view is waiting for backend authority-core state."],
    providers: [],
    supervisor_loops: [],
    recent_workflows: [],
    recent_codex_runs: [],
    runtime_config: [],
    pending_config_proposals: [],
    recent_config_revisions: [],
    owner_preferences: [],
  };
}

function buildFallbackIncidents(reason: string): DashboardIncidents {
  const generatedAt = new Date().toISOString();
  return {
    generated_at: generatedAt,
    freshness: buildBrokenFreshness(generatedAt, reason),
    summary_cards: [],
    highlights: ["Incident view is waiting for backend incident state."],
    active_incidents: [],
    recent_incidents: [],
    pending_approvals: [],
  };
}

function buildBrokenFreshness(generatedAt: string, reason: string): FreshnessPayload {
  return {
    state: "broken",
    age_seconds: 0,
    generated_at: generatedAt,
    note: reason,
  };
}
