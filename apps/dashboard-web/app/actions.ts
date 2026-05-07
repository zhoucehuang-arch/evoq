"use server";

import { redirect } from "next/navigation";

import { redirectTargetForPost } from "@/app/action-api";

function stringValue(formData: FormData, key: string): string {
  return String(formData.get(key) ?? "").trim();
}

function listValue(formData: FormData, key: string): string[] {
  return stringValue(formData, key)
    .split(/\r?\n|,/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function numberValue(formData: FormData, key: string, fallback = 0): number {
  const raw = stringValue(formData, key);
  if (!raw) {
    return fallback;
  }
  const value = Number(raw);
  return Number.isFinite(value) ? value : fallback;
}

function optionalNumberValue(formData: FormData, key: string): number | null {
  const raw = stringValue(formData, key);
  if (!raw) {
    return null;
  }
  const value = Number(raw);
  return Number.isFinite(value) ? value : null;
}

function jsonObjectValue(formData: FormData, key: string): Record<string, unknown> {
  const raw = stringValue(formData, key);
  if (!raw) {
    return {};
  }
  try {
    const parsed = JSON.parse(raw) as unknown;
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? (parsed as Record<string, unknown>) : {};
  } catch {
    return {};
  }
}

function jsonArrayValue(formData: FormData, key: string): unknown[] | null {
  const raw = stringValue(formData, key);
  if (!raw) {
    return [];
  }
  try {
    const parsed = JSON.parse(raw) as unknown;
    return Array.isArray(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

function safeCode(value: string): string {
  const normalized = value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 48);
  return normalized || `strategy_${Date.now()}`;
}

function titleFromIdea(idea: string): string {
  const firstLine = idea.split(/\r?\n/).find((line) => line.trim())?.trim() ?? "Untitled research idea";
  return firstLine.length > 96 ? `${firstLine.slice(0, 93)}...` : firstLine;
}

export async function createResearchBriefAction(formData: FormData) {
  const idea = stringValue(formData, "idea");
  const title = stringValue(formData, "title") || titleFromIdea(idea);
  const targetMarket = stringValue(formData, "target_market") || "us";
  const opportunityKind = stringValue(formData, "opportunity_kind") || "factor";
  const thesis = stringValue(formData, "thesis") || idea;

  if (!idea && !thesis) {
    redirect("/?brief=missing");
  }

  const payload = {
    title,
    thesis,
    opportunity_kind: opportunityKind,
    target_market: targetMarket,
    signal_definition:
      stringValue(formData, "signal_definition") ||
      "Owner-submitted idea pending factor formalization and deterministic signal definition.",
    expected_mechanism:
      stringValue(formData, "expected_mechanism") ||
      "Owner-submitted hypothesis pending evidence synthesis, mechanism review, and LLM challenge.",
    data_requirements: listValue(formData, "data_requirements"),
    point_in_time_controls: listValue(formData, "point_in_time_controls"),
    evaluation_plan: listValue(formData, "evaluation_plan"),
    cost_model_requirements: listValue(formData, "cost_model_requirements"),
    baseline_refs: listValue(formData, "baseline_refs"),
    invalidation_conditions: listValue(formData, "invalidation_conditions"),
    risk_controls_required: listValue(formData, "risk_controls_required"),
    attack_tests_required: listValue(formData, "attack_tests_required"),
    evidence_refs: idea ? [{ kind: "owner_idea", summary: idea }] : [],
    tool_refs: [{ kind: "dashboard_workbench", surface: "home" }],
    created_by: "dashboard",
    origin_type: "owner_dashboard_idea",
    status: "candidate",
  };

  const redirectTarget = await redirectTargetForPost("/api/v1/strategy/research-briefs", payload, {
    success: "/?brief=created",
    failurePrefix: "/?brief=failed&code=",
    unavailable: "/?brief=unavailable",
  });

  redirect(redirectTarget);
}

export async function promoteResearchBriefAction(formData: FormData) {
  const briefId = stringValue(formData, "brief_id");

  if (!briefId) {
    redirect("/research?brief=missing_id");
  }

  const redirectTarget = await redirectTargetForPost(
    `/api/v1/strategy/research-briefs/${briefId}/hypothesis`,
    {
      created_by: "dashboard",
      status: "active",
    },
    {
      success: "/research?brief=promoted",
      failurePrefix: "/research?brief=promote_failed&code=",
      unavailable: "/research?brief=unavailable",
    },
  );

  redirect(redirectTarget);
}

export async function decideApprovalAction(formData: FormData) {
  const approvalId = stringValue(formData, "approval_id");
  const decision = stringValue(formData, "decision");

  if (!approvalId || !["approved", "rejected"].includes(decision)) {
    redirect("/incidents?approval=missing");
  }

  const redirectTarget = await redirectTargetForPost(
    `/api/v1/approvals/${approvalId}/decision`,
    {
      decision,
      decided_by: "dashboard",
      reason: "Owner decision from dashboard incident queue.",
    },
    {
      success: `/incidents?approval=${decision}`,
      failurePrefix: "/incidents?approval=failed&code=",
      unavailable: "/incidents?approval=unavailable",
    },
  );

  redirect(redirectTarget);
}

export async function createStrategySpecAction(formData: FormData) {
  const hypothesisId = stringValue(formData, "hypothesis_id");
  const title = stringValue(formData, "title");
  const signalLogic = stringValue(formData, "signal_logic");

  if (!hypothesisId || !title || !signalLogic) {
    redirect("/strategy?strategy=missing_spec");
  }

  const payload = {
    hypothesis_id: hypothesisId,
    spec_code: stringValue(formData, "spec_code") || safeCode(title),
    version_label: stringValue(formData, "version_label") || "v1",
    title,
    target_market: stringValue(formData, "target_market") || "us",
    signal_logic: signalLogic,
    risk_rules: jsonObjectValue(formData, "risk_rules"),
    data_requirements: listValue(formData, "data_requirements"),
    invalidation_conditions: listValue(formData, "invalidation_conditions"),
    execution_constraints: jsonObjectValue(formData, "execution_constraints"),
    created_by: "dashboard",
    origin_type: "dashboard_strategy_lab",
  };

  const redirectTarget = await redirectTargetForPost("/api/v1/strategy/specs", payload, {
    success: "/strategy?strategy=spec_created",
    failurePrefix: "/strategy?strategy=failed&code=",
    unavailable: "/strategy?strategy=unavailable",
  });

  redirect(redirectTarget);
}

export async function recordBacktestAction(formData: FormData) {
  const strategySpecId = stringValue(formData, "strategy_spec_id");
  if (!strategySpecId) {
    redirect("/strategy?strategy=missing_backtest");
  }

  const payload = {
    strategy_spec_id: strategySpecId,
    dataset_range: stringValue(formData, "dataset_range") || null,
    sample_size: numberValue(formData, "sample_size"),
    metrics_json: {
      sharpe_ratio: numberValue(formData, "sharpe_ratio"),
      total_return_pct: numberValue(formData, "total_return_pct"),
      max_drawdown_pct: numberValue(formData, "max_drawdown_pct", 100),
      baseline_return_pct: numberValue(formData, "baseline_return_pct"),
      excess_return_pct: numberValue(formData, "excess_return_pct"),
      cost_model: {
        cost_bps: numberValue(formData, "cost_bps", 5),
        slippage_bps: numberValue(formData, "slippage_bps", 5),
      },
      baseline_refs: listValue(formData, "baseline_refs"),
      point_in_time_controls: listValue(formData, "point_in_time_controls"),
      input_bar_ids: listValue(formData, "input_bar_ids"),
      lineage: {
        input_bar_ids: listValue(formData, "input_bar_ids"),
      },
      ...jsonObjectValue(formData, "extra_metrics"),
    },
    artifact_path: stringValue(formData, "artifact_path") || null,
    created_by: "dashboard",
    origin_type: "dashboard_strategy_lab",
  };

  const redirectTarget = await redirectTargetForPost("/api/v1/strategy/backtests", payload, {
    success: "/strategy?strategy=backtest_recorded",
    failurePrefix: "/strategy?strategy=failed&code=",
    unavailable: "/strategy?strategy=unavailable",
  });

  redirect(redirectTarget);
}

export async function runFactorReplayBacktestAction(formData: FormData) {
  const strategySpecId = stringValue(formData, "strategy_spec_id");
  if (!strategySpecId) {
    redirect("/strategy?strategy=missing_backtest");
  }

  const asOf = stringValue(formData, "as_of");
  const payload = {
    strategy_spec_id: strategySpecId,
    factor_code: stringValue(formData, "factor_code") || "momentum_close_return",
    market: stringValue(formData, "market") || "us_equities",
    timeframe: stringValue(formData, "timeframe") || "1d",
    provider_key: stringValue(formData, "provider_key") || null,
    ...(asOf ? { as_of: asOf } : {}),
    top_n: numberValue(formData, "top_n", 5),
    min_percentile: numberValue(formData, "min_percentile", 0),
    cost_bps: numberValue(formData, "cost_bps", 5),
    slippage_bps: numberValue(formData, "slippage_bps", 5),
    baseline_refs: listValue(formData, "baseline_refs"),
    point_in_time_controls: listValue(formData, "point_in_time_controls"),
    created_by: "dashboard",
    origin_type: "dashboard_factor_replay_backtest",
  };

  const redirectTarget = await redirectTargetForPost("/api/v1/strategy/backtests/factor-replay", payload, {
    success: "/strategy?strategy=factor_backtest_recorded",
    failurePrefix: "/strategy?strategy=failed&code=",
    unavailable: "/strategy?strategy=unavailable",
  });

  redirect(redirectTarget);
}

export async function recordPaperRunAction(formData: FormData) {
  const strategySpecId = stringValue(formData, "strategy_spec_id");
  if (!strategySpecId) {
    redirect("/strategy?strategy=missing_paper");
  }

  const payload = {
    strategy_spec_id: strategySpecId,
    deployment_label: stringValue(formData, "deployment_label") || "paper-dashboard",
    monitoring_days: numberValue(formData, "monitoring_days"),
    metrics_json: {
      net_pnl_pct: numberValue(formData, "net_pnl_pct"),
      profit_factor: numberValue(formData, "profit_factor"),
      max_drawdown_pct: numberValue(formData, "max_drawdown_pct", 100),
      ...jsonObjectValue(formData, "extra_metrics"),
    },
    capital_allocated: optionalNumberValue(formData, "capital_allocated"),
    created_by: "dashboard",
    origin_type: "dashboard_strategy_lab",
  };

  const redirectTarget = await redirectTargetForPost("/api/v1/strategy/paper-runs", payload, {
    success: "/strategy?strategy=paper_recorded",
    failurePrefix: "/strategy?strategy=failed&code=",
    unavailable: "/strategy?strategy=unavailable",
  });

  redirect(redirectTarget);
}

export async function recordPromotionDecisionAction(formData: FormData) {
  const strategySpecId = stringValue(formData, "strategy_spec_id");
  const decision = stringValue(formData, "decision") || "rejected";
  if (!strategySpecId || !["approved", "rejected", "deferred"].includes(decision)) {
    redirect("/strategy?strategy=missing_promotion");
  }

  const payload = {
    strategy_spec_id: strategySpecId,
    paper_run_id: stringValue(formData, "paper_run_id") || null,
    target_stage: stringValue(formData, "target_stage") || "production",
    decision,
    rationale: stringValue(formData, "rationale") || "Owner dashboard promotion decision.",
    evidence_refs: listValue(formData, "evidence_refs").map((ref) => ({ ref, kind: "dashboard_evidence" })),
    decided_by: "dashboard",
    created_by: "dashboard",
    origin_type: "dashboard_strategy_lab",
  };

  const redirectTarget = await redirectTargetForPost("/api/v1/strategy/promotion-decisions", payload, {
    success: `/strategy?strategy=promotion_${decision}`,
    failurePrefix: "/strategy?strategy=failed&code=",
    unavailable: "/strategy?strategy=unavailable",
  });

  redirect(redirectTarget);
}

export async function upsertMarketDataProviderAction(formData: FormData) {
  const providerKey = stringValue(formData, "provider_key");
  const displayName = stringValue(formData, "display_name");
  if (!providerKey || !displayName) {
    redirect("/data?data=missing_provider");
  }

  const payload = {
    provider_key: providerKey,
    display_name: displayName,
    provider_type: stringValue(formData, "provider_type") || "data_vendor",
    market_coverage: listValue(formData, "market_coverage"),
    supports_realtime: stringValue(formData, "supports_realtime") === "on",
    supports_historical: stringValue(formData, "supports_historical") !== "off",
    supports_fundamentals: stringValue(formData, "supports_fundamentals") === "on",
    supports_news: stringValue(formData, "supports_news") === "on",
    entitlement_state: stringValue(formData, "entitlement_state") || "unknown",
    health_status: stringValue(formData, "health_status") || "unknown",
    latency_ms: optionalNumberValue(formData, "latency_ms"),
    freshness_sla_seconds: numberValue(formData, "freshness_sla_seconds", 120),
    notes: stringValue(formData, "notes") || null,
    created_by: "dashboard",
    origin_type: "dashboard_data_workbench",
  };

  const redirectTarget = await redirectTargetForPost("/api/v1/market-data/providers", payload, {
    success: "/data?data=provider_saved",
    failurePrefix: "/data?data=failed&code=",
    unavailable: "/data?data=unavailable",
  });

  redirect(redirectTarget);
}

export async function upsertWatchlistAction(formData: FormData) {
  const watchlistKey = stringValue(formData, "watchlist_key");
  const displayName = stringValue(formData, "display_name");
  if (!watchlistKey || !displayName) {
    redirect("/data?data=missing_watchlist");
  }

  const payload = {
    watchlist_key: watchlistKey,
    display_name: displayName,
    market_scope: stringValue(formData, "market_scope") || "us_equities",
    description: stringValue(formData, "description") || null,
    is_default: stringValue(formData, "is_default") === "on",
    created_by: "dashboard",
    origin_type: "dashboard_data_workbench",
  };

  const redirectTarget = await redirectTargetForPost("/api/v1/market-data/watchlists", payload, {
    success: "/data?data=watchlist_saved",
    failurePrefix: "/data?data=failed&code=",
    unavailable: "/data?data=unavailable",
  });

  redirect(redirectTarget);
}

export async function upsertWatchlistItemAction(formData: FormData) {
  const watchlistKey = stringValue(formData, "watchlist_key");
  const symbol = stringValue(formData, "symbol").toUpperCase();
  if (!watchlistKey || !symbol) {
    redirect("/data?data=missing_symbol");
  }

  const payload = {
    symbol,
    instrument_key: stringValue(formData, "instrument_key") || null,
    market: stringValue(formData, "market") || "us_equities",
    venue: stringValue(formData, "venue") || null,
    currency: stringValue(formData, "currency") || "USD",
    priority: numberValue(formData, "priority", 100),
    metadata_payload: jsonObjectValue(formData, "metadata_payload"),
    created_by: "dashboard",
    origin_type: "dashboard_data_workbench",
  };

  const redirectTarget = await redirectTargetForPost(
    `/api/v1/market-data/watchlists/${encodeURIComponent(watchlistKey)}/items`,
    payload,
    {
      success: "/data?data=symbol_saved",
      failurePrefix: "/data?data=failed&code=",
      unavailable: "/data?data=unavailable",
    },
  );

  redirect(redirectTarget);
}

export async function recordMarketQuoteAction(formData: FormData) {
  const providerKey = stringValue(formData, "provider_key");
  const symbol = stringValue(formData, "symbol").toUpperCase();
  if (!providerKey || !symbol) {
    redirect("/data?data=missing_quote");
  }

  const payload = {
    provider_key: providerKey,
    symbol,
    market: stringValue(formData, "market") || "us_equities",
    venue: stringValue(formData, "venue") || null,
    bid: optionalNumberValue(formData, "bid"),
    ask: optionalNumberValue(formData, "ask"),
    last: optionalNumberValue(formData, "last"),
    volume: optionalNumberValue(formData, "volume"),
    source_latency_ms: optionalNumberValue(formData, "source_latency_ms"),
    is_realtime: stringValue(formData, "is_realtime") === "on",
    payload: jsonObjectValue(formData, "payload"),
    created_by: "dashboard",
    origin_type: "dashboard_data_workbench",
  };

  const redirectTarget = await redirectTargetForPost("/api/v1/market-data/quotes", payload, {
    success: "/data?data=quote_recorded",
    failurePrefix: "/data?data=failed&code=",
    unavailable: "/data?data=unavailable",
  });

  redirect(redirectTarget);
}

export async function ingestReplayBarsAction(formData: FormData) {
  const providerKey = stringValue(formData, "provider_key") || "local-replay";
  const bars = jsonArrayValue(formData, "bars_json");
  if (!providerKey || !bars || bars.length === 0) {
    redirect("/data?data=missing_bars");
  }

  const payload = {
    provider_key: providerKey,
    adapter_key: stringValue(formData, "adapter_key") || "local_replay",
    source_ref: stringValue(formData, "source_ref") || null,
    market: stringValue(formData, "market") || "us_equities",
    timeframe: stringValue(formData, "timeframe") || "1d",
    bars,
    created_by: "dashboard",
    origin_type: "dashboard_replay_import",
  };

  const redirectTarget = await redirectTargetForPost("/api/v1/market-data/replay-bars", payload, {
    success: "/data?data=replay_ingested",
    failurePrefix: "/data?data=failed&code=",
    unavailable: "/data?data=unavailable",
  });

  redirect(redirectTarget);
}

export async function generateFactorSnapshotsAction(formData: FormData) {
  const asOf = stringValue(formData, "as_of");
  const payload = {
    factor_code: stringValue(formData, "factor_code") || "momentum_close_return",
    factor_name: stringValue(formData, "factor_name") || "Close-to-close momentum return",
    provider_key: stringValue(formData, "provider_key") || null,
    symbols: listValue(formData, "symbols").map((symbol) => symbol.toUpperCase()),
    market: stringValue(formData, "market") || "us_equities",
    timeframe: stringValue(formData, "timeframe") || "1d",
    lookback_bars: numberValue(formData, "lookback_bars", 3),
    ...(asOf ? { as_of: asOf } : {}),
    created_by: "dashboard",
    origin_type: "dashboard_factor_generation",
  };

  const redirectTarget = await redirectTargetForPost("/api/v1/market-data/factors/generate", payload, {
    success: "/data?data=factors_generated",
    failurePrefix: "/data?data=failed&code=",
    unavailable: "/data?data=unavailable",
  });

  redirect(redirectTarget);
}

export async function pauseDomainAction(formData: FormData) {
  const domain = stringValue(formData, "domain");
  if (!domain) {
    redirect("/trading?control=missing");
  }

  const redirectTarget = await redirectTargetForPost(
    "/api/v1/operator-overrides",
    {
      scope: domain,
      action: "pause",
      reason: stringValue(formData, "reason") || `Owner paused ${domain} from dashboard.`,
      activated_by: "dashboard",
      created_by: "dashboard",
      origin_type: "dashboard_control",
    },
    {
      success: `/trading?control=paused&domain=${encodeURIComponent(domain)}`,
      failurePrefix: "/trading?control=failed&code=",
      unavailable: "/trading?control=unavailable",
    },
  );

  redirect(redirectTarget);
}

export async function resumeDomainAction(formData: FormData) {
  const domain = stringValue(formData, "domain");
  if (!domain) {
    redirect("/trading?control=missing");
  }

  const redirectTarget = await redirectTargetForPost(
    "/api/v1/operator-overrides/release",
    {
      scope: domain,
      released_by: "dashboard",
      reason: stringValue(formData, "reason") || `Owner resumed ${domain} from dashboard.`,
    },
    {
      success: `/trading?control=resumed&domain=${encodeURIComponent(domain)}`,
      failurePrefix: "/trading?control=failed&code=",
      unavailable: "/trading?control=unavailable",
    },
  );

  redirect(redirectTarget);
}
