# Risk Governance

## Purpose

This document defines the risk-governance framework for Quant Evo Next-Gen.

Risk governance is not meant to suppress progress. It exists to keep learning, evolution, and trading from damaging capital, governance integrity, or recovery posture.

## Risk Philosophy

The system follows four base principles:

1. `Capital is hard to earn back`
   Downside protection must outrank optimistic recovery assumptions.
2. `Autonomy amplifies both edge and mistakes`
   The stronger the automation, the stronger the counterforce must be.
3. `Complex systems fail through coupling`
   The most dangerous failures are often cross-domain failures.
4. `Every powerful capability needs a counterforce`
   More autonomy must come with more auditability, gating, or rollback.

## Risk Domains

### Market risk

- directional exposure
- volatility exposure
- gap risk
- liquidity risk
- concentration risk
- correlation risk

### Strategy risk

- overfitting
- leakage
- false capacity assumptions
- regime failure
- invalidated thesis
- broken exit logic

### Execution risk

- duplicate orders
- missed orders
- latency
- broker-state drift
- recovery failure after interruption

### System risk

- workflow stalls
- inconsistent state sources
- scheduler failure
- heartbeat failure
- broken artifact chain

### Model risk

- hallucinated conclusions
- overconfident unsupported judgment
- context contamination
- group bias across multiple agents
- over-trust in weak sources

### Self-modification risk

- regressions introduced by self-generated patches
- accidental weakening of risk logic
- contamination of long-term principles
- privilege drift inside role or persona policies

### Governance risk

- approval bypass
- budget drift
- stealth autonomy escalation
- loss of decision lineage

## Risk Tiers

### `R1`

Examples:

- offline analysis
- document changes
- read-only distillation

### `R2`

Examples:

- acquisition updates
- ordinary scripts
- backtest harness changes

### `R3`

Examples:

- strategy implementation
- core workflow-state changes
- approval-path changes

### `R4`

Examples:

- order-routing logic
- hard risk thresholds
- kill switch behavior
- autonomy-level promotion

## Control Classes

1. `Preventive`
   permissions, allowlists, budgets, structural limits
2. `Detective`
   monitoring, anomaly detection, reconciliation
3. `Corrective`
   rollback, withdrawal, incident remediation
4. `Compensating`
   shadow mode, extra review, manual guardrails
5. `Adaptive`
   dynamic tightening when the environment worsens
6. `Forensic`
   lineage capture, evidence retention, replayability

## Trading Risk Controls

### Hard limits

These should not be editable by ordinary agents:

- `max_daily_drawdown`
- `max_total_drawdown`
- `max_position_size`
- `max_strategy_allocation`
- `max_sector_exposure`
- `max_symbol_exposure`
- `max_same_direction_overlap`

### Session controls

- session boot checks before execution
- market-calendar enforcement
- broker health and sync checks
- safe failure outside supported session windows

### Execution controls

- order idempotency keys
- deterministic intent-to-order transformation
- post-trade reconciliation
- withdrawal or halt on broker inconsistency

## Evolution Risk Controls

- bounded loop budgets
- fixed eval suites for meaningful changes
- promotion gates before adoption
- canary or shadow for higher-risk changes
- rollback on negative drift

## Knowledge and Source Controls

- source provenance
- confidence scoring
- stale-source decay
- multi-source corroboration for promoted principles
- evidence links for strategic claims

## Governance Controls

- durable approval records
- explicit actor and origin metadata
- budget ledgers
- override visibility
- autonomy mode as state, not prompt residue

## Incident Protocol

When critical risk is detected:

1. enter halt or safe mode
2. freeze risky workflows
3. alert through Discord and dashboard
4. open an incident record
5. preserve evidence for recovery and review

## Review Cadence

Risk governance should be reviewed at multiple speeds:

- continuous runtime monitoring
- daily doctor and smoke review
- weekly governance review
- milestone review before live-scope expansion

## Success Criteria

Risk governance is working when:

- capital boundaries remain intact
- incidents are explainable and recoverable
- autonomy increases do not erase visibility
- multi-agent collaboration raises quality more than it raises risk

## Current Honest Boundaries

The project should continue to document these limits clearly:

- CN live execution is not yet shipped
- some sleeve attribution remains conservative
- universal borrow / locate / maintenance-margin modeling is not complete
