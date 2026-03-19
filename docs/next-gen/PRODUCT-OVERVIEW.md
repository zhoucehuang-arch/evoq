# Product Overview

Quant Evo Next-Gen is an autonomous investment platform built around three ideas:

1. the owner should be able to operate the system mainly through Discord and a dashboard
2. research, strategy, and trading should happen inside governed workflows instead of ad hoc prompts
3. the system should be deployable on VPS infrastructure and maintainable over long periods of time

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

### Core VPS

- API and control plane
- Postgres
- supervisor loops
- Discord shell
- dashboard
- broker-facing authority

### Worker VPS

- Codex-powered execution
- heavier research and synthesis work
- isolated execution workloads

## Daily Operator Model

Most of the time, the owner should be able to:

- ask for status in Discord
- review decisions and incidents in the dashboard
- approve or pause actions in Discord
- rely on SSH only when deploying, upgrading, restoring, or recovering

## First Safe Operating Posture

- deploy Core and Worker to separate VPS nodes
- start in `paper` mode
- verify smoke checks before trusting automation
- keep Discord access limited to explicit owner accounts and channels
- keep broker credentials on Core only

## Where To Read Next

- [FAQ.md](FAQ.md)
- [GITHUB-TO-VPS-DEPLOYMENT.md](GITHUB-TO-VPS-DEPLOYMENT.md)
- [OWNER-OPERATION-QUICKSTART.md](OWNER-OPERATION-QUICKSTART.md)
- [VPS-DEPLOYMENT-RUNBOOK.md](VPS-DEPLOYMENT-RUNBOOK.md)
