from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from quant_evo_nextgen.config import Settings
from quant_evo_nextgen.db.models import PositionRecordModel
from quant_evo_nextgen.db.session import Database
from quant_evo_nextgen.services.broker import (
    BrokerAccountState,
    BrokerCancelRequest,
    BrokerCancelResult,
    BrokerExecutionRequest,
    BrokerExecutionResult,
    BrokerOrderState,
    BrokerReplaceRequest,
    BrokerReplaceResult,
    BrokerSyncRequest,
    BrokerSyncResult,
    PositionState,
)
from quant_evo_nextgen.services.execution import ExecutionService
from quant_evo_nextgen.services.state_store import StateStore
from quant_evo_nextgen.services.strategy_lab import StrategyLabService


class ScriptedAsyncBrokerAdapter:
    adapter_key = "scripted_async"

    def __init__(self) -> None:
        self.base_equity = 10000.0
        self.base_cash = 10000.0
        self.orders: dict[str, BrokerOrderState] = {}
        self.positions: dict[str, PositionState] = {}

    def execute_order(
        self,
        request: BrokerExecutionRequest,
        current_position: PositionState | None,
    ) -> BrokerExecutionResult:
        broker_order_id = f"scripted-{uuid4()}"
        current_time = datetime.now(tz=UTC)
        self.orders[broker_order_id] = BrokerOrderState(
            broker_order_id=broker_order_id,
            client_order_id=request.client_order_id,
            symbol=request.symbol,
            instrument_id=request.instrument_id,
            instrument_key=request.instrument_key,
            underlying_symbol=request.underlying_symbol,
            asset_type=request.asset_type,
            position_effect=request.position_effect,
            side=request.side,
            order_type=request.order_type,
            time_in_force=request.time_in_force,
            quantity=request.quantity,
            filled_quantity=0.0,
            requested_notional=request.requested_notional,
            avg_fill_price=None,
            limit_price=request.limit_price,
            stop_price=request.stop_price,
            status="submitted",
            broker_updated_at=current_time,
            raw_payload={"adapter": self.adapter_key, "mode": "async_submit"},
        )
        return BrokerExecutionResult(
            broker_order_id=broker_order_id,
            client_order_id=request.client_order_id,
            order_status="submitted",
            filled_quantity=0.0,
            avg_fill_price=None,
            broker_updated_at=current_time,
            raw_payload={"adapter": self.adapter_key, "mode": "async_submit"},
            resulting_position=None,
        )

    def sync_state(self, request: BrokerSyncRequest) -> BrokerSyncResult:
        return BrokerSyncResult(
            account_state=self._account_state(request),
            orders=list(self.orders.values()),
            positions=[position for position in self.positions.values() if position.quantity > 0],
            notes=[],
            raw_payload={"adapter": self.adapter_key, "full_sync": request.full_sync},
        )

    def cancel_order(
        self,
        request: BrokerCancelRequest,
        current_order: BrokerOrderState,
    ) -> BrokerCancelResult:
        current_time = datetime.now(tz=UTC)
        state = self.orders[current_order.broker_order_id]
        state.status = "canceled"
        state.broker_updated_at = current_time
        state.raw_payload = {"adapter": self.adapter_key, "action": "cancel", "reason": request.reason}
        return BrokerCancelResult(
            broker_order_id=state.broker_order_id,
            client_order_id=state.client_order_id,
            order_status=state.status,
            broker_updated_at=state.broker_updated_at,
            raw_payload=state.raw_payload,
        )

    def replace_order(
        self,
        request: BrokerReplaceRequest,
        current_order: BrokerOrderState,
    ) -> BrokerReplaceResult:
        current_time = datetime.now(tz=UTC)
        state = self.orders[current_order.broker_order_id]
        state.status = "replaced"
        state.broker_updated_at = current_time
        state.raw_payload = {"adapter": self.adapter_key, "action": "replace"}

        replacement_order = BrokerOrderState(
            broker_order_id=f"scripted-{uuid4()}",
            client_order_id=request.client_order_id,
            symbol=request.symbol,
            instrument_id=request.instrument_id,
            instrument_key=request.instrument_key,
            underlying_symbol=request.underlying_symbol,
            asset_type=request.asset_type,
            position_effect=request.position_effect,
            side=request.side,
            order_type=request.order_type,
            time_in_force=request.time_in_force,
            quantity=request.quantity,
            filled_quantity=0.0,
            requested_notional=request.requested_notional,
            avg_fill_price=None,
            limit_price=request.limit_price,
            stop_price=request.stop_price,
            status="submitted",
            broker_updated_at=current_time,
            raw_payload={"adapter": self.adapter_key, "action": "replace_submit"},
        )
        self.orders[replacement_order.broker_order_id] = replacement_order
        return BrokerReplaceResult(
            previous_order_status=state.status,
            previous_broker_updated_at=state.broker_updated_at,
            previous_raw_payload=state.raw_payload,
            replacement_order=replacement_order,
        )

    def fill_order(self, broker_order_id: str, fill_price: float) -> None:
        current_time = datetime.now(tz=UTC)
        state = self.orders[broker_order_id]
        state.status = "filled"
        state.filled_quantity = state.quantity
        state.avg_fill_price = fill_price
        state.broker_updated_at = current_time
        state.raw_payload = {"adapter": self.adapter_key, "action": "fill"}

        if state.side == "buy":
            self.positions[state.symbol] = PositionState(
                strategy_spec_id="external-sync",
                symbol=state.symbol,
                asset_type=state.asset_type,
                direction="long",
                quantity=state.quantity,
                avg_entry_price=fill_price,
                realized_pnl=0.0,
                instrument_id=state.instrument_id,
                instrument_key=state.instrument_key,
                underlying_symbol=state.underlying_symbol,
                market_price=fill_price,
                raw_payload={"adapter": self.adapter_key},
            )

    def _account_state(self, request: BrokerSyncRequest) -> BrokerAccountState:
        active_positions = [position for position in self.positions.values() if position.quantity > 0]
        gross_exposure = sum((position.market_price or position.avg_entry_price) * position.quantity for position in active_positions)
        cash = max(0.0, self.base_cash - gross_exposure)
        return BrokerAccountState(
            provider_key=request.provider_key,
            account_ref=request.account_ref,
            environment=request.environment,
            equity=self.base_equity,
            cash=cash,
            buying_power=max(0.0, self.base_equity - gross_exposure),
            gross_exposure=gross_exposure,
            net_exposure=gross_exposure,
            positions_count=len(active_positions),
            open_orders_count=sum(1 for order in self.orders.values() if order.status in {"accepted", "submitted", "partially_filled"}),
            source_captured_at=datetime.now(tz=UTC),
            source_age_seconds=0,
            raw_payload={"adapter": self.adapter_key},
        )


def test_execution_service_reports_ready_when_session_snapshot_and_reconciliation_are_green(tmp_path: Path) -> None:
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'execution-ready.db'}")
    database.create_schema()

    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'execution-ready.db'}",
        db_bootstrap_on_start=True,
        market_calendar="XNYS",
        market_timezone="America/New_York",
    )
    state_store = StateStore(database.session_factory)
    state_store.bootstrap_reference_data(settings)
    _promote_production_strategy(database)

    service = ExecutionService(database.session_factory, settings)
    service.synthesize_market_session_state(now=datetime(2026, 3, 18, 14, 0, tzinfo=UTC))
    snapshot = service.record_broker_account_snapshot(
        {
            "provider_key": "alpaca-paper",
            "account_ref": "paper-main",
            "environment": "paper",
            "equity": 10250.0,
            "cash": 6200.0,
            "buying_power": 18000.0,
            "gross_exposure": 4100.0,
            "net_exposure": 2900.0,
            "positions_count": 3,
            "open_orders_count": 1,
            "created_by": "tester",
        }
    )
    reconciliation = service.record_reconciliation_run(
        {
            "provider_key": "alpaca-paper",
            "account_ref": "paper-main",
            "account_snapshot_id": snapshot.id,
            "environment": "paper",
            "internal_equity": 10249.0,
            "internal_positions_count": 3,
            "internal_open_orders_count": 1,
            "equity_warning_pct": 0.5,
            "equity_block_pct": 2.0,
            "created_by": "tester",
        }
    )
    readiness = service.get_execution_readiness()

    assert reconciliation.status == "matched"
    assert readiness.status == "ready"
    assert readiness.trading_allowed is True
    assert readiness.market_open is True
    assert readiness.reconciliation_status == "matched"
    assert readiness.active_trading_overrides == 0


