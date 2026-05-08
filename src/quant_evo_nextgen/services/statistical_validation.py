from __future__ import annotations

from dataclasses import dataclass
from math import exp, log, sqrt
from statistics import mean, pstdev
from typing import Any


@dataclass(frozen=True, slots=True)
class StatisticalValidationResult:
    passed: bool
    notes: list[str]
    metrics: dict[str, Any]


def validate_backtest_statistics(metrics: dict[str, Any], *, sample_size: int) -> StatisticalValidationResult:
    sharpe = _float(metrics.get("sharpe_ratio"))
    max_drawdown_pct = _float(metrics.get("max_drawdown_pct"), default=100.0)
    total_return_pct = _float(metrics.get("total_return_pct"))
    excess_return_pct = _float(metrics.get("excess_return_pct"))
    trial_count = max(1, int(_float(metrics.get("trial_count"), default=1.0)))
    oos_return_pct = _float(metrics.get("oos_return_pct"), default=excess_return_pct)
    walk_forward_pass_rate = _float(metrics.get("walk_forward_pass_rate"), default=1.0 if sample_size >= 100 else 0.0)
    raw_equity_curve = metrics.get("equity_curve")
    equity_curve = raw_equity_curve if isinstance(raw_equity_curve, list) else []

    observed_returns = [
        _float(point.get("return_pct")) / 100.0
        for point in equity_curve
        if isinstance(point, dict) and point.get("return_pct") is not None
    ]
    observed_sharpe = _annualized_sharpe(observed_returns) if len(observed_returns) >= 2 else sharpe
    sharpe_for_validation = observed_sharpe if len(observed_returns) >= 20 else sharpe

    deflated_sharpe = _deflated_sharpe_ratio(
        sharpe=sharpe_for_validation,
        sample_size=sample_size,
        trial_count=trial_count,
    )
    pbo_proxy = _pbo_proxy(
        trial_count=trial_count,
        sample_size=sample_size,
        oos_return_pct=oos_return_pct,
        walk_forward_pass_rate=walk_forward_pass_rate,
        max_drawdown_pct=max_drawdown_pct,
    )

    notes: list[str] = []
    if sample_size < 120:
        notes.append("Statistical gate: sample size below 120 for robust strategy promotion.")
    if deflated_sharpe < 0.45:
        notes.append("Statistical gate: deflated Sharpe confidence is below 0.45.")
    if pbo_proxy > 0.35:
        notes.append("Statistical gate: backtest overfitting proxy is above 0.35.")
    if oos_return_pct <= 0:
        notes.append("Statistical gate: out-of-sample return is not positive.")
    if walk_forward_pass_rate < 0.5:
        notes.append("Statistical gate: walk-forward pass rate is below 50%.")

    validation_metrics = {
        "observed_sharpe_ratio": round(observed_sharpe, 6),
        "deflated_sharpe_confidence": round(deflated_sharpe, 6),
        "pbo_proxy": round(pbo_proxy, 6),
        "trial_count": trial_count,
        "oos_return_pct": oos_return_pct,
        "walk_forward_pass_rate": walk_forward_pass_rate,
        "sample_size": sample_size,
        "total_return_pct": total_return_pct,
        "excess_return_pct": excess_return_pct,
    }
    return StatisticalValidationResult(passed=not notes, notes=notes, metrics=validation_metrics)


def _deflated_sharpe_ratio(*, sharpe: float, sample_size: int, trial_count: int) -> float:
    if sample_size <= 1:
        return 0.0
    trial_penalty = sqrt(max(0.0, 2.0 * log(max(trial_count, 1))))
    adjusted = sharpe - (trial_penalty / sqrt(sample_size))
    z_score = adjusted * sqrt(sample_size - 1)
    return _logistic(z_score / 3.0)


def _pbo_proxy(
    *,
    trial_count: int,
    sample_size: int,
    oos_return_pct: float,
    walk_forward_pass_rate: float,
    max_drawdown_pct: float,
) -> float:
    trial_pressure = min(0.45, log(max(trial_count, 1)) / 10.0)
    sample_pressure = 0.25 if sample_size < 120 else 0.0
    oos_pressure = 0.25 if oos_return_pct <= 0 else 0.0
    walk_forward_pressure = max(0.0, 0.5 - walk_forward_pass_rate)
    drawdown_pressure = 0.15 if max_drawdown_pct > 15.0 else 0.0
    return min(1.0, trial_pressure + sample_pressure + oos_pressure + walk_forward_pressure + drawdown_pressure)


def _annualized_sharpe(returns: list[float]) -> float:
    if len(returns) < 2:
        return 0.0
    vol = pstdev(returns)
    if vol == 0:
        return 0.0
    return (mean(returns) / vol) * sqrt(252.0)


def _logistic(value: float) -> float:
    if value >= 50:
        return 1.0
    if value <= -50:
        return 0.0
    return 1.0 / (1.0 + exp(-value))


def _float(value: Any, *, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
