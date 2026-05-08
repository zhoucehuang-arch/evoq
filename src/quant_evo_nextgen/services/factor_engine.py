from __future__ import annotations

import ast
from dataclasses import dataclass
from statistics import mean, pstdev
from typing import Any, Callable, Sequence

from quant_evo_nextgen.db.models import HistoricalBarModel


@dataclass(frozen=True, slots=True)
class FactorResult:
    value: float
    formula: str
    components: dict[str, float]


@dataclass(frozen=True, slots=True)
class FactorDefinition:
    code: str
    name: str
    description: str
    evaluator: Callable[[Sequence[HistoricalBarModel]], FactorResult]


ALLOWED_CUSTOM_FACTOR_NAMES = {
    "momentum",
    "reversal",
    "volatility",
    "liquidity",
    "intraday_return",
    "overnight_gap",
    "range_position",
    "volume_trend",
    "risk_adjusted_momentum",
    "liquidity_adjusted_momentum",
}


def factor_catalog() -> dict[str, FactorDefinition]:
    return {
        "momentum_close_return": FactorDefinition(
            code="momentum_close_return",
            name="Close-to-close momentum return",
            description="Latest adjusted close divided by first adjusted close minus one.",
            evaluator=_momentum,
        ),
        "reversal_close_return": FactorDefinition(
            code="reversal_close_return",
            name="Close-to-close reversal score",
            description="Negative close-to-close momentum, useful for mean-reversion screens.",
            evaluator=_reversal,
        ),
        "realized_volatility": FactorDefinition(
            code="realized_volatility",
            name="Realized close-to-close volatility",
            description="Population standard deviation of close-to-close returns.",
            evaluator=_realized_volatility,
        ),
        "dollar_volume_liquidity": FactorDefinition(
            code="dollar_volume_liquidity",
            name="Average dollar-volume liquidity",
            description="Average close times volume over the lookback window.",
            evaluator=_dollar_volume_liquidity,
        ),
        "intraday_return": FactorDefinition(
            code="intraday_return",
            name="Latest intraday return",
            description="Latest close divided by latest open minus one.",
            evaluator=_intraday_return,
        ),
        "overnight_gap": FactorDefinition(
            code="overnight_gap",
            name="Latest overnight gap",
            description="Latest open divided by prior close minus one.",
            evaluator=_overnight_gap,
        ),
        "range_position": FactorDefinition(
            code="range_position",
            name="Close location in lookback range",
            description="Latest close normalized between lookback low and high.",
            evaluator=_range_position,
        ),
        "volume_trend": FactorDefinition(
            code="volume_trend",
            name="Volume trend",
            description="Second-half average volume divided by first-half average volume minus one.",
            evaluator=_volume_trend,
        ),
        "risk_adjusted_momentum": FactorDefinition(
            code="risk_adjusted_momentum",
            name="Risk-adjusted momentum",
            description="Momentum divided by realized volatility.",
            evaluator=_risk_adjusted_momentum,
        ),
        "liquidity_adjusted_momentum": FactorDefinition(
            code="liquidity_adjusted_momentum",
            name="Liquidity-adjusted momentum",
            description="Momentum scaled by a compact liquidity score.",
            evaluator=_liquidity_adjusted_momentum,
        ),
    }


def evaluate_factor(
    factor_code: str,
    bars: Sequence[HistoricalBarModel],
    *,
    custom_expression: str | None = None,
) -> FactorResult:
    if not bars:
        raise ValueError("factor evaluation requires at least one historical bar.")
    catalog = factor_catalog()
    if factor_code == "custom_linear_combo":
        if not custom_expression:
            raise ValueError("custom_linear_combo requires custom_expression.")
        components = _base_components(bars)
        value = _safe_eval_linear_expression(custom_expression, components)
        return FactorResult(value=value, formula=custom_expression, components=components)
    definition = catalog.get(factor_code)
    if definition is None:
        supported = ", ".join([*catalog.keys(), "custom_linear_combo"])
        raise ValueError(f"unsupported_factor_code: {supported}")
    return definition.evaluator(bars)


def factor_decay_payload(
    *,
    current_value: float,
    previous_value: float | None,
    previous_rank: int | None,
    current_rank: int | None,
) -> dict[str, Any]:
    if previous_value is None:
        return {
            "status": "no_prior_snapshot",
            "previous_value": None,
            "value_delta": None,
            "value_decay_pct": None,
            "rank_delta": None,
        }
    value_delta = current_value - previous_value
    base = max(abs(previous_value), 1e-12)
    value_decay_pct = ((previous_value - current_value) / base) * 100.0
    rank_delta = None if previous_rank is None or current_rank is None else current_rank - previous_rank
    status = "stable"
    if previous_value > 0 and current_value <= 0:
        status = "sign_flipped"
    elif value_decay_pct >= 50.0:
        status = "decayed"
    elif rank_delta is not None and rank_delta >= 10:
        status = "rank_decayed"
    return {
        "status": status,
        "previous_value": previous_value,
        "value_delta": round(value_delta, 12),
        "value_decay_pct": round(value_decay_pct, 6),
        "rank_delta": rank_delta,
    }


