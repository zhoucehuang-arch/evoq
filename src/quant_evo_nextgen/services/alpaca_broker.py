from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import httpx

from quant_evo_nextgen.config import Settings
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


OPEN_ORDER_STATUSES = {"accepted", "submitted", "partially_filled"}
OPTION_CONTRACT_MULTIPLIER = 100.0


def _coerce_float(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return default
    return float(value)


def _coerce_int(value: Any, default: int = 0) -> int:
    if value in (None, ""):
        return default
    return int(value)


def _coerce_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
    if not value:
        return datetime.now(tz=UTC)
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _format_decimal(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return format(Decimal(str(value)).normalize(), "f")


def _asset_type_from_alpaca(payload: dict[str, Any]) -> tuple[str, bool]:
    asset_class = str(payload.get("asset_class") or payload.get("class") or "").lower()
    if asset_class == "us_option":
        return "option", True
    if asset_class == "crypto":
        return "crypto", True
    if asset_class == "us_equity":
        return "equity", False
    return "equity", False


def _infer_underlying_symbol(symbol: str) -> str | None:
    normalized = symbol.upper()
    if len(normalized) < 16:
        return None
    suffix = normalized[-15:]
    if suffix[:6].isdigit() and suffix[6] in {"C", "P"} and suffix[7:].isdigit():
        return normalized[:-15] or None
    return None


def _position_effect_from_alpaca(payload: dict[str, Any]) -> str:
    intent = str(payload.get("position_intent") or payload.get("position_effect") or "").lower()
    if intent in {"buy_to_open", "sell_to_open", "open", "opening"}:
        return "open"
    if intent in {"buy_to_close", "sell_to_close", "buy_to_cover", "close", "closing"}:
        return "close"
    return "auto"


def _normalize_order_status(status: str) -> str:
    normalized = status.lower()
    if normalized in {"filled", "partially_filled", "canceled", "replaced", "rejected", "expired"}:
        return normalized
    if normalized in {
        "accepted",
        "accepted_for_bidding",
        "calculated",
        "done_for_day",
        "held",
        "new",
        "pending_cancel",
        "pending_new",
        "pending_replace",
        "stopped",
    }:
        return "submitted"
    return normalized


def alpaca_capability_hint_from_account(
    account: dict[str, Any],
    *,
    provider_key: str,
    account_ref: str,
    environment: str,
) -> dict[str, Any]:
    options_level = max(
        _coerce_int(account.get("options_trading_level"), 0),
        _coerce_int(account.get("options_approved_level"), 0),
    )
    shorting_enabled = bool(account.get("shorting_enabled"))
    multiplier = _coerce_float(account.get("multiplier"), 1.0)
    account_mode = "paper" if environment == "paper" else "cash"
    if shorting_enabled or multiplier > 1.0:
        account_mode = "margin"
    return {
        "capability_key": f"{provider_key}:alpaca:{environment}",
        "provider_key": provider_key,
        "broker_adapter": "alpaca",
        "account_ref": account_ref,
        "environment": environment,
        "account_mode": account_mode,
        "supports_equities": True,
        "supports_etfs": True,
        "supports_fractional": True,
        "supports_short": shorting_enabled,
        "supports_margin": shorting_enabled or multiplier > 1.0,
        "supports_options": options_level > 0,
        "supports_multi_leg_options": options_level >= 3,
        "supports_option_exercise": options_level > 0,
        "supports_option_assignment_events": options_level > 0,
        "supports_live_trading": environment != "paper",
        "supports_paper_trading": environment == "paper",
        "notes": (
            f"Seeded from Alpaca account state. options_level={options_level}, "
            f"shorting_enabled={shorting_enabled}, multiplier={multiplier:.2f}."
        ),
    }


class AlpacaBrokerAdapter:
    adapter_key = "alpaca"

    def __init__(
        self,
        settings: Settings,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.settings = settings
        self.transport = transport

    def execute_order(
        self,
        request: BrokerExecutionRequest,
        current_position: PositionState | None,
    ) -> BrokerExecutionResult:
        self._validate_request(request, current_position=current_position)
        order = self._request_json(
            "POST",
            "/v2/orders",
            environment=request.environment,
            json_body=self._build_submit_payload(request),
            success_codes={200},
        )
        normalized = self._normalize_order_state(order)
        return BrokerExecutionResult(
            broker_order_id=normalized.broker_order_id,
            client_order_id=normalized.client_order_id,
            order_status=normalized.status,
            filled_quantity=normalized.filled_quantity,
            avg_fill_price=normalized.avg_fill_price,
            broker_updated_at=normalized.broker_updated_at,
            raw_payload=normalized.raw_payload,
            resulting_position=None,
        )

    def sync_state(self, request: BrokerSyncRequest) -> BrokerSyncResult:
        account = self._request_json("GET", "/v2/account", environment=request.environment, success_codes={200})
        orders_payload = self._request_json(
            "GET",
            "/v2/orders",
            environment=request.environment,
            params={
                "status": "all" if request.full_sync else "open",
                "limit": "200",
                "direction": "desc",
                "nested": "true",
            },
            success_codes={200},
        )
        positions_payload = self._request_json("GET", "/v2/positions", environment=request.environment, success_codes={200})

        notes: list[str] = []
        normalized_orders: list[BrokerOrderState] = []
        for raw_order in orders_payload:
            if raw_order.get("legs") and not str(raw_order.get("client_order_id") or "").startswith("qe-"):
                notes.append(
                    f"Skipped unmanaged Alpaca multi-leg order {raw_order.get('id')} because it is outside the governed order lineage."
                )
                continue
            normalized_orders.append(self._normalize_order_state(raw_order))

        normalized_positions = [self._normalize_position_state(raw_position) for raw_position in positions_payload]
        long_market_value = abs(_coerce_float(account.get("long_market_value")))
        short_market_value = abs(_coerce_float(account.get("short_market_value")))

        if account.get("trade_suspended_by_user"):
            notes.append("Alpaca account is currently trade-suspended by the user.")
        if account.get("trading_blocked"):
            notes.append("Alpaca account reports trading_blocked=true.")
        if account.get("account_blocked"):
            notes.append("Alpaca account reports account_blocked=true.")

        return BrokerSyncResult(
            account_state=BrokerAccountState(
                provider_key=request.provider_key,
                account_ref=request.account_ref,
                environment=request.environment,
                equity=_coerce_float(account.get("equity")),
                cash=_coerce_float(account.get("cash")),
                buying_power=_coerce_float(account.get("buying_power"), _coerce_float(account.get("equity"))),
                gross_exposure=round(long_market_value + short_market_value, 8),
                net_exposure=round(long_market_value - short_market_value, 8),
                positions_count=len(normalized_positions),
                open_orders_count=sum(1 for order in normalized_orders if order.status in OPEN_ORDER_STATUSES),
                source_captured_at=_coerce_datetime(account.get("updated_at") or account.get("created_at")),
                source_age_seconds=0,
                raw_payload={
                    "adapter": self.adapter_key,
                    "account": account,
                    "capability_hint": alpaca_capability_hint_from_account(
                        account,
                        provider_key=request.provider_key,
                        account_ref=request.account_ref,
                        environment=request.environment,
                    ),
                },
            ),
            orders=normalized_orders,
            positions=normalized_positions,
            notes=notes,
            raw_payload={
                "adapter": self.adapter_key,
                "orders_requested_status": "all" if request.full_sync else "open",
                "orders_returned": len(orders_payload),
                "orders_synced": len(normalized_orders),
                "positions_synced": len(normalized_positions),
            },
        )

    def cancel_order(
        self,
        request: BrokerCancelRequest,
        current_order: BrokerOrderState,
    ) -> BrokerCancelResult:
        self._request_json(
            "DELETE",
            f"/v2/orders/{request.broker_order_id}",
            environment=request.environment,
            success_codes={204},
        )
        current_time = datetime.now(tz=UTC)
        raw_payload = dict(current_order.raw_payload)
        raw_payload["adapter"] = self.adapter_key
        raw_payload["cancel_reason"] = request.reason
        raw_payload["cancel_requested_at"] = current_time.isoformat()
        return BrokerCancelResult(
            broker_order_id=request.broker_order_id,
            client_order_id=request.client_order_id,
            order_status="canceled",
            broker_updated_at=current_time,
            raw_payload=raw_payload,
        )

    def replace_order(
        self,
        request: BrokerReplaceRequest,
        current_order: BrokerOrderState,
    ) -> BrokerReplaceResult:
        if request.order_type != current_order.order_type:
            raise ValueError("Alpaca replace only supports quantity and price edits without changing order_type.")
        payload = {
            "qty": _format_decimal(request.quantity),
            "time_in_force": request.time_in_force,
            "client_order_id": request.client_order_id,
        }
        if request.order_type in {"limit", "stop_limit"} and request.limit_price is None:
            raise ValueError("Alpaca replace requires limit_price for limit or stop_limit orders.")
        if request.order_type in {"stop", "stop_limit"} and request.stop_price is None:
            raise ValueError("Alpaca replace requires stop_price for stop or stop_limit orders.")
        if request.limit_price is not None:
            payload["limit_price"] = _format_decimal(request.limit_price)
        if request.stop_price is not None:
            payload["stop_price"] = _format_decimal(request.stop_price)

        order = self._request_json(
            "PATCH",
            f"/v2/orders/{request.broker_order_id}",
            environment=request.environment,
            json_body=payload,
            success_codes={200},
        )
        normalized = self._normalize_order_state(order)
        previous_raw_payload = dict(current_order.raw_payload)
        previous_raw_payload["adapter"] = self.adapter_key
        previous_raw_payload["replacement_requested_at"] = datetime.now(tz=UTC).isoformat()
        return BrokerReplaceResult(
            previous_order_status="replaced",
            previous_broker_updated_at=normalized.broker_updated_at,
            previous_raw_payload=previous_raw_payload,
            replacement_order=normalized,
        )

    def _validate_request(
        self,
        request: BrokerExecutionRequest,
        *,
        current_position: PositionState | None,
    ) -> None:
        if request.asset_type not in {"equity", "etf", "leveraged_etf", "inverse_etf", "option"}:
            raise ValueError(f"Alpaca adapter does not support asset_type `{request.asset_type}` yet.")
        if request.order_type in {"limit", "stop_limit"} and request.limit_price is None:
            raise ValueError("Alpaca limit or stop_limit orders require limit_price.")
        if request.order_type in {"stop", "stop_limit"} and request.stop_price is None:
            raise ValueError("Alpaca stop or stop_limit orders require stop_price.")
        if request.legs:
            if request.asset_type != "option":
                raise ValueError("Alpaca multi-leg execution only supports option orders.")
            if float(request.quantity).is_integer() is False:
                raise ValueError("Alpaca multi-leg option orders require whole-contract quantity.")
            if request.order_type not in {"market", "limit"}:
                raise ValueError("Alpaca multi-leg option orders support market or limit orders only.")
            for leg in request.legs:
                if leg.asset_type != "option":
                    raise ValueError("Alpaca multi-leg option orders require every leg to be an option.")
                if float(leg.ratio_quantity).is_integer() is False:
                    raise ValueError("Alpaca multi-leg option legs require whole-number ratio quantities.")
                if leg.position_effect == "auto":
                    raise ValueError("Alpaca multi-leg option legs require explicit position_effect values.")
            return
        if request.asset_type == "option":
            if float(request.quantity).is_integer() is False:
                raise ValueError("Alpaca option orders require whole-contract quantity.")
            if request.side == "buy" and request.position_effect not in {"open", "increase", "close", "reduce"}:
                raise ValueError("Alpaca option orders require an explicit open/increase or close/reduce position_effect.")
            if request.side == "sell" and request.position_effect not in {"open", "increase", "close", "reduce"}:
                raise ValueError("Alpaca option orders require an explicit open/increase or close/reduce position_effect.")
            if (
                request.side == "sell"
                and request.position_effect in {"close", "reduce"}
                and (current_position is None or current_position.asset_type != "option" or current_position.direction != "long")
            ):
                raise ValueError("Cannot submit option sell-close because no active long option position is tracked.")
            if (
                request.side == "buy"
                and request.position_effect in {"close", "reduce"}
                and (current_position is None or current_position.asset_type != "option" or current_position.direction != "short")
            ):
                raise ValueError("Cannot submit option buy-close because no active short option position is tracked.")

    def _build_submit_payload(self, request: BrokerExecutionRequest) -> dict[str, Any]:
        if request.legs:
            payload: dict[str, Any] = {
                "order_class": "mleg",
                "type": request.order_type,
                "time_in_force": request.time_in_force,
                "qty": _format_decimal(request.quantity),
                "client_order_id": request.client_order_id,
                "legs": [
                    {
                        "symbol": leg.symbol.upper(),
                        "ratio_qty": str(int(leg.ratio_quantity)),
                        "side": leg.side,
                        "position_intent": self._position_intent_for_option_leg(leg.side, leg.position_effect),
                    }
                    for leg in request.legs
                ],
            }
            if request.limit_price is not None:
                payload["limit_price"] = _format_decimal(request.limit_price)
            if request.stop_price is not None:
                payload["stop_price"] = _format_decimal(request.stop_price)
            return payload
        payload: dict[str, Any] = {
            "symbol": request.symbol.upper(),
            "side": request.side,
            "type": request.order_type,
            "time_in_force": request.time_in_force,
            "qty": _format_decimal(request.quantity),
            "client_order_id": request.client_order_id,
        }
        if request.asset_type == "option":
            payload["position_intent"] = self._position_intent_for_option_leg(request.side, request.position_effect)
        if request.limit_price is not None:
            payload["limit_price"] = _format_decimal(request.limit_price)
        if request.stop_price is not None:
            payload["stop_price"] = _format_decimal(request.stop_price)
        return payload

    def _position_intent_for_option_leg(self, side: str, position_effect: str) -> str:
        normalized_effect = position_effect.lower()
        if normalized_effect in {"open", "increase"}:
            return "buy_to_open" if side == "buy" else "sell_to_open"
        if normalized_effect in {"close", "reduce"}:
            return "buy_to_close" if side == "buy" else "sell_to_close"
        raise ValueError(f"Unsupported option position_effect for Alpaca payload: {position_effect}")

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        environment: str,
        params: dict[str, str] | None = None,
        json_body: dict[str, Any] | None = None,
        success_codes: set[int],
    ) -> Any:
        base_url, key, secret = self._connection_settings(environment)
        try:
            with httpx.Client(
                base_url=base_url.rstrip("/"),
                headers={
                    "APCA-API-KEY-ID": key,
                    "APCA-API-SECRET-KEY": secret,
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                timeout=self.settings.alpaca_timeout_seconds,
                transport=self.transport,
            ) as client:
                response = client.request(method, path, params=params, json=json_body)
        except httpx.HTTPError as exc:
            raise ValueError(f"Alpaca request failed: {exc}") from exc

        if response.status_code not in success_codes:
            message = None
            try:
                payload = response.json()
                if isinstance(payload, dict):
                    message = payload.get("message") or payload.get("code")
            except ValueError:
                message = response.text
            if response.status_code in {401, 403}:
                raise ValueError("Alpaca authentication failed. Check API key, secret, and endpoint environment.")
            raise ValueError(f"Alpaca request failed with status {response.status_code}: {message or response.text}")
        if response.status_code == 204:
            return None
        return response.json()

    def _connection_settings(self, environment: str) -> tuple[str, str, str]:
        if environment.lower() == "paper":
            key = self.settings.alpaca_paper_api_key or self.settings.alpaca_api_key
            secret = self.settings.alpaca_paper_api_secret or self.settings.alpaca_api_secret
            base_url = self.settings.alpaca_paper_base_url
        else:
            key = self.settings.alpaca_live_api_key or self.settings.alpaca_api_key
            secret = self.settings.alpaca_live_api_secret or self.settings.alpaca_api_secret
            base_url = self.settings.alpaca_live_base_url
        if not key or not secret:
            raise ValueError(
                f"Alpaca credentials are missing for environment `{environment}`. "
                "Set the matching QE_ALPACA_* API key and secret values."
            )
        return base_url, key, secret

    def _normalize_order_state(self, payload: dict[str, Any]) -> BrokerOrderState:
        raw_legs = payload.get("legs") if isinstance(payload.get("legs"), list) else []
        asset_type, asset_type_exact = _asset_type_from_alpaca(payload)
        if raw_legs:
            asset_type = "option"
            asset_type_exact = True
        quantity = abs(_coerce_float(payload.get("qty")))
        filled_quantity = abs(_coerce_float(payload.get("filled_qty")))
        limit_price = _coerce_float(payload.get("limit_price")) if payload.get("limit_price") not in (None, "") else None
        stop_price = _coerce_float(payload.get("stop_price")) if payload.get("stop_price") not in (None, "") else None
        avg_fill_price = (
            _coerce_float(payload.get("filled_avg_price"))
            if payload.get("filled_avg_price") not in (None, "")
            else None
        )
        requested_notional = (
            _coerce_float(payload.get("notional"))
            if payload.get("notional") not in (None, "")
            else round(
                quantity
                * (limit_price or avg_fill_price or 0.0)
                * (OPTION_CONTRACT_MULTIPLIER if asset_type == "option" else 1.0),
                8,
            )
        )
        raw_payload = dict(payload)
        raw_payload["adapter"] = self.adapter_key
        raw_payload["asset_type_exact"] = asset_type_exact
        symbol = str(payload.get("symbol", "")).upper()
        if not symbol and raw_legs:
            symbol = str(raw_legs[0].get("symbol", "")).upper() or "MULTI_LEG_OPTION"
        return BrokerOrderState(
            broker_order_id=str(payload["id"]),
            client_order_id=payload.get("client_order_id"),
            symbol=symbol,
            instrument_id=str(payload.get("asset_id")) if payload.get("asset_id") else None,
            instrument_key=None,
            underlying_symbol=payload.get("underlying_symbol") or _infer_underlying_symbol(symbol),
            asset_type=asset_type,
            position_effect=_position_effect_from_alpaca(payload),
            side=str(payload.get("side", "")).lower(),
            order_type=str(payload.get("type", "")).lower(),
            time_in_force=str(payload.get("time_in_force", "")).lower(),
            quantity=quantity,
            filled_quantity=filled_quantity,
            requested_notional=requested_notional,
            avg_fill_price=avg_fill_price,
            limit_price=limit_price,
            stop_price=stop_price,
            status=_normalize_order_status(str(payload.get("status", "submitted"))),
            broker_updated_at=_coerce_datetime(payload.get("updated_at") or payload.get("submitted_at") or payload.get("created_at")),
            raw_payload=raw_payload,
        )

    def _normalize_position_state(self, payload: dict[str, Any]) -> PositionState:
        asset_type, asset_type_exact = _asset_type_from_alpaca(payload)
        raw_qty = _coerce_float(payload.get("qty"))
        side = str(payload.get("side", "")).lower()
        direction = "short" if side == "short" or raw_qty < 0 else "long"
        quantity = abs(raw_qty)
        market_price = _coerce_float(payload.get("current_price"), _coerce_float(payload.get("avg_entry_price")))
        raw_payload = dict(payload)
        raw_payload["adapter"] = self.adapter_key
        raw_payload["asset_type_exact"] = asset_type_exact
        raw_payload["sync_realized_pnl_known"] = False
        symbol = str(payload.get("symbol", "")).upper()
        return PositionState(
            strategy_spec_id="external-sync",
            symbol=symbol,
            asset_type=asset_type,
            direction=direction,
            quantity=quantity,
            avg_entry_price=_coerce_float(payload.get("avg_entry_price")),
            realized_pnl=0.0,
            instrument_id=str(payload.get("asset_id")) if payload.get("asset_id") else None,
            instrument_key=None,
            underlying_symbol=payload.get("underlying_symbol") or _infer_underlying_symbol(symbol),
            contract_multiplier=OPTION_CONTRACT_MULTIPLIER if asset_type == "option" else 1.0,
            leverage_ratio=1.0,
            market_price=market_price,
            raw_payload=raw_payload,
        )