def test_execution_service_blocks_and_halts_trading_on_reconciliation_divergence(tmp_path: Path) -> None:
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'execution-halt.db'}")
    database.create_schema()

    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'execution-halt.db'}",
        db_bootstrap_on_start=True,
        market_calendar="XNYS",
        market_timezone="America/New_York",
    )
    state_store = StateStore(database.session_factory)
    state_store.bootstrap_reference_data(settings)
    _promote_production_strategy(database)

    service = ExecutionService(database.session_factory, settings)
    service.synthesize_market_session_state(now=datetime(2026, 3, 18, 14, 0, tzinfo=UTC))
    snapshot = service.record_broker_account_snapshot(
        {
            "provider_key": "alpaca-paper",
            "account_ref": "paper-main",
            "environment": "paper",
            "equity": 10000.0,
            "cash": 7000.0,
            "buying_power": 15000.0,
            "gross_exposure": 2500.0,
            "net_exposure": 2200.0,
            "positions_count": 2,
            "open_orders_count": 0,
            "created_by": "tester",
        }
    )
    reconciliation = service.record_reconciliation_run(
        {
            "provider_key": "alpaca-paper",
            "account_ref": "paper-main",
            "account_snapshot_id": snapshot.id,
            "environment": "paper",
            "internal_equity": 9700.0,
            "internal_positions_count": 1,
            "internal_open_orders_count": 0,
            "equity_warning_pct": 0.5,
            "equity_block_pct": 2.0,
            "created_by": "tester",
        }
    )
    readiness = service.get_execution_readiness()
    incidents = state_store.list_incidents(open_only=True, limit=10)
    overrides = state_store.list_operator_overrides(active_only=True)

    assert reconciliation.status == "blocked"
    assert reconciliation.halt_triggered is True
    assert readiness.status == "blocked"
    assert readiness.trading_allowed is False
    assert readiness.active_trading_overrides == 1
    assert any("reconciliation" in incident.title.lower() for incident in incidents)
    assert any(override.scope == "trading" and override.action == "pause" for override in overrides)


def test_execution_service_blocks_live_readiness_without_seeded_live_capability(tmp_path: Path) -> None:
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'execution-live-readiness.db'}")
    database.create_schema()

    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'execution-live-readiness.db'}",
        db_bootstrap_on_start=True,
        market_calendar="XNYS",
        market_timezone="America/New_York",
        default_broker_adapter="alpaca",
        default_broker_provider_key="alpaca-live",
        default_broker_account_ref="live-main",
        default_broker_environment="live",
    )
    state_store = StateStore(database.session_factory)
    state_store.bootstrap_reference_data(settings)
    _promote_production_strategy(database)

    service = ExecutionService(database.session_factory, settings)
    service.synthesize_market_session_state(now=datetime(2026, 3, 18, 14, 0, tzinfo=UTC))
    snapshot = service.record_broker_account_snapshot(
        {
            "provider_key": "alpaca-live",
            "account_ref": "live-main",
            "environment": "live",
            "equity": 10000.0,
            "cash": 7000.0,
            "buying_power": 15000.0,
            "gross_exposure": 2500.0,
            "net_exposure": 2200.0,
            "positions_count": 2,
            "open_orders_count": 0,
            "created_by": "tester",
        }
    )
    reconciliation = service.record_reconciliation_run(
        {
            "provider_key": "alpaca-live",
            "account_ref": "live-main",
            "account_snapshot_id": snapshot.id,
            "environment": "live",
            "internal_equity": 10001.0,
            "internal_positions_count": 2,
            "internal_open_orders_count": 0,
            "created_by": "tester",
        }
    )
    readiness = service.get_execution_readiness()

    assert reconciliation.status == "matched"
    assert readiness.status == "blocked"
    assert readiness.trading_allowed is False
    assert any("successful broker sync" in reason.lower() for reason in readiness.blocked_reasons)


def test_execution_service_submits_order_intent_and_updates_positions(tmp_path: Path) -> None:
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'execution-order.db'}")
    database.create_schema()

    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'execution-order.db'}",
        db_bootstrap_on_start=True,
        market_calendar="CRYPTO_24X7",
        market_timezone="UTC",
        default_broker_provider_key="paper-sim",
        default_broker_account_ref="paper-main",
    )
    state_store = StateStore(database.session_factory)
    state_store.bootstrap_reference_data(settings)
    spec_id = _promote_production_strategy(database)

    service = ExecutionService(database.session_factory, settings)
    service.synthesize_market_session_state(now=datetime(2026, 3, 18, 14, 0, tzinfo=UTC))
    snapshot = service.record_broker_account_snapshot(
        {
            "provider_key": "paper-sim",
            "account_ref": "paper-main",
            "environment": "paper",
            "equity": 10000.0,
            "cash": 10000.0,
            "buying_power": 10000.0,
            "gross_exposure": 0.0,
            "net_exposure": 0.0,
            "positions_count": 0,
            "open_orders_count": 0,
            "created_by": "tester",
        }
    )
    service.record_reconciliation_run(
        {
            "provider_key": "paper-sim",
            "account_ref": "paper-main",
            "account_snapshot_id": snapshot.id,
            "environment": "paper",
            "internal_equity": 10000.0,
            "internal_positions_count": 0,
            "internal_open_orders_count": 0,
            "created_by": "tester",
        }
    )
    intent = service.submit_order_intent(
        {
            "strategy_spec_id": spec_id,
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 4,
            "reference_price": 100.0,
            "provider_key": "paper-sim",
            "account_ref": "paper-main",
            "environment": "paper",
            "created_by": "tester",
        }
    )
    orders = service.list_order_records(limit=5)
    positions = service.list_positions(limit=5, active_only=True)
    latest_snapshot = service.list_broker_account_snapshots(limit=1)[0]

    assert intent.status == "filled"
    assert orders[0].symbol == "AAPL"
    assert orders[0].filled_quantity == 4
    assert positions[0].symbol == "AAPL"
    assert positions[0].quantity == 4
    assert latest_snapshot.positions_count == 1
    assert latest_snapshot.gross_exposure == 400.0


def test_execution_service_rejects_order_intent_when_allocation_cap_is_exceeded(tmp_path: Path) -> None:
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'execution-order-reject.db'}")
    database.create_schema()

    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'execution-order-reject.db'}",
        db_bootstrap_on_start=True,
        market_calendar="CRYPTO_24X7",
        market_timezone="UTC",
        default_broker_provider_key="paper-sim",
        default_broker_account_ref="paper-main",
    )
    state_store = StateStore(database.session_factory)
    state_store.bootstrap_reference_data(settings)
    spec_id = _promote_production_strategy(database)

    service = ExecutionService(database.session_factory, settings)
    service.upsert_allocation_policy(
        {
            "policy_key": "strict-paper",
            "environment": "paper",
            "scope": "global",
            "provider_key": "paper-sim",
            "account_ref": "paper-main",
            "max_strategy_notional_pct": 0.01,
            "max_gross_exposure_pct": 0.5,
            "max_open_positions": 4,
            "max_open_orders": 4,
            "created_by": "tester",
        }
    )
    service.synthesize_market_session_state(now=datetime(2026, 3, 18, 14, 0, tzinfo=UTC))
    snapshot = service.record_broker_account_snapshot(
        {
            "provider_key": "paper-sim",
            "account_ref": "paper-main",
            "environment": "paper",
            "equity": 10000.0,
            "cash": 10000.0,
            "buying_power": 10000.0,
            "gross_exposure": 0.0,
            "net_exposure": 0.0,
            "positions_count": 0,
            "open_orders_count": 0,
            "created_by": "tester",
        }
    )
    service.record_reconciliation_run(
        {
            "provider_key": "paper-sim",
            "account_ref": "paper-main",
            "account_snapshot_id": snapshot.id,
            "environment": "paper",
            "internal_equity": 10000.0,
            "internal_positions_count": 0,
            "internal_open_orders_count": 0,
            "created_by": "tester",
        }
    )
    intent = service.submit_order_intent(
        {
            "strategy_spec_id": spec_id,
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 5,
            "reference_price": 100.0,
            "provider_key": "paper-sim",
            "account_ref": "paper-main",
            "environment": "paper",
            "allocation_policy_key": "strict-paper",
            "created_by": "tester",
        }
    )
    orders = service.list_order_records(limit=5)

    assert intent.status == "rejected"
    assert "strategy cap" in (intent.decision_reason or "").lower()
    assert orders == []


