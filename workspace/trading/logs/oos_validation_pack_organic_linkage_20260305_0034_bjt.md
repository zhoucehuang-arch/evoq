# OOS Validation Pack — organic_linkage_upgrade_20260305_0022_bjt

- generated_at_utc: 2026-03-04T16:26:32.713830Z
- baseline: solid_altflow_technical_v1
- candidate: adaptive_basket_momo_breakout_v2
- required_pack: stress(base/1.5x/2.0x) + VIX slices + matched control + no-leak audit

## Base Stress Delta (candidate - baseline)
- sharpe_delta: -3.1435
- max_drawdown_delta: 0.0029
- total_return_delta: -0.0072
- turnover_delta: 7.4058
- tail95_delta: 0.0156
- tail99_delta: 0.014
- hit_rate_delta: -0.3841 (95% CI: -0.5689 to -0.1993)

## Gate Decision
- core_pass_count: 1/3
- stress_return_non_negative_all: False
- hit_rate_uplift_ci95_lower_gt_0: False
- hard_veto: {'data_readiness_complete': False, 'no_leak_audit_pass': True, 'capacity_compliance_ge_90pct': False}
- decision: REJECT_NO_PROMOTION
- reason: hard-veto active and/or stress+CI gates not cleared
