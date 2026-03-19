# Research Note: Rapid Parameter Hypothesis for Flow-Regime Recovery v2

- note_id: 20260302_accel_param_hypothesis_v1
- created_at_utc: 2026-03-02T16:55:00Z
- objective: provide actionable parameter hypothesis for immediate A-side acceleration

## Actionable Hypothesis

To reduce false positives in adverse volatility slices, increase entry selectivity:

1. Lower `rsi_oversold` from 40 to 36 to avoid shallow pullback entries.
2. Raise `volume_spike_mult` from 1.08 to 1.15 to demand stronger flow confirmation.
3. Lower `volatility_cap` from 0.008 to 0.006 to avoid panic-volatility entries.
4. Lower `max_position_pct` from 0.05 to 0.04 to reduce tail impact while retesting robustness.

## Why This Is Actionable

- All changes are simple threshold edits in the existing candidate implementation.
- The baseline snapshot already shows acceptable Sharpe with low drawdown, so this iteration targets robustness, not raw frequency.
- These thresholds can be validated in one rerun and compared directly against current evidence.

## Required Validation Output

- Updated OOS Sharpe / MaxDD / WinRate / expectancy_after_costs
- +/-10% sensitivity drift
- low/normal/high volatility regime Sharpe table

## Evidence Link

- baseline evidence: `evo/cycles/cycle_20260302_0640_output_evidence.md:16`