def test_execution_service_autoregisters_equity_instrument_during_order_submission(tmp_path: Path) -> None:
    database, _, service, spec_id = _prepare_trading_ready_service(
        tmp_path,
        "execution-instrument-autoregister.db",
        provider_key="paper-sim",
        account_ref="paper-main",
    )

    try:
        intent = service.submit_order_intent(
            {
                "strategy_spec_id": spec_id,
                "symbol": "AAPL",
                "side": "buy",
                "quantity": 2,
                "reference_price": 100.0,
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "created_by": "tester",
            }
        )
        instruments = service.list_instrument_definitions(limit=10)

        assert intent.status == "filled"
        assert intent.instrument_key == "equity:AAPL"
        assert instruments[0].instrument_key == "equity:AAPL"
        assert instruments[0].symbol == "AAPL"
    finally:
        database.dispose()


def test_execution_service_rejects_option_order_when_broker_capability_disables_options(tmp_path: Path) -> None:
    database, _, service, spec_id = _prepare_trading_ready_service(
        tmp_path,
        "execution-option-capability.db",
        provider_key="paper-sim",
        account_ref="paper-main",
    )

    try:
        option_instrument = service.upsert_instrument_definition(
            {
                "symbol": "AAPL240619C00200000",
                "instrument_type": "option",
                "underlying_symbol": "AAPL",
                "option_right": "call",
                "option_style": "american",
                "expiration_date": "2026-06-19",
                "strike_price": 200.0,
                "contract_multiplier": 100.0,
                "created_by": "tester",
            }
        )

        intent = service.submit_order_intent(
            {
                "strategy_spec_id": spec_id,
                "symbol": option_instrument.symbol,
                "side": "buy",
                "quantity": 1,
                "reference_price": 5.0,
                "instrument_id": option_instrument.id,
                "asset_type": "option",
                "position_effect": "open",
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "created_by": "tester",
            }
        )

        assert intent.status == "rejected"
        assert "options trading" in (intent.decision_reason or "").lower()
    finally:
        database.dispose()


def test_execution_service_rejects_short_open_when_broker_capability_disables_shorts(tmp_path: Path) -> None:
    database, _, service, spec_id = _prepare_trading_ready_service(
        tmp_path,
        "execution-short-capability.db",
        provider_key="paper-sim",
        account_ref="paper-main",
    )

    try:
        service.upsert_allocation_policy(
            {
                "policy_key": "paper-short-enabled",
                "environment": "paper",
                "scope": "global",
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "max_strategy_notional_pct": 0.05,
                "max_gross_exposure_pct": 0.8,
                "max_open_positions": 8,
                "max_open_orders": 8,
                "allow_short": True,
                "created_by": "tester",
            }
        )

        intent = service.submit_order_intent(
            {
                "strategy_spec_id": spec_id,
                "symbol": "TSLA",
                "side": "sell",
                "quantity": 1,
                "reference_price": 200.0,
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "allocation_policy_key": "paper-short-enabled",
                "created_by": "tester",
            }
        )

        assert intent.status == "rejected"
        assert "short selling" in (intent.decision_reason or "").lower()
    finally:
        database.dispose()


def test_execution_service_paper_adapter_closes_and_flips_short_positions_when_enabled(tmp_path: Path) -> None:
    database, _, service, spec_id = _prepare_trading_ready_service(
        tmp_path,
        "execution-short-lifecycle.db",
        provider_key="paper-sim",
        account_ref="paper-main",
    )

    try:
        service.upsert_allocation_policy(
            {
                "policy_key": "paper-option-wide",
                "environment": "paper",
                "scope": "global",
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "max_strategy_notional_pct": 2.0,
                "max_gross_exposure_pct": 2.0,
                "max_open_positions": 8,
                "max_open_orders": 8,
                "created_by": "tester",
            }
        )
        service.upsert_broker_capability(
            {
                "capability_key": "paper-sim:paper_sim:paper",
                "provider_key": "paper-sim",
                "broker_adapter": "paper_sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "account_mode": "paper",
                "supports_equities": True,
                "supports_etfs": True,
                "supports_fractional": True,
                "supports_short": True,
                "supports_margin": True,
                "supports_options": False,
                "supports_multi_leg_options": False,
                "supports_option_exercise": False,
                "supports_option_assignment_events": False,
                "supports_live_trading": False,
                "supports_paper_trading": True,
                "created_by": "tester",
            }
        )
        service.upsert_allocation_policy(
            {
                "policy_key": "paper-short-enabled",
                "environment": "paper",
                "scope": "global",
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "max_strategy_notional_pct": 0.05,
                "max_gross_exposure_pct": 0.8,
                "max_open_positions": 8,
                "max_open_orders": 8,
                "allow_short": True,
                "created_by": "tester",
            }
        )

        short_intent = service.submit_order_intent(
            {
                "strategy_spec_id": spec_id,
                "symbol": "TSLA",
                "side": "sell",
                "quantity": 2,
                "reference_price": 100.0,
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "allocation_policy_key": "paper-short-enabled",
                "created_by": "tester",
            }
        )
        cover_intent = service.submit_order_intent(
            {
                "strategy_spec_id": spec_id,
                "symbol": "TSLA",
                "side": "buy",
                "quantity": 1,
                "reference_price": 90.0,
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "allocation_policy_key": "paper-short-enabled",
                "created_by": "tester",
            }
        )
        flip_intent = service.submit_order_intent(
            {
                "strategy_spec_id": spec_id,
                "symbol": "TSLA",
                "side": "buy",
                "quantity": 2,
                "reference_price": 80.0,
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "allocation_policy_key": "paper-short-enabled",
                "created_by": "tester",
            }
        )
        position = service.list_positions(limit=1, active_only=True)[0]

        assert short_intent.status == "filled"
        assert cover_intent.status == "filled"
        assert flip_intent.status == "filled"
        assert position.symbol == "TSLA"
        assert position.direction == "long"
        assert position.quantity == 1
        assert position.avg_entry_price == 80.0
        assert position.realized_pnl == 30.0
    finally:
        database.dispose()


