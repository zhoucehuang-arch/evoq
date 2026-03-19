# Operations and Deployment

## 1. Purpose

This document defines how the next-generation system should be deployed and operated in real life.

The target is not just an architecture diagram that looks good. The target is a system that a non-technical owner can actually:

- deploy
- run
- inspect
- recover
- pause
- upgrade

without living inside SSH sessions.

## 2. Operating Goals

The deployment model must satisfy all of the following:

- Discord-first daily operation
- Dashboard-first visibility
- low day-0 friction
- strong runtime durability
- clear governance boundaries
- safe automated trading
- safe automated self-improvement
- simple scaling from 2 nodes to N nodes without redesign

## 3. Default Production Topology

### 3.1 Recommended default: `2 VPS, asymmetrical`

This is the recommended long-term production baseline.

```text
Discord
  -> one Discord app / bot

VPS-A Core
  -> reverse proxy
  -> core-api
  -> discord-shell
  -> workflow-runner
  -> risk-engine
  -> broker adapters
  -> approval service
  -> dashboard API
  -> postgres primary
  -> artifact metadata

VPS-B Research
  -> codex supervisor
  -> codex workers
  -> web-learning jobs
  -> scrape jobs
  -> browser automation fallback
  -> backtests
  -> eval jobs

Dashboard
  -> self-host on VPS-A or deploy frontend separately
```

### 3.2 Why this is the default

- Core trading and governance stay isolated from noisy research workloads.
- Broker credentials and control-plane authority remain on one boring, stable box.
- Codex, browsing, scraping, browser automation, and backtests can spike CPU, RAM, disk, and network without threatening the trading control path.
- Scaling beyond 2 nodes is straightforward: add more research workers, not more control masters.
- The mental model stays simple for the owner.

## 4. Single-VPS Mode

### 4.1 Allowed, but not the recommended steady state

`1 VPS` is still useful for:

- local development
- initial integration
- paper trading
- cost-constrained early operation

It is not the recommended long-term live-trading topology.

### 4.2 Why single-VPS is weaker

- Research, Codex, scraping, and browser sessions compete directly with the control plane.
- One incident can affect both runtime governance and execution.
- Secrets, risk controls, and noisy experimentation are harder to separate cleanly.
- Recovery blast radius is larger.

If single-VPS mode is used, all services must still respect the same logical split:

- control plane
- data plane
- work plane

## 5. Scaling Beyond Two Nodes

The architecture should scale as `single-writer core + elastic work plane`.

### 5.1 Node expansion order

After the first 2 nodes, the priority order is:

1. database durability and backups
2. more research workers
3. dedicated browser/scrape workers
4. dedicated backtest/eval workers

Do not scale by creating multiple autonomous masters.

### 5.2 Three-to-five node pattern

```text
Node 1
  -> Core control plane

Node 2
  -> Primary research worker

Node 3
  -> DB standby / backup / managed DB alternative

Node 4
  -> browser and scrape worker

Node 5
  -> backtest and eval worker
```

### 5.3 What should remain singular

These should remain singular in authority even when replicated for availability:

- runtime source of truth
- approval authority
- live trading authority
- risk limits
- strategy promotion authority
- goal promotion authority

## 6. Service Placement

### 6.1 VPS-A Core

Owns:

- Discord bot runtime
- owner intent routing
- workflow state transitions
- approvals
- incidents
- budget governance
- risk governance
- broker writes
- dashboard read models
- authoritative Postgres

Must not be used for:

- opportunistic scraping bursts
- large browser farms
- heavy backtests
- uncontrolled Codex fan-out

### 6.2 VPS-B Research

Owns:

- Codex worker execution
- repo-aware implementation tasks
- web-learning tasks
- evidence extraction
- browser automation fallback
- backtests
- evals

Must not hold:

- broker trading secrets
- Discord bot token if avoidable
- final promotion authority

## 7. Discord-First Operation

The owner experience should be primarily:

- ask in Discord
- approve in Discord
- inspect trends in the dashboard
- use SSH only for exceptional repair

The system should support natural-language intents such as:

- "What is the system state right now?"
- "Pause self-evolution tonight but keep paper trading."
- "Switch to conservative mode before market open."
- "Why was this strategy rejected from production?"
- "What did the system learn in the last 24 hours?"

## 8. Discord Runtime Constraints

Discord interaction handling must respect platform constraints:

- initial interaction response within 3 seconds
- follow-up window of 15 minutes on interaction tokens

This means long-running work must always:

- acknowledge quickly
- detach into durable workflow execution
- post progress and completion asynchronously

## 9. Codex Execution Policy

Codex should be central to execution, but not used as the only runtime brain.

Recommended split:

- Codex CLI / Codex-compatible workers for repo-aware code, shell, repair, refactor, and implementation tasks
- standard model calls for routing and low-cost classification
- research-oriented model calls for long-form external synthesis

Codex workers should run in isolated workspaces with:

- explicit inputs
- explicit budget
- explicit output schema
- artifact capture
- eval hooks
- review hooks

## 10. Learning and Web Acquisition

The default acquisition stack should be layered:

1. official APIs
2. hosted web search
3. search + scrape services
4. browser automation fallback
5. manual or GUI debugging only when necessary

