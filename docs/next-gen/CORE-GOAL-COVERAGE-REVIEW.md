# Core Goal Coverage Review

## Purpose

This review checks whether the two deepest product goals are actually covered by the design:

- `auto-evolution`
- `auto-trading`

The test is not whether these goals are mentioned. The test is whether each has a governed operating loop.

## Summary Verdict

The current design gets the main direction right for both goals.

- `auto-evolution`: core loop exists, but measurement and promotion detail still matter
- `auto-trading`: main loop exists, but production safety depends on explicit execution and broker edge rules

This means the design is no longer concept-only. It is mostly a closed-loop architecture that still benefits from clear edge constraints.

## Auto-Evolution Coverage

### What is already covered

- continuous intake of external information
- evidence extraction and synthesis
- capability-gap detection
- improvement-goal creation
- Codex execution cycles
- review / eval / canary / rollback paths
- memory updates after accepted change

Related documents:

- [WORKFLOW-CATALOG.md](WORKFLOW-CATALOG.md)
- [STATE-MODEL.md](STATE-MODEL.md)
- [CODEX-WORKER-PROTOCOL.md](CODEX-WORKER-PROTOCOL.md)
- [RISK-GOVERNANCE.md](RISK-GOVERNANCE.md)

### Why this is now a real loop

```text
learning
  -> evidence
  -> capability_gap
  -> improvement_goal
  -> codex_run
  -> review / eval
  -> canary or rollback
  -> memory update
```

This is a governable loop, not just agents talking to themselves.

### Remaining clarifications worth keeping explicit

1. `Capability scorecard`
   Define capability dimensions and how score changes are measured.
2. `Evolution priority formula`
   Define which capability gaps outrank others.
3. `Self-upgrade ladder`
   Separate low-, medium-, and high-impact self-change.
4. `Benchmark eval sets`
   Keep fixed eval suites for before/after comparisons.
5. `Source trust decay`
   Define expiration and down-weighting for stale outside knowledge.
6. `Anti-stall replanning`
   If evolution produces no useful output for too long, force replanning.

## Auto-Trading Coverage

### What is already covered

- strategy path from hypothesis to production
- paper to limited-live progression
- deterministic risk engine
- signal-to-order workflow
- session boot
- reconciliation
- halt / freeze / safe mode behavior

Related documents:

- [STATE-MODEL.md](STATE-MODEL.md)
- [WORKFLOW-CATALOG.md](WORKFLOW-CATALOG.md)
- [RISK-GOVERNANCE.md](RISK-GOVERNANCE.md)

### Why this is closer to a production loop

```text
hypothesis
  -> strategy_spec
  -> backtest
  -> paper
  -> limited_live
  -> production
  -> degradation detection
  -> withdrawal / replacement
```

The boundary near capital already assumes deterministic execution backed by hard risk rules.

### Remaining clarifications worth keeping explicit

1. `Order idempotency policy`
   Define duplicate-order protection keys.
2. `Broker reconciliation cadence`
   Define intraday, close, and restart reconciliation cadence.
3. `Market calendar rules`
   Define holiday, premarket, postmarket, and halt handling.
4. `Position sizing policy`
   Define strategy-level and portfolio-level sizing formulas.
5. `Promotion thresholds`
   Define paper-to-live thresholds in measurable terms.
6. `Execution degradation logic`
   Define broker / data degradation fallbacks.
7. `Strategy correlation budget`
   Define same-direction portfolio overlap controls.

## Coverage Matrix

| Core Goal | Closed Loop Present | Governance Present | Risk Gate Present | Remaining Detail Work |
|---|---|---|---|---|
| Auto-evolution | Yes | Yes | Yes | Medium |
| Auto-trading | Yes | Yes | Yes | Medium |

## Important Judgment

The system is not failing because the direction is wrong.

The more accurate judgment is:

- direction is right
- the main loops exist
- the work that still matters is explicit policy detail, not a ground-up rewrite

## Next Clarifications With Highest Value

- keep benchmark eval suites durable
- keep promotion thresholds measurable
- keep reconciliation and market-calendar behavior explicit
- keep evolution priority and source-trust decay formalized

## Final Acceptance Questions

The system should eventually be judged by two questions:

1. Can it identify capability gaps, learn, improve, evaluate, and update durable memory without constant owner steering?
2. Can it progress strategies, execute safely, reconcile truth, and withdraw degraded paths without constant owner supervision?

Only when both answers are yes does the product fully satisfy the core mission.
