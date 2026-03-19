from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4


@dataclass(slots=True)
class PositionState:
    strategy_spec_id: str
    symbol: str
    asset_type: str
    direction: str
    quantity: float
    avg_entry_price: float
    realized_pnl: float
    instrument_id: str | None = None
    instrument_key: str | None = None
    underlying_symbol: str | None = None
    contract_multiplier: float = 1.0
    leverage_ratio: float = 1.0
    market_price: float | None = None
    raw_payload: dict[str, object] | None = None


@dataclass(slots=True)
class BrokerOrderState:
    broker_order_id: str
    client_order_id: str | None
    symbol: str
    instrument_id: str | None
    instrument_key: str | None
    underlying_symbol: str | None
    asset_type: str
    position_effect: str
    side: str
    order_type: str
    time_in_force: str
    quantity: float
    filled_quantity: float
    requested_notional: float
    avg_fill_price: float | None
    limit_price: float | None
    stop_price: float | None
    status: str
    broker_updated_at: datetime
    raw_payload: dict[str, object]


@dataclass(slots=True)
class BrokerAccountState:
    provider_key: str
    account_ref: str
    environment: str
    equity: float
    cash: float
    buying_power: float
    gross_exposure: float
    net_exposure: float
    positions_count: int
    open_orders_count: int
    source_captured_at: datetime
    source_age_seconds: int
    raw_payload: dict[str, object]


@dataclass(slots=True)
class BrokerExecutionRequest:
    order_intent_id: str
    client_order_id: str
    strategy_spec_id: str
    provider_key: str
    account_ref: str
    environment: str
    symbol: str
    instrument_id: str | None
    instrument_key: str | None
    underlying_symbol: str | None
    asset_type: str
    position_effect: str
    side: str
    order_type: str
    time_in_force: str
    quantity: float
    reference_price: float
    requested_notional: float
    limit_price: float | None
    stop_price: float | None
    allow_short: bool
    contract_multiplier: float = 1.0
    leverage_ratio: float = 1.0
    legs: tuple["BrokerExecutionLeg", ...] = ()


@dataclass(slots=True)
class BrokerExecutionLeg:
    leg_index: int
    symbol: str
    instrument_id: str | None
    instrument_key: str | None
    underlying_symbol: str | None
    asset_type: str
    side: str
    position_effect: str
    quantity: float
    ratio_quantity: float
    reference_price: float
    requested_notional: float


@dataclass(slots=True)
class BrokerExecutionResult:
    broker_order_id: str
    client_order_id: str | None
    order_status: str
    filled_quantity: float
    avg_fill_price: float | None
    broker_updated_at: datetime
    raw_payload: dict[str, object]
    resulting_position: PositionState | None
    closed_position: bool = False


@dataclass(slots=True)
class BrokerSyncRequest:
    provider_key: str
    account_ref: str
    environment: str
    full_sync: bool = True


@dataclass(slots=True)
class BrokerSyncResult:
    account_state: BrokerAccountState
    orders: list[BrokerOrderState]
    positions: list[PositionState]
    notes: list[str]
    raw_payload: dict[str, object]


@dataclass(slots=True)
class BrokerCancelRequest:
    provider_key: str
    account_ref: str
    environment: str
    broker_order_id: str
    client_order_id: str | None
    reason: str


@dataclass(slots=True)
class BrokerCancelResult:
    broker_order_id: str
    client_order_id: str | None
    order_status: str
    broker_updated_at: datetime
    raw_payload: dict[str, object]


@dataclass(slots=True)
class BrokerReplaceRequest:
    provider_key: str
    account_ref: str
    environment: str
    broker_order_id: str
    client_order_id: str | None
    symbol: str
    instrument_id: str | None
    instrument_key: str | None
    underlying_symbol: str | None
    asset_type: str
    position_effect: str
    side: str
    order_type: str
    time_in_force: str
    quantity: float
    reference_price: float
    requested_notional: float
    limit_price: float | None
    stop_price: float | None
    contract_multiplier: float = 1.0
    leverage_ratio: float = 1.0


@dataclass(slots=True)
class BrokerReplaceResult:
    previous_order_status: str
    previous_broker_updated_at: datetime
    previous_raw_payload: dict[str, object]
    replacement_order: BrokerOrderState


