# Paper Note: PatchTST for Short-Horizon Alpha Research

- timestamp_utc: 2026-03-02T06:06:00Z
- search_provider: searxng
- query_scope: time_series_transformer_patching_financial_signal_extraction
- source_url: https://arxiv.org/abs/2211.14730
- paper_id: arXiv:2211.14730

## Why This Matters for System A
Patch-based sequence modeling can reduce attention cost while preserving local structure. For System A, this can improve near-term forecasting features used in event-driven and flow-driven entries where short windows and frequent refresh are required.

## Extracted Core Method
The paper states two core components:
1. Segment each time series into patch tokens.
2. Use channel-independence so each channel shares embedding and Transformer weights.

A practical formulation for implementation in our pipeline:
- Input per symbol/channel: x in R^L
- Patch length P, stride S
- Number of patches: N = floor((L - P) / S) + 1
- Patch token i: p_i = x[(i-1)S : (i-1)S + P]
- Token embedding: e_i = W_p p_i + b_p
- Transformer over {e_i}_{i=1..N}, with shared weights across channels

## Deployable Signal Mapping for Backtest
Construct a forecast-derived score usable by staging strategies:
- y_hat_t+h: model forecast for horizon h
- mu_t, sigma_t: rolling mean/std of forecast residuals
- Forecast z-score: z_t = (y_hat_t+h - y_t) / max(sigma_t, 1e-6)

Long-entry candidate condition (example):
- z_t > 1.0
- volume_spike_mult > 1.5
- short trend filter close_t > SMA_15

Exit:
- z_t < 0 or stop_loss/take_profit hit.

## Evidence Snippet
From arXiv abstract (source_url):
- The method uses "segmentation of time series into subseries-level patches" and "channel-independence".
- Claimed benefits include reduced attention memory/compute and better long-term forecasting accuracy compared with prior Transformer baselines.

## Integration Plan (Immediate)
1. Add PatchTST-style patch feature generator to candidate preprocessing.
2. Produce one staging candidate with forecast z-score + existing flow/technical filters.
3. Validate with current backtest contract metrics: Sharpe, MDD, WinRate, PF, trade_count.
