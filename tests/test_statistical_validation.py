from __future__ import annotations

from quant_evo_nextgen.services.statistical_validation import validate_backtest_statistics


def test_validate_backtest_statistics_passes_strong_oos_walk_forward_case() -> None:
    result = validate_backtest_statistics(
        {
            "sharpe_ratio": 1.4,
            "total_return_pct": 18.0,
            "excess_return_pct": 9.0,
            "oos_return_pct": 4.0,
            "walk_forward_pass_rate": 0.8,
            "max_drawdown_pct": 8.0,
            "trial_count": 3,
        },
        sample_size=180,
    )

    assert result.passed is True
    assert result.notes == []
    assert result.metrics["deflated_sharpe_confidence"] >= 0.45
    assert result.metrics["pbo_proxy"] <= 0.35


def test_validate_backtest_statistics_blocks_small_overfit_negative_oos_case() -> None:
    result = validate_backtest_statistics(
        {
            "sharpe_ratio": 0.2,
            "total_return_pct": 2.0,
            "excess_return_pct": -1.0,
            "oos_return_pct": -0.5,
            "walk_forward_pass_rate": 0.25,
            "max_drawdown_pct": 22.0,
            "trial_count": 50,
        },
        sample_size=60,
    )

    assert result.passed is False
    assert any("sample size below 120" in note for note in result.notes)
    assert any("out-of-sample return is not positive" in note for note in result.notes)
    assert result.metrics["pbo_proxy"] > 0.35


def test_validate_backtest_statistics_uses_equity_curve_observed_returns() -> None:
    result = validate_backtest_statistics(
        {
            "sharpe_ratio": -1.0,
            "total_return_pct": 11.0,
            "excess_return_pct": 7.0,
            "oos_return_pct": 3.0,
            "walk_forward_pass_rate": 0.7,
            "max_drawdown_pct": 7.0,
            "trial_count": 2,
            "equity_curve": [{"return_pct": 0.05 + (index % 3) * 0.01} for index in range(30)],
        },
        sample_size=150,
    )

    assert result.metrics["observed_sharpe_ratio"] > 0
    assert result.metrics["observed_sharpe_ratio"] != -1.0