def test_execution_service_paper_adapter_executes_long_option_open_and_close(tmp_path: Path) -> None:
    database, _, service, spec_id = _prepare_trading_ready_service(
        tmp_path,
        "execution-option-lifecycle.db",
        provider_key="paper-sim",
        account_ref="paper-main",
    )

    try:
        service.upsert_allocation_policy(
            {
                "policy_key": "paper-option-wide",
                "environment": "paper",
                "scope": "global",
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "max_strategy_notional_pct": 2.0,
                "max_gross_exposure_pct": 2.0,
                "max_open_positions": 8,
                "max_open_orders": 8,
                "created_by": "tester",
            }
        )
        service.upsert_broker_capability(
            {
                "capability_key": "paper-sim:paper_sim:paper",
                "provider_key": "paper-sim",
                "broker_adapter": "paper_sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "account_mode": "paper",
                "supports_equities": True,
                "supports_etfs": True,
                "supports_fractional": True,
                "supports_short": False,
                "supports_margin": False,
                "supports_options": True,
                "supports_multi_leg_options": False,
                "supports_option_exercise": False,
                "supports_option_assignment_events": False,
                "supports_live_trading": False,
                "supports_paper_trading": True,
                "created_by": "tester",
            }
        )
        option_instrument = service.upsert_instrument_definition(
            {
                "symbol": "AAPL240619C00200000",
                "instrument_type": "option",
                "underlying_symbol": "AAPL",
                "option_right": "call",
                "option_style": "american",
                "expiration_date": "2026-06-19",
                "strike_price": 200.0,
                "contract_multiplier": 100.0,
                "created_by": "tester",
            }
        )

        open_intent = service.submit_order_intent(
            {
                "strategy_spec_id": spec_id,
                "symbol": option_instrument.symbol,
                "side": "buy",
                "quantity": 1,
                "reference_price": 5.0,
                "instrument_id": option_instrument.id,
                "asset_type": "option",
                "position_effect": "open",
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "allocation_policy_key": "paper-option-wide",
                "created_by": "tester",
            }
        )
        close_intent = service.submit_order_intent(
            {
                "strategy_spec_id": spec_id,
                "symbol": option_instrument.symbol,
                "side": "sell",
                "quantity": 1,
                "reference_price": 6.0,
                "instrument_id": option_instrument.id,
                "asset_type": "option",
                "position_effect": "close",
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "allocation_policy_key": "paper-option-wide",
                "created_by": "tester",
            }
        )
        positions = service.list_positions(limit=5, active_only=False)
        order_records = service.list_order_records(limit=5)

        assert open_intent.status == "filled"
        assert open_intent.requested_notional == 500.0
        assert close_intent.status == "filled"
        assert order_records[0].requested_notional == 600.0
        assert positions[0].asset_type == "option"
        assert positions[0].status == "closed"
        assert positions[0].realized_pnl == 100.0
        assert positions[0].instrument_key.startswith("option:AAPL:2026-06-19:call:")
    finally:
        database.dispose()


def test_execution_service_rejects_option_open_when_premium_exceeds_buying_power(tmp_path: Path) -> None:
    database, _, service, spec_id = _prepare_trading_ready_service(
        tmp_path,
        "execution-option-buying-power.db",
        provider_key="paper-sim",
        account_ref="paper-main",
    )

    try:
        service.upsert_allocation_policy(
            {
                "policy_key": "paper-option-wide",
                "environment": "paper",
                "scope": "global",
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "max_strategy_notional_pct": 2.0,
                "max_gross_exposure_pct": 2.0,
                "max_open_positions": 8,
                "max_open_orders": 8,
                "created_by": "tester",
            }
        )
        service.upsert_broker_capability(
            {
                "capability_key": "paper-sim:paper_sim:paper",
                "provider_key": "paper-sim",
                "broker_adapter": "paper_sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "account_mode": "paper",
                "supports_equities": True,
                "supports_etfs": True,
                "supports_fractional": True,
                "supports_short": False,
                "supports_margin": False,
                "supports_options": True,
                "supports_multi_leg_options": False,
                "supports_option_exercise": False,
                "supports_option_assignment_events": False,
                "supports_live_trading": False,
                "supports_paper_trading": True,
                "created_by": "tester",
            }
        )
        option_instrument = service.upsert_instrument_definition(
            {
                "symbol": "AAPL240619C00250000",
                "instrument_type": "option",
                "underlying_symbol": "AAPL",
                "option_right": "call",
                "option_style": "american",
                "expiration_date": "2026-06-19",
                "strike_price": 250.0,
                "contract_multiplier": 100.0,
                "created_by": "tester",
            }
        )

        intent = service.submit_order_intent(
            {
                "strategy_spec_id": spec_id,
                "symbol": option_instrument.symbol,
                "side": "buy",
                "quantity": 2,
                "reference_price": 60.0,
                "instrument_id": option_instrument.id,
                "asset_type": "option",
                "position_effect": "open",
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "allocation_policy_key": "paper-option-wide",
                "created_by": "tester",
            }
        )

        assert intent.status == "rejected"
        assert "available cash" in (intent.decision_reason or "").lower()
    finally:
        database.dispose()


def test_execution_service_fills_multi_leg_option_structure_in_paper_mode(tmp_path: Path) -> None:
    database, _, service, spec_id = _prepare_trading_ready_service(
        tmp_path,
        "execution-multi-leg-option.db",
        provider_key="paper-sim",
        account_ref="paper-main",
    )

    try:
        service.upsert_allocation_policy(
            {
                "policy_key": "paper-option-spread",
                "environment": "paper",
                "scope": "global",
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "max_strategy_notional_pct": 2.0,
                "max_gross_exposure_pct": 2.0,
                "max_open_positions": 8,
                "max_open_orders": 8,
                "created_by": "tester",
            }
        )
        service.upsert_broker_capability(
            {
                "capability_key": "paper-sim:paper_sim:paper",
                "provider_key": "paper-sim",
                "broker_adapter": "paper_sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "account_mode": "paper",
                "supports_options": True,
                "supports_multi_leg_options": True,
                "supports_paper_trading": True,
                "created_by": "tester",
            }
        )
        long_leg = service.upsert_instrument_definition(
            {
                "symbol": "AAPL260619C00200000",
                "instrument_type": "option",
                "underlying_symbol": "AAPL",
                "option_right": "call",
                "option_style": "american",
                "expiration_date": "2026-06-19",
                "strike_price": 200.0,
                "contract_multiplier": 100.0,
                "created_by": "tester",
            }
        )
        short_leg = service.upsert_instrument_definition(
            {
                "symbol": "AAPL260619C00210000",
                "instrument_type": "option",
                "underlying_symbol": "AAPL",
                "option_right": "call",
                "option_style": "american",
                "expiration_date": "2026-06-19",
                "strike_price": 210.0,
                "contract_multiplier": 100.0,
                "created_by": "tester",
            }
        )

        intent = service.submit_order_intent(
            {
                "strategy_spec_id": spec_id,
                "symbol": "AAPL-BULL-CALL",
                "side": "buy",
                "quantity": 1,
                "reference_price": 2.0,
                "asset_type": "option",
                "position_effect": "open",
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "allocation_policy_key": "paper-option-spread",
                "created_by": "tester",
                "legs": [
                    {
                        "symbol": long_leg.symbol,
                        "instrument_id": long_leg.id,
                        "side": "buy",
                        "position_effect": "open",
                        "quantity": 1,
                        "reference_price": 5.0,
                    },
                    {
                        "symbol": short_leg.symbol,
                        "instrument_id": short_leg.id,
                        "side": "sell",
                        "position_effect": "open",
                        "quantity": 1,
                        "reference_price": 3.0,
                    },
                ],
            }
        )

        positions = service.list_positions(limit=10)
        order_records = service.list_order_records(limit=5)

        assert intent.status == "filled"
        assert intent.leg_count == 2
        assert len(intent.legs) == 2
        assert intent.legs[0].instrument_key == long_leg.instrument_key
        assert intent.legs[1].instrument_key == short_leg.instrument_key
        assert len(order_records) == 1
        assert order_records[0].status == "filled"
        assert {position.symbol for position in positions} == {long_leg.symbol, short_leg.symbol}
        assert {position.direction for position in positions} == {"long", "short"}
    finally:
        database.dispose()


