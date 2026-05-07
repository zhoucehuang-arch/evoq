# EvoQ Market Data Hub Plan

This plan turns the current optimization direction into structure, not positioning. EvoQ should stay function-led: market data, research, backtesting, paper/live execution, UI, and IM should be explicit capabilities. LLMs are invoked only where they improve interpretation, synthesis, or workflow automation.

## Product Decisions

- US equities are the first-class market. A-shares are a planned second market with a separate provider and calendar profile.
- Market data is a core service, not an execution side effect and not an agent role.
- UI and IM must consume the same API contracts. Discord, web dashboard, or another IM surface should not own business logic.
- Provider readiness is observable before trading logic uses data. Freshness, entitlement state, provider health, and latency are part of the runtime state.
- LLM usage is optional and bounded: explain market state, summarize watchlist changes, draft strategy hypotheses, and annotate backtest results. It should not replace deterministic data ingestion, freshness checks, or risk gates.

## Stage 1: Foundation

Implemented in this stage:

- `MarketDataService` owns provider registry, watchlists, quote snapshots, and freshness checks.
- New API surface under `/api/v1/market-data/*`.
- Durable tables for providers, watchlists, watchlist items, and quote snapshots.
- Freshness summaries that are directly usable by dashboard widgets or IM status messages.

Stage 1 intentionally does not ship a live vendor connector. It creates the stable internal shape that Alpaca, Polygon, IBKR, OpenBB, AKShare, Tushare, or other adapters can write into.

## Stage 2: US Realtime Path

Recommended order:

1. Add a US provider adapter interface with pull and stream modes.
2. Implement Alpaca as the first real adapter because the repo already has Alpaca execution concepts.
3. Add Polygon or IBKR as the second quote provider for fallback and cross-checking.
4. Add a provider heartbeat job that records health and latest quote snapshots.
5. Block paper/live order paths when the required symbols are stale or missing.

Minimum readiness gates:

- Provider entitlement is known and acceptable.
- Provider heartbeat is fresh.
- Required watchlist symbols have quote snapshots within SLA.
- Quote provider market session matches the target venue session.

## Stage 3: Dashboard and IM

Dashboard:

- Market data provider status panel.
- Default US watchlist view.
- Freshness badges per symbol.
- Quote table with provider and age.
- Backtest and paper-run pages should display the data source and data freshness used for the run.

IM:

- `/watchlist add AAPL`
- `/market status`
- `/quote AAPL`
- `/freshness us-core`
- Push alerts when provider status degrades or watchlist symbols go stale.

## Stage 4: A-Share Extension

A-share support should be added as a parallel market profile, not as hardcoded symbol exceptions.

- Add CN provider adapters after the US adapter path is stable.
- Add market calendars for SSE/SZSE.
- Add symbol normalization and venue routing.
- Keep CN quote freshness and entitlement checks separate from US checks.
- Do not enable live CN execution until broker/account/reconciliation paths are validated end to end.

## Stage 5: Strategy and Backtest Integration

After live market data ingestion is stable:

- Persist historical bars through the same market data boundary.
- Attach provider lineage to each backtest run.
- Require strategy hypotheses to declare market scope and data requirements.
- Promote strategies only when historical data lineage, paper data freshness, and execution readiness all pass.

## Stage 6: LLM Quant Research Audit

Implemented in this stage:

- `StrategyResearchBrief` captures LLM-originated factor, event, regime, microstructure, execution, and portfolio-overlay opportunities before they become strategy hypotheses.
- The research brief stores model provenance, prompt hash, tool traces, evidence references, data requirements, point-in-time controls, cost/slippage requirements, baseline comparisons, invalidation conditions, risk controls, and attack/leakage tests.
- A deterministic audit gate marks each brief as `ready_for_spec`, `needs_evidence`, or `blocked`.
- Only `ready_for_spec` briefs can be promoted through the new `/api/v1/strategy/research-briefs/{brief_id}/hypothesis` path.

This keeps the split explicit: LLMs generate and organize candidate opportunities, while EvoQ's quant runtime decides whether the idea is sufficiently specified for traditional backtest, paper, risk, and execution validation.

Next recommended work after this slice:

1. Attach market-data provider lineage and freshness snapshots to each research brief and later backtest run.
2. Add a point-in-time replay runner that consumes research briefs and produces auditable backtest artifacts.
3. Add purged walk-forward and baseline comparison fields to backtest records.
4. Add TradeTrap-style attack tests for tool-output tampering, memory poisoning, leakage, and ledger mismatch.
5. Add dashboard and IM views for research briefs grouped by audit status.

## LLM Insertion Points

LLMs should be functions, not personas:

- Explain why a symbol is stale or excluded.
- Summarize market and watchlist changes for IM.
- Convert operator intent into watchlist or backtest actions.
- Draft strategy hypotheses from deterministic data summaries.
- Review backtest and paper-run diagnostics for human approval.

The system should not create named analyst, trader, or risk-manager roles unless that structure maps to real code ownership or runtime boundaries.
