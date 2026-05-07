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
  MarketDataWorkbenchPayload,
  StrategyResearchBriefCard,
  StrategyLifecyclePayload,
} from "@/lib/types";
import {
  buildDemoEvolution,
  buildDemoIncidents,
  buildDemoLearning,
  buildDemoOverview,
  buildDemoSystem,
  buildDemoTrading,
} from "@/lib/demo-dashboard";

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
  if (DASHBOARD_DEMO_MODE) {
    return buildDemoTrading();
  }
  return fetchJson("/api/v1/dashboard/trading", buildFallbackTrading);
}

export async function fetchResearchBriefs(): Promise<StrategyResearchBriefCard[]> {
  if (DASHBOARD_DEMO_MODE) {
    return buildDemoResearchBriefs();
  }
  return fetchJson("/api/v1/strategy/research-briefs", () => []);
}

export async function fetchStrategyLifecycle(): Promise<StrategyLifecyclePayload> {
  if (DASHBOARD_DEMO_MODE) {
    return buildDemoStrategyLifecycle();
  }
  const [hypotheses, specs, backtests, paperRuns, promotionDecisions] = await Promise.all([
    fetchJson("/api/v1/strategy/hypotheses", () => []),
    fetchJson("/api/v1/strategy/specs", () => []),
    fetchJson("/api/v1/strategy/backtests", () => []),
    fetchJson("/api/v1/strategy/paper-runs", () => []),
    fetchJson("/api/v1/strategy/promotion-decisions", () => []),
  ]);

  return {
    hypotheses,
    specs,
    backtests,
    paper_runs: paperRuns,
    promotion_decisions: promotionDecisions,
  } as StrategyLifecyclePayload;
}

export async function fetchMarketDataWorkbench(): Promise<MarketDataWorkbenchPayload> {
  if (DASHBOARD_DEMO_MODE) {
    return buildDemoMarketDataWorkbench();
  }
  const [providers, watchlists, quotes, ingestionRuns, historicalBars, factorSnapshots, freshness] = await Promise.all([
    fetchJson("/api/v1/market-data/providers", () => []),
    fetchJson("/api/v1/market-data/watchlists", () => []),
    fetchJson("/api/v1/market-data/quotes", () => []),
    fetchJson("/api/v1/market-data/ingestion-runs", () => []),
    fetchJson("/api/v1/market-data/historical-bars", () => []),
    fetchJson("/api/v1/market-data/factors", () => []),
    fetchJson("/api/v1/market-data/freshness", () => ({
      generated_at: new Date().toISOString(),
      fresh: 0,
      stale: 0,
      missing: 0,
      items: [],
    })),
  ]);
  const itemGroups = await Promise.all(
    (watchlists as { watchlist_key: string }[]).slice(0, 8).map((watchlist) =>
      fetchJson(`/api/v1/market-data/watchlists/${encodeURIComponent(watchlist.watchlist_key)}/items`, () => []),
    ),
  );

  return {
    providers,
    watchlists,
    watchlist_items: itemGroups.flat(),
    quotes,
    ingestion_runs: ingestionRuns,
    historical_bars: historicalBars,
    factor_snapshots: factorSnapshots,
    freshness,
  } as MarketDataWorkbenchPayload;
}

export async function fetchLearning(): Promise<DashboardLearning> {
  if (DASHBOARD_DEMO_MODE) {
    return buildDemoLearning();
  }
  return fetchJson("/api/v1/dashboard/learning", buildFallbackLearning);
}

function buildDemoStrategyLifecycle(): StrategyLifecyclePayload {
  const now = new Date().toISOString();
  return {
    hypotheses: [
      {
        id: "hyp_demo_001",
        title: "Post-earnings liquidity reversal",
        thesis: "Attention shocks fade after liquidity recovers.",
        target_market: "us",
        current_stage: "hypothesis",
        status: "active",
        created_at: now,
      },
    ],
    specs: [
      {
        id: "spec_demo_001",
        hypothesis_id: "hyp_demo_001",
        spec_code: "post_earnings_liquidity_v1",
        version_label: "v1",
        title: "Post-earnings liquidity reversal",
        target_market: "us",
        current_stage: "paper_candidate",
        latest_backtest_gate: "passed",
        latest_paper_gate: null,
        status: "active",
        created_at: now,
      },
    ],
    backtests: [
      {
        id: "bt_demo_001",
        strategy_spec_id: "spec_demo_001",
        dataset_range: "2024-01-01..2026-01-01",
        sample_size: 240,
        gate_result: "passed",
        gate_notes: ["Backtest cleared the research gate."],
        metrics_json: { sharpe_ratio: 1.21, total_return_pct: 14.2, max_drawdown_pct: 8.1 },
        artifact_path: "workspace/trading/logs/demo_backtest.md",
        total_return_pct: 14.2,
        sharpe_ratio: 1.21,
        max_drawdown_pct: 8.1,
        created_at: now,
      },
    ],
    paper_runs: [],
    promotion_decisions: [],
  };
}

