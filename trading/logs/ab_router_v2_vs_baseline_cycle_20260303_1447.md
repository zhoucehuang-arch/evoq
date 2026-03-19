# A/B Backtest - Router v2 vs Baseline

- generated_at_utc: 2026-03-03T14:57:31.582837Z
- split: 67/33 OOS
- cost scenarios: base=4bps, 1.5x=6bps, 2x=8bps

## Base Scenario OOS
- baseline sharpe: 0.633
- router_v2 sharpe: -1.0444
- sharpe delta: -1.6774
- baseline max_dd: 0.0029
- router_v2 max_dd: 0.008
- max_dd delta: 0.0051
- return delta: -0.006
- trade delta: 24

## Router Switch Diagnostics
- switch_count: 859
- switch_rate: 0.1581
- whipsaw_count: 345
- whipsaw_rate: 0.4016

## Promotion Check
- improved_dimensions_3: 0
- meets_ge_2_of_3: False
- hard_risk_gate_fail: False
- decision: FAIL
