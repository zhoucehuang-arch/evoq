"""Adaptive Basket Variant: Event Reaction v1"""

STRATEGY_META = {
    "id": "adaptive_basket_event_react_v1",
    "name": "Adaptive Basket Event Reaction v1",
    "version": "1.0.0",
    "archetype": "event_driven",
    "asset_class": "equity",
    "holding_period_minutes": [15, 720],
    "symbols": ["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL"],
    "signal_sources": ["event_proxy", "technical", "flow_proxy"],
    "params": {
        "rsi_period": 14,
        "rsi_entry_min": 45,
        "rsi_exit_min": 66,
        "sma_period": 12,
        "shock_threshold": 0.004,
        "volume_spike_mult": 1.0,
        "stop_loss_pct": -0.012,
        "take_profit_pct": 0.022,
        "max_position_pct": 0.035,
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
    need = max(params["sma_period"], params["rsi_period"] + 1)
    if len(bars) < need:
        return {"action": "HOLD", "confidence": 0.0, "reason": "insufficient"}

    closes = [b["close"] for b in bars]
    vols = [b["volume"] for b in bars]
    price = closes[-1]
    prev = closes[-2]
    shock = (price - prev) / max(prev, 1e-6)
    rsi = compute_rsi(closes, params["rsi_period"])
    ma = sma(closes, params["sma_period"])
    vma = sma(vols, params["sma_period"])
    if rsi is None or ma is None or vma is None:
        return {"action": "HOLD", "confidence": 0.0, "reason": "warmup"}

    vol_mult = vols[-1] / max(vma, 1)
    regime_ok = abs(shock) >= params["shock_threshold"]

    if regime_ok and shock > 0 and price >= ma and rsi >= params["rsi_entry_min"] and vol_mult >= params["volume_spike_mult"]:
        shock_strength = min(abs(shock) / params["shock_threshold"], 2.0)
        confidence = min(0.92, 0.52 + 0.16 * (shock_strength / 2.0) + 0.10 * min(vol_mult, 2.5) + 0.08 * min((rsi - 50) / 25, 1.0))
        return {"action": "BUY", "confidence": round(confidence, 2), "reason": f"event_entry shock={shock:.3f} vol={vol_mult:.2f} rsi={rsi:.1f}"}

    if shock < -0.002 or rsi >= params["rsi_exit_min"] or price < ma * 0.995:
        return {"action": "SELL", "confidence": 0.72, "reason": f"event_exit shock={shock:.3f} rsi={rsi:.1f} price_ma={price/ma:.3f}"}

    return {"action": "HOLD", "confidence": 0.0, "reason": "no_setup"}