class BrokerAdapter(Protocol):
    adapter_key: str

    def execute_order(
        self,
        request: BrokerExecutionRequest,
        current_position: PositionState | None,
    ) -> BrokerExecutionResult:
        ...

    def sync_state(self, request: BrokerSyncRequest) -> BrokerSyncResult:
        ...

    def cancel_order(
        self,
        request: BrokerCancelRequest,
        current_order: BrokerOrderState,
    ) -> BrokerCancelResult:
        ...

    def replace_order(
        self,
        request: BrokerReplaceRequest,
        current_order: BrokerOrderState,
    ) -> BrokerReplaceResult:
        ...


def broker_capability_defaults(broker_adapter: str, environment: str) -> dict[str, object]:
    if broker_adapter == "paper_sim":
        return {
            "account_mode": "paper" if environment == "paper" else "cash",
            "supports_equities": True,
            "supports_etfs": True,
            "supports_fractional": True,
            "supports_short": False,
            "supports_margin": False,
            "supports_options": False,
            "supports_multi_leg_options": False,
            "supports_option_exercise": False,
            "supports_option_assignment_events": False,
            "supports_live_trading": False,
            "supports_paper_trading": environment == "paper",
            "notes": "Bootstrap default broker capability for paper simulation.",
        }
    if broker_adapter == "alpaca":
        return {
            "account_mode": "paper" if environment == "paper" else "cash",
            "supports_equities": True,
            "supports_etfs": True,
            "supports_fractional": True,
            "supports_short": False,
            "supports_margin": False,
            "supports_options": False,
            "supports_multi_leg_options": False,
            "supports_option_exercise": False,
            "supports_option_assignment_events": False,
            "supports_live_trading": environment != "paper",
            "supports_paper_trading": environment == "paper",
            "notes": (
                "Conservative Alpaca bootstrap capability. Run broker sync to seed account-specific "
                "short, margin, and options permissions."
            ),
        }
    return {
        "account_mode": "paper" if environment == "paper" else "cash",
        "supports_equities": True,
        "supports_etfs": True,
        "supports_fractional": False,
        "supports_short": False,
        "supports_margin": False,
        "supports_options": False,
        "supports_multi_leg_options": False,
        "supports_option_exercise": False,
        "supports_option_assignment_events": False,
        "supports_live_trading": environment != "paper",
        "supports_paper_trading": environment == "paper",
        "notes": "Conservative default broker capability.",
    }


