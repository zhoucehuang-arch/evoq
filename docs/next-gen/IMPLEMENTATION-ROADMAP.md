# IMPLEMENTATION ROADMAP

## 1. Purpose

This roadmap turns the next-gen design package into an implementation program with clear milestones, review gates, and reflection prompts.

## 2. Delivery Principles

- Build from the inside out: state, contracts, deployment, control plane, then autonomy loops.
- Keep every stage runnable before moving on.
- Every stage ends with review, reflection, and a written next-step decision.
- Do not fake automation. If a loop is not live yet, surface it as pending.
- Keep the architecture invariant fixed: one authoritative core, one authoritative runtime database, and an elastic research plane that can scale from 2 nodes to N without redesigning governance.

## 3. Stage Plan

### Audit Gate: Multi-Expert Hardening

Deliverables:

- Hidden requirements review
- Mission priority clarification
- Bootstrap-vs-production separation
- Provider portability requirements
- Learning safety requirements
- Owner absence and takeover requirements

Acceptance:

- The design package is explicit about hidden constraints that would otherwise surface as late production failures
- Further implementation is constrained by those requirements instead of rediscovering them piecemeal

Review checklist:

- Are any major runtime truths still implicit?
- Could a non-technical owner still be surprised by a hidden failure mode?

Reflection prompts:

- What would fail silently if the owner disappeared for a week?
- What would poison the system slowly without an obvious incident?

### Stage 1: Foundation

Deliverables:

- Root environment template
- Docker Compose baseline
- Backend package scaffold
- Dashboard app scaffold
- Repo-derived status API

Acceptance:

- Services can boot locally with mock or repo-derived data
- Dashboard can render against the API
- Owner can understand the system shape without reading code

Review checklist:

- Are deployment steps short and repeatable?
- Are the config names readable for a non-technical owner?
- Is the API honest about what is live versus placeholder?

Reflection prompts:

- What felt more complex than it should?
- What did we add that is not yet earning its keep?

### Stage 2: State and Persistence

Deliverables:

- Postgres schema
- Migrations
- Core state entities
- Workflow event tables
- Approval tables

Acceptance:

- The system can persist goals, tasks, workflows, decisions, and incidents
- A restart does not erase runtime state

Review checklist:

- Does every high-value action have a durable record?
- Are there any important states still trapped in logs or memory?

### Stage 3: Discord Control Plane

Deliverables:

- Discord bot setup flow
- Slash commands
- Natural language router
- Approval cards
- Owner preference memory

Acceptance:

- Owner can perform most read-only operations via Discord
- High-risk actions produce confirmation cards instead of silent execution

Review checklist:

- Are responses clear in Chinese?
- Are we avoiding fake confirmations?
- Is clarification only used when necessary?

### Stage 4: Dashboard and Read Models

Deliverables:

- Overview page
- Trading page
- Evolution page
- Learning page
- System page
- Incident page

Acceptance:

- Freshness is visible
- Mobile layout remains usable
- Dashboard shows both auto-trading and auto-evolution state

Review checklist:

- Can the owner decide whether intervention is needed in under 30 seconds?
- Does the UI hide bad states or expose them honestly?

### Stage 5: Codex Fabric

Deliverables:

- Codex run request schema
- Worker isolation
- Command builder and execution wrapper
- Artifact capture
- Review and eval handoff

Acceptance:

- A Codex task can be queued, executed, reviewed, and archived
- Outputs are structured and traceable

Review checklist:

- Are we giving Codex too much power anywhere?
- Are workspaces isolated enough to avoid accidental contamination?

### Stage 6: Learning Mesh

Deliverables:

- Source ingest jobs
- Evidence extraction
- Topic synthesis
- Principle promotion pipeline

Acceptance:

- The system can ingest, dedupe, and distill external information
- Long-term memory only receives promoted artifacts

Review checklist:

- Are we controlling knowledge pollution?
- Are we promoting facts or just confident summaries?

### Stage 7: Strategy Lab

Deliverables:

- Hypothesis lifecycle
- Strategy spec contract
- Backtest integration
- Paper promotion logic
- Withdrawal flow

Acceptance:

- Strategy lifecycle becomes explicit and queryable
- No direct jump from idea to production

Review checklist:

- Are promotion thresholds explicit?
- Are we capturing why a strategy failed?

### Stage 8: Trading and Risk

Deliverables:

- Broker adapters
- Session boot checks
- Signal-to-order pipeline
- Reconciliation
- Halt and freeze controls

Acceptance:

- Orders are idempotent
- Broker state can be reconciled after restart
- Risk controls can stop execution immediately

Review checklist:

- Is there any path to capital without deterministic safeguards?
- Can the system explain every live order?

### Stage 9: Auto-Evolution

Deliverables:

- Capability gap mining
- Improvement goals
- Codex-driven implementation loop
- Eval ladder
- Shadow and canary gates

Acceptance:

- The system can identify, propose, implement, evaluate, and either promote or roll back self-improvements

Review checklist:

- Are we measuring actual capability gain?
- Are we changing too much at once?

### Stage 10: Hardening

Deliverables:

- Backup and restore
- Safe mode
- Incident automation
- Budget governance
- Runbooks

Acceptance:

- The system can recover from dependency failures, restart cleanly, and degrade safely

Review checklist:

- Does the owner have a path forward during a bad night?
- Are the runbooks written for humans, not engineers?

## 4. Review Cadence

Every implementation slice should end with:

1. Build or test validation
2. A written review note
3. A reflection note
4. A next-slice decision

## 5. Initial Focus

The current active focus is:

- Stage 2: State and persistence
- Audit-gap closure from the multi-expert review
- Topology hardening around the `2 VPS, asymmetrical` production default
- Provider abstraction for custom OpenAI-compatible relays
- Discord control actions backed by durable state
- Dashboard read models backed by the database instead of repo-only state
- Learning safety mechanisms: source health, revalidation, and trust decay
- Operator absence, recovery drill, and break-glass design
- The future continuous loop supervisor that will run bounded outer loops instead of one-shot autonomy

These slices create the first trustworthy operating loop instead of just a visible shell.

## 6. Full-System Plan Reference

For the full delivery sequence, stage status board, and definition of done for the entire system, see:

- [FULL-SYSTEM-STAGE-PLAN.md](FULL-SYSTEM-STAGE-PLAN.md)
