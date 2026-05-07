# Productization Completion Plan

## 1. Purpose

This document converts the existing architecture into a finish plan for a deployable product.

The target is not merely "more features." The target is:

- dashboard-first owner operation
- Telegram gateway for alerts, light approvals, pause/resume, and emergency control
- simple owner entry for ideas and commands, with deeper structured fields available when needed
- governed Codex-centered execution
- deployment-level market selection with one active market mode per runtime
- one-machine local deployment path that matches the single-VPS profile
- durable learning, strategy, and trading state
- safe unattended VPS operation
- a deployment and recovery model a non-technical owner can actually use

## 2. Product Finish Gates

The system is only product-complete when all of the following are true:

1. The owner can inspect system health, learning, strategy, trading, and incidents primarily from Telegram and the dashboard.
2. Runtime configuration is durable, proposal-driven, auditable, and reversible.
3. Risky owner actions and risky system promotions always flow through approvals and versioned records.
4. Broker truth, order recovery, sync, and reconciliation are real rather than paper-only scaffolds.
5. Auto-evolution is bounded by review, eval, canary, rollback, and objective-drift controls.
6. Owner-facing workflows stay simple at the entry point while preserving structured evidence, audit, and risk gates underneath.
7. VPS deployment, local deployment, backup, restore, upgrade, and break-glass operations are scripted and validated.

## 2.1 Dashboard Product Completion Contract

For the current productization pass, "usable" means the owner can complete the following from the dashboard without falling back to Discord-style command input:

1. Submit a simple idea or a structured strategy design.
2. See every research brief, its audit status, blockers, and next action.
3. Promote a ready research brief into a strategy hypothesis.
4. Convert a hypothesis into a deterministic strategy spec.
5. Record a backtest result with sample size, return, Sharpe, drawdown, and artifact reference.
6. Record a paper run with monitoring days, PnL, profit factor, drawdown, and capital allocation.
7. Approve or reject promotion into a later strategy stage.
8. Inspect and act on pending approvals.
9. Register market-data providers, watchlists, watchlist items, and quote snapshots.
10. Inspect freshness so research and strategy work does not pretend stale data is usable.
11. Run the same local/single-VPS shape with scripted health and smoke checks.

The entry must remain simple: the owner can start with one sentence. The product still has to preserve the professional inner gates: evidence, point-in-time control, baseline, cost model, attack tests, backtest, paper, approval, and rollback.

## 3. Current Position

Already materially live:

- durable runtime state and governance kernel
- dashboard pages with real backend read models
- Codex fabric with persistent runs, attempts, and artifacts
- bounded supervisor loops
- learning ingest, synthesis, and quarantine base
- strategy lab lifecycle
- governed paper/external-style execution path
- canonical instrument registry and broker capability registry
- runtime config registry with proposals, approvals, and revision history

Still not complete:

- Telegram gateway security and richer owner UX
- real broker adapters
- deployment-level market mode closure for `us` versus `cn`
- multi-instrument trading closure for options, short lifecycle, and leverage-aware execution
- governed strategy-to-capital promotion closure
- full auto-evolution closure
- VPS productization and operator runbooks

## 4. Finish Order

### 4.0 Stage 0: Planning Contract Closure

Scope:

- formal memory-plane contract
- formal skill-plane contract
- named failure taxonomy and fallback policy
- dashboard and Telegram state tables
- initial `DESIGN.md` for product surfaces

Done when:

- learning and self-improvement are backed by explicit runtime contracts
- reusable skills have provenance, quality gates, and rollback posture
- operator-facing states are specified before more UI expansion
- major failures are named, surfaced, and recoverable by design

### 4.1 Stage A: Owner Control Plane Hardening

Scope:

- Telegram allowlists / trusted-operator model
- channel and DM safety defaults
- richer approval ergonomics
- natural-language owner flows for common configuration and control actions
- incident-safe Chinese-first interaction quality

Done when:

- Telegram can act as the lightweight gateway without becoming the primary work surface
- risky actions are approval-backed
- operator access and bot surface are explicitly bounded

### 4.2 Stage B: Multi-Instrument Broker Truth Closure

Scope:

- canonical instrument and broker capability model
- deployment-level market mode contract: `us` or `cn`
- durable portfolio sleeve attribution for `us_equities`, `us_options`, and `cn_equities`
- sleeve-specific market calendars, broker profiles, source packs, and capital policy
- equities, options, and short/margin-aware order semantics
- paper/live product-parity execution logic
- one or more real broker adapters
- authenticated sync loops
- cancel/replace/sync parity with broker truth
- symbol ownership within sleeves
- live capital guardrails tied to strategy stage

Done when:

- the trading kernel no longer relies on equity-only assumptions
- one deployment selects one market mode and the active sleeve family follows from that choice
- US and China strategies are separated in runtime truth rather than only by prose fields
- at least one real broker path supports the target product surface end-to-end
- restart recovery works against a real broker
- limited-live mode has real reconciliation confidence
- strategy capital limits are enforced at execution time

### 4.3 Stage C: Governed Auto-Evolution Closure

Scope:

- improvement goal objects
- shadow and canary execution lanes
- review and eval promotion gates
- objective-drift review
- rollback and freeze controls for promoted changes

Done when:

- the system can improve itself without bypassing mission or safety boundaries
- promoted changes are traceable, reviewable, and reversible

### 4.4 Stage D: Local And VPS Productization

Scope:

- production compose / systemd deployment shape for the 1-VPS topology
- one-machine local deployment path using the same runtime shape with loopback bindings
- health checks, startup ordering, and smoke checks
- backup and restore scripts
- upgrade procedure
- operator runbooks
- simple env templates for relay-based API users

Done when:

- a fresh VPS deployment can be brought online from a runbook
- the same product can be brought online on a local machine with the same single-host shape
- a restore drill succeeds
- safe mode and break-glass actions are documented and tested

## 5. Immediate Next Build Queue

1. Close durable sleeve attribution and per-sleeve runtime state for `us_equities`, `us_options`, and `cn_equities`.
2. Close deployment-level market mode so one runtime explicitly selects `us` or `cn`.
3. Add a first-class quant signal layer so candidate generation, ranking, and sizing do not depend on LLM free-form reasoning.
4. Formalize the memory plane, skill plane, and failure taxonomy before expanding autonomous learning and self-improvement.
5. Close multi-instrument paper execution and product-aware risk rules on top of the new instrument and broker capability model.
6. Harden Telegram gateway security and owner workflow ergonomics.
7. Implement the first real broker adapter and authenticated sync loop.
8. Add sleeve-specific acquisition packs, research artifacts, and promotion thresholds.
9. Add an initial `DESIGN.md` plus dashboard and Telegram interaction-state contracts.
10. Add product-grade deployment checks, backup scaffolding, and operator runbooks for both local and VPS use.
11. Close governed strategy-to-capital promotion.
12. Close governed auto-evolution promotion and rollback.

## 6. Non-Negotiable Constraints

- Do not redesign the single-writer core plus elastic work-plane architecture.
- Do not multiply autonomous masters.
- Do not treat chat history as runtime truth.
- Do not allow self-improvement or live-trading promotion without audit, rollback, and bounded authority.
- Do not optimize for novelty at the expense of owner governability.
