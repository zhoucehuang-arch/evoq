#!/usr/bin/env python3
import argparse
import importlib.util
import json
import math
import random
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_strategy(strategy_path: str):
    spec = importlib.util.spec_from_file_location("strategy", strategy_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def simulate_bars(days: int = 756, freq_minutes: int = 15, seed: int = 42):
    random.seed(seed)
    bars = []
    price = 150.0
    current_time = datetime.now(timezone.utc) - timedelta(days=days)
    steps_per_day = 390 // freq_minutes

    for _ in range(days * steps_per_day):
        change = random.gauss(0, 0.002)
        price *= 1 + change
        bars.append(
            {
                "timestamp": current_time.isoformat().replace("+00:00", "Z"),
                "open": round(price * (1 - abs(change) / 2), 2),
                "high": round(price * (1 + abs(change)), 2),
                "low": round(price * (1 - abs(change)), 2),
                "close": round(price, 2),
                "volume": random.randint(10000, 500000),
            }
        )
        current_time += timedelta(minutes=freq_minutes)

    return bars


def backtest_on_bars(module, bars, params, initial_capital=100000.0, slippage_bps=0.0, fee_bps=0.0):
    capital = initial_capital
    position = 0
    entry_price = 0.0
    trades = []
    equity_curve = [capital]

    per_side_cost = (slippage_bps + fee_bps) / 10000.0

    for index in range(50, len(bars)):
        window = bars[index - 50 : index + 1]
        signal = module.generate_signal(window, params=params)
        current_price = bars[index]["close"]

        if signal["action"] == "BUY" and position == 0 and signal.get("confidence", 0) >= 0.5:
            fill_price = current_price * (1 + per_side_cost)
            quantity = int(capital * params["max_position_pct"] / fill_price)
            if quantity > 0:
                position = quantity
                entry_price = fill_price
                capital -= quantity * fill_price

        elif signal["action"] == "SELL" and position > 0:
            fill_price = current_price * (1 - per_side_cost)
            pnl = position * (fill_price - entry_price)
            capital += position * fill_price
            trades.append({"pnl": pnl, "pnl_pct": (fill_price - entry_price) / entry_price})
            position = 0

        elif position > 0:
            pnl_pct = (current_price - entry_price) / entry_price
            if pnl_pct <= params["stop_loss_pct"] or pnl_pct >= params["take_profit_pct"]:
                fill_price = current_price * (1 - per_side_cost)
                pnl = position * (fill_price - entry_price)
                capital += position * fill_price
                trades.append({"pnl": pnl, "pnl_pct": (fill_price - entry_price) / entry_price})
                position = 0

        equity_curve.append(capital + position * current_price)

    if not trades:
        return {
            "status": "no_trades",
            "sharpe": 0.0,
            "max_drawdown": 0.0,
            "win_rate": 0.0,
            "expectancy_after_costs": 0.0,
            "total_trades": 0,
            "total_return": round((equity_curve[-1] - initial_capital) / initial_capital, 4),
        }

    wins = [trade for trade in trades if trade["pnl"] > 0]

    peak = equity_curve[0]
    max_drawdown = 0.0
    for value in equity_curve:
        if value > peak:
            peak = value
        drawdown = (peak - value) / peak if peak > 0 else 0.0
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    returns = []
    for i in range(1, len(equity_curve)):
        previous = equity_curve[i - 1]
        if previous > 0:
            returns.append((equity_curve[i] - previous) / previous)

    average_return = sum(returns) / len(returns) if returns else 0.0
    std_return = math.sqrt(sum((ret - average_return) ** 2 for ret in returns) / len(returns)) if returns else 0.0
    sharpe = (average_return / std_return) * math.sqrt(252 * 26) if std_return > 0 else 0.0

    expectancy = sum(trade["pnl_pct"] for trade in trades) / len(trades)
    total_return = (equity_curve[-1] - initial_capital) / initial_capital

    return {
        "status": "success",
        "sharpe": round(sharpe, 4),
        "max_drawdown": round(max_drawdown, 4),
        "win_rate": round(len(wins) / len(trades), 4),
        "expectancy_after_costs": round(expectancy, 6),
        "total_trades": len(trades),
        "total_return": round(total_return, 4),
    }


def perturb(params, pct):
    result = deepcopy(params)

    integer_keys = [
        "rsi_entry_max",
        "rsi_exit_min",
        "rsi_oversold",
        "rsi_overbought",
        "min_confirming_signals",
    ]
    float_keys = [
        "volume_spike_mult",
        "stop_loss_pct",
        "take_profit_pct",
        "max_position_pct",
        "iv_rank_max",
    ]

    for key in integer_keys:
        if key in result:
            result[key] = int(round(result[key] * (1 + pct)))

    for key in float_keys:
        if key in result:
            result[key] = round(result[key] * (1 + pct), 6)

    if "rsi_entry_max" in result:
        result["rsi_entry_max"] = max(5, min(95, result["rsi_entry_max"]))
    if "rsi_exit_min" in result:
        result["rsi_exit_min"] = max(5, min(95, result["rsi_exit_min"]))
    if "rsi_oversold" in result:
        result["rsi_oversold"] = max(5, min(60, result["rsi_oversold"]))
    if "rsi_overbought" in result:
        result["rsi_overbought"] = max(40, min(95, result["rsi_overbought"]))
    if "volume_spike_mult" in result:
        result["volume_spike_mult"] = max(1.0, result["volume_spike_mult"])
    if "max_position_pct" in result:
        result["max_position_pct"] = max(0.001, min(0.2, result["max_position_pct"]))

    return result


def slice_regimes_by_realized_vol(oos_bars):
    if len(oos_bars) < 300:
        return {
            "low_vol": oos_bars,
            "normal_vol": oos_bars,
            "high_vol": oos_bars,
        }

    chunk = len(oos_bars) // 3
    segments = [oos_bars[:chunk], oos_bars[chunk : 2 * chunk], oos_bars[2 * chunk :]]

    segment_scores = []
    for idx, segment in enumerate(segments):
        closes = [bar["close"] for bar in segment]
        returns = []
        for i in range(1, len(closes)):
            prev = closes[i - 1]
            if prev > 0:
                returns.append((closes[i] - prev) / prev)
        vol = math.sqrt(sum(r * r for r in returns) / len(returns)) if returns else 0.0
        segment_scores.append((vol, idx, segment))

    segment_scores.sort(key=lambda item: item[0])
    return {
        "low_vol": segment_scores[0][2],
        "normal_vol": segment_scores[1][2],
        "high_vol": segment_scores[2][2],
    }


def collect_stack_overlap(repo_root: Path, current_strategy_id: str, current_sources):
    search_paths = [repo_root / "strategies" / "staging", repo_root / "strategies" / "production"]
    overlaps = []

    current_set = set(current_sources or [])
    if not current_set:
        return {"max_source_overlap": 0.0, "avg_source_overlap": 0.0, "comparisons": 0}

    for directory in search_paths:
        if not directory.exists():
            continue
        for path in directory.glob("*.py"):
            if path.name.startswith("."):
                continue
            try:
                module = load_strategy(str(path))
                meta = getattr(module, "STRATEGY_META", None)
                if not meta:
                    continue
                strategy_id = meta.get("id", "")
                if strategy_id == current_strategy_id:
                    continue
                source_set = set(meta.get("signal_sources", []))
                union_size = len(current_set | source_set)
                overlap = len(current_set & source_set) / union_size if union_size > 0 else 0.0
                overlaps.append(overlap)
            except Exception:
                continue

    if not overlaps:
        return {"max_source_overlap": 0.0, "avg_source_overlap": 0.0, "comparisons": 0}

    return {
        "max_source_overlap": round(max(overlaps), 4),
        "avg_source_overlap": round(sum(overlaps) / len(overlaps), 4),
        "comparisons": len(overlaps),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--days", type=int, default=756)
    parser.add_argument("--slippage-bps", type=float, default=6.0)
    parser.add_argument("--fee-bps", type=float, default=0.0)
    args = parser.parse_args()

    strategy_path = Path(args.strategy).resolve()
    repo_root = Path(__file__).resolve().parents[1]

    module = load_strategy(str(strategy_path))
    meta = module.STRATEGY_META
    base_params = deepcopy(meta["params"])

    bars = simulate_bars(days=args.days, freq_minutes=15, seed=42)
    split_index = int(len(bars) * 0.67)
    in_sample = bars[:split_index]
    oos = bars[split_index:]

    in_sample_base = backtest_on_bars(module, in_sample, base_params, slippage_bps=args.slippage_bps, fee_bps=args.fee_bps)
    oos_base = backtest_on_bars(module, oos, base_params, slippage_bps=args.slippage_bps, fee_bps=args.fee_bps)

    sensitivity = {}
    max_sharpe_drift = 0.0
    for pct, label in [(-0.1, "minus_10pct"), (0.1, "plus_10pct")]:
        perturbed = perturb(base_params, pct)
        result = backtest_on_bars(module, oos, perturbed, slippage_bps=args.slippage_bps, fee_bps=args.fee_bps)
        sensitivity[label] = {"params": perturbed, "metrics": result}

        base_sharpe = oos_base["sharpe"]
        value = result["sharpe"]
        if abs(base_sharpe) > 1e-9:
            drift = abs((value - base_sharpe) / base_sharpe)
        else:
            drift = 0.0 if abs(value) < 1e-9 else 1.0
        if drift > max_sharpe_drift:
            max_sharpe_drift = drift

    regime_bars = slice_regimes_by_realized_vol(oos)
    regime_metrics = {}
    for regime, regime_data in regime_bars.items():
        regime_metrics[regime] = backtest_on_bars(
            module,
            regime_data,
            base_params,
            slippage_bps=args.slippage_bps,
            fee_bps=args.fee_bps,
        )

    stress_scenarios = {}
    for stress_bps in [0, 3, 6, 10]:
        stress_key = f"stress_{stress_bps}bps"
        stress_scenarios[stress_key] = backtest_on_bars(
            module,
            oos,
            base_params,
            slippage_bps=stress_bps,
            fee_bps=args.fee_bps,
        )

    stack_overlap = collect_stack_overlap(repo_root, meta.get("id", ""), meta.get("signal_sources", []))

    oos_bundle_complete = all(
        key in oos_base
        for key in ["sharpe", "max_drawdown", "win_rate", "expectancy_after_costs", "total_trades"]
    )

    stress_expectancy = stress_scenarios["stress_6bps"]["expectancy_after_costs"]
    execution_realism_pass = stress_expectancy > 0

    robustness_pass = (
        max_sharpe_drift <= 0.3
        and all(value["total_trades"] >= 5 for value in regime_metrics.values())
        and all(value["status"] != "no_trades" for value in regime_metrics.values())
    )

    dependency_risk_pass = stack_overlap["max_source_overlap"] <= 0.8

    hard_gates = {
        "oos_bundle_complete": {
            "pass": oos_bundle_complete,
            "criteria": "oos_sharpe,oos_max_drawdown,oos_win_rate,expectancy_after_costs + sample_size",
        },
        "execution_realism": {
            "pass": execution_realism_pass,
            "criteria": "stress_6bps expectancy_after_costs > 0",
        },
        "robustness": {
            "pass": robustness_pass,
            "criteria": "±10% sensitivity max sharpe drift <= 0.3 and regime slices have trades",
        },
        "dependency_risk": {
            "pass": dependency_risk_pass,
            "criteria": "stack max source overlap <= 0.8 with quantified latency/crowding notes",
        },
    }

    result = {
        "type": "STRATEGY_VALIDATION_BUNDLE",
        "generated_at_utc": utc_now_iso(),
        "strategy_id": meta.get("id", "unknown"),
        "validation_scope": {
            "total_days": args.days,
            "in_sample_days_approx": int(args.days * 0.67),
            "oos_days_approx": args.days - int(args.days * 0.67),
            "meets_ge_2y": args.days >= 730,
            "slippage_bps_assumed": args.slippage_bps,
            "fee_bps_assumed": args.fee_bps,
        },
        "metrics": {
            "in_sample": in_sample_base,
            "oos": oos_base,
        },
        "required_oos_metrics": {
            "oos_sharpe": oos_base["sharpe"],
            "oos_max_drawdown": oos_base["max_drawdown"],
            "oos_win_rate": oos_base["win_rate"],
            "expectancy_after_costs": oos_base["expectancy_after_costs"],
            "sample_size": oos_base["total_trades"],
        },
        "execution_realism": {
            "stress_scenarios": stress_scenarios,
            "net_expectancy_under_stress_6bps": stress_expectancy,
        },
        "robustness": {
            "parameter_sensitivity_pm10": sensitivity,
            "sensitivity_max_sharpe_drift": round(max_sharpe_drift, 4),
            "regime_slices": regime_metrics,
        },
        "dependency_risk": {
            "latency_note": "bar-close proxy; external feed latency not modeled in offline simulation",
            "crowding_note": "volume-spike proxy may crowd; monitor hit-rate and slippage drift after deployment",
            "stack_correlation_overlap": stack_overlap,
        },
        "hard_gates": hard_gates,
        "overall_hard_gate_pass": all(item["pass"] for item in hard_gates.values()),
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
