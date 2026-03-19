# Productization Completion Plan

## 1. Purpose

This document converts the existing architecture into a finish plan for a deployable product.

The target is not merely "more features." The target is:

- Discord-first owner control
- dashboard-first visibility
- governed Codex-centered execution
- durable learning, strategy, and trading state
- safe unattended VPS operation
- a deployment and recovery model a non-technical owner can actually use

## 2. Product Finish Gates

The system is only product-complete when all of the following are true:

1. The owner can inspect system health, learning, strategy, trading, and incidents primarily from Discord and the dashboard.
2. Runtime configuration is durable, proposal-driven, auditable, and reversible.
3. Risky owner actions and risky system promotions always flow through approvals and versioned records.
4. Broker truth, order recovery, sync, and reconciliation are real rather than paper-only scaffolds.
5. Auto-evolution is bounded by review, eval, canary, rollback, and objective-drift controls.
6. VPS deployment, backup, restore, upgrade, and break-glass operations are scripted and validated.

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

- Discord operator security and richer owner UX
- real broker adapters
- multi-instrument trading closure for options, short lifecycle, and leverage-aware execution
- governed strategy-to-capital promotion closure
- full auto-evolution closure
- VPS productization and operator runbooks

## 4. Finish Order

### 4.1 Stage A: Owner Control Plane Hardening

Scope:

- Discord allowlists / trusted-operator model
- channel and DM safety defaults
- richer approval ergonomics
- natural-language owner flows for common configuration and control actions
- incident-safe Chinese-first interaction quality

Done when:

- Discord can act as the primary owner console
- risky actions are approval-backed
- operator access and bot surface are explicitly bounded

### 4.2 Stage B: Multi-Instrument Broker Truth Closure

Scope:

- canonical instrument and broker capability model
- equities, options, and short/margin-aware order semantics
- paper/live product-parity execution logic
- one or more real broker adapters
- authenticated sync loops
- cancel/replace/sync parity with broker truth
- portfolio sleeve attribution and symbol ownership
- live capital guardrails tied to strategy stage

Done when:

- the trading kernel no longer relies on equity-only assumptions
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

### 4.4 Stage D: VPS Productization

Scope:

- production compose / systemd deployment shape for the 2-VPS topology
- health checks, startup ordering, and smoke checks
- backup and restore scripts
- upgrade procedure
- operator runbooks
- simple env templates for relay-based API users

Done when:

- a fresh VPS deployment can be brought online from a runbook
- a restore drill succeeds
- safe mode and break-glass actions are documented and tested

## 5. Immediate Next Build Queue

1. Close multi-instrument paper execution and product-aware risk rules on top of the new instrument and broker capability model.
2. Harden Discord operator security and owner workflow ergonomics.
3. Implement the first real broker adapter and authenticated sync loop.
4. Add product-grade deployment checks, backup scaffolding, and operator runbooks.
5. Close governed strategy-to-capital promotion.
6. Close governed auto-evolution promotion and rollback.

## 6. Non-Negotiable Constraints

- Do not redesign the single-writer core plus elastic work-plane architecture.
- Do not multiply autonomous masters.
- Do not treat Discord chat history as runtime truth.
- Do not allow self-improvement or live-trading promotion without audit, rollback, and bounded authority.
- Do not optimize for novelty at the expense of owner governability.
