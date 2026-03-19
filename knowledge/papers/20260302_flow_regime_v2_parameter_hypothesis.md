# Research Note - Flow Regime v2 Parameter Hypothesis

- cycle_id: cycle_20260302_1651
- generated_at_utc: 2026-03-02T16:53:00Z
- search_provider: local_repo_filesystem
- query_scope: prior cycle artifacts + candidate parameter deltas

## Actionable Hypothesis
If `volume_spike_mult` is relaxed from `1.08` to `1.03` while keeping `rsi_oversold` in `[36, 40]`, entry density should increase by 10-18% and improve sample stability without materially worsening max drawdown, provided the volatility cap remains <= `0.0075`.

## Why This Is Actionable
- Current run (`volume_spike_mult=1.05`, `rsi_oversold=38`) produced profitable but moderate trade count (`82`).
- The flow-proxy threshold is likely the main throttle on entry frequency.
- Regime gate (`volatility_floor/cap`) can absorb noise from a looser volume trigger.

## Next Test Grid
- `volume_spike_mult`: `[1.03, 1.05, 1.08]`
- `rsi_oversold`: `[36, 38, 40]`
- keep fixed:
  - `volatility_cap=0.0075`
  - `stop_loss_pct=-0.018`
  - `take_profit_pct=0.028`

## Promotion Guardrails
- Require Sharpe >= 1.0 in baseline run.
- Require max_drawdown <= 0.004 in same run.
- Require no negative expectancy under 6 bps cost stress.
