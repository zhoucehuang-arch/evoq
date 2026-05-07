"""Adaptive Basket Variant: Mean-Reversion Pullback v1"""

STRATEGY_META = {
    "id": "adaptive_basket_mr_pullback_v1",
    "name": "Adaptive Basket MR Pullback v1",
    "version": "1.0.0",
    "archetype": "mean_reversion",
    "asset_class": "equity",
    "holding_period_minutes": [30, 1440],
    "symbols": ["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL"],
    "signal_sources": ["technical", "flow_proxy"],
    "params": {
        "rsi_period": 14,
        "rsi_entry_max": 42,
        "rsi_exit_min": 56,
        "sma_period": 20,
        "volume_spike_mult": 1.1,
        "stop_loss_pct": -0.015,
        "take_profit_pct": 0.020,
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
    need = max(params["sma_period"], params["rsi_period"] + 1)
    if len(bars) < need:
        return {"action": "HOLD", "confidence": 0.0, "reason": "insufficient"}

    closes = [b["close"] for b in bars]
    vols = [b["volume"] for b in bars]
    price = closes[-1]
    rsi = compute_rsi(closes, params["rsi_period"])
    ma = sma(closes, params["sma_period"])
    vma = sma(vols, params["sma_period"])
    if rsi is None or ma is None or vma is None:
        return {"action": "HOLD", "confidence": 0.0, "reason": "warmup"}

    vol_mult = vols[-1] / max(vma, 1)
    regime_ok = abs((closes[-1] - closes[-20]) / max(closes[-20], 1e-6)) < 0.06
    pullback = price <= ma * 0.998

    if regime_ok and pullback and rsi <= params["rsi_entry_max"] and vol_mult >= params["volume_spike_mult"]:
        confidence = min(0.86, 0.48 + 0.18 * (params["rsi_entry_max"] - rsi) / max(params["rsi_entry_max"], 1) + 0.08 * min(vol_mult, 2.0))
        return {"action": "BUY", "confidence": round(confidence, 2), "reason": f"mr_entry rsi={rsi:.1f} vol={vol_mult:.2f} pullback={price/ma:.3f}"}

    if rsi >= params["rsi_exit_min"] or price >= ma or price < ma * 0.985:
        return {"action": "SELL", "confidence": 0.68, "reason": f"mr_exit rsi={rsi:.1f} price_ma={price/ma:.3f}"}

    return {"action": "HOLD", "confidence": 0.0, "reason": "no_setup"}
