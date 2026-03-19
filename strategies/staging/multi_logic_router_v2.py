"""
Multi-Logic Router v2

Adds stricter routing with score hysteresis proxy, confidence floor,
and regime-specific entry throttles to reduce switch whipsaw.
"""

STRATEGY_META = {
    "id": "multi_logic_router_v2",
    "name": "Dynamic Multi-Logic Router v2",
    "version": "2.0.0",
    "archetype": "multi_factor",
    "asset_class": "equity",
    "holding_period_minutes": [60, 2880],
    "symbols": ["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL"],
    "signal_sources": ["technical", "flow_proxy", "regime_router"],
    "params": {
        "rsi_period": 14,
        "sma_fast": 12,
        "sma_slow": 30,
        "vol_window_short": 8,
        "vol_window_long": 32,
        "volume_spike_mult": 1.45,
        "event_jump_pct": 0.013,
        "switch_margin": 0.12,
        "confidence_floor": 0.72,
        "stop_loss_pct": -0.018,
        "take_profit_pct": 0.032,
        "max_position_pct": 0.04,
    },
}


def compute_sma(values, period):
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def compute_rsi(prices, period=14):
    if len(prices) < period + 1:
        return None

    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    gains = [delta if delta > 0 else 0 for delta in deltas]
    losses = [-delta if delta < 0 else 0 for delta in deltas]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for idx in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[idx]) / period
        avg_loss = (avg_loss * (period - 1) + losses[idx]) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def compute_volatility(returns):
    if not returns:
        return 0.0
    mean_value = sum(returns) / len(returns)
    variance = sum((value - mean_value) ** 2 for value in returns) / len(returns)
    return variance ** 0.5


def compute_router_state(closes, volumes, params):
    sma_fast = compute_sma(closes, params["sma_fast"])
    sma_slow = compute_sma(closes, params["sma_slow"])
    volume_avg = compute_sma(volumes, params["sma_fast"])

    if sma_fast is None or sma_slow is None or volume_avg is None:
        return None

    price = closes[-1]
    previous_price = closes[-2]
    ret_1 = (price / previous_price) - 1.0 if previous_price > 0 else 0.0

    returns = []
    for idx in range(1, len(closes)):
        prev = closes[idx - 1]
        if prev > 0:
            returns.append((closes[idx] / prev) - 1.0)

    short_slice = returns[-params["vol_window_short"] :]
    long_slice = returns[-params["vol_window_long"] :]
    vol_short = compute_volatility(short_slice)
    vol_long = compute_volatility(long_slice)
    vol_ratio = vol_short / max(vol_long, 1e-9)

    trend_strength = abs(sma_fast - sma_slow) / max(sma_slow, 1e-9)
    volume_spike = volumes[-1] / max(volume_avg, 1)
    rsi = compute_rsi(closes, params["rsi_period"])

    trend_score = 0.0
    if trend_strength >= 0.0035:
        trend_score += 0.40
    if vol_ratio <= 1.02:
        trend_score += 0.25
    if price >= sma_slow:
        trend_score += 0.35

    momentum_score = 0.0
    if volume_spike >= params["volume_spike_mult"]:
        momentum_score += 0.50
    if ret_1 >= 0.002:
        momentum_score += 0.25
    if price >= sma_fast:
        momentum_score += 0.25

    reversion_score = 0.0
    if vol_ratio >= 1.18:
        reversion_score += 0.35
    if rsi is not None and rsi <= 34:
        reversion_score += 0.40
    if price <= sma_fast * 0.9975:
        reversion_score += 0.25

    event_risk_score = 0.0
    if abs(ret_1) >= params["event_jump_pct"]:
        event_risk_score += 0.45
    if volume_spike >= 1.9:
        event_risk_score += 0.30
    if vol_ratio >= 1.3:
        event_risk_score += 0.25

    scores = {
        "trend": min(1.0, trend_score),
        "momentum": min(1.0, momentum_score),
        "reversion": min(1.0, reversion_score),
        "event_risk": min(1.0, event_risk_score),
    }

    ordered = sorted(["trend", "momentum", "reversion"], key=lambda key: scores[key], reverse=True)
    top_logic = ordered[0]
    second_logic = ordered[1]

    return {
        "scores": scores,
        "top_logic": top_logic,
        "second_logic": second_logic,
        "top_score": scores[top_logic],
        "second_score": scores[second_logic],
        "score_gap": scores[top_logic] - scores[second_logic],
        "rsi": rsi,
        "price": price,
        "sma_fast": sma_fast,
        "sma_slow": sma_slow,
        "volume_spike": volume_spike,
        "vol_ratio": vol_ratio,
        "ret_1": ret_1,
    }


def route_logic(state, params):
    if state is None:
        return None

    if state["scores"]["event_risk"] >= 0.8:
        return "event_risk"

    if state["top_score"] < 0.66:
        return None

    if state["score_gap"] < params["switch_margin"]:
        if state["scores"]["trend"] >= 0.62:
            return "trend"
        return None

    return state["top_logic"]


def generate_signal(bars, params=None):
    if params is None:
        params = STRATEGY_META["params"]

    lookback = max(params["sma_slow"], params["rsi_period"] + 2, params["vol_window_long"] + 2)
    if len(bars) < lookback:
        return {"action": "HOLD", "confidence": 0.0, "reason": "Insufficient data"}

    closes = [bar["close"] for bar in bars]
    volumes = [bar["volume"] for bar in bars]

    state = compute_router_state(closes, volumes, params)
    if state is None or state["rsi"] is None:
        return {"action": "HOLD", "confidence": 0.0, "reason": "Indicator warmup"}

    logic = route_logic(state, params)
    if logic == "event_risk":
        return {
            "action": "SELL",
            "confidence": 0.85,
            "reason": "Event-risk de-risk trigger",
        }

    if logic is None:
        return {"action": "HOLD", "confidence": 0.0, "reason": "No stable routed logic"}

    rsi = state["rsi"]
    price = state["price"]
    sma_fast = state["sma_fast"]
    sma_slow = state["sma_slow"]

    confidence = 0.65 + min(0.25, state["top_score"] * 0.25)

    if logic == "trend":
        valid = price >= sma_slow and rsi <= 47 and state["vol_ratio"] <= 1.08
    elif logic == "momentum":
        valid = (
            price >= sma_fast
            and rsi <= 56
            and state["volume_spike"] >= params["volume_spike_mult"]
            and state["ret_1"] >= 0.002
        )
    else:
        valid = rsi <= 33 and price <= sma_fast * 0.998

    if valid and confidence >= params["confidence_floor"]:
        return {
            "action": "BUY",
            "confidence": round(confidence, 2),
            "reason": f"Router v2 entry via {logic}",
        }

    if rsi >= 66 or price < sma_slow * 0.988:
        return {
            "action": "SELL",
            "confidence": 0.72,
            "reason": "Router v2 exit condition",
        }

    return {"action": "HOLD", "confidence": 0.0, "reason": f"No entry ({logic})"}