def test_execution_service_submits_multi_leg_option_structure_for_external_adapter(tmp_path: Path) -> None:
    adapter = ScriptedAsyncBrokerAdapter()
    database, settings, service, spec_id = _prepare_trading_ready_service(
        tmp_path,
        "execution-alpaca-multi-leg.db",
        provider_key="alpaca-paper",
        account_ref="paper-main",
        adapters={"alpaca": adapter},
    )
    settings.default_broker_adapter = "alpaca"

    try:
        service.upsert_allocation_policy(
            {
                "policy_key": "alpaca-option-spread",
                "environment": "paper",
                "scope": "global",
                "provider_key": "alpaca-paper",
                "account_ref": "paper-main",
                "max_strategy_notional_pct": 2.0,
                "max_gross_exposure_pct": 2.0,
                "max_open_positions": 8,
                "max_open_orders": 8,
                "created_by": "tester",
            }
        )
        service.upsert_broker_capability(
            {
                "capability_key": "alpaca-paper:alpaca:paper",
                "provider_key": "alpaca-paper",
                "broker_adapter": "alpaca",
                "account_ref": "paper-main",
                "environment": "paper",
                "account_mode": "paper",
                "supports_options": True,
                "supports_multi_leg_options": True,
                "supports_paper_trading": True,
                "created_by": "tester",
            }
        )
        long_leg = service.upsert_instrument_definition(
            {
                "symbol": "AAPL260619C00200000",
                "instrument_type": "option",
                "underlying_symbol": "AAPL",
                "option_right": "call",
                "option_style": "american",
                "expiration_date": "2026-06-19",
                "strike_price": 200.0,
                "contract_multiplier": 100.0,
                "created_by": "tester",
            }
        )
        short_leg = service.upsert_instrument_definition(
            {
                "symbol": "AAPL260619C00210000",
                "instrument_type": "option",
                "underlying_symbol": "AAPL",
                "option_right": "call",
                "option_style": "american",
                "expiration_date": "2026-06-19",
                "strike_price": 210.0,
                "contract_multiplier": 100.0,
                "created_by": "tester",
            }
        )

        intent = service.submit_order_intent(
            {
                "strategy_spec_id": spec_id,
                "symbol": "AAPL-BULL-CALL",
                "side": "buy",
                "quantity": 1,
                "reference_price": 2.0,
                "asset_type": "option",
                "position_effect": "open",
                "provider_key": "alpaca-paper",
                "account_ref": "paper-main",
                "environment": "paper",
                "broker_adapter": "alpaca",
                "allocation_policy_key": "alpaca-option-spread",
                "created_by": "tester",
                "legs": [
                    {
                        "symbol": long_leg.symbol,
                        "instrument_id": long_leg.id,
                        "side": "buy",
                        "position_effect": "open",
                        "quantity": 1,
                        "reference_price": 5.0,
                    },
                    {
                        "symbol": short_leg.symbol,
                        "instrument_id": short_leg.id,
                        "side": "sell",
                        "position_effect": "open",
                        "quantity": 1,
                        "reference_price": 3.0,
                    },
                ],
            }
        )

        order_records = service.list_order_records(limit=5)

        assert intent.status == "submitted"
        assert intent.leg_count == 2
        assert len(order_records) == 1
        assert order_records[0].status == "submitted"
        assert order_records[0].leg_count == 2
    finally:
        database.dispose()


def test_execution_service_allows_covered_call_and_buy_to_close(tmp_path: Path) -> None:
    database, _, service, spec_id = _prepare_trading_ready_service(
        tmp_path,
        "execution-covered-call.db",
        provider_key="paper-sim",
        account_ref="paper-main",
    )

    try:
        service.record_broker_account_snapshot(
            {
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "equity": 25000.0,
                "cash": 25000.0,
                "buying_power": 25000.0,
                "gross_exposure": 0.0,
                "net_exposure": 0.0,
                "positions_count": 0,
                "open_orders_count": 0,
                "created_by": "tester",
            }
        )
        service.upsert_allocation_policy(
            {
                "policy_key": "paper-covered-call",
                "environment": "paper",
                "scope": "global",
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "max_strategy_notional_pct": 2.0,
                "max_gross_exposure_pct": 2.0,
                "max_open_positions": 8,
                "max_open_orders": 8,
                "allow_short": True,
                "created_by": "tester",
            }
        )
        service.upsert_broker_capability(
            {
                "capability_key": "paper-sim:paper_sim:paper",
                "provider_key": "paper-sim",
                "broker_adapter": "paper_sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "account_mode": "paper",
                "supports_options": True,
                "supports_paper_trading": True,
                "created_by": "tester",
            }
        )
        option_instrument = service.upsert_instrument_definition(
            {
                "symbol": "AAPL260619C00055000",
                "instrument_type": "option",
                "underlying_symbol": "AAPL",
                "option_right": "call",
                "option_style": "american",
                "expiration_date": "2026-06-19",
                "strike_price": 55.0,
                "contract_multiplier": 100.0,
                "created_by": "tester",
            }
        )

        stock_intent = service.submit_order_intent(
            {
                "strategy_spec_id": spec_id,
                "symbol": "AAPL",
                "side": "buy",
                "quantity": 100,
                "reference_price": 50.0,
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "allocation_policy_key": "paper-covered-call",
                "created_by": "tester",
            }
        )
        short_call = service.submit_order_intent(
            {
                "strategy_spec_id": spec_id,
                "symbol": option_instrument.symbol,
                "side": "sell",
                "quantity": 1,
                "reference_price": 2.0,
                "instrument_id": option_instrument.id,
                "asset_type": "option",
                "position_effect": "open",
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "allocation_policy_key": "paper-covered-call",
                "created_by": "tester",
            }
        )
        close_call = service.submit_order_intent(
            {
                "strategy_spec_id": spec_id,
                "symbol": option_instrument.symbol,
                "side": "buy",
                "quantity": 1,
                "reference_price": 1.0,
                "instrument_id": option_instrument.id,
                "asset_type": "option",
                "position_effect": "close",
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "allocation_policy_key": "paper-covered-call",
                "created_by": "tester",
            }
        )
        positions = service.list_positions(limit=10, active_only=False)
        option_row = next(position for position in positions if position.symbol == option_instrument.symbol)
        stock_row = next(position for position in positions if position.symbol == "AAPL")

        assert stock_intent.status == "filled"
        assert short_call.status == "filled"
        assert close_call.status == "filled"
        assert option_row.status == "closed"
        assert option_row.realized_pnl == 100.0
        assert stock_row.status == "active"
        assert stock_row.quantity == 100
    finally:
        database.dispose()


def test_execution_service_allows_short_put_roll_and_releases_old_reserve(tmp_path: Path) -> None:
    database, _, service, spec_id = _prepare_trading_ready_service(
        tmp_path,
        "execution-short-put-roll.db",
        provider_key="paper-sim",
        account_ref="paper-main",
    )

    try:
        service.upsert_allocation_policy(
            {
                "policy_key": "paper-put-roll",
                "environment": "paper",
                "scope": "global",
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "max_strategy_notional_pct": 5.0,
                "max_gross_exposure_pct": 5.0,
                "max_open_positions": 8,
                "max_open_orders": 8,
                "allow_short": True,
                "created_by": "tester",
            }
        )
        service.upsert_broker_capability(
            {
                "capability_key": "paper-sim:paper_sim:paper",
                "provider_key": "paper-sim",
                "broker_adapter": "paper_sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "account_mode": "paper",
                "supports_options": True,
                "supports_multi_leg_options": True,
                "supports_paper_trading": True,
                "created_by": "tester",
            }
        )
        near_put = service.upsert_instrument_definition(
            {
                "symbol": "AAPL260619P00050000",
                "instrument_type": "option",
                "underlying_symbol": "AAPL",
                "option_right": "put",
                "option_style": "american",
                "expiration_date": "2026-06-19",
                "strike_price": 50.0,
                "contract_multiplier": 100.0,
                "created_by": "tester",
            }
        )
        rolled_put = service.upsert_instrument_definition(
            {
                "symbol": "AAPL260717P00045000",
                "instrument_type": "option",
                "underlying_symbol": "AAPL",
                "option_right": "put",
                "option_style": "american",
                "expiration_date": "2026-07-17",
                "strike_price": 45.0,
                "contract_multiplier": 100.0,
                "created_by": "tester",
            }
        )

        open_short_put = service.submit_order_intent(
            {
                "strategy_spec_id": spec_id,
                "symbol": near_put.symbol,
                "side": "sell",
                "quantity": 1,
                "reference_price": 2.0,
                "instrument_id": near_put.id,
                "asset_type": "option",
                "position_effect": "open",
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "allocation_policy_key": "paper-put-roll",
                "created_by": "tester",
            }
        )
        roll_intent = service.submit_order_intent(
            {
                "strategy_spec_id": spec_id,
                "symbol": "AAPL-PUT-ROLL",
                "side": "buy",
                "quantity": 1,
                "reference_price": 0.5,
                "asset_type": "option",
                "position_effect": "open",
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "allocation_policy_key": "paper-put-roll",
                "created_by": "tester",
                "legs": [
                    {
                        "symbol": near_put.symbol,
                        "instrument_id": near_put.id,
                        "side": "buy",
                        "position_effect": "close",
                        "quantity": 1,
                        "reference_price": 1.0,
                    },
                    {
                        "symbol": rolled_put.symbol,
                        "instrument_id": rolled_put.id,
                        "side": "sell",
                        "position_effect": "open",
                        "quantity": 1,
                        "reference_price": 1.5,
                    },
                ],
            }
        )
        positions = service.list_positions(limit=10, active_only=False)
        near_row = next(position for position in positions if position.symbol == near_put.symbol)
        rolled_row = next(position for position in positions if position.symbol == rolled_put.symbol)

        assert open_short_put.status == "filled"
        assert roll_intent.status == "filled"
        assert near_row.status == "closed"
        assert rolled_row.status == "active"
        assert rolled_row.direction == "short"
        assert rolled_row.avg_entry_price == 1.5
    finally:
        database.dispose()


