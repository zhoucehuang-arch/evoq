"""
Multi-Logic Router v1

Routes between trend, momentum, mean-reversion, and event-risk de-risking
using lightweight regime scores from OHLCV features.
"""

STRATEGY_META = {
    "id": "multi_logic_router_v1",
    "name": "Dynamic Multi-Logic Router",
    "version": "1.0.0",
    "archetype": "multi_factor",
    "asset_class": "equity",
    "holding_period_minutes": [30, 2880],
    "symbols": ["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL"],
    "signal_sources": ["technical", "flow_proxy", "regime_router"],
    "params": {
        "rsi_period": 14,
        "sma_fast": 10,
        "sma_slow": 30,
        "vol_window_short": 8,
        "vol_window_long": 32,
        "volume_spike_mult": 1.35,
        "event_jump_pct": 0.012,
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


def regime_scores(closes, volumes, params):
    sma_fast = compute_sma(closes, params["sma_fast"])
    sma_slow = compute_sma(closes, params["sma_slow"])
    volume_avg = compute_sma(volumes, params["sma_fast"])

    if sma_fast is None or sma_slow is None or volume_avg is None:
        return None

    price = closes[-1]
    previous_price = closes[-2]
    ret_1 = (price / previous_price) - 1.0 if previous_price > 0 else 0.0

    rets = []
    for i in range(1, len(closes)):
        if closes[i - 1] > 0:
            rets.append((closes[i] / closes[i - 1]) - 1.0)

    short_slice = rets[-params["vol_window_short"] :]
    long_slice = rets[-params["vol_window_long"] :]
    vol_short = compute_volatility(short_slice)
    vol_long = compute_volatility(long_slice)
    vol_ratio = vol_short / max(vol_long, 1e-9)

    trend_strength = abs(sma_fast - sma_slow) / max(sma_slow, 1e-9)
    volume_spike = volumes[-1] / max(volume_avg, 1)

    trend_score = 0.0
    if trend_strength >= 0.004:
        trend_score += 0.45
    if vol_ratio <= 0.95:
        trend_score += 0.25
    if price >= sma_slow:
        trend_score += 0.30

    momentum_score = 0.0
    if volume_spike >= params["volume_spike_mult"]:
        momentum_score += 0.45
    if ret_1 >= 0.0025:
        momentum_score += 0.30
    if price >= sma_fast:
        momentum_score += 0.25

    reversion_score = 0.0
    rsi = compute_rsi(closes, params["rsi_period"])
    if vol_ratio >= 1.20:
        reversion_score += 0.40
    if rsi is not None and rsi <= 33:
        reversion_score += 0.35
    if price <= sma_fast * 0.997:
        reversion_score += 0.25

    event_risk_score = 0.0
    if abs(ret_1) >= params["event_jump_pct"]:
        event_risk_score += 0.45
    if volume_spike >= 1.8:
        event_risk_score += 0.35
    if vol_ratio >= 1.3:
        event_risk_score += 0.20

    return {
        "trend": min(1.0, trend_score),
        "momentum": min(1.0, momentum_score),
        "reversion": min(1.0, reversion_score),
        "event_risk": min(1.0, event_risk_score),
        "rsi": rsi,
        "sma_fast": sma_fast,
        "sma_slow": sma_slow,
        "price": price,
        "volume_spike": volume_spike,
    }


def generate_signal(bars, params=None):
    if params is None:
        params = STRATEGY_META["params"]

    lookback = max(params["sma_slow"], params["rsi_period"] + 2, params["vol_window_long"] + 2)
    if len(bars) < lookback:
        return {"action": "HOLD", "confidence": 0.0, "reason": "Insufficient data"}

    closes = [bar["close"] for bar in bars]
    volumes = [bar["volume"] for bar in bars]

    state = regime_scores(closes, volumes, params)
    if state is None or state["rsi"] is None:
        return {"action": "HOLD", "confidence": 0.0, "reason": "Indicator warmup"}

    chosen_logic = max(
        ["trend", "momentum", "reversion", "event_risk"],
        key=lambda key: state[key],
    )

    rsi = state["rsi"]
    price = state["price"]
    sma_fast = state["sma_fast"]
    sma_slow = state["sma_slow"]

    if state["event_risk"] >= 0.85:
        return {
            "action": "SELL",
            "confidence": 0.85,
            "reason": "Router de-risk: high event_risk score",
        }

    if chosen_logic == "trend":
        if price >= sma_slow and rsi <= 48:
            return {
                "action": "BUY",
                "confidence": 0.74,
                "reason": "Trend logic entry",
            }

    elif chosen_logic == "momentum":
        if price >= sma_fast and rsi <= 58 and state["volume_spike"] >= params["volume_spike_mult"]:
            return {
                "action": "BUY",
                "confidence": 0.76,
                "reason": "Momentum logic entry",
            }

    elif chosen_logic == "reversion":
        if rsi <= 33 and price <= sma_fast * 0.998:
            return {
                "action": "BUY",
                "confidence": 0.71,
                "reason": "Reversion logic entry",
            }

    if rsi >= 62 or price < sma_slow * 0.992:
        return {
            "action": "SELL",
            "confidence": 0.7,
            "reason": "Router exit condition",
        }

    return {
        "action": "HOLD",
        "confidence": 0.0,
        "reason": f"No entry ({chosen_logic})",
    }