def _base_components(bars: Sequence[HistoricalBarModel]) -> dict[str, float]:
    return {
        "momentum": _momentum(bars).value,
        "reversal": _reversal(bars).value,
        "volatility": _realized_volatility(bars).value,
        "liquidity": _dollar_volume_liquidity(bars).value,
        "intraday_return": _intraday_return(bars).value,
        "overnight_gap": _overnight_gap(bars).value,
        "range_position": _range_position(bars).value,
        "volume_trend": _volume_trend(bars).value,
        "risk_adjusted_momentum": _risk_adjusted_momentum(bars).value,
        "liquidity_adjusted_momentum": _liquidity_adjusted_momentum(bars).value,
    }


def _safe_eval_linear_expression(expression: str, values: dict[str, float]) -> float:
    parsed = ast.parse(expression, mode="eval")

    def visit(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
            return float(node.value)
        if isinstance(node, ast.Name):
            if node.id not in ALLOWED_CUSTOM_FACTOR_NAMES:
                raise ValueError(f"unsupported_custom_factor_component: {node.id}")
            return float(values[node.id])
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -visit(node.operand)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.UAdd):
            return visit(node.operand)
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            left = visit(node.left)
            right = visit(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if right == 0:
                raise ValueError("custom_factor_divide_by_zero")
            return left / right
        raise ValueError(f"unsupported_custom_factor_expression_node: {type(node).__name__}")

    return visit(parsed)


def _momentum(bars: Sequence[HistoricalBarModel]) -> FactorResult:
    first_close = _close(bars[0])
    latest_close = _close(bars[-1])
    value = 0.0 if first_close == 0 else (latest_close / first_close) - 1.0
    return FactorResult(value=value, formula="(latest_close / first_close) - 1", components={})


def _reversal(bars: Sequence[HistoricalBarModel]) -> FactorResult:
    value = -_momentum(bars).value
    return FactorResult(value=value, formula="-((latest_close / first_close) - 1)", components={})


def _realized_volatility(bars: Sequence[HistoricalBarModel]) -> FactorResult:
    returns = _returns(bars)
    value = pstdev(returns) if len(returns) > 1 else 0.0
    return FactorResult(value=value, formula="population_stddev(close_to_close_returns)", components={})


def _dollar_volume_liquidity(bars: Sequence[HistoricalBarModel]) -> FactorResult:
    dollar_volumes = [_close(bar) * (bar.volume or 0.0) for bar in bars]
    value = mean(dollar_volumes) if dollar_volumes else 0.0
    return FactorResult(value=value, formula="average(close * volume)", components={})


def _intraday_return(bars: Sequence[HistoricalBarModel]) -> FactorResult:
    latest = bars[-1]
    value = 0.0 if latest.open == 0 else (_close(latest) / latest.open) - 1.0
    return FactorResult(value=value, formula="latest_close / latest_open - 1", components={})


def _overnight_gap(bars: Sequence[HistoricalBarModel]) -> FactorResult:
    if len(bars) < 2:
        return FactorResult(value=0.0, formula="latest_open / previous_close - 1", components={})
    previous_close = _close(bars[-2])
    value = 0.0 if previous_close == 0 else (bars[-1].open / previous_close) - 1.0
    return FactorResult(value=value, formula="latest_open / previous_close - 1", components={})


def _range_position(bars: Sequence[HistoricalBarModel]) -> FactorResult:
    low = min(bar.low for bar in bars)
    high = max(bar.high for bar in bars)
    value = 0.5 if high == low else (_close(bars[-1]) - low) / (high - low)
    return FactorResult(value=value, formula="(latest_close - lookback_low) / (lookback_high - lookback_low)", components={})


def _volume_trend(bars: Sequence[HistoricalBarModel]) -> FactorResult:
    midpoint = max(1, len(bars) // 2)
    first = [bar.volume or 0.0 for bar in bars[:midpoint]]
    second = [bar.volume or 0.0 for bar in bars[midpoint:]]
    first_mean = mean(first) if first else 0.0
    second_mean = mean(second) if second else first_mean
    value = 0.0 if first_mean == 0 else (second_mean / first_mean) - 1.0
    return FactorResult(value=value, formula="second_half_average_volume / first_half_average_volume - 1", components={})


def _risk_adjusted_momentum(bars: Sequence[HistoricalBarModel]) -> FactorResult:
    momentum = _momentum(bars).value
    volatility = _realized_volatility(bars).value
    value = momentum / max(volatility, 1e-9)
    return FactorResult(value=value, formula="momentum / max(realized_volatility, epsilon)", components={})


def _liquidity_adjusted_momentum(bars: Sequence[HistoricalBarModel]) -> FactorResult:
    momentum = _momentum(bars).value
    liquidity = _dollar_volume_liquidity(bars).value
    liquidity_score = liquidity / (liquidity + 1_000_000.0)
    value = momentum * liquidity_score
    return FactorResult(value=value, formula="momentum * dollar_volume / (dollar_volume + 1000000)", components={})


def _returns(bars: Sequence[HistoricalBarModel]) -> list[float]:
    closes = [_close(bar) for bar in bars]
    return [
        (closes[index] / closes[index - 1]) - 1.0
        for index in range(1, len(closes))
        if closes[index - 1] != 0
    ]


def _close(bar: HistoricalBarModel) -> float:
    return bar.adjusted_close if bar.is_adjusted and bar.adjusted_close is not None else bar.close
