# Full System Stage Plan

## 1. Purpose

This document is the execution blueprint for the next-generation autonomous investment system.
It is not only a technical roadmap. It defines the full governed build order required to reach the target system.

The target system must satisfy these end-state requirements together:

- Discord-first natural-language control for the owner
- dashboard-first observability for runtime, learning, strategy, and incidents
- Codex-centered execution compatible with the owner's relay API
- multi-agent debate and reflection, but always under governance and budget bounds
- continuous online learning, reflection, and capability strengthening
- governed strategy lifecycle from hypothesis to paper to limited live to withdrawal
- unattended VPS operation with safe degradation and recovery
- simple deployment and operations for a non-technical owner

## 2. Definition Of Done

The system is only considered complete when all of the following are true:

1. Core runtime truth lives in durable state, not in Discord chat history or transient prompt context.
2. The owner can primarily observe and control the system through Discord and the dashboard.
3. The system can run safely during owner absence with bounded automation and safe-mode behavior.
4. Learning, strategy, trading, and auto-evolution all have explicit workflows, budgets, audits, and rollback paths.
5. Multi-agent debate is governed by role, budget, stop conditions, and promotion rules.
6. VPS deployment, backup, upgrade, restore, and break-glass procedures are implemented and validated.

## 3. Stage Status Board

| Stage | Name | Status | Notes |
|---|---|---|---|
| 0 | Audit and reference research | completed | Multi-angle audit and architecture direction established |
| 1 | Foundation scaffold | completed | Backend, dashboard shell, Discord shell baseline |
| 2 | Persistence and governance kernel | completed | Durable runtime truth, approvals, incidents, loops, dashboard counts |
| 3 | Discord control plane | in_progress | Approvals, NL config proposals, and durable config revisions are live; security and richer owner workflows still pending |
| 4 | Dashboard website | in_progress | Page-specific read models are live; richer owner actions still pending |
| 5 | Codex fabric | in_progress | Durable queue, artifacts, Ralph-style retries, review/eval phases are live |
| 6 | Continuous loop supervisor | in_progress | Persisted bounded loops are live; several defaults are active |
| 7 | Learning mesh | in_progress | Documents, evidence, insight gates, quarantine, resynthesis are live |
| 8 | Strategy lab | in_progress | Hypothesis/spec/backtest/paper/promotion/withdrawal are live |
| 9 | Trading and risk | in_progress | Session guard, readiness, paper order path, and reconciliation halts live; external broker sync still pending |
| 10 | Auto-evolution | pending | Improvement goals, shadow/canary, objective drift review |
| 11 | Hardening and production ops | pending | 2 VPS deploy, backup/restore, drills, safe mode, runbooks |

## 4. Stage Detail

### 4.1 Stage 0: Audit And Reference Research

Goals:

- audit the system through architecture, trading-risk, autonomy, security, ops, owner-experience, and cost lenses
- make hidden requirements explicit
- research external references without copying them blindly

Done when:

- the multi-expert review exists
- hidden constraints are encoded into the design
- later implementation is explicitly constrained by those findings

### 4.2 Stage 1: Foundation Scaffold

Goals:

- create a runnable backend and dashboard shell
- define honest bootstrap behavior before production automation
- expose repo-derived status instead of empty placeholder UI

Done when:

- API starts
- dashboard builds
- Discord shell can read status
- tests pass

### 4.3 Stage 2: Persistence And Governance Kernel

Goals:

- establish the authoritative runtime database
- persist goals, approvals, incidents, overrides, workflow runs, and loop state
- move dashboard truth away from repo-only reads

Done when:

- restart does not lose core runtime state
- control actions have durable records
- heartbeat and workflow history are auditable
- dashboard surfaces DB-backed runtime truth

### 4.4 Stage 3: Discord Control Plane

Goals:

- make Discord the real owner control surface
- support both slash commands and natural-language routing
- force high-risk actions through approval-backed flows

Done when:

- common owner read actions work through Discord
- high-risk write actions generate durable approval objects
- Chinese and English interaction paths are readable and stable

### 4.5 Stage 4: Dashboard Website

Goals:

- deliver a real owner dashboard rather than a shell
- show degraded, stale, and risky states honestly
- make intervention decisions fast

Done when:

- overview, trading, learning, evolution, incidents, and system pages are operational
- mobile and desktop views are usable
- risky states are never cosmetically hidden

### 4.6 Stage 5: Codex Fabric

Goals:

- turn Codex CLI / Codex-compatible execution into a governed runtime layer
- persist requests, attempts, artifacts, and outcomes
- support Ralph-style retries, handoffs, review, and eval

