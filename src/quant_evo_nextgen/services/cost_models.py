from __future__ import annotations

from dataclasses import asdict, dataclass
from math import sqrt
from statistics import mean, pstdev
from typing import Any, Sequence

from quant_evo_nextgen.db.models import HistoricalBarModel


@dataclass(frozen=True, slots=True)
class TradeCostBreakdown:
    symbol: str
    notional: float
    price: float
    volume: float
    volatility: float
    fixed_bps: float
    commission_bps: float
    spread_bps: float
    participation_slippage_bps: float
    market_impact_bps: float
    total_bps: float
    total_pct: float


@dataclass(frozen=True, slots=True)
class CostModelConfig:
    fixed_bps: float = 0.0
    commission_bps: float = 0.0
    spread_bps: float = 0.0
    participation_rate_slippage_bps: float = 0.0
    square_root_impact_coefficient: float = 0.0
    trade_notional: float = 100_000.0

    @classmethod
    def from_backtest_payload(
        cls,
        *,
        cost_bps: float,
        slippage_bps: float,
        payload: dict[str, Any] | None = None,
    ) -> "CostModelConfig":
        payload = payload or {}
        return cls(
            fixed_bps=float(payload.get("fixed_bps", cost_bps)),
            commission_bps=float(payload.get("commission_bps", 0.0)),
            spread_bps=float(payload.get("spread_bps", slippage_bps)),
            participation_rate_slippage_bps=float(payload.get("participation_rate_slippage_bps", 0.0)),
            square_root_impact_coefficient=float(payload.get("square_root_impact_coefficient", 0.0)),
            trade_notional=float(payload.get("trade_notional", 100_000.0)),
        )

    def apply_trade(
        self,
        *,
        symbol: str,
        trade_size: float,
        price: float,
        volatility: float,
        volume: float,
    ) -> TradeCostBreakdown:
        dollar_volume = max(price * volume, 1.0)
        participation = max(trade_size, 0.0) / dollar_volume
        participation_slippage_bps = self.participation_rate_slippage_bps * participation
        market_impact_bps = self.square_root_impact_coefficient * volatility * sqrt(participation) * 10_000.0
        total_bps = (
            self.fixed_bps
            + self.commission_bps
            + self.spread_bps
            + participation_slippage_bps
            + market_impact_bps
        )
        return TradeCostBreakdown(
            symbol=symbol,
            notional=trade_size,
            price=price,
            volume=volume,
            volatility=volatility,
            fixed_bps=self.fixed_bps,
            commission_bps=self.commission_bps,
            spread_bps=self.spread_bps,
            participation_slippage_bps=round(participation_slippage_bps, 8),
            market_impact_bps=round(market_impact_bps, 8),
            total_bps=round(total_bps, 8),
            total_pct=round(total_bps / 100.0, 8),
        )


def estimate_symbol_trade_cost(
    *,
    symbol: str,
    bars: Sequence[HistoricalBarModel],
    config: CostModelConfig,
) -> TradeCostBreakdown:
    if not bars:
        return config.apply_trade(symbol=symbol, trade_size=config.trade_notional, price=1.0, volatility=0.0, volume=0.0)
    latest = bars[-1]
    price = _close(latest)
    volume = latest.volume or 0.0
    returns = [
        (_close(bars[index]) / _close(bars[index - 1])) - 1.0
        for index in range(1, len(bars))
        if _close(bars[index - 1]) != 0
    ]
    volatility = pstdev(returns) if len(returns) > 1 else 0.0
    return config.apply_trade(
        symbol=symbol,
        trade_size=config.trade_notional,
        price=max(price, 1e-9),
        volatility=volatility,
        volume=max(volume, 0.0),
    )


def aggregate_cost_pct(costs: Sequence[TradeCostBreakdown]) -> float:
    if not costs:
        return 0.0
    return round(mean(cost.total_pct for cost in costs), 8)


def cost_model_payload(config: CostModelConfig, costs: Sequence[TradeCostBreakdown]) -> dict[str, Any]:
    return {
        "fixed_bps": config.fixed_bps,
        "commission_bps": config.commission_bps,
        "spread_bps": config.spread_bps,
        "participation_rate_slippage_bps": config.participation_rate_slippage_bps,
        "square_root_impact_coefficient": config.square_root_impact_coefficient,
        "trade_notional": config.trade_notional,
        "total_cost_pct": aggregate_cost_pct(costs),
        "per_symbol": [asdict(cost) for cost in costs],
    }


def _close(bar: HistoricalBarModel) -> float:
    return bar.adjusted_close if bar.is_adjusted and bar.adjusted_close is not None else bar.close
