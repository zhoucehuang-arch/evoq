import json
from datetime import UTC, datetime
from pathlib import Path

import httpx

from quant_evo_nextgen.config import Settings
from quant_evo_nextgen.services.alpaca_broker import AlpacaBrokerAdapter
from quant_evo_nextgen.services.broker import (
    BrokerCancelRequest,
    BrokerExecutionLeg,
    BrokerExecutionRequest,
    BrokerOrderState,
    BrokerReplaceRequest,
    BrokerSyncRequest,
)


def test_alpaca_adapter_submits_limit_order(tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["payload"] = json.loads(request.content.decode("utf-8"))
        captured["headers"] = dict(request.headers)
        return httpx.Response(
            200,
            json={
                "id": "alpaca-order-1",
                "client_order_id": "qe-intent-1",
                "symbol": "AAPL",
                "asset_id": "asset-aapl",
                "asset_class": "us_equity",
                "side": "buy",
                "type": "limit",
                "time_in_force": "day",
                "qty": "2",
                "filled_qty": "0",
                "limit_price": "100.5",
                "status": "accepted",
                "updated_at": "2026-03-19T10:00:00Z",
            },
        )

    adapter = AlpacaBrokerAdapter(_settings(tmp_path), transport=httpx.MockTransport(handler))
    result = adapter.execute_order(
        BrokerExecutionRequest(
            order_intent_id="intent-1",
            client_order_id="qe-intent-1",
            strategy_spec_id="strategy-1",
            provider_key="alpaca-paper",
            account_ref="paper-main",
            environment="paper",
            symbol="AAPL",
            instrument_id=None,
            instrument_key="equity:AAPL",
            underlying_symbol=None,
            asset_type="equity",
            position_effect="open",
            side="buy",
            order_type="limit",
            time_in_force="day",
            quantity=2,
            reference_price=100.0,
            requested_notional=201.0,
            limit_price=100.5,
            stop_price=None,
            allow_short=False,
        ),
        current_position=None,
    )

    assert captured["method"] == "POST"
    assert captured["path"] == "/v2/orders"
    assert captured["headers"]["apca-api-key-id"] == "paper-key"
    assert captured["payload"] == {
        "symbol": "AAPL",
        "side": "buy",
        "type": "limit",
        "time_in_force": "day",
        "qty": "2",
        "client_order_id": "qe-intent-1",
        "limit_price": "100.5",
    }
    assert result.broker_order_id == "alpaca-order-1"
    assert result.order_status == "submitted"
    assert result.filled_quantity == 0.0


def test_alpaca_adapter_submits_multi_leg_option_order(tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["payload"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(
            200,
            json={
                "id": "alpaca-mleg-1",
                "client_order_id": "qe-intent-mleg-1",
                "asset_class": "us_option",
                "qty": "1",
                "filled_qty": "0",
                "limit_price": "2.00",
                "status": "accepted",
                "updated_at": "2026-03-19T10:15:00Z",
                "legs": [
                    {
                        "symbol": "AAPL260619C00200000",
                        "side": "buy",
                        "position_intent": "buy_to_open",
                    },
                    {
                        "symbol": "AAPL260619C00210000",
                        "side": "sell",
                        "position_intent": "sell_to_open",
                    },
                ],
            },
        )

    adapter = AlpacaBrokerAdapter(_settings(tmp_path), transport=httpx.MockTransport(handler))
    result = adapter.execute_order(
        BrokerExecutionRequest(
            order_intent_id="intent-mleg-1",
            client_order_id="qe-intent-mleg-1",
            strategy_spec_id="strategy-1",
            provider_key="alpaca-paper",
            account_ref="paper-main",
            environment="paper",
            symbol="AAPL-BULL-CALL",
            instrument_id=None,
            instrument_key=None,
            underlying_symbol="AAPL",
            asset_type="option",
            position_effect="open",
            side="buy",
            order_type="limit",
            time_in_force="day",
            quantity=1,
            reference_price=2.0,
            requested_notional=200.0,
            limit_price=2.0,
            stop_price=None,
            allow_short=True,
            legs=(
                BrokerExecutionLeg(
                    leg_index=1,
                    symbol="AAPL260619C00200000",
                    instrument_id=None,
                    instrument_key="option:AAPL:2026-06-19:call:200.00000000",
                    underlying_symbol="AAPL",
                    asset_type="option",
                    side="buy",
                    position_effect="open",
                    quantity=1,
                    ratio_quantity=1,
                    reference_price=5.0,
                    requested_notional=500.0,
                ),
                BrokerExecutionLeg(
                    leg_index=2,
                    symbol="AAPL260619C00210000",
                    instrument_id=None,
                    instrument_key="option:AAPL:2026-06-19:call:210.00000000",
                    underlying_symbol="AAPL",
                    asset_type="option",
                    side="sell",
                    position_effect="open",
                    quantity=1,
                    ratio_quantity=1,
                    reference_price=3.0,
                    requested_notional=300.0,
                ),
            ),
        ),
        current_position=None,
    )

    assert captured["payload"] == {
        "order_class": "mleg",
        "type": "limit",
        "time_in_force": "day",
        "qty": "1",
        "client_order_id": "qe-intent-mleg-1",
        "legs": [
            {
                "symbol": "AAPL260619C00200000",
                "ratio_qty": "1",
                "side": "buy",
                "position_intent": "buy_to_open",
            },
            {
                "symbol": "AAPL260619C00210000",
                "ratio_qty": "1",
                "side": "sell",
                "position_intent": "sell_to_open",
            },
        ],
        "limit_price": "2",
    }
    assert result.broker_order_id == "alpaca-mleg-1"
    assert result.order_status == "submitted"


def test_alpaca_adapter_syncs_option_position_and_capability_hint(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v2/account":
            return httpx.Response(
                200,
                json={
                    "id": "acct-1",
                    "status": "ACTIVE",
                    "equity": "10350.50",
                    "cash": "6200.25",
                    "buying_power": "18000.00",
                    "long_market_value": "4100.25",
                    "short_market_value": "1200.00",
                    "shorting_enabled": True,
                    "options_approved_level": 2,
                    "updated_at": "2026-03-19T10:05:00Z",
                },
            )
        if request.url.path == "/v2/orders":
            return httpx.Response(
                200,
                json=[
                    {
                        "id": "alpaca-order-2",
                        "client_order_id": "qe-intent-2",
                        "symbol": "AAPL260619C00200000",
                        "asset_id": "option-1",
                        "asset_class": "us_option",
                        "side": "sell",
                        "type": "limit",
                        "time_in_force": "day",
                        "qty": "1",
                        "filled_qty": "0",
                        "limit_price": "6.00",
                        "status": "new",
                        "position_intent": "sell_to_close",
                        "updated_at": "2026-03-19T10:06:00Z",
                    }
                ],
            )
        if request.url.path == "/v2/positions":
            return httpx.Response(
                200,
                json=[
                    {
                        "asset_id": "option-1",
                        "symbol": "AAPL260619C00200000",
                        "asset_class": "us_option",
                        "side": "long",
                        "qty": "1",
                        "avg_entry_price": "5.00",
                        "current_price": "6.00",
                    }
                ],
            )
        raise AssertionError(f"Unexpected path: {request.url.path}")

    adapter = AlpacaBrokerAdapter(_settings(tmp_path), transport=httpx.MockTransport(handler))
    result = adapter.sync_state(
        BrokerSyncRequest(
            provider_key="alpaca-paper",
            account_ref="paper-main",
            environment="paper",
            full_sync=True,
        )
    )

    assert result.account_state.gross_exposure == 5300.25
    assert result.account_state.net_exposure == 2900.25
    assert result.account_state.open_orders_count == 1
    assert result.account_state.raw_payload["capability_hint"]["supports_options"] is True
    assert result.orders[0].asset_type == "option"
    assert result.orders[0].position_effect == "close"
    assert result.orders[0].requested_notional == 600.0
    assert result.positions[0].underlying_symbol == "AAPL"
    assert result.positions[0].contract_multiplier == 100.0


def test_alpaca_adapter_cancels_order(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(204)

    adapter = AlpacaBrokerAdapter(_settings(tmp_path), transport=httpx.MockTransport(handler))
    result = adapter.cancel_order(
        BrokerCancelRequest(
            provider_key="alpaca-paper",
            account_ref="paper-main",
            environment="paper",
            broker_order_id="alpaca-order-3",
            client_order_id="qe-intent-3",
            reason="owner cancel",
        ),
        _current_order("alpaca-order-3"),
    )

    assert result.order_status == "canceled"
    assert result.client_order_id == "qe-intent-3"


def test_alpaca_adapter_replaces_limit_order(tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["payload"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(
            200,
            json={
                "id": "alpaca-order-4b",
                "client_order_id": "qe-intent-4b",
                "symbol": "AAPL",
                "asset_class": "us_equity",
                "side": "buy",
                "type": "limit",
                "time_in_force": "day",
                "qty": "3",
                "filled_qty": "0",
                "limit_price": "98.5",
                "status": "accepted",
                "updated_at": "2026-03-19T10:12:00Z",
            },
        )

    adapter = AlpacaBrokerAdapter(_settings(tmp_path), transport=httpx.MockTransport(handler))
    result = adapter.replace_order(
        BrokerReplaceRequest(
            provider_key="alpaca-paper",
            account_ref="paper-main",
            environment="paper",
            broker_order_id="alpaca-order-4",
            client_order_id="qe-intent-4b",
            symbol="AAPL",
            instrument_id=None,
            instrument_key="equity:AAPL",
            underlying_symbol=None,
            asset_type="equity",
            position_effect="open",
            side="buy",
            order_type="limit",
            time_in_force="day",
            quantity=3,
            reference_price=98.0,
            requested_notional=295.5,
            limit_price=98.5,
            stop_price=None,
        ),
        _current_order("alpaca-order-4"),
    )

    assert captured["method"] == "PATCH"
    assert captured["path"] == "/v2/orders/alpaca-order-4"
    assert captured["payload"] == {
        "qty": "3",
        "time_in_force": "day",
        "client_order_id": "qe-intent-4b",
        "limit_price": "98.5",
    }
    assert result.previous_order_status == "replaced"
    assert result.replacement_order.broker_order_id == "alpaca-order-4b"


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'alpaca-broker.db'}",
        alpaca_api_key="paper-key",
        alpaca_api_secret="paper-secret",
        alpaca_paper_base_url="https://paper.example.com",
    )


def _current_order(order_id: str) -> BrokerOrderState:
    return BrokerOrderState(
        broker_order_id=order_id,
        client_order_id="qe-intent-3" if order_id == "alpaca-order-3" else "qe-intent-4",
        symbol="AAPL",
        instrument_id=None,
        instrument_key="equity:AAPL",
        underlying_symbol=None,
        asset_type="equity",
        position_effect="open",
        side="buy",
        order_type="limit",
        time_in_force="day",
        quantity=1.0,
        filled_quantity=0.0,
        requested_notional=99.0,
        avg_fill_price=None,
        limit_price=99.0,
        stop_price=None,
        status="submitted",
        broker_updated_at=datetime(2026, 3, 19, 10, 0, tzinfo=UTC),
        raw_payload={"adapter": "alpaca"},
    )
