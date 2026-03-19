# A_FAST_MUTATION_REQUEST Result - adaptive_basket_20260303_1451

- generated_at_utc: 2026-03-03T14:56:00Z
- objective: 3 lightweight adaptive signal variants for same-day paper execution

## variant_mr_pullback
- strategy_id: adaptive_basket_mr_pullback_v1
- strategy_path: strategies/staging/adaptive_basket_mr_pullback_v1.py
- entry_rules: BUY if price <= SMA20*0.998 AND RSI14 <= 42 AND volume >= SMA20(volume)*1.1
- exit_rules: SELL if RSI14 >= 56 OR price >= SMA20 OR price < SMA20*0.985; stop=-1.5%, take=+2.0%
- regime_filter: abs(20-bar return) < 6% (non-trending noise window)
- confidence_formula: conf=min(0.86, 0.48 + 0.18*(42-RSI)/42 + 0.08*min(vol_mult,2.0))
- quick_backtest_5d: Sharpe=6.38, MDD=0.0001, WinRate=1.00, PF=999, Trades=1

## variant_momo_breakout
- strategy_id: adaptive_basket_momo_breakout_v1
- strategy_path: strategies/staging/adaptive_basket_momo_breakout_v1.py
- entry_rules: BUY if close > prev20_high*1.001 AND RSI14 >= 55 AND volume >= SMA20(volume)*1.2 AND SMA10>=SMA20
- exit_rules: SELL if RSI14 >= 70 OR close < SMA10 OR SMA10 < SMA20; stop=-1.7%, take=+3.0%
- regime_filter: trend-up required (SMA10 >= SMA20)
- confidence_formula: conf=min(0.90, 0.50 + 0.12*min(vol_mult,2.5) + 0.10*min((RSI-50)/20,1) + 8*breakout_strength)
- quick_backtest_5d: Sharpe=-20.59, MDD=0.0005, WinRate=0.00, PF=0.00, Trades=2

## variant_event_react
- strategy_id: adaptive_basket_event_react_v1
- strategy_path: strategies/staging/adaptive_basket_event_react_v1.py
- entry_rules: BUY if 1-bar shock > 0.4% AND close >= SMA12 AND RSI14 >= 45 AND volume >= SMA12(volume)
- exit_rules: SELL if shock < -0.2% OR RSI14 >= 66 OR close < SMA12*0.995; stop=-1.2%, take=+2.2%
- regime_filter: abs(shock) >= 0.4% (event-proxy active)
- confidence_formula: conf=min(0.92, 0.52 + 0.16*(shock_strength/2) + 0.10*min(vol_mult,2.5) + 0.08*min((RSI-50)/25,1))
- quick_backtest_5d: Sharpe=-6.62, MDD=0.0002, WinRate=0.00, PF=0.00, Trades=1

## Note
- Evidence-first: all variants are executable and tested on quick 5d synthetic backtest; metrics indicate MR variant currently strongest while momentum/event variants need threshold relaxation before promotion.
