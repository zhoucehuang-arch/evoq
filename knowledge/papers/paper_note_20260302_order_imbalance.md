# Paper Note: Order Imbalance and Intraday Reversion

- artifact_id: paper_note_20260302_order_imbalance
- created_at_utc: 2026-03-02T06:39:00Z
- source_status: research note (external claims pending primary-source verification)

## Practical Takeaways

1. Intraday order imbalance can create temporary price pressure that reverts after liquidity normalizes.
2. Relative volume spikes help identify moments when imbalance signals are more informative.
3. RSI or similar stretch filters can avoid entering neutral-flow periods.

## Strategy Mapping

- Alternative-data proxies: order-imbalance indicator, relative-volume multiplier.
- Technical filter: RSI stretch threshold and ATR-based risk bounds.
- Operational guard: intraday-only to reduce overnight gap risk.

## Required Validation Before Promotion

- OOS performance package with sample size.
- Cost-adjusted expectancy under at least two slippage scenarios.
- +/-10% sensitivity and regime-slice stability checks.
- Correlation overlap check versus active stack.

## Known Risks

- Proxy quality drift when market microstructure changes.
- Signal crowding in high-attention names.
- Slippage expansion during fast tape conditions.