The important rule is:

- browser and GUI are fallbacks, not the primary design center

## 11. Dashboard Deployment

The dashboard can be deployed in either of two ways:

- self-host frontend on `VPS-A Core`
- separate frontend deployment pointing to the Core API

For ease of ownership, both are acceptable as long as:

- the dashboard remains read-mostly
- live trading secrets never reach the frontend
- the dashboard is clearly separate from approval authority

## 12. Secrets Model

Secrets must be centralized and minimal.

Rules:

- broker secrets stay on Core only
- research workers receive only the secrets they need
- Codex workers do not receive global production secrets by default
- one primary `.env` or secret manager authority exists per environment

## 13. Deployment Modes

### 13.1 `safe_mode`

Used for:

- first deployment
- recovery
- upgrades
- incidents

Behavior:

- read-only diagnostics stay on
- high-risk autonomy pauses
- live promotion pauses

### 13.2 `paper_mode`

Used when:

- learning and evolution are active
- trading remains paper-only

### 13.3 `limited_live_mode`

Used when:

- reconciliation is proven
- strategy whitelist is explicit
- capital caps are explicit
- kill switch is tested

## 14. Backup and Restore

Minimum backup scope:

- Postgres
- artifact metadata
- deployment config
- workflow and approval history
- repo state

The restore target must be able to recover:

- last consistent runtime state
- last safe mode
- last trading freeze state

## 15. Upgrade Policy

Upgrades must be understandable, interruptible, and reversible.

Recommended sequence:

1. enter `safe_mode`
2. pause evolution promotion
3. back up Postgres and artifact metadata
4. deploy new version
5. run migrations
6. run smoke checks
7. resume normal mode only after health is green

Never:

- upgrade core components during uncontrolled live execution
- change schema without backup
- hot-edit production logic without audit trail

## 16. Easy-Operation Acceptance Criteria

The system only counts as easy to operate if:

1. A new environment can be brought up without memorizing internals.
2. Most daily control happens from Discord and the dashboard.
3. The owner can tell whether intervention is needed in under a minute.
4. Incidents have a safe-mode path and a written recovery path.
5. Scaling from 2 nodes to more workers does not require redesigning authority boundaries.

## 17. Local Bootstrap vs Production

The current repository bootstrap stack is intentionally simpler than the target production topology.

Rules:

- `docker-compose.yml` is a local bootstrap and integration stack.
- It must not be mistaken for the final production deployment shape.
- Production deployment decisions must always defer to the `2 VPS, asymmetrical` authority split.
- Local bootstrap convenience must never silently redefine production governance.

### 17.1 Current bootstrap Codex runner

The local bootstrap stack should now include a dedicated `codex-fabric-runner` service.

Rules:

- it should use a dedicated image that contains both the Python app runtime and the Codex CLI
- it should mount the workspace so `.qe/codex_runs/...` state survives container restarts
- relay users should set `QE_OPENAI_API_KEY` and `QE_OPENAI_BASE_URL`; the runner exports that key as both `OPENAI_API_KEY` and `CODEX_API_KEY` for Codex CLI execution
- this bootstrap runner is for integration and paper-mode validation, not proof that the final 2-VPS production split has been completed

### 17.2 Current production assets in this repository

The repository now contains concrete production-shaped assets for the `2 VPS` topology:

- Core stack compose: `ops/production/core/docker-compose.core.yml`
- Worker stack compose: `ops/production/worker/docker-compose.worker.yml`
- Core env template: `ops/production/core/core.env.example`
- Worker env template: `ops/production/worker/worker.env.example`
- Core bring-up and shutdown scripts: `ops/bin/core-up.sh`, `ops/bin/core-down.sh`
- Worker bring-up script: `ops/bin/worker-up.sh`
- Core smoke, backup, and restore scripts: `ops/bin/core-smoke.sh`, `ops/bin/backup-postgres.sh`, `ops/bin/restore-postgres.sh`
- Systemd units: `ops/systemd/quant-evo-core.service`, `ops/systemd/quant-evo-worker.service`
- VPS runbook: `docs/next-gen/VPS-DEPLOYMENT-RUNBOOK.md`

These assets materially reduce deployment ambiguity, but they still need a real Linux VPS drill before productization can be called fully complete.

## 18. Owner Absence Model

The system must remain safe when the owner is unavailable.

Minimum absence windows to design for:

- 72 hours
- 7 days
- 30 days

Rules:

- Risk posture must degrade safely when owner confirmations are unavailable.
- Pending high-risk approvals must expire into a safe state.
- Learning may continue under tighter controls even when promotion pauses.
- Live trading authority must never depend on the owner being awake at the right minute.

## 19. Manual Takeover and Break-Glass

The system must support manual takeover paths that are simple and reliable.

Required break-glass controls:

- freeze trading
- freeze execution
- freeze evolution
- freeze learning
- force global safe mode

These controls must be available through:

- Discord
- direct server-side runbook steps
- persisted state records

## 20. Drill Cadence

Resilience only counts if it is practiced.

The operations model must schedule recurring drills for:

- backup restore
- Discord bot credential rotation
- provider relay outage
- broker outage and reconciliation
- failover to safe mode during owner absence