def test_execution_service_blocks_short_equity_without_locate(tmp_path: Path) -> None:
    database, _, service, spec_id = _prepare_trading_ready_service(
        tmp_path,
        "execution-short-locate.db",
        provider_key="paper-sim",
        account_ref="paper-main",
    )

    try:
        service.upsert_allocation_policy(
            {
                "policy_key": "paper-short-equity",
                "environment": "paper",
                "scope": "global",
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "max_strategy_notional_pct": 2.0,
                "max_gross_exposure_pct": 2.0,
                "max_open_positions": 8,
                "max_open_orders": 8,
                "allow_short": True,
                "created_by": "tester",
            }
        )
        service.upsert_broker_capability(
            {
                "capability_key": "paper-sim:paper_sim:paper",
                "provider_key": "paper-sim",
                "broker_adapter": "paper_sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "account_mode": "margin",
                "supports_short": True,
                "supports_margin": True,
                "supports_paper_trading": True,
                "created_by": "tester",
            }
        )
        shortable = service.upsert_instrument_definition(
            {
                "symbol": "HTB",
                "instrument_type": "equity",
                "is_shortable": True,
                "metadata_payload": {"borrow_status": "hard_to_borrow", "locate_required": True},
                "created_by": "tester",
            }
        )

        intent = service.submit_order_intent(
            {
                "strategy_spec_id": spec_id,
                "symbol": shortable.symbol,
                "side": "sell",
                "quantity": 10,
                "reference_price": 50.0,
                "instrument_id": shortable.id,
                "asset_type": "equity",
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "allocation_policy_key": "paper-short-equity",
                "created_by": "tester",
            }
        )

        assert intent.status == "rejected"
        assert "locate" in (intent.decision_reason or "").lower()
    finally:
        database.dispose()


def test_execution_service_blocks_short_equity_when_maintenance_margin_breaks(tmp_path: Path) -> None:
    database, _, service, spec_id = _prepare_trading_ready_service(
        tmp_path,
        "execution-short-margin.db",
        provider_key="paper-sim",
        account_ref="paper-main",
    )

    try:
        service.upsert_allocation_policy(
            {
                "policy_key": "paper-short-margin",
                "environment": "paper",
                "scope": "global",
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "max_strategy_notional_pct": 5.0,
                "max_gross_exposure_pct": 5.0,
                "max_open_positions": 8,
                "max_open_orders": 8,
                "allow_short": True,
                "created_by": "tester",
            }
        )
        service.upsert_broker_capability(
            {
                "capability_key": "paper-sim:paper_sim:paper",
                "provider_key": "paper-sim",
                "broker_adapter": "paper_sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "account_mode": "margin",
                "supports_short": True,
                "supports_margin": True,
                "supports_paper_trading": True,
                "created_by": "tester",
            }
        )
        leveraged_short = service.upsert_instrument_definition(
            {
                "symbol": "MARG",
                "instrument_type": "equity",
                "is_shortable": True,
                "metadata_payload": {
                    "borrow_status": "easy_to_borrow",
                    "locate_required": True,
                    "maintenance_margin_pct": 0.8,
                },
                "created_by": "tester",
            }
        )

        intent = service.submit_order_intent(
            {
                "strategy_spec_id": spec_id,
                "symbol": leveraged_short.symbol,
                "side": "sell",
                "quantity": 300,
                "reference_price": 50.0,
                "instrument_id": leveraged_short.id,
                "asset_type": "equity",
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "allocation_policy_key": "paper-short-margin",
                "signal_payload": {"locate_confirmed": True},
                "created_by": "tester",
            }
        )

        assert intent.status == "rejected"
        assert "maintenance requirement" in (intent.decision_reason or "").lower()
    finally:
        database.dispose()


def test_execution_service_records_option_expiration_and_closes_position(tmp_path: Path) -> None:
    database, _, service, spec_id = _prepare_trading_ready_service(
        tmp_path,
        "execution-option-expiration.db",
        provider_key="paper-sim",
        account_ref="paper-main",
    )

    try:
        service.upsert_allocation_policy(
            {
                "policy_key": "paper-option-expiry",
                "environment": "paper",
                "scope": "global",
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "max_strategy_notional_pct": 2.0,
                "max_gross_exposure_pct": 2.0,
                "max_open_positions": 8,
                "max_open_orders": 8,
                "created_by": "tester",
            }
        )
        service.upsert_broker_capability(
            {
                "capability_key": "paper-sim:paper_sim:paper",
                "provider_key": "paper-sim",
                "broker_adapter": "paper_sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "account_mode": "paper",
                "supports_options": True,
                "supports_paper_trading": True,
                "created_by": "tester",
            }
        )
        option_instrument = service.upsert_instrument_definition(
            {
                "symbol": "AAPL260619C00200000",
                "instrument_type": "option",
                "underlying_symbol": "AAPL",
                "option_right": "call",
                "option_style": "american",
                "expiration_date": "2026-06-19",
                "strike_price": 200.0,
                "contract_multiplier": 100.0,
                "created_by": "tester",
            }
        )

        open_intent = service.submit_order_intent(
            {
                "strategy_spec_id": spec_id,
                "symbol": option_instrument.symbol,
                "side": "buy",
                "quantity": 1,
                "reference_price": 5.0,
                "instrument_id": option_instrument.id,
                "asset_type": "option",
                "position_effect": "open",
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "allocation_policy_key": "paper-option-expiry",
                "created_by": "tester",
            }
        )
        position = service.list_positions(limit=1, active_only=True)[0]
        event = service.record_option_lifecycle_event(
            {
                "event_type": "expiration",
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "symbol": option_instrument.symbol,
                "position_id": position.id,
                "instrument_id": option_instrument.id,
                "created_by": "tester",
            }
        )
        positions = service.list_positions(limit=5, active_only=False)
        events = service.list_option_lifecycle_events(limit=5)

        assert open_intent.status == "filled"
        assert event.status == "applied"
        assert event.state_applied is True
        assert event.review_required is False
        assert positions[0].status == "expired"
        assert positions[0].quantity == 0
        assert positions[0].notional_value == 0
        assert positions[0].realized_pnl == -500.0
        assert events[0].event_type == "expiration"
    finally:
        database.dispose()


