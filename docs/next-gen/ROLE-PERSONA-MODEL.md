# Role Persona Model

## Purpose

This document defines how agents are assembled in Quant Evo Next-Gen.

The goal is to move away from giant role prompt files toward a composable model that is governable, reusable, and easier to evaluate.

## Design Objective

The system should retain:

- multi-agent division of labor
- different personalities and reasoning styles
- cross-role challenge and refinement

But it should avoid:

- mixing role definition and personality into one giant prompt blob
- hiding tool permissions inside prompt prose
- role sprawl that only burns tokens
- pulling too many agents into a task without clear gain

## Composition Model

A running agent instance is assembled from:

```text
agent_instance =
  role
  + persona
  + policy
  + skillset
  + workflow_context
  + memory_scope
```

### `role`

Defines responsibility and success criteria.

### `persona`

Defines reasoning bias, communication style, and challenge posture.

### `policy`

Defines permissions, budgets, approvals, tool boundaries, and risk limits.

### `skillset`

Defines tool patterns, task templates, and execution helpers.

### `workflow_context`

Defines the current workflow, phase, inputs, and outputs.

### `memory_scope`

Defines what memory is visible for the task instead of exposing everything.

## Role Catalog

### Governance roles

- `planner`
- `judge`
- `governor`

### Learning roles

- `scout`
- `synthesizer`
- `archivist`

### Research roles

- `researcher`
- `skeptic`
- `forensic`

### Build roles

- `builder`
- `reviewer`
- `operator`

### Trading and safety roles

- `strategist`
- `guardian`
- `executor`

## Persona Catalog

Personas are biases, not job descriptions.

Recommended personas:

- `contrarian`
- `conservative`
- `creative`
- `forensic`
- `execution_first`
- `systems_thinker`
- `market_native`
- `cost_sensitive`

## Policy Objects

Policies should be structured rather than buried in prompt text.

Required policy fields:

- `max_rounds`
- `max_duration_sec`
- `max_token_budget`
- `tool_allowlist`
- `tool_denylist`
- `write_scope`
- `approval_mode`
- `memory_scope`
- `risk_tier`
- `allowed_workflows`

Example policy tiers:

- `P0-observer`
- `P1-analyst`
- `P2-builder`
- `P3-operator`
- `P4-guardian`

## Skillsets

Skillsets are where the system should increasingly store reusable know-how.

That keeps repeated work out of giant prompts and improves:

- quality
- token efficiency
- repeatability
- governance

## Assembly Rules

- one task should not automatically spawn every role
- role selection should match workflow phase
- personas should create useful tension, not random noise
- high-cost councils should be reserved for high-uncertainty or high-impact tasks

## Anti-Patterns

- one giant agent doing everything
- many nearly identical agents debating without differentiated policy
- unlimited memory visibility
- unlimited tool visibility
- role names that imply capability instead of responsibility
