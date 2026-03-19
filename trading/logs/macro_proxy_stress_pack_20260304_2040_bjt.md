# Macro Proxy Stress Pack (BJT 20:40)

- generated_at_utc: 2026-03-04T12:33:30.319300Z
- scenarios: base/1.5x/2.0x cost stress
- gates: stress + VIX proxy slices + matched control + no-leak proxy audit

## Base Scenario Delta (candidate_event_window - baseline_all)
- sharpe_delta: -3.702
- max_drawdown_delta: -0.0004
- total_return_delta: -0.0009
- trades_delta: -1
- tail95_delta: -0.0076
- tail99_delta: -0.0076

## Gate Decision
- pass_count: 3/4
- decision: REJECT
- reject_reason_if_any: cost-stress/tail profile insufficient vs baseline