def test_execution_service_applies_long_call_exercise_into_underlying_position(tmp_path: Path) -> None:
    database, _, service, spec_id = _prepare_trading_ready_service(
        tmp_path,
        "execution-option-exercise.db",
        provider_key="paper-sim",
        account_ref="paper-main",
    )

    try:
        service.upsert_allocation_policy(
            {
                "policy_key": "paper-option-exercise",
                "environment": "paper",
                "scope": "global",
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "max_strategy_notional_pct": 3.0,
                "max_gross_exposure_pct": 3.0,
                "max_open_positions": 8,
                "max_open_orders": 8,
                "created_by": "tester",
            }
        )
        service.upsert_broker_capability(
            {
                "capability_key": "paper-sim:paper_sim:paper",
                "provider_key": "paper-sim",
                "broker_adapter": "paper_sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "account_mode": "paper",
                "supports_options": True,
                "supports_option_exercise": True,
                "supports_paper_trading": True,
                "created_by": "tester",
            }
        )
        option_instrument = service.upsert_instrument_definition(
            {
                "symbol": "AAPL260619C00200000",
                "instrument_type": "option",
                "underlying_symbol": "AAPL",
                "option_right": "call",
                "option_style": "american",
                "expiration_date": "2026-06-19",
                "strike_price": 200.0,
                "contract_multiplier": 100.0,
                "created_by": "tester",
            }
        )

        service.submit_order_intent(
            {
                "strategy_spec_id": spec_id,
                "symbol": option_instrument.symbol,
                "side": "buy",
                "quantity": 1,
                "reference_price": 5.0,
                "instrument_id": option_instrument.id,
                "asset_type": "option",
                "position_effect": "open",
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "allocation_policy_key": "paper-option-exercise",
                "created_by": "tester",
            }
        )
        option_position = next(
            position for position in service.list_positions(limit=10, active_only=True) if position.symbol == option_instrument.symbol
        )

        event = service.record_option_lifecycle_event(
            {
                "event_type": "exercise",
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "symbol": option_instrument.symbol,
                "position_id": option_position.id,
                "instrument_id": option_instrument.id,
                "metadata_payload": {"underlying_market_price": 210.0},
                "created_by": "tester",
            }
        )
        positions = service.list_positions(limit=10, active_only=False)
        option_row = next(position for position in positions if position.symbol == option_instrument.symbol)
        stock_row = next(position for position in positions if position.symbol == "AAPL" and position.asset_type == "equity")

        assert event.status == "applied"
        assert event.state_applied is True
        assert event.review_required is False
        assert event.resulting_symbol == "AAPL"
        assert event.cash_flow == -20000.0
        assert option_row.status == "exercised"
        assert option_row.quantity == 0
        assert option_row.realized_pnl == -500.0
        assert stock_row.quantity == 100
        assert stock_row.avg_entry_price == 200.0
        assert stock_row.market_price == 210.0
        assert stock_row.unrealized_pnl == 1000.0
    finally:
        database.dispose()


def test_execution_service_applies_short_put_assignment_into_underlying_position(tmp_path: Path) -> None:
    database, _, service, spec_id = _prepare_trading_ready_service(
        tmp_path,
        "execution-option-assignment.db",
        provider_key="paper-sim",
        account_ref="paper-main",
    )

    try:
        service.upsert_broker_capability(
            {
                "capability_key": "paper-sim:paper_sim:paper",
                "provider_key": "paper-sim",
                "broker_adapter": "paper_sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "account_mode": "paper",
                "supports_options": True,
                "supports_option_assignment_events": True,
                "supports_paper_trading": True,
                "created_by": "tester",
            }
        )
        option_instrument = service.upsert_instrument_definition(
            {
                "symbol": "AAPL260619P00200000",
                "instrument_type": "option",
                "underlying_symbol": "AAPL",
                "option_right": "put",
                "option_style": "american",
                "expiration_date": "2026-06-19",
                "strike_price": 200.0,
                "contract_multiplier": 100.0,
                "created_by": "tester",
            }
        )

        with database.session_factory() as session:
            position = PositionRecordModel(
                strategy_spec_id=spec_id,
                provider_key="paper-sim",
                account_ref="paper-main",
                environment="paper",
                symbol=option_instrument.symbol,
                instrument_id=option_instrument.id,
                instrument_key=option_instrument.instrument_key,
                underlying_symbol="AAPL",
                asset_type="option",
                direction="short",
                quantity=1,
                avg_entry_price=4.0,
                market_price=4.0,
                notional_value=400.0,
                realized_pnl=0.0,
                unrealized_pnl=0.0,
                created_by="tester",
                origin_type="seed",
                origin_id="seed-short-put",
                status="active",
            )
            session.add(position)
            session.commit()
            session.refresh(position)
            option_position_id = position.id

        event = service.record_option_lifecycle_event(
            {
                "event_type": "assignment",
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "symbol": option_instrument.symbol,
                "position_id": option_position_id,
                "instrument_id": option_instrument.id,
                "metadata_payload": {"underlying_market_price": 195.0},
                "created_by": "tester",
            }
        )
        positions = service.list_positions(limit=10, active_only=False)
        option_row = next(position for position in positions if position.symbol == option_instrument.symbol)
        stock_row = next(position for position in positions if position.symbol == "AAPL" and position.asset_type == "equity")

        assert event.status == "applied"
        assert event.state_applied is True
        assert event.review_required is False
        assert event.resulting_symbol == "AAPL"
        assert event.cash_flow == -20000.0
        assert option_row.status == "assigned"
        assert option_row.quantity == 0
        assert option_row.realized_pnl == 400.0
        assert stock_row.quantity == 100
        assert stock_row.avg_entry_price == 200.0
        assert stock_row.market_price == 195.0
        assert stock_row.unrealized_pnl == -500.0
    finally:
        database.dispose()


def test_execution_service_applies_leverage_weighted_strategy_cap_for_leveraged_etf(tmp_path: Path) -> None:
    database, _, service, spec_id = _prepare_trading_ready_service(
        tmp_path,
        "execution-leveraged-etf-risk.db",
        provider_key="paper-sim",
        account_ref="paper-main",
    )

    try:
        leveraged_instrument = service.upsert_instrument_definition(
            {
                "symbol": "TQQQ",
                "instrument_type": "leveraged_etf",
                "display_symbol": "TQQQ",
                "leverage_ratio": 3.0,
                "created_by": "tester",
            }
        )

        intent = service.submit_order_intent(
            {
                "strategy_spec_id": spec_id,
                "symbol": leveraged_instrument.symbol,
                "side": "buy",
                "quantity": 2,
                "reference_price": 100.0,
                "instrument_id": leveraged_instrument.id,
                "asset_type": "leveraged_etf",
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "created_by": "tester",
            }
        )

        assert intent.status == "rejected"
        assert "strategy cap" in (intent.decision_reason or "").lower()
    finally:
        database.dispose()


def test_execution_service_syncs_external_broker_state_and_recovers_submitted_order(tmp_path: Path) -> None:
    adapter = ScriptedAsyncBrokerAdapter()
    database, settings, service, spec_id = _prepare_trading_ready_service(
        tmp_path,
        "execution-external-sync.db",
        provider_key="scripted-broker",
        account_ref="paper-main",
        adapters={"scripted_async": adapter},
    )

    try:
        intent = service.submit_order_intent(
            {
                "strategy_spec_id": spec_id,
                "symbol": "AAPL",
                "side": "buy",
                "quantity": 4,
                "reference_price": 100.0,
                "provider_key": "scripted-broker",
                "account_ref": "paper-main",
                "environment": "paper",
                "broker_adapter": "scripted_async",
                "created_by": "tester",
            }
        )
        order_record = service.list_order_records(limit=1)[0]
        assert intent.status == "submitted"
        assert order_record.status == "submitted"

        adapter.fill_order(order_record.broker_order_id, 101.0)
        restarted_service = ExecutionService(database.session_factory, settings, adapters={"scripted_async": adapter})
        sync_run = restarted_service.sync_broker_state(
            {
                "provider_key": "scripted-broker",
                "account_ref": "paper-main",
                "environment": "paper",
                "broker_adapter": "scripted_async",
                "created_by": "tester",
            }
        )
        synced_order = restarted_service.list_order_records(limit=1)[0]
        synced_position = restarted_service.list_positions(limit=1)[0]
        latest_snapshot = restarted_service.list_broker_account_snapshots(limit=1)[0]

        assert sync_run.status == "synchronized"
        assert synced_order.status == "filled"
        assert synced_order.client_order_id == f"qe-{intent.id}"
        assert synced_position.symbol == "AAPL"
        assert synced_position.quantity == 4
        assert latest_snapshot.positions_count == 1
        assert latest_snapshot.gross_exposure == 404.0
    finally:
        database.dispose()


