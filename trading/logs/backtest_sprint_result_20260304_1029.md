# BACKTEST_SPRINT_RESULT - A_RESEARCH_SPRINT_20260304_1029

- generated_at_utc: 2026-03-04T10:30:00Z
- objective: intraday research sprint with at least one NEW experiment result today

## tested_variants
- adaptive_basket_mr_pullback_v1
- adaptive_basket_momo_breakout_v1
- adaptive_basket_momo_breakout_v2 (NEW today)

## top3_metrics
1. adaptive_basket_momo_breakout_v1
   - Sharpe: 4.39
   - MaxDD: 0.0005
   - WinRate: 0.59
   - ProfitFactor: 2.07
   - trade_count: 17
2. adaptive_basket_momo_breakout_v2 (NEW)
   - Sharpe: 4.27
   - MaxDD: 0.0007
   - WinRate: 0.65
   - ProfitFactor: 1.95
   - trade_count: 23
3. adaptive_basket_mr_pullback_v1
   - Sharpe: 1.01
   - MaxDD: 0.0008
   - WinRate: 0.71
   - ProfitFactor: 1.94
   - trade_count: 14

## selected_candidate
- adaptive_basket_momo_breakout_v2
- selection_rationale: comparable Sharpe to v1 but materially higher throughput (`trade_count=23`) and improved win-rate (`0.65`), making it better for intraday execution stability.

## risk_constraints
- Keep hard limits unchanged (no leverage increase, preserve global DD guard).
- Per-strategy max position cap remains 4%.
- Use stop-loss/take-profit from strategy params (-1.5% / +2.8%).
- If live slippage regime worsens, downscale to 0.7x size.

## evidence
- new strategy artifact: `strategies/staging/adaptive_basket_momo_breakout_v2.py`
- backtest artifacts:
  - `trading/logs/backtest_mr_pullback_v1_30d_20260304_1029.json`
  - `trading/logs/backtest_momo_breakout_v1_30d_20260304_1029.json`
  - `trading/logs/backtest_momo_breakout_v2_30d_20260304_1029.json`