function buildDemoResearchBriefs(): StrategyResearchBriefCard[] {
  const now = new Date().toISOString();
  return [
    {
      id: "brief_demo_ready",
      title: "Post-earnings drift with liquidity normalization",
      opportunity_kind: "event",
      target_market: "us",
      audit_status: "ready_for_spec",
      audit_notes: ["Research brief satisfies the LLM quant opportunity gate."],
      readiness_score: 1,
      promoted_hypothesis_id: null,
      status: "candidate",
      created_at: now,
    },
    {
      id: "brief_demo_evidence",
      title: "A-share volume expansion ranking overlay",
      opportunity_kind: "factor",
      target_market: "cn",
      audit_status: "needs_evidence",
      audit_notes: ["Missing Point-in-time controls.", "Missing Baseline comparisons."],
      readiness_score: 0.692,
      promoted_hypothesis_id: null,
      status: "candidate",
      created_at: now,
    },
  ];
}

function buildDemoMarketDataWorkbench(): MarketDataWorkbenchPayload {
  const now = new Date().toISOString();
  return {
    providers: [
      {
        id: "provider_demo_001",
        provider_key: "paper-sim",
        display_name: "Paper Simulation Feed",
        provider_type: "internal",
        market_coverage: ["us_equities"],
        supports_realtime: false,
        supports_historical: true,
        supports_fundamentals: false,
        supports_news: false,
        entitlement_state: "ready",
        health_status: "healthy",
        latency_ms: 0,
        freshness_sla_seconds: 120,
        last_heartbeat_at: now,
        notes: "Demo provider for local product validation.",
        updated_at: now,
      },
    ],
    watchlists: [
      {
        id: "watchlist_demo_001",
        watchlist_key: "owner-us-core",
        display_name: "Owner US Core",
        market_scope: "us_equities",
        description: "Core symbols used for research validation.",
        is_default: true,
        item_count: 2,
        updated_at: now,
      },
    ],
    watchlist_items: [
      {
        id: "watchlist_item_demo_001",
        watchlist_key: "owner-us-core",
        symbol: "AAPL",
        instrument_key: null,
        market: "us_equities",
        venue: "NASDAQ",
        currency: "USD",
        priority: 10,
        metadata_payload: {},
        updated_at: now,
      },
    ],
    quotes: [
      {
        id: "quote_demo_001",
        provider_key: "paper-sim",
        symbol: "AAPL",
        market: "us_equities",
        venue: "NASDAQ",
        bid: 189.1,
        ask: 189.2,
        last: 189.16,
        volume: 1200000,
        as_of: now,
        source_latency_ms: 0,
        is_realtime: false,
        created_at: now,
      },
    ],
    ingestion_runs: [
      {
        id: "ingest_demo_001",
        provider_key: "paper-sim",
        adapter_key: "local_replay",
        source_ref: "demo-bars.json",
        market: "us_equities",
        symbols: ["AAPL"],
        bar_count: 3,
        started_at: now,
        completed_at: now,
        error_message: null,
        status: "completed",
        created_at: now,
      },
    ],
    historical_bars: [
      {
        id: "bar_demo_001",
        ingestion_run_id: "ingest_demo_001",
        provider_key: "paper-sim",
        symbol: "AAPL",
        market: "us_equities",
        venue: "NASDAQ",
        timeframe: "1d",
        bar_start: now,
        open: 187.4,
        high: 190.1,
        low: 186.8,
        close: 189.16,
        volume: 1200000,
        adjusted_close: null,
        is_adjusted: false,
        created_at: now,
      },
    ],
    factor_snapshots: [
      {
        id: "factor_demo_001",
        factor_code: "momentum_close_return",
        factor_name: "Close-to-close momentum return",
        symbol: "AAPL",
        market: "us_equities",
        as_of: now,
        value: 0.021,
        rank: 1,
        percentile: 1,
        lookback_bars: 3,
        input_bar_ids: ["bar_demo_001"],
        lineage_payload: { provider_key: "paper-sim", timeframe: "1d", formula: "(latest_close / first_close) - 1" },
        created_at: now,
      },
    ],
    freshness: {
      generated_at: now,
      fresh: 1,
      stale: 0,
      missing: 0,
      items: [
        {
          symbol: "AAPL",
          market: "us_equities",
          provider_key: "paper-sim",
          status: "fresh",
          age_seconds: 8,
          last_quote_at: now,
          last_price: 189.16,
          provider_health: "healthy",
          reason: null,
        },
      ],
    },
  };
}

export async function fetchEvolution(): Promise<DashboardEvolution> {
  if (DASHBOARD_DEMO_MODE) {
    return buildDemoEvolution();
  }
  return fetchJson("/api/v1/dashboard/evolution", buildFallbackEvolution);
}

export async function fetchSystem(): Promise<DashboardSystem> {
  if (DASHBOARD_DEMO_MODE) {
    return buildDemoSystem();
  }
  return fetchJson("/api/v1/dashboard/system", buildFallbackSystem);
}

export async function fetchIncidents(): Promise<DashboardIncidents> {
  if (DASHBOARD_DEMO_MODE) {
    return buildDemoIncidents();
  }
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
