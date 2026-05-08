# GitHub Landing Page Guide

This page explains how to read the GitHub project page and where to go next.

## What The README Is Optimized For

The root README is intentionally written for three audiences:

1. **Owner**: wants to know what EvoQ does and how to run it safely.
2. **Builder**: wants to understand architecture, local setup, validation, and contribution paths.
3. **Operator**: wants deployment, smoke checks, paper-first activation, and break-glass guidance.

It is not trying to be a full architecture spec. It is the front door.

## Recommended GitHub Reading Path

### If you are new

1. [../../README.md](../../README.md)
2. [EVOQ-BEGINNER-README.md](EVOQ-BEGINNER-README.md)
3. [EVOQ-USER-MANUAL.md](EVOQ-USER-MANUAL.md)
4. [FAQ.md](FAQ.md)

### If you want to run it locally

1. [../../README.md](../../README.md#quick-start-from-github-to-local-dashboard)
2. Clone the repo or download the ZIP from GitHub.
3. Install Python dependencies with `python -m pip install -e ".[dev]"`.
4. Install dashboard dependencies with `npm ci` in `apps/dashboard-web`.
5. Start with `ops/tools/start_local.ps1`.
6. Verify with `ops/tools/smoke_local.ps1`.
7. Continue with [EVOQ-USER-MANUAL.md](EVOQ-USER-MANUAL.md).

### If you want to deploy it

1. [GITHUB-TO-VPS-DEPLOYMENT.md](GITHUB-TO-VPS-DEPLOYMENT.md)
2. [VPS-DEPLOYMENT-RUNBOOK.md](VPS-DEPLOYMENT-RUNBOOK.md)
3. [FIRST-PAPER-RUN-CHECKLIST.md](FIRST-PAPER-RUN-CHECKLIST.md)
4. [BREAK-GLASS-RUNBOOK.md](BREAK-GLASS-RUNBOOK.md)

### If you want to understand safety

1. [../../README.md](../../README.md#safety-model)
2. [RISK-GOVERNANCE.md](RISK-GOVERNANCE.md)
3. [EVOQ-COMPLETE-DELIVERY-PLAN.md](EVOQ-COMPLETE-DELIVERY-PLAN.md)
4. [../../SECURITY.md](../../SECURITY.md)

## README Design Reflection

The older README over-emphasized Discord-first operation and VPS deployment. That was no longer aligned with the current product:

- Dashboard is now the primary owner surface.
- The chat gateway is optional and light, not the main operating model.
- The useful first path is local replay data -> deterministic factors -> PIT replay backtest -> paper evidence.
- LLMs are a research/challenge layer, not a direct trading engine.

The current README therefore leads with:

- dashboard-first workflow
- deterministic quant backbone
- paper-first and live-gated posture
- local quick start before VPS deployment
- explicit safety boundaries

## Inspiration From Comparable Projects

The README structure intentionally borrows patterns from strong open-source finance projects:

- Qlib-style pipeline framing: data -> signal/factor -> backtest -> production gates.
- OpenBB-style usability framing: make the research surface discoverable quickly.
- FinGPT-style LLM framing: use LLMs as a financial research layer, not as ungrounded execution authority.

EvoQ's own distinction is the governed runtime shape: one authoritative Core, dashboard-first operation, deterministic quant gates, and explicit paper-to-live progression.
