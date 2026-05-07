# EvoQ Complete Delivery Plan

## 1. Target

EvoQ is complete enough for the user's current goal when it can run as a local or VPS-deployable quant research and paper-trading system with:

- deterministic quant data, factor, backtest, portfolio, risk, and paper execution paths
- LLM-assisted research, hypothesis generation, evidence checking, diagnosis, and strategy critique
- no direct path from LLM output to capital-facing execution
- durable audit records for data lineage, model provenance, prompts, tool traces, backtests, paper runs, promotions, withdrawals, incidents, and overrides
- dashboard and API surfaces that let the owner understand whether the system is healthy, stale, blocked, or ready for the next gate
- a repeatable test and smoke-validation path that must pass before every handoff

This plan treats LLM as an advantage layer, not as the trading engine. The trading engine remains quant-first.

## 2. Completion Definition

The project is not considered landed until all checks below are true.

### Product Readiness

- The owner can start the backend and dashboard locally with documented commands.
- The system can ingest or replay market data into durable tables.
- A research idea can move through this path:
  `research brief -> audit gate -> hypothesis -> strategy spec -> backtest -> paper run -> promotion or rejection`.
- The dashboard exposes market data freshness, strategy lifecycle, backtest status, paper run status, risk readiness, and incidents.
- The system can produce a first paper-trading run without manual database edits.

### Quant Readiness

- Factor and signal generation can run without LLMs.
- Backtests are replayable and store data lineage, cost assumptions, baselines, and gate results.
- Paper execution is restart-safe and reconciles durable order, position, and account state.
- Promotion gates require backtest evidence, paper evidence, risk controls, and explicit rationale.

### LLM Readiness

- LLM-generated opportunities must enter as structured research briefs.
- Every LLM research artifact records model, cutoff, prompt hash or prompt reference, tool traces, evidence references, and data timestamps.
- LLMs can suggest, explain, challenge, and diagnose, but cannot bypass data, backtest, paper, risk, or approval gates.
- LLM value is measured with ablations or review outcomes, not assumed from fluent explanations.

### Operational Readiness

- Full tests pass.
- Database migrations apply from scratch.
- A smoke script proves the main lifecycle works on a clean local database.
- Secrets are not stored in repo, generated docs, or runtime records.
- There is a safe mode and documented stop/recovery path.

## 3. Current Baseline

Already live or recently added:

- durable strategy lab lifecycle: hypothesis, spec, backtest, paper run, promotion, withdrawal
- durable paper order path, session guard, readiness, reconciliation, incidents, and dashboard exposure
- market data foundation: providers, watchlists, quotes, freshness
- local replay historical-bar ingestion with durable ingestion runs
- deterministic factor kernels: `momentum_close_return`, `reversal_close_return`, `realized_volatility`, and `dollar_volume_liquidity`
- PIT factor replay backtest from factor snapshots with cost, slippage, baseline, and lineage gates
- execution readiness blocks when existing market-data quotes are stale beyond 48 hours
- report-only live readiness endpoint that cannot place orders
- LLM quant research audit: research briefs with deterministic `ready_for_spec`, `needs_evidence`, and `blocked` gates
- repo-local Windows test runner under `ops/tools/run_tests.ps1`

Current verified baseline:

- `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ops\tools\run_tests.ps1 -q`
- latest result: `135 passed`
- `npm run build` in `apps/dashboard-web`
- `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ops\tools\smoke_local.ps1`

## 4. Delivery Phases

### Phase 0: Repo And Validation Lock

Goal:

- make the current mixed repo state safe to continue from

Build:

- update roadmap documents so market-data and research-audit additions are reflected
- confirm migration order from existing database to latest revision
- add or update a clean smoke-test command
- keep old/original project material out of active runtime paths

Acceptance:

- full tests pass
- `git diff --check` has no real whitespace errors
- a fresh SQLite schema can be created with all current models
- docs identify current active runtime directories clearly

### Phase 1: Market Data Adapter And Historical Store

Goal:

- turn the market-data hub from schema/API foundation into useful data intake

Build:

