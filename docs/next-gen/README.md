# Next-Gen Autonomous Investment System

This folder defines the next-generation architecture for the project.

The goal is not to keep stacking prompts, bots, and agent personas on top of OpenClaw-style runtime behavior. The goal is to build a long-running autonomous system that is:

- durable
- governable
- auditable
- recoverable
- Discord-first for the owner
- able to keep learning, debating, improving, and trading
- powered by Codex-compatible execution without making Codex the only control brain

## Core Goals

The new design keeps the same product goals:

- Discord remains the primary IM and control surface.
- Multi-agent debate remains a core quality mechanism.
- Continuous web learning, reflection, and self-improvement remain first-class loops.
- The system runs continuously on VPS infrastructure.
- Automated trading remains a core capability.
- A dashboard website remains part of the operator experience.
- Governance, state consistency, risk control, and token efficiency become much stronger.

## Recommended Architecture

The current recommended target is:

```text
Discord Shell
  -> slash commands
  -> threads
  -> alerts
  -> approvals
  -> reports

Control Plane
  -> FastAPI core
  -> durable workflow engine
  -> state machine
  -> goal/task/approval/incident records
  -> deterministic risk governance

Council Engine
  -> multi-agent planning
  -> debate
  -> decision reduction
  -> goal revision

Execution Fabric
  -> Codex CLI / Codex-compatible workers
  -> repo-aware code and ops tasks
  -> structured artifacts
  -> eval and review loops

Learning Mesh
  -> API-first source ingest
  -> web search
  -> scrape and browser fallback
  -> evidence extraction
  -> synthesis and principle promotion

Strategy Lab
  -> hypothesis
  -> backtest
  -> paper
  -> promotion gates

Trading and Risk
  -> deterministic order controls
  -> broker adapters
  -> reconciliation
  -> halt and freeze controls

Observability
  -> traces
  -> metrics
  -> audit
  -> lineage
  -> budget tracking
```

## Topology Decision

The long-term topology decision is now explicit:

- Best-fit production default: `2 VPS, asymmetrical`
- Control/data authority stays on `VPS-A Core`
- Heavy research and Codex work runs on `VPS-B Research`
- Scaling beyond 2 nodes means adding more research workers, not more control-plane masters
- Use `1 Discord bot`, not one bot per persona

Read the full decision here:

- [TOPOLOGY-AND-SCALING-DECISION.md](TOPOLOGY-AND-SCALING-DECISION.md)

## Start Here

If you are preparing the repository for GitHub publication and then deploying it onto VPS nodes, start with:

1. [GITHUB-TO-VPS-DEPLOYMENT.md](GITHUB-TO-VPS-DEPLOYMENT.md)
2. [VPS-DEPLOYMENT-RUNBOOK.md](VPS-DEPLOYMENT-RUNBOOK.md)
3. [OWNER-OPERATION-QUICKSTART.md](OWNER-OPERATION-QUICKSTART.md)
4. [CURRENT-DELIVERY-STATUS.md](CURRENT-DELIVERY-STATUS.md)

## Design Package

1. [SYSTEM-CHARTER.md](SYSTEM-CHARTER.md)
2. [STATE-MODEL.md](STATE-MODEL.md)
3. [WORKFLOW-CATALOG.md](WORKFLOW-CATALOG.md)
4. [ROLE-PERSONA-MODEL.md](ROLE-PERSONA-MODEL.md)
5. [CODEX-WORKER-PROTOCOL.md](CODEX-WORKER-PROTOCOL.md)
6. [RISK-GOVERNANCE.md](RISK-GOVERNANCE.md)
7. [MULTI-EXPERT-SYSTEM-REVIEW.md](MULTI-EXPERT-SYSTEM-REVIEW.md)
8. [TOPOLOGY-AND-SCALING-DECISION.md](TOPOLOGY-AND-SCALING-DECISION.md)
9. [OPERATIONS-AND-DEPLOYMENT.md](OPERATIONS-AND-DEPLOYMENT.md)
10. [DISCORD-NL-INTERACTION-MODEL.md](DISCORD-NL-INTERACTION-MODEL.md)
11. [CORE-GOAL-COVERAGE-REVIEW.md](CORE-GOAL-COVERAGE-REVIEW.md)
12. [DASHBOARD-WEBSITE-SPEC.md](DASHBOARD-WEBSITE-SPEC.md)
13. [IMPLEMENTATION-ROADMAP.md](IMPLEMENTATION-ROADMAP.md)
14. [IMPLEMENTATION-REVIEW-LOG.md](IMPLEMENTATION-REVIEW-LOG.md)
15. [FULL-SYSTEM-STAGE-PLAN.md](FULL-SYSTEM-STAGE-PLAN.md)
16. [REFERENCE-IMPLEMENTATION-RESEARCH.md](REFERENCE-IMPLEMENTATION-RESEARCH.md)

## Relationship to the Current Repository

Existing repo assets are still useful, including:

- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [protocols](../../protocols)
- [config](../../config)
- [knowledge](../../knowledge)
- [strategies](../../strategies)
- [memory](../../memory)

But the next-gen system changes some core responsibilities:

- `Discord` is no longer the runtime source of truth. It is the control and presentation shell.
- `GitHub repo` is no longer the runtime source of truth. It stores code, prompts, assets, and versioned artifacts.
- `Postgres` becomes the runtime source of truth.
- Multi-agent behavior remains, but only under workflow, budget, evidence, and decision constraints.
- `Codex` becomes the default execution worker for code and ops work, not a side helper.

## Reading Order

Recommended reading order:

1. `SYSTEM-CHARTER`
2. `STATE-MODEL`
3. `WORKFLOW-CATALOG`
4. `ROLE-PERSONA-MODEL`
5. `CODEX-WORKER-PROTOCOL`
6. `RISK-GOVERNANCE`
7. `MULTI-EXPERT-SYSTEM-REVIEW`
8. `TOPOLOGY-AND-SCALING-DECISION`
9. `OPERATIONS-AND-DEPLOYMENT`
10. `DISCORD-NL-INTERACTION-MODEL`
11. `CORE-GOAL-COVERAGE-REVIEW`
12. `DASHBOARD-WEBSITE-SPEC`
13. `IMPLEMENTATION-ROADMAP`
14. `IMPLEMENTATION-REVIEW-LOG`
15. `FULL-SYSTEM-STAGE-PLAN`
16. `REFERENCE-IMPLEMENTATION-RESEARCH`

## Implementation Principles

- Lock the end-state architecture before optimizing the build order.
- Keep all autonomy inside durable workflow and audit boundaries.
- High-risk actions must always have rollback conditions.
- Multi-agent debate must emit structured decision records.
- Learning must be promoted into evidence and principles, not left as prompt residue.
- Self-modification must pass eval, shadow, and promotion gates before reaching live trading paths.