Done when:

- a Codex task can be requested, executed, reviewed, evaluated, and archived
- artifacts and lineage are durable
- control logic does not depend on transient prompt memory

### 4.7 Stage 6: Continuous Loop Supervisor

Goals:

- implement the outer-loop runtime that keeps the system moving
- borrow the persistence idea of Ralph Loop without losing governance bounds
- add token, cost, failure, and stop-condition control

Current live loops:

- governance-heartbeat
- source-revalidation
- research-intake
- research-distillation
- learning-synthesis

Done when:

- long-running work is not one-shot
- every loop has budget, validator, stop conditions, and degradation behavior
- no loop can spin indefinitely without governance control

### 4.8 Stage 7: Learning Mesh

Goals:

- let the system learn continuously without poisoning long-term memory
- separate intake, evidence, synthesis, quarantine, and promotion
- decay stale trust and revalidate sources

Currently live:

- durable `document`
- durable `evidence_item`
- durable `insight`
- quarantine and promotion-state gating
- source-health-aware synthesis
- resynthesis path for existing learning items

Done when:

- long-term memory only accepts promoted artifacts
- stale, weak, or hostile content has a quarantine path
- principle, causal-case, and playbook promotion are live

### 4.9 Stage 8: Strategy Lab

Goals:

- make strategy development a governed lifecycle instead of prompt fragments
- force ideas through explicit evaluation stages
- make promotion and withdrawal auditable

Currently live:

- durable `hypothesis`
- durable `strategy_spec`
- durable `backtest_run`
- durable `paper_run`
- durable `promotion_decision`
- durable `withdrawal_decision`
- strategy lab API endpoints
- trading dashboard strategy-lifecycle views
- strategy-evaluation supervisor context from durable strategy state

Done when:

- no idea can jump directly to production
- every promotion and withdrawal has durable evidence and rationale
- allocation and portfolio policy are connected to the lifecycle

### 4.10 Stage 9: Trading And Risk

Goals:

- build the real capital-facing execution kernel
- connect signal-to-order flow to session guards and kill switches
- make reconciliation first-class

Includes:

- broker adapters
- market/session guards
- signal-to-order translation
- reconciliation
- risk halts
- kill switches

Currently live:

- durable `market_calendar_state`
- durable `broker_account_snapshot`
- durable `reconciliation_run`
- durable `broker_sync_run`
- durable `allocation_policy`
- durable `order_intent`
- durable `order_record`
- durable `position_record`
- execution readiness API and trading dashboard exposure
- governed order-intent submission API
- paper broker adapter for simulated fills and durable position updates
- external-style broker sync, cancel, replace, and restart recovery path
- reconciliation-triggered trading halt plus incident escalation
- cross-strategy symbol-collision guard for shared broker accounts
- active supervisor `market-session-guard`

Done when:

- order paths are auditable and restart-safe
- risk halt can stop trading immediately
- broker divergence and reconciliation failures surface as incidents

### 4.11 Stage 10: Auto-Evolution

Goals:

- let the system improve itself without rewriting its mission
- keep self-improvement governed by review, eval, and canary paths

Includes:

- capability-gap mining
- improvement goals
- Codex build cycle
- shadow and canary promotion
- objective drift review

Done when:

- every self-improvement action is either validated and promoted or rejected and archived
- auto-evolution cannot directly modify live authority paths without governance

### 4.12 Stage 11: Hardening And Production Ops

Goals:

- finish the production-ready operating envelope
- make the system survivable, recoverable, and governable on VPS

Includes:

- 2 VPS asymmetrical deployment
- backup and restore
- disaster drills
- safe mode
- break-glass procedures
- logs, metrics, alerts
- runbooks

Done when:

- the owner does not need constant SSH access
- there is a clear manual takeover path during incidents
- backup and restore have been exercised in practice

## 5. Mandatory Review After Every Stage

Every stage must pass all of these reviews before being considered complete:

1. Architecture review
2. Trading-risk and capital-safety review
3. Learning-poison and autonomy-drift review
4. Security and permission-boundary review
5. Operations and owner-experience review
6. Cost and token-efficiency review
7. Test and regression review

If any review fails, the stage is not done.

## 6. Current Recommended Build Order

1. Extend Stage 8 into allocation policy, governed promotion flows, and tighter trading-readiness gates.
2. Build Stage 9 trading and risk controls before enabling any real autonomous live execution.
3. Extend Stage 7 into principle, causal-case, and playbook promotion.
4. Build Stage 10 auto-evolution on top of the governed strategy and learning substrate.
5. Finish Stage 11 hardening, VPS topology, recovery drills, and runbooks.
