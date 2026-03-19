"""
Solid Strategy v1: Alternative-Flow + Technical Confluence

Core idea:
- Use volume-spike as a tradable proxy for abnormal flow (options/dark-pool attention).
- Combine with RSI pullback and short SMA trend filter for higher-quality entries.
- Exit on momentum mean-recovery, trend break, or risk controls.

Target holding period: intraday to ~3 trading days (<= 20 days).
"""

STRATEGY_META = {
    "id": "solid_altflow_technical_v1",
    "name": "Alternative-Flow + Technical Confluence",
    "version": "1.0.0",
    "archetype": "multi_factor",
    "asset_class": "equity",
    "holding_period_minutes": [60, 4320],
    "symbols": ["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL"],
    "signal_sources": ["options_flow_proxy", "technical"],
    "params": {
        "rsi_period": 14,
        "rsi_entry_max": 35,
        "rsi_exit_min": 55,
        "sma_period": 15,
        "volume_spike_mult": 1.5,
        "stop_loss_pct": -0.02,
        "take_profit_pct": 0.03,
        "max_position_pct": 0.05,
    },
}


def compute_rsi(prices, period=14):
    if len(prices) < period + 1:
        return None

    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    gains = [value if value > 0 else 0 for value in deltas]
    losses = [-value if value < 0 else 0 for value in deltas]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for index in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[index]) / period
        avg_loss = (avg_loss * (period - 1) + losses[index]) / period

    if avg_loss == 0:
        return 100.0

    relative_strength = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + relative_strength))


def compute_sma(values, period):
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def generate_signal(bars, params=None):
    if params is None:
        params = STRATEGY_META["params"]

    lookback = max(params["sma_period"], params["rsi_period"] + 1)
    if len(bars) < lookback:
        return {"action": "HOLD", "confidence": 0.0, "reason": "Insufficient data"}

    closes = [bar["close"] for bar in bars]
    volumes = [bar["volume"] for bar in bars]

    rsi = compute_rsi(closes, params["rsi_period"])
    sma = compute_sma(closes, params["sma_period"])
    volume_avg = compute_sma(volumes, params["sma_period"])
    price = closes[-1]
    volume = volumes[-1]

    if rsi is None or sma is None or volume_avg is None:
        return {"action": "HOLD", "confidence": 0.0, "reason": "Indicator warmup"}

    abnormal_flow_proxy = volume > volume_avg * params["volume_spike_mult"]

    if abnormal_flow_proxy and rsi <= params["rsi_entry_max"] and price >= sma * 0.995:
        flow_strength = min(1.0, volume / max(volume_avg, 1))
        confidence = min(0.85, 0.55 + 0.1 * flow_strength)
        return {
            "action": "BUY",
            "confidence": round(confidence, 2),
            "reason": (
                f"Confluence entry: RSI={rsi:.1f}, vol_spike={volume/volume_avg:.2f}x, "
                f"price_vs_sma={price/sma:.3f}"
            ),
        }

    if rsi >= params["rsi_exit_min"] or price < sma * 0.99:
        return {
            "action": "SELL",
            "confidence": 0.7,
            "reason": f"Exit signal: RSI={rsi:.1f}, price_vs_sma={price/sma:.3f}",
        }

    return {"action": "HOLD", "confidence": 0.0, "reason": "No confluence"}
