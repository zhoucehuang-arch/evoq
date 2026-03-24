# Product Overview

Quant Evo Next-Gen is an autonomous investment platform built around three ideas:

1. the owner should be able to operate the system mainly through Discord and a dashboard
2. research, strategy, and trading should happen inside governed workflows instead of ad hoc prompts
3. the system should be deployable on VPS infrastructure and maintainable over long periods of time

## Why This Project Exists

Many autonomous-investment projects can produce impressive demos but weak operating posture.

This project is deliberately optimized for a different outcome:

- a non-terminal-first owner experience
- durable system memory and governed write paths
- long-running supervision instead of one-shot prompting
- paper-first activation instead of accidental live escalation

The target is not just a clever agent loop. The target is an operating system for autonomous research, controlled strategy evolution, and governed trading.

## Who It Is For

- owners who want to talk to the system in Discord and review it in a dashboard
- operators who want multi-agent challenge and refinement without creating many sovereign daemons
- builders who want a design that can start on one VPS and scale the worker plane later without changing the product shell

## Who It Is Not For

- people looking for a toy bot or a single-script strategy runner
- operators who do not want approval, audit, or rollback boundaries
- anyone treating live trading as something to switch on before paper-mode evidence is clean

## Main Capabilities

### 1. Research and learning

- gathers information from APIs, search, scrape, and browser fallback paths
- stores research outputs as durable documents and evidence
- promotes learning into reusable insights and principles

### 2. Multi-agent review

- uses specialized roles to plan, challenge, and refine work
- keeps debate inside structured workflows
- turns discussion into explicit decisions rather than leaving it in prompt residue

### 3. Strategy lifecycle

- supports hypothesis creation
- tracks strategy specs, backtests, paper runs, promotions, and withdrawals
- keeps strategy movement visible and auditable

### 4. Governed execution

- routes execution through controlled workers
- records approvals, overrides, incidents, and rollbacks
- keeps trading and self-improvement inside explicit governance boundaries

### 5. Owner operations

- Discord is the main write surface
- Dashboard is the main read and review surface
- SSH is mainly for deployment, upgrades, restore, and break-glass work

## Recommended Runtime Shape

### Single-VPS first

- one VPS running `single_vps_compact`
- Core remains the authority node
- the same machine also hosts the Codex worker runtime
- Discord and dashboard stay the main owner surfaces

### Scale out later

- keep `Core` as the authority node
- add `1 Worker VPS` for heavier Codex execution and research
- keep broker-facing secrets on Core only

## Market Mode

The product supports both US and China-market operation, but one deployment chooses one market mode:

- `QE_DEPLOYMENT_MARKET_MODE=us`
  - activates `us_equities` and `us_options`
- `QE_DEPLOYMENT_MARKET_MODE=cn`
  - activates `cn_equities`

This is a product rule, not just a doc suggestion. It keeps one runtime easier to govern and keeps market-specific broker truth explicit.

## Current Trading Surface

- `US` mode currently supports governed equities, options, multi-leg option structure, and Alpaca-backed paper/live progression.
- `CN` mode currently supports A-share research, ranking, market-session governance, and paper-first operation.
- The current honest boundaries are:
  - `CN live` broker execution is not shipped yet
  - sleeve attribution is still conservative in some cross-strategy cases
  - universal maintenance-margin and borrow-fee modeling is not fully closed across every product path

## Daily Operator Model

Most of the time, the owner should be able to:

- ask for status in Discord
- review decisions and incidents in the dashboard
- approve or pause actions in Discord
- rely on SSH only when deploying, upgrading, restoring, or recovering

## First Safe Operating Posture

- deploy `single_vps_compact` first unless you already need stronger isolation
- start in `paper` mode
- verify smoke checks before trusting automation
- keep Discord access limited to explicit owner accounts and channels
- keep broker credentials on Core only
- add the Worker later when you want more isolation or more research throughput

## What Good Looks Like

When the system is behaving as intended:

- the owner can handle most control actions from Discord
- the dashboard makes trading, learning, evolution, and incidents legible at a glance
- worker activity stays productive without becoming the authority layer
- paper and live transitions remain deliberate, evidence-based, and reversible

## Where To Read Next

- [FAQ.md](FAQ.md)
- [GITHUB-TO-VPS-DEPLOYMENT.md](GITHUB-TO-VPS-DEPLOYMENT.md)
- [FIRST-PAPER-RUN-CHECKLIST.md](FIRST-PAPER-RUN-CHECKLIST.md)
- [OPERATOR-JOURNEYS.md](OPERATOR-JOURNEYS.md)
- [OWNER-OPERATION-QUICKSTART.md](OWNER-OPERATION-QUICKSTART.md)
- [VPS-DEPLOYMENT-RUNBOOK.md](VPS-DEPLOYMENT-RUNBOOK.md)