class PaperBrokerAdapter:
    adapter_key = "paper_sim"

    def execute_order(
        self,
        request: BrokerExecutionRequest,
        current_position: PositionState | None,
    ) -> BrokerExecutionResult:
        fill_price = request.limit_price or request.reference_price
        broker_order_id = f"paper-{uuid4()}"
        broker_updated_at = datetime.now(tz=UTC)
        multiplier = request.contract_multiplier if request.asset_type == "option" else 1.0
        option_order = request.asset_type == "option"
        if request.asset_type not in {"equity", "etf", "leveraged_etf", "inverse_etf", "option"}:
            raise ValueError("Paper adapter does not support this instrument type yet.")

        if request.side == "buy":
            if current_position is None:
                if option_order and request.position_effect in {"close", "reduce"}:
                    raise ValueError("Cannot buy to close because no active option position exists.")
                new_position = PositionState(
                    strategy_spec_id=request.strategy_spec_id,
                    symbol=request.symbol,
                    asset_type=request.asset_type,
                    direction="long",
                    quantity=request.quantity,
                    avg_entry_price=fill_price,
                    realized_pnl=0.0,
                    instrument_id=request.instrument_id,
                    instrument_key=request.instrument_key,
                    underlying_symbol=request.underlying_symbol,
                    contract_multiplier=request.contract_multiplier,
                    leverage_ratio=request.leverage_ratio,
                    market_price=fill_price,
                    raw_payload={"adapter": self.adapter_key},
                )
            elif current_position.direction == "short":
                if option_order and request.position_effect in {"open", "increase"}:
                    raise ValueError("Cannot buy to open while a short option position is active.")
                realized_increment = (current_position.avg_entry_price - fill_price) * min(
                    request.quantity,
                    current_position.quantity,
                ) * multiplier
                if request.quantity == current_position.quantity:
                    return BrokerExecutionResult(
                        broker_order_id=broker_order_id,
                        client_order_id=request.client_order_id,
                        order_status="filled",
                        filled_quantity=request.quantity,
                        avg_fill_price=fill_price,
                        broker_updated_at=broker_updated_at,
                        raw_payload={
                            "adapter": self.adapter_key,
                            "filled_at": broker_updated_at.isoformat(),
                            "mode": "instant_fill",
                        },
                        resulting_position=PositionState(
                            strategy_spec_id=current_position.strategy_spec_id,
                            symbol=current_position.symbol,
                            asset_type=current_position.asset_type,
                            direction=current_position.direction,
                            quantity=0.0,
                            avg_entry_price=current_position.avg_entry_price,
                            realized_pnl=current_position.realized_pnl + realized_increment,
                            instrument_id=current_position.instrument_id,
                            instrument_key=current_position.instrument_key,
                            underlying_symbol=current_position.underlying_symbol,
                            contract_multiplier=current_position.contract_multiplier,
                            leverage_ratio=current_position.leverage_ratio,
                            market_price=fill_price,
                            raw_payload={"adapter": self.adapter_key},
                        ),
                        closed_position=True,
                    )
                if request.quantity < current_position.quantity:
                    remaining_quantity = current_position.quantity - request.quantity
                    return BrokerExecutionResult(
                        broker_order_id=broker_order_id,
                        client_order_id=request.client_order_id,
                        order_status="filled",
                        filled_quantity=request.quantity,
                        avg_fill_price=fill_price,
                        broker_updated_at=broker_updated_at,
                        raw_payload={
                            "adapter": self.adapter_key,
                            "filled_at": broker_updated_at.isoformat(),
                            "mode": "instant_fill",
                        },
                        resulting_position=PositionState(
                            strategy_spec_id=current_position.strategy_spec_id,
                            symbol=current_position.symbol,
                            asset_type=current_position.asset_type,
                            direction=current_position.direction,
                            quantity=remaining_quantity,
                            avg_entry_price=current_position.avg_entry_price,
                            realized_pnl=current_position.realized_pnl + realized_increment,
                            instrument_id=current_position.instrument_id,
                            instrument_key=current_position.instrument_key,
                            underlying_symbol=current_position.underlying_symbol,
                            contract_multiplier=current_position.contract_multiplier,
                            leverage_ratio=current_position.leverage_ratio,
                            market_price=fill_price,
                            raw_payload={"adapter": self.adapter_key},
                        ),
                    )

                if option_order:
                    raise ValueError("Cannot buy through a short option position into a new long option position.")
                long_quantity = request.quantity - current_position.quantity
                new_position = PositionState(
                    strategy_spec_id=request.strategy_spec_id,
                    symbol=request.symbol,
                    asset_type=request.asset_type,
                    direction="long",
                    quantity=long_quantity,
                    avg_entry_price=fill_price,
                    realized_pnl=current_position.realized_pnl + realized_increment,
                    instrument_id=request.instrument_id,
                    instrument_key=request.instrument_key,
                    underlying_symbol=request.underlying_symbol,
                    contract_multiplier=request.contract_multiplier,
                    leverage_ratio=request.leverage_ratio,
                    market_price=fill_price,
                    raw_payload={"adapter": self.adapter_key},
                )
            else:
                if option_order and request.position_effect in {"close", "reduce"}:
                    raise ValueError("Cannot buy to close a long option position.")
                combined_quantity = current_position.quantity + request.quantity
                weighted_entry = (
                    (current_position.quantity * current_position.avg_entry_price) + (request.quantity * fill_price)
                ) / combined_quantity
                new_position = PositionState(
                    strategy_spec_id=current_position.strategy_spec_id,
                    symbol=current_position.symbol,
                    asset_type=current_position.asset_type,
                    direction="long",
                    quantity=combined_quantity,
                    avg_entry_price=weighted_entry,
                    realized_pnl=current_position.realized_pnl,
                    instrument_id=current_position.instrument_id,
                    instrument_key=current_position.instrument_key,
                    underlying_symbol=current_position.underlying_symbol,
                    contract_multiplier=current_position.contract_multiplier,
                    leverage_ratio=current_position.leverage_ratio,
                    market_price=fill_price,
                    raw_payload={"adapter": self.adapter_key},
                )
            return BrokerExecutionResult(
                broker_order_id=broker_order_id,
                client_order_id=request.client_order_id,
                order_status="filled",
                filled_quantity=request.quantity,
                avg_fill_price=fill_price,
                broker_updated_at=broker_updated_at,
                raw_payload={
                    "adapter": self.adapter_key,
                    "filled_at": broker_updated_at.isoformat(),
                    "mode": "instant_fill",
                },
                resulting_position=new_position,
            )

        if current_position is None:
            if option_order and request.position_effect in {"close", "reduce"}:
                raise ValueError("Cannot sell to close because no active option position exists.")
            if request.allow_short:
                new_position = PositionState(
                    strategy_spec_id=request.strategy_spec_id,
                    symbol=request.symbol,
                    asset_type=request.asset_type,
                    direction="short",
                    quantity=request.quantity,
                    avg_entry_price=fill_price,
                    realized_pnl=0.0,
                    instrument_id=request.instrument_id,
                    instrument_key=request.instrument_key,
                    underlying_symbol=request.underlying_symbol,
                    contract_multiplier=request.contract_multiplier,
                    leverage_ratio=request.leverage_ratio,
                    market_price=fill_price,
                    raw_payload={"adapter": self.adapter_key},
                )
                return BrokerExecutionResult(
                    broker_order_id=broker_order_id,
                    client_order_id=request.client_order_id,
                    order_status="filled",
                    filled_quantity=request.quantity,
                    avg_fill_price=fill_price,
                    broker_updated_at=broker_updated_at,
                    raw_payload={
                        "adapter": self.adapter_key,
                        "filled_at": broker_updated_at.isoformat(),
                        "mode": "instant_fill",
                    },
                    resulting_position=new_position,
                )
            raise ValueError("Cannot sell because no long position exists and shorting is disabled.")

        if current_position.direction == "short":
            if not request.allow_short:
                raise ValueError("Cannot increase a short position because shorting is disabled.")
            if option_order and request.position_effect in {"close", "reduce"}:
                raise ValueError("Cannot sell to close a short option position.")
            combined_quantity = current_position.quantity + request.quantity
            weighted_entry = (
                (current_position.quantity * current_position.avg_entry_price) + (request.quantity * fill_price)
            ) / combined_quantity
            return BrokerExecutionResult(
                broker_order_id=broker_order_id,
                client_order_id=request.client_order_id,
                order_status="filled",
                filled_quantity=request.quantity,
                avg_fill_price=fill_price,
                broker_updated_at=broker_updated_at,
                raw_payload={
                    "adapter": self.adapter_key,
                    "filled_at": broker_updated_at.isoformat(),
                    "mode": "instant_fill",
                },
                resulting_position=PositionState(
                    strategy_spec_id=current_position.strategy_spec_id,
                    symbol=current_position.symbol,
                    asset_type=current_position.asset_type,
                    direction="short",
                    quantity=combined_quantity,
                    avg_entry_price=weighted_entry,
                    realized_pnl=current_position.realized_pnl,
                    instrument_id=current_position.instrument_id,
                    instrument_key=current_position.instrument_key,
                    underlying_symbol=current_position.underlying_symbol,
                    contract_multiplier=current_position.contract_multiplier,
                    leverage_ratio=current_position.leverage_ratio,
                    market_price=fill_price,
                    raw_payload={"adapter": self.adapter_key},
                ),
            )

        if request.quantity > current_position.quantity and (option_order or not request.allow_short):
            if option_order:
                raise ValueError("Sell quantity exceeds the active long option contracts.")
            raise ValueError("Sell quantity exceeds the active long position and shorting is disabled.")

        if option_order and request.position_effect in {"open", "increase"}:
            raise ValueError("Cannot sell to open against an active long option position.")

        realized_increment = (fill_price - current_position.avg_entry_price) * min(
            request.quantity,
            current_position.quantity,
        ) * multiplier

        if request.quantity == current_position.quantity:
            return BrokerExecutionResult(
                broker_order_id=broker_order_id,
                client_order_id=request.client_order_id,
                order_status="filled",
                filled_quantity=request.quantity,
                avg_fill_price=fill_price,
                broker_updated_at=broker_updated_at,
                raw_payload={
                    "adapter": self.adapter_key,
                    "filled_at": broker_updated_at.isoformat(),
                    "mode": "instant_fill",
                },
                resulting_position=PositionState(
                    strategy_spec_id=current_position.strategy_spec_id,
                    symbol=current_position.symbol,
                    asset_type=current_position.asset_type,
                    direction=current_position.direction,
                    quantity=0.0,
                    avg_entry_price=current_position.avg_entry_price,
                    realized_pnl=current_position.realized_pnl + realized_increment,
                    instrument_id=current_position.instrument_id,
                    instrument_key=current_position.instrument_key,
                    underlying_symbol=current_position.underlying_symbol,
                    contract_multiplier=current_position.contract_multiplier,
                    leverage_ratio=current_position.leverage_ratio,
                    market_price=fill_price,
                    raw_payload={"adapter": self.adapter_key},
                ),
                closed_position=True,
            )

        if request.quantity < current_position.quantity:
            remaining_quantity = current_position.quantity - request.quantity
            return BrokerExecutionResult(
                broker_order_id=broker_order_id,
                client_order_id=request.client_order_id,
                order_status="filled",
                filled_quantity=request.quantity,
                avg_fill_price=fill_price,
                broker_updated_at=broker_updated_at,
                raw_payload={
                    "adapter": self.adapter_key,
                    "filled_at": broker_updated_at.isoformat(),
                    "mode": "instant_fill",
                },
                resulting_position=PositionState(
                    strategy_spec_id=current_position.strategy_spec_id,
                    symbol=current_position.symbol,
                    asset_type=current_position.asset_type,
                    direction=current_position.direction,
                    quantity=remaining_quantity,
                    avg_entry_price=current_position.avg_entry_price,
                    realized_pnl=current_position.realized_pnl + realized_increment,
                    instrument_id=current_position.instrument_id,
                    instrument_key=current_position.instrument_key,
                    underlying_symbol=current_position.underlying_symbol,
                    contract_multiplier=current_position.contract_multiplier,
                    leverage_ratio=current_position.leverage_ratio,
                    market_price=fill_price,
                    raw_payload={"adapter": self.adapter_key},
                ),
            )

        if request.allow_short:
            if option_order:
                raise ValueError("Cannot sell through a long option position into a new short option position.")
            short_quantity = request.quantity - current_position.quantity
            return BrokerExecutionResult(
                broker_order_id=broker_order_id,
                client_order_id=request.client_order_id,
                order_status="filled",
                filled_quantity=request.quantity,
                avg_fill_price=fill_price,
                broker_updated_at=broker_updated_at,
                raw_payload={
                    "adapter": self.adapter_key,
                    "filled_at": broker_updated_at.isoformat(),
                    "mode": "instant_fill",
                },
                resulting_position=PositionState(
                    strategy_spec_id=request.strategy_spec_id,
                    symbol=request.symbol,
                    asset_type=request.asset_type,
                    direction="short",
                    quantity=short_quantity,
                    avg_entry_price=fill_price,
                    realized_pnl=current_position.realized_pnl + realized_increment,
                    instrument_id=request.instrument_id,
                    instrument_key=request.instrument_key,
                    underlying_symbol=request.underlying_symbol,
                    contract_multiplier=request.contract_multiplier,
                    leverage_ratio=request.leverage_ratio,
                    market_price=fill_price,
                    raw_payload={"adapter": self.adapter_key},
                ),
            )

        raise ValueError("Unsupported sell path in paper adapter.")

    def sync_state(self, request: BrokerSyncRequest) -> BrokerSyncResult:
        raise ValueError(
            "Paper adapter does not support broker sync because fills are already internalized in local state."
        )

    def cancel_order(
        self,
        request: BrokerCancelRequest,
        current_order: BrokerOrderState,
    ) -> BrokerCancelResult:
        raise ValueError("Paper adapter cannot cancel orders because paper fills are immediate.")

    def replace_order(
        self,
        request: BrokerReplaceRequest,
        current_order: BrokerOrderState,
    ) -> BrokerReplaceResult:
        raise ValueError("Paper adapter cannot replace orders because paper fills are immediate.")
