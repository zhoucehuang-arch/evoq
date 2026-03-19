# OFF_MARKET_RESEARCH_PACKET - explorer

- generated_at_utc: 2026-03-04T00:02:00Z
- cycle_mode: off-market deepen research + strategy mutation

## new_hypotheses
1. **Regime switch basket (MR↔MOMO)**
   - If trend regime is weak/range-bound, prioritize `mr_pullback`.
   - If trend regime is positive (SMA10>SMA20 + breakout), switch to `momo_breakout`.
2. **Event-react as scaler, not primary trigger**
   - Use event shock score to scale position size (0.7x~1.2x), instead of hard entry gate.
3. **Sample-size gate for promotion**
   - Promotion to tomorrow execution requires `trade_count >= 10` on 20d fast probe and non-negative Sharpe.

## evidence
- Variant implementations:
  - `strategies/staging/adaptive_basket_mr_pullback_v1.py`
  - `strategies/staging/adaptive_basket_momo_breakout_v1.py`
  - `strategies/staging/adaptive_basket_event_react_v1.py`
- Prior quick validation summary:
  - `trading/logs/adaptive_basket_20260303_1451_variants.md`

## backtest_or_probe
20d fast probes (same script/contract):
- `mr_pullback_v1`: Sharpe 3.90, MDD 0.0004, WinRate 0.88, PF 7.51, Trades 8
- `momo_breakout_v1`: Sharpe 4.03, MDD 0.0005, WinRate 0.56, PF 1.75, Trades 16
- `event_react_v1`: Sharpe -4.05, MDD 0.0004, WinRate 0.25, PF 0.03, Trades 4

Probe artifact paths:
- `trading/logs/backtest_adaptive_basket_mr_pullback_v1_20d_20260304.json`
- `trading/logs/backtest_adaptive_basket_momo_breakout_v1_20d_20260304.json`
- `trading/logs/backtest_adaptive_basket_event_react_v1_20d_20260304.json`

## reflection
- Improvement: sample size stabilized vs 5d test; breakout signal recovered materially with more bars.
- Failure: event-react remains weak standalone; likely too noisy without context weighting.
- Delta learned: tomorrow should run dual-core (`MR + MOMO`) and demote event-react to overlay scaler.

## tomorrow_execution_candidate
- Candidate set: `adaptive_basket_mr_pullback_v1` + `adaptive_basket_momo_breakout_v1`
- Execution rule:
  - Use MR as default in neutral regime.
  - Promote MOMO when trend gate is active.
  - Keep event-react as size overlay only (not entry primary).
- Risk hard-limits unchanged: max position cap per strategy, stop-loss/take-profit enforced, no leverage increase.
