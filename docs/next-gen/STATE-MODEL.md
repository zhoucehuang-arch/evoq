# State Model

## Purpose

This document defines the state model for Quant Evo Next-Gen.

The goal is to replace chat residue and file-scattered assumptions with explicit entities, events, and transitions.

## Canonical State Sources

### Primary truth

`Postgres` is the canonical runtime fact store.

### Secondary stores

- `Git repository`
  code, strategies, docs, versioned artifacts
- `Artifact store`
  reports, backtests, charts, raw captures, model outputs, bundles
- `Discord`
  interaction traces and notifications only, not canonical truth

### Derived state

These are useful, but not authoritative:

- Discord message history
- thread discussions
- README or deployment notes
- temporary workspace files
- live agent context windows

## State Layers

1. `Governance State`
   goals, budgets, approvals, autonomy mode, policy
2. `Workflow State`
   plans, tasks, workflow runs, retries, pauses
3. `Knowledge State`
   documents, evidence, insights, principles, playbooks
4. `Strategy State`
   hypotheses, specs, versions, backtests, paper, live posture
5. `Execution State`
   accounts, orders, positions, risk events, broker sync
6. `Evolution State`
   capability gaps, improvement goals, Codex runs, evals, promotions

## Core Entity Catalog

### Governance entities

- `system_policy`
- `autonomy_mode`
- `budget_ledger`
- `approval_request`
- `approval_decision`
- `goal`
- `goal_revision`

### Workflow entities

- `plan`
- `task`
- `workflow_definition`
- `workflow_run`
- `workflow_event`
- `heartbeat`
- `incident`

### Council entities

- `council_session`
- `council_member_assignment`
- `council_turn`
- `decision_card`
- `decision_vote`

### Knowledge entities

- `document`
- `document_chunk`
- `evidence_item`
- `insight`
- `principle`
- `causal_case`
- `playbook`
- `topic_watch`

### Strategy entities

- `hypothesis`
- `strategy_spec`
- `strategy_version`
- `backtest_run`
- `paper_run`
- `live_run`
- `promotion_decision`
- `withdrawal_decision`

### Trading entities

- `broker_account_snapshot`
- `market_snapshot`
- `signal_event`
- `order_intent`
- `order_record`
- `position_record`
- `risk_limit`
- `risk_event`

### Evolution entities

- `capability_gap`
- `improvement_goal`
- `codex_run`
- `patch_artifact`
- `eval_run`
- `deployment_candidate`
- `deployment_event`

## Required Global Fields

Every important entity should carry:

- `id`
- `created_at`
- `updated_at`
- `created_by`
- `origin_type`
- `origin_id`
- `status`
- `trace_id`

## State Transition Rules

- every meaningful transition should produce a durable event
- approval-gated transitions should reference the approval object
- risky transitions should be reversible or explicitly irreversible by design
- read models should be derived from durable state, not from chat reconstruction

## Truth Rules

- Discord can request change, but does not own truth
- Git can store artifacts, but does not own live runtime truth
- dashboards should read from APIs backed by durable state
- reconciled broker truth must be written back into runtime state

## Why This Matters

Without this model, the system drifts back into:

- prompt-heavy behavior
- split truth
- weak auditability
- poor restart recovery
- hidden coupling between human chat and machine state

The state model is what keeps the shell natural while the runtime stays governable.
