"""
Backtest runner for validating strategy candidates during micro-cycles and
higher-level review cycles. It can fetch historical data from Alpaca in the
future, but currently uses a local bar simulator for cold-start validation.
"""

import argparse
import importlib.util
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path


def load_strategy(strategy_path: str):
    """Dynamically load a strategy module from a file path."""
    spec = importlib.util.spec_from_file_location("strategy", strategy_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load strategy module from {strategy_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def simulate_bars(symbol: str, days: int = 30, freq_minutes: int = 15):
    """
    Generate simulated OHLCV bar data for cold-start testing.

    Production environments should replace this with an Alpaca data call such
    as:
    GET https://data.alpaca.markets/v2/stocks/{symbol}/bars
    """
    import random

    random.seed(42)
    bars = []
    price = 150.0
    timestamp = datetime.utcnow() - timedelta(days=days)

    for _ in range(days * (390 // freq_minutes)):  # 390 minutes per trading day
        change = random.gauss(0, 0.002)
        price *= 1 + change
        bars.append(
            {
                "timestamp": timestamp.isoformat() + "Z",
                "open": round(price * (1 - abs(change) / 2), 2),
                "high": round(price * (1 + abs(change)), 2),
                "low": round(price * (1 - abs(change)), 2),
                "close": round(price, 2),
                "volume": random.randint(10000, 500000),
            }
        )
        timestamp += timedelta(minutes=freq_minutes)

    return bars


def run_backtest(
    strategy_path: str,
    days: int = 30,
    initial_capital: float = 100000.0,
):
    """Run a single-strategy backtest and return summary metrics."""
    module = load_strategy(strategy_path)
    meta = module.STRATEGY_META
    params = meta["params"]
    symbols = meta["symbols"]
    symbol = symbols[0] if isinstance(symbols, list) else "SPY"

    bars = simulate_bars(symbol, days)
    if len(bars) < 50:
        return {"status": "error", "message": "insufficient data"}

    capital = initial_capital
    position = 0
    entry_price = 0.0
    trades = []
    equity_curve = [capital]

    for i in range(50, len(bars)):
        window = bars[i - 50 : i + 1]
        signal = module.generate_signal(window, params=params)
        current_price = bars[i]["close"]

        if signal["action"] == "BUY" and position == 0 and signal["confidence"] >= 0.5:
            qty = int(capital * params["max_position_pct"] / current_price)
            if qty > 0:
                position = qty
                entry_price = current_price
                capital -= qty * current_price

        elif signal["action"] == "SELL" and position > 0:
            pnl = position * (current_price - entry_price)
            capital += position * current_price
            trades.append(
                {
                    "entry": entry_price,
                    "exit": current_price,
                    "pnl": round(pnl, 2),
                    "pnl_pct": round((current_price - entry_price) / entry_price, 4),
                }
            )
            position = 0

        # Enforce stop-loss and take-profit exits while a position is open.
        elif position > 0:
            pnl_pct = (current_price - entry_price) / entry_price
            if pnl_pct <= params["stop_loss_pct"] or pnl_pct >= params["take_profit_pct"]:
                pnl = position * (current_price - entry_price)
                capital += position * current_price
                trades.append(
                    {
                        "entry": entry_price,
                        "exit": current_price,
                        "pnl": round(pnl, 2),
                        "pnl_pct": round(pnl_pct, 4),
                    }
                )
                position = 0

        total_value = capital + position * current_price
        equity_curve.append(total_value)

    # Compute summary metrics after the backtest completes.
    if not trades:
        return {"status": "no_trades", "message": "no trades during backtest window"}

    wins = [trade for trade in trades if trade["pnl"] > 0]
    total_return = (equity_curve[-1] - initial_capital) / initial_capital
    max_drawdown = 0.0
    peak = equity_curve[0]

    for value in equity_curve:
        peak = max(peak, value)
        drawdown = (peak - value) / peak
        max_drawdown = max(max_drawdown, drawdown)

    returns = [
        (equity_curve[i] - equity_curve[i - 1]) / equity_curve[i - 1]
        for i in range(1, len(equity_curve))
        if equity_curve[i - 1] > 0
    ]
    avg_return = sum(returns) / len(returns) if returns else 0
    std_return = (
        (sum((value - avg_return) ** 2 for value in returns) / len(returns)) ** 0.5
        if returns
        else 1
    )
    sharpe = (avg_return / std_return) * (252 * 26) ** 0.5 if std_return > 0 else 0

    return {
        "status": "success",
        "strategy_id": meta["id"],
        "backtest_days": days,
        "initial_capital": initial_capital,
        "final_value": round(equity_curve[-1], 2),
        "total_return": round(total_return, 4),
        "sharpe_ratio": round(sharpe, 2),
        "max_drawdown": round(max_drawdown, 4),
        "total_trades": len(trades),
        "win_rate": round(len(wins) / len(trades), 2) if trades else 0,
        "profit_factor": round(
            sum(trade["pnl"] for trade in wins)
            / abs(sum(trade["pnl"] for trade in trades if trade["pnl"] < 0))
            if any(trade["pnl"] < 0 for trade in trades)
            else 999,
            2,
        ),
        "avg_pnl_pct": round(sum(trade["pnl_pct"] for trade in trades) / len(trades), 4),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


def main():
    parser = argparse.ArgumentParser(description="Strategy Backtest Runner")
    parser.add_argument("strategy", help="Path to strategy .py file")
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--capital", type=float, default=100000.0)
    parser.add_argument("--output", default=None, help="Output JSON path")
    args = parser.parse_args()

    result = run_backtest(args.strategy, args.days, args.capital)
    output = json.dumps(result, indent=2, ensure_ascii=False)
    print(output)

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as output_file:
            output_file.write(output)

    return 0 if result.get("status") == "success" and result.get("sharpe_ratio", 0) > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
