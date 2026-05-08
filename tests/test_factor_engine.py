from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from quant_evo_nextgen.db.models import HistoricalBarModel
from quant_evo_nextgen.services.factor_engine import evaluate_factor, factor_catalog, factor_decay_payload


def test_factor_catalog_exposes_builtin_factors() -> None:
    catalog = factor_catalog()

    assert set(catalog) == {
        "momentum_close_return",
        "reversal_close_return",
        "realized_volatility",
        "dollar_volume_liquidity",
        "intraday_return",
        "overnight_gap",
        "range_position",
        "volume_trend",
        "risk_adjusted_momentum",
        "liquidity_adjusted_momentum",
    }


def test_evaluate_factor_uses_adjusted_close_and_components() -> None:
    bars = _bars([100.0, 104.0, 110.0], adjusted=True)

    momentum = evaluate_factor("momentum_close_return", bars)
    reversal = evaluate_factor("reversal_close_return", bars)
    combo = evaluate_factor(
        "custom_linear_combo",
        bars,
        custom_expression="momentum + 0.5 * reversal + intraday_return",
    )

    assert momentum.value == pytest.approx(0.10)
    assert reversal.value == pytest.approx(-0.10)
    assert combo.components["momentum"] == pytest.approx(0.10)
    assert combo.value == pytest.approx(0.10 + 0.5 * -0.10 + combo.components["intraday_return"])


def test_custom_factor_sandbox_rejects_unknown_names_and_calls() -> None:
    bars = _bars([100.0, 101.0, 102.0])

    with pytest.raises(ValueError, match="unsupported_custom_factor_component"):
        evaluate_factor("custom_linear_combo", bars, custom_expression="momentum + unsafe_name")

    with pytest.raises(ValueError, match="unsupported_custom_factor_expression_node"):
        evaluate_factor("custom_linear_combo", bars, custom_expression="__import__('os').system('true')")


def test_evaluate_factor_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match="at least one historical bar"):
        evaluate_factor("momentum_close_return", [])


def test_factor_decay_payload_classifies_decay_and_rank_loss() -> None:
    decayed = factor_decay_payload(
        current_value=0.02,
        previous_value=0.10,
        previous_rank=1,
        current_rank=2,
    )
    rank_decayed = factor_decay_payload(
        current_value=0.09,
        previous_value=0.10,
        previous_rank=1,
        current_rank=15,
    )

    assert decayed["status"] == "decayed"
    assert decayed["value_decay_pct"] == pytest.approx(80.0)
    assert rank_decayed["status"] == "rank_decayed"
    assert rank_decayed["rank_delta"] == 14


def _bars(closes: list[float], *, adjusted: bool = False) -> list[HistoricalBarModel]:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    bars: list[HistoricalBarModel] = []
    for index, close in enumerate(closes):
        bars.append(
            HistoricalBarModel(
                provider_key="local-replay",
                symbol="AAPL",
                market="us_equities",
                timeframe="1d",
                bar_start=start + timedelta(days=index),
                open=close - 1.0,
                high=close + 2.0,
                low=close - 2.0,
                close=close,
                adjusted_close=close if adjusted else None,
                is_adjusted=adjusted,
                volume=1_000_000 + index,
                payload={},
            )
        )
    return bars