def test_execution_service_can_cancel_and_replace_open_external_orders(tmp_path: Path) -> None:
    adapter = ScriptedAsyncBrokerAdapter()
    database, _, service, spec_id = _prepare_trading_ready_service(
        tmp_path,
        "execution-external-manage.db",
        provider_key="scripted-broker",
        account_ref="paper-main",
        adapters={"scripted_async": adapter},
    )
    try:
        first_intent = service.submit_order_intent(
            {
                "strategy_spec_id": spec_id,
                "symbol": "AAPL",
                "side": "buy",
                "quantity": 2,
                "reference_price": 100.0,
                "provider_key": "scripted-broker",
                "account_ref": "paper-main",
                "environment": "paper",
                "broker_adapter": "scripted_async",
                "created_by": "tester",
            }
        )
        first_order = service.list_order_records(limit=1)[0]
        canceled = service.cancel_order(
            first_order.id,
            {"reason": "cancel stale quote", "created_by": "tester"},
        )

        second_intent = service.submit_order_intent(
            {
                "strategy_spec_id": spec_id,
                "symbol": "MSFT",
                "side": "buy",
                "quantity": 2,
                "reference_price": 90.0,
                "provider_key": "scripted-broker",
                "account_ref": "paper-main",
                "environment": "paper",
                "broker_adapter": "scripted_async",
                "created_by": "tester",
            }
        )
        replace_source = service.list_order_records(limit=2)[0]
        replacement = service.replace_order(
            replace_source.id,
            {
                "quantity": 3,
                "reference_price": 95.0,
                "limit_price": 94.5,
                "time_in_force": "gtc",
                "rationale": "improve entry",
                "created_by": "tester",
            },
        )
        order_records = service.list_order_records(limit=5)
        latest_snapshot = service.list_broker_account_snapshots(limit=1)[0]

        assert first_intent.status == "submitted"
        assert canceled.status == "canceled"
        assert second_intent.status == "submitted"
        assert replacement.parent_order_record_id == replace_source.id
        assert replacement.status == "submitted"
        assert replacement.client_order_id is not None
        assert latest_snapshot.open_orders_count == 1
        assert any(order.status == "replaced" for order in order_records)
    finally:
        database.dispose()


def test_execution_service_blocks_cross_strategy_symbol_collisions(tmp_path: Path) -> None:
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'execution-symbol-collision.db'}")
    database.create_schema()

    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'execution-symbol-collision.db'}",
        db_bootstrap_on_start=True,
        market_calendar="CRYPTO_24X7",
        market_timezone="UTC",
        default_broker_provider_key="paper-sim",
        default_broker_account_ref="paper-main",
    )
    state_store = StateStore(database.session_factory)
    state_store.bootstrap_reference_data(settings)
    spec_a = _promote_production_strategy(database)
    spec_b = _promote_production_strategy(database)
    service = ExecutionService(database.session_factory, settings)
    service.synthesize_market_session_state(now=datetime(2026, 3, 18, 14, 0, tzinfo=UTC))
    snapshot = service.record_broker_account_snapshot(
        {
            "provider_key": "paper-sim",
            "account_ref": "paper-main",
            "environment": "paper",
            "equity": 10000.0,
            "cash": 10000.0,
            "buying_power": 10000.0,
            "gross_exposure": 0.0,
            "net_exposure": 0.0,
            "positions_count": 0,
            "open_orders_count": 0,
            "created_by": "tester",
        }
    )
    service.record_reconciliation_run(
        {
            "provider_key": "paper-sim",
            "account_ref": "paper-main",
            "account_snapshot_id": snapshot.id,
            "environment": "paper",
            "internal_equity": 10000.0,
            "internal_positions_count": 0,
            "internal_open_orders_count": 0,
            "created_by": "tester",
        }
    )

    first_intent = service.submit_order_intent(
        {
            "strategy_spec_id": spec_a,
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 4,
            "reference_price": 100.0,
            "provider_key": "paper-sim",
            "account_ref": "paper-main",
            "environment": "paper",
            "created_by": "tester",
        }
    )
    second_intent = service.submit_order_intent(
        {
            "strategy_spec_id": spec_b,
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 3,
            "reference_price": 100.0,
            "provider_key": "paper-sim",
            "account_ref": "paper-main",
            "environment": "paper",
            "created_by": "tester",
        }
    )

    assert first_intent.status == "filled"
    assert second_intent.status == "rejected"
    assert "another strategy" in (second_intent.decision_reason or "").lower()


def _promote_production_strategy(database: Database) -> str:
    strategy_service = StrategyLabService(database.session_factory)
    hypothesis = strategy_service.create_hypothesis(
        {
            "title": "Controlled paper alpha",
            "thesis": "A governed strategy is required before execution can be ready.",
            "target_market": "us-equities",
            "mechanism": "Small controlled signals with explicit limits.",
            "created_by": "tester",
        }
    )
    spec = strategy_service.create_strategy_spec(
        {
            "hypothesis_id": hypothesis.id,
            "spec_code": f"ready-{hypothesis.id[:8]}",
            "title": "Controlled paper alpha",
            "target_market": "us-equities",
            "signal_logic": "Bounded production path for execution-readiness testing.",
            "created_by": "tester",
        }
    )
    strategy_service.record_promotion_decision(
        {
            "strategy_spec_id": spec.id,
            "target_stage": "production",
            "decision": "approved",
            "rationale": "Promoted for readiness-path testing.",
            "decided_by": "tester",
        }
    )
    return spec.id


def _prepare_trading_ready_service(
    tmp_path: Path,
    db_name: str,
    *,
    provider_key: str,
    account_ref: str,
    adapters: dict[str, object] | None = None,
) -> tuple[Database, Settings, ExecutionService, str]:
    database = Database(f"sqlite+pysqlite:///{tmp_path / db_name}")
    database.create_schema()

    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / db_name}",
        db_bootstrap_on_start=True,
        market_calendar="CRYPTO_24X7",
        market_timezone="UTC",
        default_broker_provider_key=provider_key,
        default_broker_account_ref=account_ref,
    )
    state_store = StateStore(database.session_factory)
    state_store.bootstrap_reference_data(settings)
    spec_id = _promote_production_strategy(database)

    service = ExecutionService(database.session_factory, settings, adapters=adapters)
    service.synthesize_market_session_state(now=datetime(2026, 3, 18, 14, 0, tzinfo=UTC))
    snapshot = service.record_broker_account_snapshot(
        {
            "provider_key": provider_key,
            "account_ref": account_ref,
            "environment": "paper",
            "equity": 10000.0,
            "cash": 10000.0,
            "buying_power": 10000.0,
            "gross_exposure": 0.0,
            "net_exposure": 0.0,
            "positions_count": 0,
            "open_orders_count": 0,
            "created_by": "tester",
        }
    )
    service.record_reconciliation_run(
        {
            "provider_key": provider_key,
            "account_ref": account_ref,
            "account_snapshot_id": snapshot.id,
            "environment": "paper",
            "internal_equity": 10000.0,
            "internal_positions_count": 0,
            "internal_open_orders_count": 0,
            "created_by": "tester",
        }
    )
    return database, settings, service, spec_id
