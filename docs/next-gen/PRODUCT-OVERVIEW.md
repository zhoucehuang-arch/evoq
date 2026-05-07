# Product Overview

EvoQ is a dashboard-first autonomous investment runtime for quant research, paper trading, and governed system evolution.

The core product idea is simple:

1. owners should understand and operate the system mainly through the dashboard
2. LLMs should help with research, evidence synthesis, critique, and diagnosis
3. deterministic quant logic should own data, factors, backtests, risk checks, and execution gates
4. every capital-facing step should remain paper-first and auditable until explicit readiness and approval gates are clean

## Why This Project Exists

Many “AI trading” projects blur three things that should stay separate:

- idea generation
- quantitative measurement
- execution authority

EvoQ keeps those boundaries explicit.

LLMs are useful for reading, summarizing, challenging, and explaining. They are not trusted as the tick-to-trade engine. The quant path stores market data, computes factors, records lineage, runs backtests, evaluates paper runs, and blocks unsafe readiness states.

## Who It Is For

- owners who want a non-terminal-first operating surface
- builders exploring financial LLM systems without giving LLMs direct trade authority
- quant/system engineers who want reproducible gates around factors, backtests, paper execution, incidents, and approvals
- operators who want a single-VPS-first product that can later scale into Core + Worker topology

## Who It Is Not For

- anyone looking for an immediate live-trading bot
- users who want to bypass paper evidence and approval gates
- teams that do not want durable audit records, risk controls, or rollback paths
- high-frequency traders looking for low-latency tick execution

## Main Capabilities

### Dashboard operation

The dashboard exposes:

- Workbench / owner idea intake
- Research briefs and audit status
- Strategy lifecycle
- Market data and factor workbench
- Trading readiness
- Learning memory
- Evolution proposals
- System doctor
- Incidents and approvals

### Market data and factors

The current local path supports:

- provider registry
- watchlists
- quote snapshots
- freshness checks
- local replay historical bars
- ingestion run records
- factor snapshots

Supported deterministic factors:

- `momentum_close_return`
- `reversal_close_return`
- `realized_volatility`
- `dollar_volume_liquidity`

### Strategy evidence

Strategy records cover:

- hypothesis
- strategy spec
- PIT factor replay backtest
- cost and slippage model
- baseline comparison
- input-bar lineage
- equity curve
- paper run
- promotion or withdrawal decision

### Execution readiness

Trading readiness checks include:

- approved production strategy
- active market session
- broker account snapshot
- broker reconciliation
- active trading overrides
- provider incidents
- stale market-data quote blocking

The live-readiness report endpoint is report-only and cannot place orders.

## Recommended Runtime Shape

### Local development

Use the Windows/PowerShell local tools first:

- `ops/tools/start_local.ps1`
- `ops/tools/smoke_local.ps1`
- `ops/tools/run_tests.ps1`

### Single-VPS first

Recommended first real deployment:

- one VPS
- `single_vps_compact`
- local Postgres
- paper broker posture
- dashboard-first owner operation
- Telegram as light alert/approval gateway

### Scale out later

When needed:

- keep Core as the authority node
- add a Worker VPS for heavier Codex/research execution
- keep broker-facing secrets on Core only

## Market Mode

One deployment chooses one market mode:

- `us`: US equities/options research and paper/live-gated progression
- `cn`: China A-share research/ranking/paper-first operation

Running both markets at once should use separate deployments.

## Current Boundaries

- Live trading is not the default path.
- CN live broker execution is not shipped.
- Broker integrations still require environment-specific verification.
- Backtests are only useful when data lineage, cost assumptions, baseline comparison, and PIT controls are present.
- LLM output must be grounded and reviewed before it becomes strategy evidence.

## What Good Looks Like

A healthy EvoQ run should show:

- dashboard pages reachable
- API doctor clean or explainable
- market data freshness visible
- deterministic factors generated from stored bars
- strategy backtests gated by cost/baseline/lineage
- paper runs recorded before promotion
- execution readiness showing explicit blockers/warnings
- no unresolved incidents hiding behind vague success messages

## Start Here

- [Root README](../../README.md)
- [Beginner README](EVOQ-BEGINNER-README.md)
- [User Manual](EVOQ-USER-MANUAL.md)
- [GitHub Landing Page Guide](GITHUB-README-GUIDE.md)
- [Complete Delivery Plan](EVOQ-COMPLETE-DELIVERY-PLAN.md)
