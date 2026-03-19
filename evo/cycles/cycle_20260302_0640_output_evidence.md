# Cycle Output Evidence - cycle_20260302_0640

- mode: strategy_discovery
- agent: explorer
- generated_at_utc: 2026-03-02T06:10:00Z

## Method
1. Built a new candidate strategy with multi-signal confluence:
   - RSI pullback trigger
   - abnormal volume spike proxy for informed flow
   - fast/slow trend alignment
   - realized-volatility regime gating
2. Ran backtest using `scripts/run_backtest.py` with 240 simulated trading days.
3. Captured metrics for checkpoint evidence and rapid-output compliance.

## Metrics Snapshot
- strategy_id: `flow_regime_recovery_v1`
- status: `success`
- backtest_days: `240`
- final_value: `100508.71`
- total_return: `0.0051`
- sharpe_ratio: `1.38`
- max_drawdown: `0.0027`
- total_trades: `113`
- win_rate: `0.42`
- profit_factor: `1.36`
- avg_pnl_pct: `0.0009`

## Deliverable Paths
- candidate: `strategies/candidates/cycle_20260302_0640_flow_regime_recovery_v1.py`
- paper_note: `knowledge/papers/20260302_vpin_regime_filtering_notes.md`
- cycle_artifact: `evo/cycles/cycle_20260302_0640_output_evidence.md`
