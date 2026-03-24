# System Charter

## Purpose

The mission of this system is to become a long-running autonomous investment and self-improvement platform that can keep learning, reasoning, improving, and trading without requiring constant owner supervision.

It is not a single trading bot. It is an operating system for governed research, controlled self-improvement, and bounded execution.

## End-State Vision

The target end state is `Discord-native but workflow-governed`:

- from the owner experience, it still feels like interacting with a multi-role autonomous team
- under the shell, it behaves like a state machine plus workflow engine plus artifact system
- Codex is the default execution engine for complex implementation work
- capital-facing behavior remains deterministic and policy-bound

## Core Missions

1. `Capital Mission`
   Pursue durable risk-adjusted returns inside explicit capital boundaries.
2. `Learning Mission`
   Expand the system's understanding of markets, methods, tools, and itself.
3. `Capability Mission`
   Improve research, coding, review, operations, memory, and risk-control ability over time.
4. `Governance Mission`
   Keep the whole system explainable, auditable, recoverable, and efficient while it grows stronger.

## Non-Goals

The system should not optimize for:

- apparent agent count
- long prompts as a substitute for structured state
- unrestricted capital decisions by free-form chat agents
- frequent production changes without evidence, review, and risk controls
- the illusion of total autonomy at the cost of safety

## Constitutional Principles

### State over chat

Chat is the shell. Durable state is the truth.

### Evidence over eloquence

Important decisions require evidence, artifacts, or measurable evaluation.

### Determinism at the edge of capital

Anything touching orders, positions, risk thresholds, or production rollout requires deterministic enforcement.

### Debate with budgets

Multi-agent discussion is allowed only inside round, time, and token budgets.

### Self-improvement with gates

High-impact self-change requires evaluation, review, and rollback-ready promotion.

### Preserve lineage

Strategies, principles, patches, and incidents must remain traceable.

### Discord as shell, not truth

Discord is the interaction layer, not the canonical runtime database.

## Operating Domains

The system is organized into these domains:

1. `Governance`
   goals, approvals, budgets, autonomy mode, policy
2. `Learning`
   source intake, evidence, synthesis, principles
3. `Research`
   market reasoning, hypotheses, experiments
4. `Execution`
   backtests, paper, trading, reconciliation, halts
5. `Evolution`
   improvement goals, Codex runs, review, promotion
6. `Memory`
   documents, principles, causal cases, playbooks
7. `Observability`
   logs, traces, metrics, doctor, incidents

## Autonomy Levels

### `A0: Manual Advisory`

- research and recommendations only
- no autonomous trading
- no autonomous patch deployment

### `A1: Research Automation`

- autonomous learning and experiment proposal
- offline backtests and evaluation allowed
- no real trading execution

### `A2: Paper Autonomous`

- autonomous paper progression
- autonomous low-risk improvement candidates
- risky actions still require approval

### `A3: Limited Live Autonomous`

- bounded live execution inside explicit capital and market limits
- automatic risk intervention and rollback remain active
- important self-change still goes through governance

### `A4: Charter-Bound Full Autonomy`

- high autonomy inside hard charter constraints
- kill switches, budgets, and hard risk boundaries still remain
- no unbounded sovereignty

## Hard Boundaries

These must exist as policy, not just prompt text:

- max capital utilization
- max per-strategy allocation
- max daily drawdown
- max portfolio drawdown
- max correlation overlap
- allowed markets and asset classes
- disallowed trading windows
- allowed auto-modification paths
- forbidden code paths
- daily token budget
- weekly evolution budget
- deploy authority policy
- strategy-merge authority policy

## System Success Criteria

Success is not measured by returns alone.

Also required:

- risk-adjusted performance improvement
- durable learning output
- stable and recoverable autonomous workflows
- positive quality impact from multi-agent debate
- measurable benefit from self-improvement
- acceptable operations and token cost

## Failure Definitions

The system is failing when:

- runtime truth diverges from durable state for long periods
- key trading or deployment actions cannot be explained
- multi-agent debate turns into high-cost low-signal chatter
- self-change creates repeated regressions without clean rollback
- governance becomes easier to bypass as the system becomes more capable

## Amendment Rules

The charter is not immutable, but charter changes must include:

- the reason for the change
- the impacted domains
- newly introduced risk
- the rollback path
- governance approval

High-frequency runtime tuning may change often. Constitutional boundaries should not.

## Priority Order

The system's priorities are:

1. survivability
2. auditability and recoverability
3. capital protection
4. governance continuity
5. learning and capability growth
6. return optimization inside the above constraints
