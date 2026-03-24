# Codex Worker Protocol

## Purpose

This document defines how `Codex` is integrated as the default execution engine inside EvoQ.

Core conclusions:

- `Codex` is the default worker for high-value implementation and analysis tasks.
- `Codex` is not the sole governance center.
- every Codex run must be wrapped by workflow, policy, budget, review, and artifact capture

## Why Codex Is First-Class

Codex is a strong fit because it is naturally good at:

- repository exploration
- code implementation and refactoring
- test creation and repair
- deployment and operations scripting
- structured execution through CLI-driven workflows

The system should prefer Codex for concrete execution instead of asking a general-purpose agent to simulate implementation in long-form chat.

## Architectural Position

```text
Council / Planner / Governor
  -> task specification
  -> policy + budget + write scope

Codex Fabric
  -> worker queue
  -> workspace isolation
  -> run execution
  -> artifact capture
  -> review / eval handoff

Kernel
  -> state persistence
  -> retries
  -> approvals
  -> metrics
```

## Supported Execution Modes

### `local_exec`

Default mode for VPS operation:

```bash
codex exec --json --output-schema <schema.json> -C <workspace> "<prompt>"
```

Use for:

- long-running local VPS operation
- repository tasks
- controlled writes inside a bounded workspace

### `local_review`

Use for patch or diff review:

```bash
codex review --uncommitted
```

### `local_apply`

Use to apply generated patches inside the target workspace:

```bash
codex apply
```

### `cloud_exec`

Optional future mode for bursty or asynchronous workloads.

Rules:

- cloud execution is optional, not a hard dependency
- all cloud results must still write back local durable state and artifacts

## Worker Classes

Different task types should use different worker classes instead of one giant universal prompt.

### `analysis_worker`

Use for:

- repo research
- dependency comparisons
- root-cause analysis
- architecture mapping

### `implementation_worker`

Use for:

- writing code
- editing code
- adding tests
- creating scripts
- updating configuration

### `review_worker`

Use for:

- diff review
- regression detection
- risk spotting
- test-gap review

### `strategy_worker`

Use for:

- strategy implementation
- backtest harness generation
- metric extraction
- research artifact generation

### `ops_worker`

Use for:

- deployment scripts
- maintenance repair
- incident remediation candidates
- monitoring updates

## Worker Request Object

Every Codex run should receive a structured request object.

Required fields:

- `codex_run_id`
- `goal_id`
- `task_id`
- `worker_class`
- `objective`
- `context_summary`
- `write_scope`
- `do_not_touch`
- `success_criteria`
- `risk_notes`
- `output_schema`
- `network_policy`
- `token_budget`
- `time_budget_sec`

## Workspace Isolation

Codex workers must run in isolated workspaces so concurrent tasks cannot corrupt each other.

Recommended modes:

- repo-local scratch workspace for bounded patch tasks
- ephemeral temp workspace for high-risk experiments
- read-only workspace for pure analysis and review

Hard rules:

- each run writes only to its own workspace
- no worker writes directly to the main tree without a review path
- only reviewed artifacts may flow back into durable truth

## Required Outputs

Codex must return more than a natural-language summary.

Each run should produce:

- structured result JSON
- command log or execution summary
- changed file list when code is modified
- test / validation result summary
- explicit failure reason when blocked

## Risk Tiers

### `R1`

Examples:

- reading docs
- adding comments
- tiny analysis scripts

Requirements:

- structured output
- basic logging

### `R2`

Examples:

- ordinary code changes
- acquisition logic updates
- strategy research script changes

Requirements:

- review worker or `codex review`
- at least one validation step

### `R3`

Examples:

- strategy implementation changes
- state-machine changes
- approval logic updates

Requirements:

- explicit review
- stronger validation
- promotion gate

### `R4`

Examples:

- order-routing logic
- risk thresholds
- kill switch behavior
- autonomy-level changes

Requirements:

- hard governance gate
- mandatory review
- eval before adoption
- shadow or canary when applicable

## Input Discipline

Codex should receive structured context, not raw chat history.

Include:

- objective
- current context summary
- allowed write scope
- forbidden scope
- success criteria
- explicit risks
- output schema

Avoid:

- dumping full historical chat into the worker
- omitting success criteria
- omitting write boundaries
- combining unrelated risky tasks into one run

## Governance Separation

The relationship should be:

- council proposes and frames the task
- Codex executes and returns artifacts
- reviewers or governance layers decide whether to adopt the result

Do not let one worker become proposer, approver, and deployer without separation.

## Failure Model

Temporary failures:

- network issues
- tool unavailability
- workspace conflicts
- transient test failures

Hard failures:

- unclear task definition
- invalid write scope
- exhausted budget
- permission mismatch
- impossible output schema

Even failures must report:

- failure reason
- completed work
- blockers
- recommended next step

## Permissions

Every Codex run must explicitly declare:

- whether network access is allowed
- whether shell writes are allowed
- whether secrets are accessible
- whether broker credentials are accessible
- whether production config is accessible

Defaults:

- no secrets by default
- no production broker access by default
- no direct deploy authority by default

## Abstraction Layer

The system should call an internal `codex worker protocol`, not depend on raw CLI details forever.

That keeps the top layer stable if the bottom layer later changes from CLI to SDK or another managed mode.

## Metrics

Track Codex fabric value over time:

- task completion rate
- token cost by task class
- latency by task class
- review pass rate
- eval pass rate
- regression incident rate
- human work saved

## Non-Negotiable Boundaries

- Codex workers do not directly own production release authority.
- Codex workers do not directly own broker capital authority.
- high-risk outputs always pass a governance threshold.
- every run must remain auditable end to end.
