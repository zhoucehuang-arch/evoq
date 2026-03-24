# Workflow Catalog

## Purpose

This document defines the long-running workflow families that make the system operate as a product instead of a loose collection of agents.

Agents, Discord, Codex, and memory should all cooperate through workflows.

## Workflow Design Rules

Every workflow should explicitly define:

- trigger conditions
- input objects
- participating roles
- allowed tools
- budget and timeout
- output artifacts
- success criteria
- failure criteria
- approval requirements
- retry policy
- exit conditions

## Workflow Families

1. `Governance Workflows`
2. `Learning Workflows`
3. `Council Workflows`
4. `Strategy Workflows`
5. `Execution Workflows`
6. `Evolution Workflows`
7. `Memory Workflows`
8. `Incident Workflows`

## Governance Workflows

### `WF-GOV-001 Goal Admission`

- admit or reject new goals
- create durable goal and decision records

### `WF-GOV-002 Daily Governance Heartbeat`

- inspect queue depth, budget, risk state, loop health, broker connectivity, and Discord health

### `WF-GOV-003 Weekly Objective Review`

- continue, revise, or stop existing goals

### `WF-GOV-006 Runtime Config Governance`

- handle governed runtime-config proposals, approvals, and revisions

## Learning Workflows

### `WF-LRN-001 Source Ingest`

- fetch raw material
- normalize metadata
- deduplicate
- assign topic
- score source trust
- create `document`

### `WF-LRN-002 Evidence Extraction`

- convert documents into cited evidence items

### `WF-LRN-003 Topic Synthesis`

- turn multiple evidence items into actionable insight

### `WF-LRN-004 Principle Promotion`

- promote stable, repeated insight into durable principle memory

## Council Workflows

### Lightweight council

Use for medium-uncertainty questions with tight budget.

### Full council

Use for:

- major strategy shifts
- major system design changes
- high-impact market or risk decisions

## Strategy Workflows

### `WF-STR-001 Hypothesis Intake`

- create a new hypothesis candidate

### `WF-STR-002 Strategy Spec`

- translate hypothesis into a structured strategy spec

### `WF-STR-003 Backtest Evaluation`

- implement or update strategy
- run backtest
- review metrics and data quality

### `WF-STR-004 Paper Promotion`

- move a validated strategy into paper mode

### `WF-STR-005 Limited Live Promotion`

- move from paper to bounded live mode only after risk and governance gates

### `WF-STR-006 Withdrawal`

- withdraw or freeze degraded strategies

## Execution Workflows

### Session boot

- broker connectivity
- market status
- strategy readiness
- risk-switch health

### Signal to order

- convert signals into deterministic order intent

### Reconciliation

- sync broker state, orders, positions, and restart recovery

## Evolution Workflows

### Capability gap review

- identify where the system is weak

### Improvement proposal

- convert gaps into concrete improvement goals

### Codex execution

- run bounded implementation or analysis work

### Review / eval / promotion

- test whether the proposed improvement should be accepted, canaried, or rejected

## Memory Workflows

### Memory distillation

- turn high-value daily activity into durable memory

### Playbook maintenance

- turn repeated incidents or stable procedures into operator playbooks

## Incident Workflows

### `risk.halt`

- immediately halt or freeze risky execution paths

### Incident record and review

- open incident
- preserve evidence
- assign follow-up tasks
- record prevention measures

## Priority Guidance

Default priority order:

1. safety workflows
2. trading execution and recovery
3. incidents
4. governance
5. strategy evaluation
6. learning
7. evolution

## Budget Guidance

- safety workflows may exceed normal budget when needed, but must leave a trail
- execution workflows prioritize latency and determinism
- council workflows must enforce strict round and participant budgets
- learning workflows should batch and deduplicate
- evolution workflows must justify cost against expected value

## Exit States

Each workflow should end in one of:

- completed
- rejected
- halted
- rolled_back
- escalated
- expired

And each should produce at least one durable artifact or event.
