"""Adaptive Basket Variant: Momentum Breakout v2 (new experiment)"""

STRATEGY_META = {
    "id": "adaptive_basket_momo_breakout_v2",
    "name": "Adaptive Basket Momentum Breakout v2",
    "version": "2.0.0",
    "archetype": "momentum",
    "asset_class": "equity",
    "holding_period_minutes": [30, 1440],
    "symbols": ["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL"],
    "signal_sources": ["technical", "flow_proxy", "regime_overlay"],
    "params": {
        "rsi_period": 14,
        "rsi_entry_min": 52,
        "rsi_exit_min": 68,
        "sma_fast": 8,
        "sma_slow": 20,
        "breakout_lookback": 18,
        "volume_spike_mult": 1.1,
        "stop_loss_pct": -0.015,
        "take_profit_pct": 0.028,
        "max_position_pct": 0.04,
    },
}


def compute_rsi(prices, period=14):
    if len(prices) < period + 1:
        return None
    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def sma(values, period):
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def generate_signal(bars, params=None):
    if params is None:
        params = STRATEGY_META["params"]
    need = max(params["sma_slow"], params["breakout_lookback"] + 1, params["rsi_period"] + 1)
    if len(bars) < need:
        return {"action": "HOLD", "confidence": 0.0, "reason": "insufficient"}

    closes = [b["close"] for b in bars]
    vols = [b["volume"] for b in bars]

    price = closes[-1]
    prev_high = max(closes[-params["breakout_lookback"] - 1:-1])
    rsi = compute_rsi(closes, params["rsi_period"])
    fast = sma(closes, params["sma_fast"])
    slow = sma(closes, params["sma_slow"])
    vma = sma(vols, params["sma_slow"])
    if rsi is None or fast is None or slow is None or vma is None:
        return {"action": "HOLD", "confidence": 0.0, "reason": "warmup"}

    vol_mult = vols[-1] / max(vma, 1)
    trend_ok = fast >= slow and price >= slow
    breakout = price > prev_high * 1.0005

    if trend_ok and breakout and rsi >= params["rsi_entry_min"] and vol_mult >= params["volume_spike_mult"]:
        breakout_strength = (price / max(prev_high, 1e-6)) - 1.0
        confidence = min(
            0.92,
            0.50
            + 0.10 * min(vol_mult, 2.5)
            + 0.10 * min((rsi - 50) / 20, 1.0)
            + 10.0 * breakout_strength,
        )
        return {
            "action": "BUY",
            "confidence": round(confidence, 2),
            "reason": f"momo_v2_entry rsi={rsi:.1f} vol={vol_mult:.2f} brk={price/prev_high:.3f}",
        }

    if rsi >= params["rsi_exit_min"] or price < fast * 0.998 or fast < slow:
        return {
            "action": "SELL",
            "confidence": 0.72,
            "reason": f"momo_v2_exit rsi={rsi:.1f} fast_slow={fast/slow:.3f}",
        }

    return {"action": "HOLD", "confidence": 0.0, "reason": "no_setup"}
