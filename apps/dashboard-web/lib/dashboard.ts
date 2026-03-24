import "server-only";

import {
  DashboardEvolution,
  DashboardFrontendStatus,
  DashboardIncidents,
  DashboardLearning,
  DashboardOverview,
  DashboardSystem,
  DashboardTrading,
  FreshnessPayload,
} from "@/lib/types";

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");
const DASHBOARD_API_TOKEN = (process.env.QE_DASHBOARD_API_TOKEN ?? "").trim();
const DASHBOARD_DEMO_MODE = ["1", "true", "yes", "on"].includes(
  (process.env.QE_DASHBOARD_DEMO_MODE ?? process.env.NEXT_PUBLIC_DASHBOARD_DEMO_MODE ?? "").trim().toLowerCase(),
);

export async function fetchOverview(options?: { demo?: boolean }): Promise<DashboardOverview> {
  if (DASHBOARD_DEMO_MODE || options?.demo) {
    return buildDemoOverview();
  }
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

type DashboardFetchFailure = {
  kind: DashboardFrontendStatus["error_kind"];
  detail: string;
  operator_action: string;
  status_code?: number | null;
};

async function fetchJson<T>(path: string, fallback: (failure: DashboardFetchFailure) => T): Promise<T> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      cache: "no-store",
      headers: DASHBOARD_API_TOKEN ? { "X-Quant-Evo-Dashboard-Token": DASHBOARD_API_TOKEN } : undefined,
    });

    if (!response.ok) {
      return fallback(await classifyHttpFailure(response));
    }

    return (await response.json()) as T;
  } catch (error) {
    return fallback(classifyThrownFailure(error));
  }
}

function buildDemoOverview(): DashboardOverview {
  const generatedAt = new Date().toISOString();
  return {
    generated_at: generatedAt,
    freshness: {
      state: "fresh",
      age_seconds: 12,
      generated_at: generatedAt,
      note: "Demo preview mode",
    },
    headline: "Single-VPS authority core is healthy, research loops are active, and live execution is still gated behind approvals.",
    summary_cards: [
      { label: "Production strategies", value: "4", tone: "good", hint: "2 equities, 2 options sleeves live-ready" },
      { label: "Pending approvals", value: "2", tone: "warn", hint: "Live rollout and config promotion waiting" },
      { label: "Market mode", value: "us", tone: "good", hint: "US equities + options deployment" },
      { label: "Learning docs", value: "128", tone: "good", hint: "Fresh research and post-mortems retained" },
      { label: "Ready insights", value: "9", tone: "good", hint: "Ready for governance review" },
      { label: "Principle memory", value: "34", tone: "good", hint: "Promoted, durable operating knowledge" },
      { label: "Active overrides", value: "1", tone: "warn", hint: "One guarded exposure override" },
    ],
    highlights: [
      "Discord owner control, dashboard monitoring, and governed research loops are online.",
      "The runtime is still in paper-first posture even though multiple sleeves are execution-ready.",
      "Codex work is queued behind governed approvals instead of acting as an unbounded control plane.",
      "Long-term memory remains separated from raw research intake so promotion stays explicit.",
    ],
    strategy: {
      candidates: 12,
      staging: 5,
      production: 4,
      active_production: true,
    },
    learning: {
      principles: 34,
      causal_cases: 91,
      document_count: 128,
      insight_count: 48,
      ready_insight_count: 9,
      quarantined_insight_count: 3,
      occupied_feature_cells: 22,
      feature_coverage_pct: 36.7,
      total_generations: 187,
    },
    system: {
      mode: "paper_live_guarded",
      risk_state: "normal",
      deployment_market_mode: "us",
      active_sleeves: ["equities", "options", "event"],
      market_calendar: "XNYS",
      market_timezone: "America/New_York",
      codex_queue_depth: 2,
      active_goals: 6,
      open_incidents: 1,
      pending_approvals: 2,
      active_overrides: 1,
      repo_root: "/opt/evoq",
    },
  };
}

function buildFallbackOverview(failure: DashboardFetchFailure): DashboardOverview {
  const generatedAt = new Date().toISOString();
  return {
    generated_at: generatedAt,
    freshness: buildBrokenFreshness(generatedAt, failure),
    frontend_status: buildFrontendStatus(failure),
    headline: "Dashboard API is unavailable, so the frontend is showing a degraded fallback view.",
    summary_cards: [
      { label: "Production strategies", value: "0", tone: "warn", hint: "Waiting for API" },
      { label: "Pending approvals", value: "0", tone: "neutral", hint: "Waiting for API" },
      { label: "Market mode", value: "unconfigured", tone: "neutral", hint: "Waiting for API" },
      { label: "Learning docs", value: "0", tone: "warn", hint: "Waiting for API" },
      { label: "Ready insights", value: "0", tone: "neutral", hint: "Waiting for API" },
      { label: "Principle memory", value: "0", tone: "neutral", hint: "Repo-backed memory is waiting for API" },
      { label: "Active overrides", value: "0", tone: "warn", hint: "Waiting for API" },
    ],
    highlights: [
      "The frontend is running, but the backend aggregation API could not be reached.",
      failure.operator_action,
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
      document_count: 0,
      insight_count: 0,
      ready_insight_count: 0,
      quarantined_insight_count: 0,
      occupied_feature_cells: 0,
      feature_coverage_pct: 0,
      total_generations: 0,
    },
    system: {
      mode: "degraded",
      risk_state: "observe",
      deployment_market_mode: "unconfigured",
      active_sleeves: [],
      market_calendar: null,
      market_timezone: null,
      codex_queue_depth: 0,
      active_goals: 0,
      open_incidents: 0,
      pending_approvals: 0,
      active_overrides: 0,
      repo_root: "unavailable",
    },
  };
}