- provider adapter interface for realtime, historical bars, corporate actions, and news metadata
- Alpaca adapter as the first US path because existing execution concepts already reference Alpaca
- CSV/local replay adapter for offline testing without network or paid data
- historical bar tables with provider lineage, symbol, venue, timestamp, adjusted/unadjusted fields, and ingestion run id
- freshness and entitlement gates that strategy and paper paths can query

Acceptance:

- local replay adapter can ingest a sample dataset
- provider readiness blocks stale or missing symbols
- quotes and historical bars are queryable through API
- tests cover provider readiness, stale data, duplicate ingestion, and historical-bar retrieval

### Phase 2: Deterministic Quant Signal Kernel

Goal:

- make EvoQ useful even when no LLM is present

Build:

- universe definitions for `us_equities` first
- factor registry with simple deterministic factors: momentum, reversal, volatility, volume/liquidity, event-window features
- candidate ranking tables with timestamps and data lineage
- signal snapshots connected to strategy specs
- turnover, concentration, and minimum liquidity constraints

Acceptance:

- factor generation runs from stored market data
- factor outputs are replayable from the same inputs
- top candidates can be queried by API
- tests cover factor math, missing data handling, ranking stability, and lineage

### Phase 3: Backtest And Evidence Engine

Goal:

- convert strategy specs into auditable evidence instead of loose performance claims

Build:

- point-in-time replay runner
- purged walk-forward split support
- cost and slippage model contract
- baseline comparison contract: cash, buy-and-hold, equal-weight, index or sector baseline
- backtest artifact table or artifact manifest
- added metrics: turnover, trade count, Sortino, Calmar, tail loss, exposure, hit ratio, cost sensitivity
- stricter promotion gate that checks lineage, baselines, costs, and leakage controls

Acceptance:

- a sample strategy can produce a backtest run from stored data
- backtest cannot pass without cost assumptions and baseline comparison
- leakage/PIT missing data marks the run `failed` or `needs_review`
- tests cover positive path, missing cost model, weak baseline, and hard drawdown failure

### Phase 4: LLM Research And Challenge Loop

Goal:

- maximize LLM advantage without making it the execution authority

Build:

- research brief creation from evidence packets and deterministic market summaries
- challenge pass that asks LLM to find leakage, overfitting, weak mechanism, missing costs, and bad baselines
- contradiction records attached to briefs/specs/backtests
- prompt templates stored as versioned artifacts, referenced by hash
- model/cutoff/tool trace capture for every generated brief or diagnosis
- LLM ablation field: whether a decision came from deterministic logic, LLM suggestion, or human approval

Acceptance:

- LLM output can draft a complete research brief but cannot promote it unless audit fields pass
- challenge notes are durable and visible
- unsafe requests such as direct live deployment remain blocked
- tests cover missing provenance, unsafe shortcut, challenge note persistence, and brief-to-hypothesis promotion

### Phase 5: Strategy Spec And Safe Code Path

Goal:

- turn approved research into executable strategy logic safely

Build:

- strategy template registry
- parameter schema for each strategy template
- safe strategy code validation or AST allowlist for LLM-generated strategy snippets
- strategy spec versioning and comparison
- invalidation condition tracking after each backtest and paper run

Acceptance:

- a strategy spec can bind to deterministic factor outputs
- unsafe code patterns are rejected before runtime
- strategy versions can be compared and rolled back
- tests cover template validation, parameter bounds, rejected unsafe code, and version lineage

### Phase 6: Paper Trading Closure

Goal:

- make the first realistic paper run possible end to end

Build:

- scheduler or supervisor loop that runs selected paper strategies
- paper orders connected to latest approved signal snapshots
- account, position, order, and reconciliation views tied to strategy spec id
- daily paper report with PnL, drawdown, exposure, trades, slippage assumption, and incidents
- paper stop conditions: stale data, reconciliation mismatch, drawdown breach, exposure breach, missing market session

Acceptance:

- a sample strategy can run through paper-sim without manual DB edits
- paper run updates order, position, account, and strategy state
- readiness blocks paper execution when market data is stale
- tests cover normal paper path, stale-data block, reconciliation halt, and drawdown stop

### Phase 7: Dashboard And Owner Workflow

Goal:

- make the system actually operable

Build:

- research brief dashboard panel grouped by audit status
- factor/candidate view
- backtest artifact view
- paper run view with current gate state
- market data freshness panel connected to strategy readiness
- owner action endpoints for promote, reject, withdraw, pause, and resume
- Chinese-friendly summaries for the main owner decisions

