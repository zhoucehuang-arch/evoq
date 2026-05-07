# Paper Note - VPIN x Regime Filtering

- cycle_id: cycle_20260302_0640
- search_provider: local_repo_filesystem
- query_scope: strategy templates + prior validation bundle constraints
- relevance_score: 0.72

## Reference
- Easley, Lopez de Prado, O'Hara (2012): Flow toxicity and VPIN-style informed-flow proxy.

## Core Formula
- Signed volume imbalance approximation:
  - `imbalance_t = abs(buy_volume_t - sell_volume_t)`
- Rolling toxicity score:
  - `toxicity_t = mean(imbalance_{t-k+1...t}) / mean(total_volume_{t-k+1...t})`

## Adaptation For Current System
- We cannot directly observe signed aggressive flow in current cold-start pipeline.
- Practical proxy used in candidate design:
  - abnormal volume spike vs moving average (`volume_t / avg_volume_t`)
  - paired with RSI pullback and trend filter
  - regime gating with realized volatility floor/cap to avoid fragile entries

## Why It Matters For A-Side
- Supplies an alternative-data-style signal even when only OHLCV is available.
- Reduces false positives in low-liquidity or panic-volatility slices.
- Supports pre-verdict gate direction: improve robustness and dependency-risk closure with measurable filters.

## Next Validation Hooks
- Add toxicity-proxy decile buckets and compare expectancy per bucket.
- Add regime-slice Sharpe report (low/normal/high vol) for each candidate.
- Add stack overlap comparison count > 0 for dependency-risk closure.
