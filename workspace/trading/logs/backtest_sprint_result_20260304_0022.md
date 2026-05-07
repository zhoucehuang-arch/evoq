# BACKTEST_SPRINT_RESULT - daytime_backtest_sprint_v1

- timestamp_utc: 2026-03-04T00:26:00Z
- goal: day-session backtest/validation throughput for annualized-100 sprint
- window: intraday 30d + stress slices

## tested_variants
- adaptive_basket_mr_pullback_v1
- adaptive_basket_momo_breakout_v1
- adaptive_basket_event_react_v1

## top3_metrics
1. adaptive_basket_momo_breakout_v1
   - 30d: Sharpe 4.39, MaxDD 0.0005, WinRate 0.59, PF 2.07, Trades 17
   - stress(0/3/6/10bps) expectancy: 0.006014 / 0.005410 / 0.004807 / 0.004004
2. adaptive_basket_mr_pullback_v1
   - 30d: Sharpe 1.01, MaxDD 0.0008, WinRate 0.71, PF 1.94, Trades 14
   - stress(0/3/6/10bps) expectancy: -0.001460 / -0.002514 / -0.002644 / -0.003441
3. adaptive_basket_event_react_v1
   - 30d: Sharpe -4.69, MaxDD 0.0006, WinRate 0.17, PF 0.02, Trades 6
   - stress(0/3/6/10bps) expectancy: -0.002845 / -0.003443 / -0.004041 / -0.004837

## selected_candidate
- adaptive_basket_momo_breakout_v1
- rationale: best throughput-adjusted profile (highest Sharpe among tested + highest trade_count + positive stress-slice expectancy under 6/10bps)

## risk_constraints
- Keep hard limits: no leverage increase, preserve global drawdown guard.
- Position cap remains strategy-level max_position_pct in code.
- Gate for next promotion: require repeated 30d/20d re-run consistency and trade_count >= 15.
- Keep event_react in non-primary mode until stress expectancy turns positive.

## evidence
- 30d backtests:
  - trading/logs/backtest_mr_pullback_v1_30d_20260304.json
  - trading/logs/backtest_momo_breakout_v1_30d_20260304.json
  - trading/logs/backtest_event_react_v1_30d_20260304.json
- stress slices:
  - trading/logs/validation_mr_pullback_v1_30d_20260304.json
  - trading/logs/validation_momo_breakout_v1_30d_20260304.json
  - trading/logs/validation_event_react_v1_30d_20260304.json