Acceptance:

- owner can see what is ready, blocked, stale, running, or failed
- owner can approve or reject key gates without touching the database
- dashboard smoke test verifies the main pages load
- API tests cover new read models and owner action paths

### Phase 8: Ops, Deployment, And Recovery

Goal:

- move from local runnable to VPS-usable

Build:

- one-machine local deployment path
- optional two-plane deployment: stable core plus research worker
- backup and restore commands
- migration runbook
- safe mode command
- broker/data provider secret checklist
- health check endpoint that includes DB, provider freshness, supervisor state, and risk state

Acceptance:

- clean local setup works from documented commands
- restore rehearsal works against a test backup
- health endpoint fails closed when critical dependencies are missing
- tests and smoke checks are documented and reproducible

### Phase 9: Limited Live Readiness Gate

Goal:

- prepare for live trading without enabling it by default

Build:

- explicit live-disabled default
- small-capital live gate with owner approval
- broker capability and account environment checks
- live order dry-run review packet
- hard kill switch and manual takeover session
- live incident escalation

Acceptance:

- no live order can be sent without explicit config, broker readiness, strategy promotion, owner approval, and risk readiness
- live readiness can be reviewed without placing a live order
- tests cover blocked-by-default live path, approval-required path, and kill-switch path

## 5. Execution Order

Recommended order from the current state:

1. Phase 0: validation lock and docs alignment
2. Phase 1: local replay and Alpaca market data adapter
3. Phase 2: deterministic factor and candidate ranking kernel
4. Phase 3: point-in-time backtest and evidence engine
5. Phase 4: LLM research/challenge automation
6. Phase 6: paper trading closure
7. Phase 7: dashboard and owner workflow
8. Phase 8: ops and recovery
9. Phase 9: limited live readiness only after paper evidence is stable

Phase 5 can run alongside Phases 2 and 3 if strategy templates are kept narrow and write scopes stay separate.

## 6. Mandatory Test Gates

Every implementation slice must finish with:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ops\tools\run_tests.ps1 -q
```

For slices touching migrations:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ops\tools\run_tests.ps1 tests/test_api_persistence.py -q
```

For slices touching strategy or paper execution:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ops\tools\run_tests.ps1 tests/test_strategy_lab.py tests/test_execution_service.py -q
```

For each phase completion, add one smoke check:

- create a fresh local database
- seed or ingest sample market data
- create or promote one research brief
- create one strategy spec
- run one backtest or paper simulation, depending on phase
- verify dashboard/API read models expose the result

## 7. Non-Negotiable Constraints

- Do not let LLM output place, size, modify, or cancel live orders directly.
- Do not promote a strategy without data lineage, cost assumptions, baselines, and paper evidence.
- Do not treat historical backtest alone as proof of alpha.
- Do not store secrets in prompts, reports, docs, test fixtures, or runtime artifacts.
- Do not let research workers access broker secrets.
- Do not enable live trading until the limited live readiness gate is implemented and explicitly approved.

## 8. Immediate Next Slice

The latest completed implementation slice landed Phase 1 plus the smallest useful part of Phase 2:

1. Add a local replay market-data adapter.
2. Add historical bar storage and API.
3. Add one deterministic factor calculation path.
4. Attach data lineage from bars to factor candidates.
5. Add tests for ingestion, freshness, factor generation, and API reads.
6. Run the full test suite.

This was the right slice because it gives EvoQ a deterministic quant backbone. LLM research briefs already exist; they now have replayed market data and factor outputs to reason about.

The latest follow-up slice moved into Phase 3 and Phase 7:

1. Bind strategy specs to stored factor snapshots.
2. Add a point-in-time replay backtest runner.
3. Require cost assumptions and baseline comparison before a backtest can pass.
4. Persist backtest artifacts and lineage from bars -> factors -> signals -> portfolio results.
5. Add tests for leakage controls, missing cost model, weak baseline, and hard drawdown failure.

Next implementation work should keep expanding breadth, not reopening the architecture:

1. Continue enriching broker-specific live readiness drills without adding any live order path.
2. Add more production hardening around deployment observability and backup/restore.
