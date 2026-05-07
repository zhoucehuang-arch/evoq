"""
Cycle candidate: Flow-Regime Recovery v1

Hypothesis:
- Abnormal volume spikes proxy informed flow.
- Oversold RSI entries work better when short trend is still constructive.
- Avoid extreme low/high volatility regimes to reduce fragile entries.
"""

import math


STRATEGY_META = {
    "id": "flow_regime_recovery_v1",
    "name": "Flow-Regime Recovery v1",
    "version": "1.0.0",
    "archetype": "multi_factor",
    "asset_class": "equity",
    "holding_period_minutes": [60, 2880],
    "symbols": ["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL"],
    "signal_sources": ["options_flow_proxy", "technical", "regime_filter"],
    "params": {
        "rsi_period": 14,
        "rsi_oversold": 40,
        "rsi_exit": 62,
        "sma_fast": 12,
        "sma_slow": 35,
        "volume_ma_period": 20,
        "volume_spike_mult": 1.08,
        "vol_lookback": 20,
        "volatility_floor": 0.0002,
        "volatility_cap": 0.0080,
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

    for idx in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[idx]) / period
        avg_loss = (avg_loss * (period - 1) + losses[idx]) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def compute_sma(values, period):
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def compute_realized_vol(closes, lookback):
    if len(closes) < lookback + 1:
        return None
    window = closes[-(lookback + 1) :]
    returns = []
    for idx in range(1, len(window)):
        prev = window[idx - 1]
        if prev <= 0:
            continue
        returns.append((window[idx] - prev) / prev)
    if not returns:
        return None
    mean = sum(returns) / len(returns)
    var = sum((value - mean) ** 2 for value in returns) / len(returns)
    return math.sqrt(var)


def generate_signal(bars, params=None):
    if params is None:
        params = STRATEGY_META["params"]

    min_required = max(
        params["rsi_period"] + 1,
        params["sma_slow"],
        params["volume_ma_period"] + 1,
        params["vol_lookback"] + 1,
    )
    if len(bars) < min_required:
        return {"action": "HOLD", "confidence": 0.0, "reason": "insufficient_data"}

    closes = [bar["close"] for bar in bars]
    volumes = [bar["volume"] for bar in bars]

    current_price = closes[-1]
    rsi = compute_rsi(closes, params["rsi_period"])
    sma_fast = compute_sma(closes, params["sma_fast"])
    sma_slow = compute_sma(closes, params["sma_slow"])
    rv = compute_realized_vol(closes, params["vol_lookback"])

    if rsi is None or sma_fast is None or sma_slow is None or rv is None:
        return {"action": "HOLD", "confidence": 0.0, "reason": "indicator_na"}

    avg_volume = sum(volumes[-(params["volume_ma_period"] + 1) : -1]) / params["volume_ma_period"]
    vol_spike = volumes[-1] >= avg_volume * params["volume_spike_mult"]

    trend_ok = current_price >= sma_slow * 0.99 and sma_fast >= sma_slow * 0.995
    regime_ok = params["volatility_floor"] <= rv <= params["volatility_cap"]

    if rsi <= params["rsi_oversold"] and vol_spike and trend_ok and regime_ok:
        oversold_strength = max(0.0, (params["rsi_oversold"] - rsi) / max(params["rsi_oversold"], 1))
        confidence = 0.56 + min(0.34, oversold_strength)
        return {
            "action": "BUY",
            "confidence": round(confidence, 2),
            "reason": "oversold_flow_regime_entry",
        }

    if rsi >= params["rsi_exit"]:
        return {"action": "SELL", "confidence": 0.79, "reason": "rsi_recovered"}

    if current_price < sma_fast * 0.995:
        return {"action": "SELL", "confidence": 0.71, "reason": "fast_trend_break"}

    if not regime_ok:
        return {"action": "SELL", "confidence": 0.66, "reason": "regime_exit"}

    return {"action": "HOLD", "confidence": 0.0, "reason": "no_signal"}
