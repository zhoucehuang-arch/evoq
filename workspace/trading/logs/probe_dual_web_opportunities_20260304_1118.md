# Dual Probe Pack - Web Opportunities (Explorer)

- timestamp_utc: 2026-03-04T11:18:00Z
- task_id: IMMEDIATE_WEB_OUTCOME_PUSH_20260304_1108
- probe_mode: 60d fast A/B probe (base-cost only)

## Opportunity 1: Macro Dispersion Proxy
- source_url: https://www.investing.com/economic-calendar/
- candidate: `adaptive_basket_momo_breakout_v1`
- baseline: `solid_altflow_technical_v1`
- baseline metrics: Sharpe 2.10, MDD 0.0006, Return 0.0008, Trades 2
- candidate metrics: Sharpe 2.14, MDD 0.0007, Return 0.0009, Trades 31
- delta (candidate - baseline): Sharpe +0.04, MDD +0.0001, Return +0.0001, Trades +29
- decision: PASS_TO_NEXT_STRESS_STAGE
- note: Needs full gates (1.5x/2x costs, VIX slices, matched controls, no-leak audit)

## Opportunity 2: Earnings Surprise + RelVol Proxy
- source_url: https://www.tradingview.com/markets/stocks-usa/earnings/
- candidate: `adaptive_basket_event_react_v1`
- baseline: `solid_altflow_technical_v1`
- baseline metrics: Sharpe 2.10, MDD 0.0006, Return 0.0008, Trades 2
- candidate metrics: Sharpe 0.51, MDD 0.0006, Return 0.0001, Trades 13
- delta (candidate - baseline): Sharpe -1.59, MDD +0.0000, Return -0.0007, Trades +11
- decision: REJECT
- reject reason: Underperforms baseline on Sharpe and return in base probe.

## Next Experiment
- Run required gates for Opportunity 1 only:
  - cost stress: base/1.5x/2.0x
  - VIX regime slices
  - matched control cohort
  - no-leak timestamp audit