function buildFallbackTrading(failure: DashboardFetchFailure): DashboardTrading {
  const generatedAt = new Date().toISOString();
  return {
    generated_at: generatedAt,
    freshness: buildBrokenFreshness(generatedAt, failure),
    frontend_status: buildFrontendStatus(failure),
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

function buildFallbackLearning(failure: DashboardFetchFailure): DashboardLearning {
  const generatedAt = new Date().toISOString();
  return {
    generated_at: generatedAt,
    freshness: buildBrokenFreshness(generatedAt, failure),
    frontend_status: buildFrontendStatus(failure),
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

function buildFallbackEvolution(failure: DashboardFetchFailure): DashboardEvolution {
  const generatedAt = new Date().toISOString();
  return {
    generated_at: generatedAt,
    freshness: buildBrokenFreshness(generatedAt, failure),
    frontend_status: buildFrontendStatus(failure),
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

function buildFallbackSystem(failure: DashboardFetchFailure): DashboardSystem {
  const generatedAt = new Date().toISOString();
  return {
    generated_at: generatedAt,
    freshness: buildBrokenFreshness(generatedAt, failure),
    frontend_status: buildFrontendStatus(failure),
    summary_cards: [
      { label: "Providers", value: "unknown", tone: "warn", hint: "Waiting for API" },
      { label: "Supervisor loops", value: "unknown", tone: "warn", hint: "Waiting for API" },
      { label: "Config proposals", value: "unknown", tone: "neutral", hint: "Waiting for API" },
      { label: "Owner preferences", value: "unknown", tone: "neutral", hint: "Waiting for API" },
    ],
    highlights: [
      buildFailureHeadline(failure),
      failure.operator_action,
      "Treat this as degraded until core-api connectivity and freshness recover.",
    ],
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

function buildFallbackIncidents(failure: DashboardFetchFailure): DashboardIncidents {
  const generatedAt = new Date().toISOString();
  return {
    generated_at: generatedAt,
    freshness: buildBrokenFreshness(generatedAt, failure),
    frontend_status: buildFrontendStatus(failure),
    summary_cards: [],
    highlights: ["Incident view is waiting for backend incident state."],
    active_incidents: [],
    recent_incidents: [],
    pending_approvals: [],
  };
}

async function classifyHttpFailure(response: Response): Promise<DashboardFetchFailure> {
  const detail = await extractFailureDetail(response);
  if (response.status === 401 || response.status === 403) {
    return {
      kind: "auth",
      detail,
      status_code: response.status,
      operator_action: "Check QE_DASHBOARD_API_TOKEN on the dashboard and verify the backend dashboard token setting.",
    };
  }
  if ([502, 503, 504].includes(response.status)) {
    return {
      kind: "unavailable",
      detail,
      status_code: response.status,
      operator_action: "Confirm core-api is up, reachable from the dashboard host, and not blocked by the reverse proxy.",
    };
  }
  if (response.status >= 500) {
    return {
      kind: "server",
      detail,
      status_code: response.status,
      operator_action: "Inspect core-api logs and the doctor endpoint before trusting any dashboard state.",
    };
  }
  return {
    kind: "http",
    detail,
    status_code: response.status,
    operator_action: "Inspect the failing API route and backend response before using this view for decisions.",
  };
}

function classifyThrownFailure(error: unknown): DashboardFetchFailure {
  if (error instanceof Error) {
    const message = error.message || "Dashboard API unavailable";
    return {
      kind: error.name === "TypeError" ? "network" : "unknown",
      detail: message,
      operator_action:
        error.name === "TypeError"
          ? "Check NEXT_PUBLIC_API_BASE_URL, local network reachability, and whether core-api is listening."
          : "Inspect the dashboard host logs and retry after confirming backend reachability.",
    };
  }
  return {
    kind: "unknown",
    detail: "Dashboard API unavailable",
    operator_action: "Inspect dashboard and backend logs before trusting this view.",
  };
}

async function extractFailureDetail(response: Response): Promise<string> {
  const fallback = `API returned ${response.status}`;
  try {
    const contentType = response.headers.get("content-type") ?? "";
    if (contentType.includes("application/json")) {
      const payload = (await response.json()) as { detail?: unknown; message?: unknown };
      const detail = typeof payload.detail === "string" ? payload.detail : typeof payload.message === "string" ? payload.message : undefined;
      return detail ? `${fallback}: ${detail}` : fallback;
    }

    const text = (await response.text()).trim();
    if (!text) {
      return fallback;
    }
    return `${fallback}: ${text.slice(0, 160)}`;
  } catch {
    return fallback;
  }
}

function buildFailureHeadline(failure: DashboardFetchFailure): string {
  switch (failure.kind) {
    case "auth":
      return "System view could not authenticate to the dashboard API.";
    case "unavailable":
      return "System view could not reach the backend authority-core API.";
    case "server":
      return "System view reached the backend, but the backend returned a server error.";
    case "http":
      return "System view received an unexpected HTTP response from the backend API.";
    case "network":
      return "System view could not establish a network path to the backend API.";
    default:
      return "System view is waiting for backend authority-core state.";
  }
}

function buildFrontendStatus(failure: DashboardFetchFailure): DashboardFrontendStatus {
  return {
    degraded: true,
    error_kind: failure.kind,
    detail: failure.detail,
    operator_action: failure.operator_action,
    status_code: failure.status_code ?? null,
  };
}

function buildBrokenFreshness(generatedAt: string, failure: DashboardFetchFailure): FreshnessPayload {
  return {
    state: "broken",
    age_seconds: 0,
    generated_at: generatedAt,
    note: failure.detail,
  };
}
