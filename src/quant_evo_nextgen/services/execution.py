from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from typing import Any, Callable, Sequence
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from quant_evo_nextgen.config import Settings
from quant_evo_nextgen.contracts.state import (
    AllocationPolicySummary,
    AllocationPolicyUpsert,
    BrokerAccountSnapshotCreate,
    BrokerAccountSnapshotSummary,
    BrokerCapabilitySummary,
    BrokerCapabilityUpsert,
    BrokerSyncRunCreate,
    BrokerSyncRunSummary,
    ExecutionReadinessSummary,
    InstrumentDefinitionSummary,
    InstrumentDefinitionUpsert,
    MarketSessionStateCreate,
    MarketSessionStateSummary,
    OrderCancelCreate,
    OrderIntentCreate,
    OrderLegSummary,
    OrderIntentSummary,
    OptionLifecycleEventCreate,
    OptionLifecycleEventSummary,
    OrderReplaceCreate,
    OrderRecordSummary,
    PositionRecordSummary,
    ProviderIncidentCreate,
    ProviderIncidentResolve,
    ProviderIncidentSummary,
    ReconciliationRunCreate,
    ReconciliationRunSummary,
)
from quant_evo_nextgen.db.models import (
    AllocationPolicyModel,
    BrokerAccountSnapshotModel,
    BrokerCapabilityModel,
    BrokerSyncRunModel,
    IncidentModel,
    InstrumentDefinitionModel,
    MarketCalendarStateModel,
    OrderIntentModel,
    OrderLegModel,
    OrderRecordModel,
    OptionLifecycleEventModel,
    OperatorOverrideModel,
    PositionRecordModel,
    ProviderIncidentModel,
    ProviderProfileModel,
    ReconciliationRunModel,
    StrategySpecModel,
)
from quant_evo_nextgen.services.broker import (
    BrokerAdapter,
    BrokerCancelRequest,
    BrokerExecutionLeg,
    BrokerExecutionRequest,
    BrokerExecutionResult,
    BrokerOrderState,
    BrokerReplaceRequest,
    BrokerSyncRequest,
    PaperBrokerAdapter,
    PositionState,
    broker_capability_defaults,
)
from quant_evo_nextgen.services.alpaca_broker import AlpacaBrokerAdapter


OPEN_PROVIDER_INCIDENT_STATUSES = ("open", "investigating", "mitigated")


@dataclass(slots=True)
class ResolvedOrderLeg:
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
class OrderCapitalProfile:
    current_maintenance_requirement: float
    projected_maintenance_requirement: float
    current_gross_exposure: float
    projected_gross_exposure: float
    net_cash_delta: float
    liquidity_release: float
    liquidity_need: float
    effective_notional: float


class ExecutionService:
    def __init__(
        self,
        session_factory: Callable[[], Session],
        settings: Settings,
        adapters: dict[str, BrokerAdapter] | None = None,
    ) -> None:
        self.session_factory = session_factory
        self.settings = settings
        self.adapters: dict[str, BrokerAdapter] = {
            "paper_sim": PaperBrokerAdapter(),
            "alpaca": AlpacaBrokerAdapter(settings),
        }
        if adapters:
            self.adapters.update(adapters)

    def record_market_session_state(
        self,
        payload: MarketSessionStateCreate | dict[str, Any],
    ) -> MarketSessionStateSummary:
        request = MarketSessionStateCreate.model_validate(payload)
        with self.session_factory() as session:
            market_state = MarketCalendarStateModel(
                market_calendar=request.market_calendar,
                market_timezone=request.market_timezone,
                session_label=request.session_label,
                is_market_open=request.is_market_open,
                trading_allowed=request.trading_allowed,
                next_open_at=request.next_open_at,
                next_close_at=request.next_close_at,
                created_by=request.created_by,
                origin_type=request.origin_type,
                origin_id=request.origin_id,
                status=request.status,
            )
            session.add(market_state)
            session.commit()
            session.refresh(market_state)
            return self._market_state_summary(market_state)

    def synthesize_market_session_state(
        self,
        *,
        now: datetime | None = None,
        created_by: str = "supervisor",
        origin_type: str = "workflow",
        origin_id: str | None = None,
    ) -> MarketSessionStateSummary:
        current_time = now or datetime.now(tz=UTC)
        payload = self._build_market_session_payload(
            current_time,
            market_calendar=self.settings.market_calendar,
            market_timezone=self.settings.market_timezone,
        )
        payload.update(
            {
                "created_by": created_by,
                "origin_type": origin_type,
                "origin_id": origin_id,
                "status": "observed",
            }
        )
        return self.record_market_session_state(payload)

    def list_market_session_states(
        self,
        *,
        limit: int = 20,
        market_calendar: str | None = None,
    ) -> list[MarketSessionStateSummary]:
        with self.session_factory() as session:
            query = select(MarketCalendarStateModel).order_by(MarketCalendarStateModel.created_at.desc()).limit(limit)
            if market_calendar:
                query = query.where(MarketCalendarStateModel.market_calendar == market_calendar)
            rows = session.scalars(query).all()
            return [self._market_state_summary(row) for row in rows]

    def record_broker_account_snapshot(
        self,
        payload: BrokerAccountSnapshotCreate | dict[str, Any],
    ) -> BrokerAccountSnapshotSummary:
        request = BrokerAccountSnapshotCreate.model_validate(payload)
        with self.session_factory() as session:
            provider = self._ensure_provider_profile(session, request.provider_key)
            captured_at = request.source_captured_at or datetime.now(tz=UTC)
            snapshot = BrokerAccountSnapshotModel(
                provider_key=request.provider_key,
                account_ref=request.account_ref,
                environment=request.environment,
                equity=request.equity,
                cash=request.cash,
                buying_power=request.buying_power,
                gross_exposure=request.gross_exposure,
                net_exposure=request.net_exposure,
                positions_count=request.positions_count,
                open_orders_count=request.open_orders_count,
                source_captured_at=captured_at,
                source_age_seconds=request.source_age_seconds,
                payload=request.payload,
                created_by=request.created_by,
                origin_type=request.origin_type,
                origin_id=request.origin_id,
                status=request.status,
            )
            session.add(snapshot)
            if provider.health_status == "unknown":
                provider.health_status = "healthy"
            session.commit()
            session.refresh(snapshot)
            return self._account_snapshot_summary(snapshot)

    def list_broker_account_snapshots(
        self,
        *,
        limit: int = 20,
        provider_key: str | None = None,
        environment: str | None = None,
    ) -> list[BrokerAccountSnapshotSummary]:
        with self.session_factory() as session:
            query = select(BrokerAccountSnapshotModel).order_by(BrokerAccountSnapshotModel.created_at.desc()).limit(limit)
            if provider_key:
                query = query.where(BrokerAccountSnapshotModel.provider_key == provider_key)
            if environment:
                query = query.where(BrokerAccountSnapshotModel.environment == environment)
            rows = session.scalars(query).all()
            return [self._account_snapshot_summary(row) for row in rows]

    def record_reconciliation_run(
        self,
        payload: ReconciliationRunCreate | dict[str, Any],
    ) -> ReconciliationRunSummary:
        request = ReconciliationRunCreate.model_validate(payload)
        with self.session_factory() as session:
            snapshot = self._resolve_snapshot(
                session,
                provider_key=request.provider_key,
                account_ref=request.account_ref,
                environment=request.environment,
                account_snapshot_id=request.account_snapshot_id,
            )
            provider = self._ensure_provider_profile(session, request.provider_key)

            broker_equity = request.broker_equity if request.broker_equity is not None else (snapshot.equity if snapshot else 0.0)
            broker_positions_count = (
                request.broker_positions_count if request.broker_positions_count is not None else (snapshot.positions_count if snapshot else 0)
            )
            broker_open_orders_count = (
                request.broker_open_orders_count
                if request.broker_open_orders_count is not None
                else (snapshot.open_orders_count if snapshot else 0)
            )

            equity_delta_abs = round(abs(request.internal_equity - broker_equity), 8)
            equity_base = max(abs(broker_equity), abs(request.internal_equity), 1e-9)
            equity_delta_pct = round((equity_delta_abs / equity_base) * 100.0, 6)
            position_delta_count = abs(request.internal_positions_count - broker_positions_count)
            order_delta_count = abs(request.internal_open_orders_count - broker_open_orders_count)

            notes = list(request.notes)
            status, blocking_reason = self._evaluate_reconciliation(
                snapshot=snapshot,
                equity_delta_pct=equity_delta_pct,
                position_delta_count=position_delta_count,
                order_delta_count=order_delta_count,
                equity_warning_pct=request.equity_warning_pct,
                equity_block_pct=request.equity_block_pct,
                notes=notes,
            )

            halt_triggered = False
            if status == "blocked":
                provider.health_status = "degraded"
                if request.trigger_halt_on_blocked:
                    halt_triggered = self._ensure_trading_halt(
                        session,
                        provider_key=request.provider_key,
                        reason=blocking_reason or "Reconciliation is blocked.",
                        created_by=request.created_by,
                        origin_type=request.origin_type,
                        origin_id=request.origin_id,
                    )

            reconciliation = ReconciliationRunModel(
                provider_key=request.provider_key,
                account_ref=request.account_ref,
                account_snapshot_id=snapshot.id if snapshot else request.account_snapshot_id,
                environment=request.environment,
                internal_equity=request.internal_equity,
                broker_equity=broker_equity,
                equity_delta_abs=equity_delta_abs,
                equity_delta_pct=equity_delta_pct,
                internal_positions_count=request.internal_positions_count,
                broker_positions_count=broker_positions_count,
                internal_open_orders_count=request.internal_open_orders_count,
                broker_open_orders_count=broker_open_orders_count,
                position_delta_count=position_delta_count,
                order_delta_count=order_delta_count,
                blocking_reason=blocking_reason,
                notes=notes,
                checked_at=request.checked_at or datetime.now(tz=UTC),
                halt_triggered=halt_triggered,
                created_by=request.created_by,
                origin_type=request.origin_type,
                origin_id=request.origin_id,
                status=status,
            )
            session.add(reconciliation)
            session.commit()
            session.refresh(reconciliation)
            return self._reconciliation_summary(reconciliation)

    def list_reconciliation_runs(
        self,
        *,
        limit: int = 20,
        provider_key: str | None = None,
        statuses: Sequence[str] | None = None,
    ) -> list[ReconciliationRunSummary]:
        with self.session_factory() as session:
            query = select(ReconciliationRunModel).order_by(ReconciliationRunModel.checked_at.desc()).limit(limit)
            if provider_key:
                query = query.where(ReconciliationRunModel.provider_key == provider_key)
            if statuses:
                query = query.where(ReconciliationRunModel.status.in_(list(statuses)))
            rows = session.scalars(query).all()
            return [self._reconciliation_summary(row) for row in rows]

    def create_provider_incident(
        self,
        payload: ProviderIncidentCreate | dict[str, Any],
    ) -> ProviderIncidentSummary:
        request = ProviderIncidentCreate.model_validate(payload)
        with self.session_factory() as session:
            provider = self._ensure_provider_profile(session, request.provider_key)
            provider.health_status = request.health_status
            incident = ProviderIncidentModel(
                provider_key=request.provider_key,
                title=request.title,
                summary=request.summary,
                severity=request.severity,
                created_by=request.created_by,
                origin_type=request.origin_type,
                origin_id=request.origin_id,
                status=request.status,
            )
            session.add(incident)
            session.commit()
            session.refresh(incident)
            return self._provider_incident_summary(incident)

    def resolve_provider_incident(
        self,
        incident_id: str,
        payload: ProviderIncidentResolve | dict[str, Any],
    ) -> ProviderIncidentSummary:
        request = ProviderIncidentResolve.model_validate(payload)
        with self.session_factory() as session:
            incident = session.get(ProviderIncidentModel, incident_id)
            if incident is None:
                raise ValueError(f"Provider incident not found: {incident_id}")

            incident.resolved_at = datetime.now(tz=UTC)
            incident.status = "resolved"
            if request.resolution_note:
                incident.summary = f"{incident.summary}\nResolution: {request.resolution_note}"

            remaining_open = session.scalar(
                select(func.count())
                .select_from(ProviderIncidentModel)
                .where(
                    ProviderIncidentModel.provider_key == incident.provider_key,
                    ProviderIncidentModel.status.in_(OPEN_PROVIDER_INCIDENT_STATUSES),
                )
            )
            provider = self._ensure_provider_profile(session, incident.provider_key)
            if not remaining_open:
                provider.health_status = request.health_status

            session.commit()
            session.refresh(incident)
            return self._provider_incident_summary(incident)

    def list_provider_incidents(
        self,
        *,
        limit: int = 20,
        open_only: bool = False,
        provider_key: str | None = None,
    ) -> list[ProviderIncidentSummary]:
        with self.session_factory() as session:
            query = select(ProviderIncidentModel).order_by(ProviderIncidentModel.detected_at.desc()).limit(limit)
            if open_only:
                query = query.where(ProviderIncidentModel.status.in_(OPEN_PROVIDER_INCIDENT_STATUSES))
            if provider_key:
                query = query.where(ProviderIncidentModel.provider_key == provider_key)
            rows = session.scalars(query).all()
            return [self._provider_incident_summary(row) for row in rows]

    def upsert_instrument_definition(
        self,
        payload: InstrumentDefinitionUpsert | dict[str, Any],
    ) -> InstrumentDefinitionSummary:
        request = InstrumentDefinitionUpsert.model_validate(payload)
        instrument_key = request.instrument_key or self._canonical_instrument_key(
            instrument_type=request.instrument_type,
            symbol=request.symbol,
            underlying_symbol=request.underlying_symbol,
            expiration_date=request.expiration_date.isoformat() if request.expiration_date else None,
            option_right=request.option_right,
            strike_price=request.strike_price,
        )
        display_symbol = request.display_symbol or self._display_symbol_for_instrument(
            instrument_type=request.instrument_type,
            symbol=request.symbol,
            underlying_symbol=request.underlying_symbol,
            expiration_date=request.expiration_date.isoformat() if request.expiration_date else None,
            option_right=request.option_right,
            strike_price=request.strike_price,
        )
        with self.session_factory() as session:
            instrument = session.scalar(
                select(InstrumentDefinitionModel).where(InstrumentDefinitionModel.instrument_key == instrument_key)
            )
            if instrument is None:
                instrument = InstrumentDefinitionModel(
                    instrument_key=instrument_key,
                    created_by=request.created_by,
                    origin_type=request.origin_type,
                    origin_id=request.origin_id,
                    status=request.status,
                )
                session.add(instrument)

            instrument.symbol = request.symbol.upper()
            instrument.display_symbol = display_symbol
            instrument.instrument_type = request.instrument_type
            instrument.venue = request.venue
            instrument.currency = request.currency.upper()
            instrument.underlying_symbol = request.underlying_symbol.upper() if request.underlying_symbol else None
            instrument.option_right = request.option_right
            instrument.option_style = request.option_style
            instrument.expiration_date = request.expiration_date
            instrument.strike_price = request.strike_price
            instrument.contract_multiplier = request.contract_multiplier
            instrument.leverage_ratio = request.leverage_ratio
            instrument.inverse_exposure = request.inverse_exposure
            instrument.is_marginable = request.is_marginable
            instrument.is_shortable = request.is_shortable
            instrument.metadata_payload = request.metadata_payload
            instrument.status = request.status

            session.commit()
            session.refresh(instrument)
            return self._instrument_summary(instrument)

    def list_instrument_definitions(
        self,
        *,
        limit: int = 50,
        instrument_type: str | None = None,
        underlying_symbol: str | None = None,
    ) -> list[InstrumentDefinitionSummary]:
        with self.session_factory() as session:
            query = select(InstrumentDefinitionModel).order_by(InstrumentDefinitionModel.updated_at.desc()).limit(limit)
            if instrument_type:
                query = query.where(InstrumentDefinitionModel.instrument_type == instrument_type)
            if underlying_symbol:
                query = query.where(InstrumentDefinitionModel.underlying_symbol == underlying_symbol.upper())
            rows = session.scalars(query).all()
            return [self._instrument_summary(row) for row in rows]

    def upsert_broker_capability(
        self,
        payload: BrokerCapabilityUpsert | dict[str, Any],
    ) -> BrokerCapabilitySummary:
        request = BrokerCapabilityUpsert.model_validate(payload)
        with self.session_factory() as session:
            capability = session.scalar(
                select(BrokerCapabilityModel).where(BrokerCapabilityModel.capability_key == request.capability_key)
            )
            if capability is None:
                capability = BrokerCapabilityModel(
                    capability_key=request.capability_key,
                    created_by=request.created_by,
                    origin_type=request.origin_type,
                    origin_id=request.origin_id,
                    status=request.status,
                )
                session.add(capability)

            capability.provider_key = request.provider_key
            capability.broker_adapter = request.broker_adapter
            capability.account_ref = request.account_ref
            capability.environment = request.environment
            capability.account_mode = request.account_mode
            capability.supports_equities = request.supports_equities
            capability.supports_etfs = request.supports_etfs
            capability.supports_fractional = request.supports_fractional
            capability.supports_short = request.supports_short
            capability.supports_margin = request.supports_margin
            capability.supports_options = request.supports_options
            capability.supports_multi_leg_options = request.supports_multi_leg_options
            capability.supports_option_exercise = request.supports_option_exercise
            capability.supports_option_assignment_events = request.supports_option_assignment_events
            capability.supports_live_trading = request.supports_live_trading
            capability.supports_paper_trading = request.supports_paper_trading
            capability.notes = request.notes
            capability.status = request.status

            session.commit()
            session.refresh(capability)
            return self._broker_capability_summary(capability)

    def list_broker_capabilities(
        self,
        *,
        limit: int = 50,
        provider_key: str | None = None,
        broker_adapter: str | None = None,
        environment: str | None = None,
    ) -> list[BrokerCapabilitySummary]:
        with self.session_factory() as session:
            query = select(BrokerCapabilityModel).order_by(BrokerCapabilityModel.updated_at.desc()).limit(limit)
            if provider_key:
                query = query.where(BrokerCapabilityModel.provider_key == provider_key)
            if broker_adapter:
                query = query.where(BrokerCapabilityModel.broker_adapter == broker_adapter)
            if environment:
                query = query.where(BrokerCapabilityModel.environment == environment)
            rows = session.scalars(query).all()
            return [self._broker_capability_summary(row) for row in rows]

    def upsert_allocation_policy(
        self,
        payload: AllocationPolicyUpsert | dict[str, Any],
    ) -> AllocationPolicySummary:
        request = AllocationPolicyUpsert.model_validate(payload)
        with self.session_factory() as session:
            if request.strategy_spec_id is not None and session.get(StrategySpecModel, request.strategy_spec_id) is None:
                raise ValueError(f"Strategy spec not found: {request.strategy_spec_id}")

            policy = session.scalar(
                select(AllocationPolicyModel).where(AllocationPolicyModel.policy_key == request.policy_key)
            )
            if policy is None:
                policy = AllocationPolicyModel(
                    policy_key=request.policy_key,
                    created_by=request.created_by,
                    origin_type=request.origin_type,
                    origin_id=request.origin_id,
                    status=request.status,
                )
                session.add(policy)

            policy.environment = request.environment
            policy.scope = request.scope
            policy.strategy_spec_id = request.strategy_spec_id
            policy.provider_key = request.provider_key
            policy.account_ref = request.account_ref
            policy.max_strategy_notional_pct = request.max_strategy_notional_pct
            policy.max_gross_exposure_pct = request.max_gross_exposure_pct
            policy.max_open_positions = request.max_open_positions
            policy.max_open_orders = request.max_open_orders
            policy.allow_short = request.allow_short
            policy.allow_fractional = request.allow_fractional
            policy.notes = request.notes
            policy.status = request.status
            session.commit()
            session.refresh(policy)
            return self._allocation_policy_summary(policy)

    def list_allocation_policies(
        self,
        *,
        limit: int = 20,
        environment: str | None = None,
    ) -> list[AllocationPolicySummary]:
        with self.session_factory() as session:
            query = select(AllocationPolicyModel).order_by(AllocationPolicyModel.updated_at.desc()).limit(limit)
            if environment:
                query = query.where(AllocationPolicyModel.environment == environment)
            rows = session.scalars(query).all()
            return [self._allocation_policy_summary(row) for row in rows]

    def submit_order_intent(
        self,
        payload: OrderIntentCreate | dict[str, Any],
    ) -> OrderIntentSummary:
        request = OrderIntentCreate.model_validate(payload)
        readiness = self.get_execution_readiness()
        provider_key = request.provider_key or self.settings.default_broker_provider_key
        account_ref = request.account_ref or self.settings.default_broker_account_ref
        broker_adapter = request.broker_adapter or self.settings.default_broker_adapter

        with self.session_factory() as session:
            strategy = session.get(StrategySpecModel, request.strategy_spec_id)
            if strategy is None:
                raise ValueError(f"Strategy spec not found: {request.strategy_spec_id}")

            instrument = self._resolve_or_register_instrument(session, request)
            effective_request = request.model_copy(
                update={
                    "symbol": instrument.symbol.upper() if instrument is not None else request.symbol.upper(),
                    "asset_type": instrument.instrument_type if instrument is not None else request.asset_type.lower(),
                    "instrument_id": instrument.id if instrument is not None else request.instrument_id,
                    "instrument_key": instrument.instrument_key if instrument is not None else request.instrument_key,
                }
            )
            resolved_legs = self._resolve_order_legs(
                session,
                request=effective_request,
                instrument=instrument,
            )
            policy = self._resolve_allocation_policy(
                session,
                policy_key=effective_request.allocation_policy_key,
                strategy_spec_id=effective_request.strategy_spec_id,
                environment=effective_request.environment,
                provider_key=provider_key,
                account_ref=account_ref,
            )
            latest_snapshot = self._resolve_snapshot(
                session,
                provider_key=provider_key,
                account_ref=account_ref,
                environment=effective_request.environment,
                account_snapshot_id=None,
            )
            broker_capability = self._effective_broker_capability(
                session,
                provider_key=provider_key,
                account_ref=account_ref,
                environment=effective_request.environment,
                broker_adapter=broker_adapter,
            )
            symbol_positions = self._active_positions_for_symbol(
                session,
                provider_key=provider_key,
                account_ref=account_ref,
                environment=effective_request.environment,
                symbol=effective_request.symbol,
            )
            current_position = next(
                (
                    position
                    for position in symbol_positions
                    if position.strategy_spec_id == effective_request.strategy_spec_id and position.status == "active"
                ),
                None,
            )
            active_positions = self._active_positions(
                session,
                provider_key=provider_key,
                account_ref=account_ref,
                environment=effective_request.environment,
            )
            related_symbol_conflicts = self._related_symbol_conflicts(
                session,
                provider_key=provider_key,
                account_ref=account_ref,
                environment=effective_request.environment,
                strategy_spec_id=effective_request.strategy_spec_id,
                request_symbol=effective_request.symbol,
                order_legs=resolved_legs,
                instrument=instrument,
            )
            simulation_error: str | None = None
            try:
                capital_profile = self._build_order_capital_profile(
                    session,
                    provider_key=provider_key,
                    account_ref=account_ref,
                    environment=effective_request.environment,
                    request=effective_request,
                    active_positions=active_positions,
                    order_legs=resolved_legs,
                    allow_short=policy.allow_short if policy is not None else False,
                )
            except ValueError as exc:
                simulation_error = str(exc)
                requested_notional = self._parent_requested_notional(
                    request=effective_request,
                    instrument=instrument,
                    order_legs=resolved_legs,
                )
                capital_profile = OrderCapitalProfile(
                    current_maintenance_requirement=0.0,
                    projected_maintenance_requirement=0.0,
                    current_gross_exposure=0.0,
                    projected_gross_exposure=0.0,
                    net_cash_delta=0.0,
                    liquidity_release=0.0,
                    liquidity_need=0.0,
                    effective_notional=requested_notional,
                )
            else:
                requested_notional = self._parent_requested_notional(
                    request=effective_request,
                    instrument=instrument,
                    order_legs=resolved_legs,
                )
            open_orders_count = self._count_open_orders(
                session,
                provider_key=provider_key,
                account_ref=account_ref,
                environment=effective_request.environment,
            )

            decision_reason = simulation_error or self._validate_order_request(
                readiness=readiness,
                strategy=strategy,
                policy=policy,
                request=effective_request,
                instrument=instrument,
                broker_capability=broker_capability,
                requested_notional=requested_notional,
                latest_snapshot=latest_snapshot,
                active_positions=active_positions,
                open_orders_count=open_orders_count,
                current_position=current_position,
                symbol_positions=symbol_positions,
                related_symbol_conflicts=related_symbol_conflicts,
                order_legs=resolved_legs,
                broker_adapter=broker_adapter,
                capital_profile=capital_profile,
            )

            intent = OrderIntentModel(
                strategy_spec_id=effective_request.strategy_spec_id,
                allocation_policy_id=policy.id if policy is not None else None,
                provider_key=provider_key,
                account_ref=account_ref,
                environment=effective_request.environment,
                broker_adapter=broker_adapter,
                symbol=effective_request.symbol.upper(),
                instrument_id=effective_request.instrument_id,
                instrument_key=effective_request.instrument_key,
                underlying_symbol=instrument.underlying_symbol if instrument is not None else None,
                asset_type=effective_request.asset_type,
                position_effect=effective_request.position_effect,
                side=effective_request.side,
                order_type=effective_request.order_type,
                time_in_force=effective_request.time_in_force,
                quantity=effective_request.quantity,
                reference_price=effective_request.reference_price,
                requested_notional=requested_notional,
                limit_price=effective_request.limit_price,
                stop_price=effective_request.stop_price,
                requested_at=datetime.now(tz=UTC),
                decision_reason=decision_reason,
                rationale=effective_request.rationale,
                signal_payload=effective_request.signal_payload,
                created_by=effective_request.created_by,
                origin_type=effective_request.origin_type,
                origin_id=effective_request.origin_id,
                status="rejected" if decision_reason else "accepted",
            )
            session.add(intent)
            session.flush()
            order_legs = self._persist_order_legs(
                session,
                order_intent_id=intent.id,
                resolved_legs=resolved_legs,
                created_by=effective_request.created_by,
                origin_type=effective_request.origin_type,
                origin_id=effective_request.origin_id,
            )
            client_order_id = self._client_order_id(intent.id)

            if decision_reason:
                session.commit()
                session.refresh(intent)
                return self._order_intent_summary(intent, session=session)

            adapter = self.adapters.get(broker_adapter)
            if adapter is None:
                intent.status = "rejected"
                intent.decision_reason = f"Unsupported broker adapter: {broker_adapter}"
                session.commit()
                session.refresh(intent)
                return self._order_intent_summary(intent, session=session)

            current_position_instrument = (
                self._resolve_position_instrument(session, current_position)
                if current_position is not None
                else None
            )
            current_position_state = (
                PositionState(
                    strategy_spec_id=current_position.strategy_spec_id,
                    symbol=current_position.symbol,
                    asset_type=current_position.asset_type,
                    direction=current_position.direction,
                    quantity=current_position.quantity,
                    avg_entry_price=current_position.avg_entry_price,
                    realized_pnl=current_position.realized_pnl,
                    instrument_id=current_position.instrument_id,
                    instrument_key=current_position.instrument_key,
                    underlying_symbol=current_position.underlying_symbol,
                    contract_multiplier=self._contract_multiplier(current_position_instrument, current_position.asset_type),
                    leverage_ratio=self._leverage_ratio(current_position_instrument, current_position.asset_type),
                )
                if current_position is not None
                else None
            )

            try:
                if broker_adapter == "paper_sim" and len(resolved_legs) > 1:
                    result = self._execute_paper_multi_leg_fill(
                        session,
                        request=effective_request,
                        provider_key=provider_key,
                        account_ref=account_ref,
                        order_legs=resolved_legs,
                        allow_short=policy.allow_short if policy is not None else False,
                        client_order_id=client_order_id,
                    )
                else:
                    result = adapter.execute_order(
                        BrokerExecutionRequest(
                            order_intent_id=intent.id,
                            client_order_id=client_order_id,
                            strategy_spec_id=effective_request.strategy_spec_id,
                            provider_key=provider_key,
                            account_ref=account_ref,
                            environment=effective_request.environment,
                            symbol=effective_request.symbol.upper(),
                            instrument_id=effective_request.instrument_id,
                            instrument_key=effective_request.instrument_key,
                            underlying_symbol=instrument.underlying_symbol if instrument is not None else None,
                            asset_type=effective_request.asset_type,
                            position_effect=effective_request.position_effect,
                            side=effective_request.side,
                            order_type=effective_request.order_type,
                            time_in_force=effective_request.time_in_force,
                            quantity=effective_request.quantity,
                            reference_price=effective_request.reference_price,
                            requested_notional=requested_notional,
                            contract_multiplier=self._contract_multiplier(instrument, effective_request.asset_type),
                            leverage_ratio=self._leverage_ratio(instrument, effective_request.asset_type),
                            limit_price=effective_request.limit_price,
                            stop_price=effective_request.stop_price,
                            allow_short=(
                                (policy.allow_short if policy is not None else False)
                                or (
                                    effective_request.asset_type == "option"
                                    and effective_request.side == "sell"
                                    and effective_request.position_effect in {"open", "increase"}
                                )
                            ),
                            legs=tuple(
                                BrokerExecutionLeg(
                                    leg_index=leg.leg_index,
                                    symbol=leg.symbol,
                                    instrument_id=leg.instrument_id,
                                    instrument_key=leg.instrument_key,
                                    underlying_symbol=leg.underlying_symbol,
                                    asset_type=leg.asset_type,
                                    side=leg.side,
                                    position_effect=leg.position_effect,
                                    quantity=leg.quantity,
                                    ratio_quantity=leg.ratio_quantity,
                                    reference_price=leg.reference_price,
                                    requested_notional=leg.requested_notional,
                                )
                                for leg in resolved_legs
                            ),
                        ),
                        current_position_state,
                    )
            except ValueError as exc:
                intent.status = "rejected"
                intent.decision_reason = str(exc)
                session.commit()
                session.refresh(intent)
                return self._order_intent_summary(intent, session=session)

            order_record = OrderRecordModel(
                order_intent_id=intent.id,
                strategy_spec_id=effective_request.strategy_spec_id,
                provider_key=provider_key,
                account_ref=account_ref,
                environment=effective_request.environment,
                broker_order_id=result.broker_order_id,
                client_order_id=result.client_order_id,
                symbol=effective_request.symbol.upper(),
                instrument_id=effective_request.instrument_id,
                instrument_key=effective_request.instrument_key,
                underlying_symbol=instrument.underlying_symbol if instrument is not None else None,
                asset_type=effective_request.asset_type,
                position_effect=effective_request.position_effect,
                side=effective_request.side,
                order_type=effective_request.order_type,
                time_in_force=effective_request.time_in_force,
                quantity=effective_request.quantity,
                filled_quantity=result.filled_quantity,
                requested_notional=requested_notional,
                avg_fill_price=result.avg_fill_price,
                limit_price=effective_request.limit_price,
                stop_price=effective_request.stop_price,
                submitted_at=datetime.now(tz=UTC),
                broker_updated_at=result.broker_updated_at,
                raw_payload=result.raw_payload,
                created_by=effective_request.created_by,
                origin_type=effective_request.origin_type,
                origin_id=effective_request.origin_id,
                status=result.order_status,
            )
            session.add(order_record)
            session.flush()
            for leg in order_legs:
                leg.order_record_id = order_record.id

            intent.status = result.order_status
            intent.decision_reason = "Accepted by execution policy and submitted to broker adapter."

            self._apply_position_update(
                session,
                current_position=current_position,
                result=result,
                request=effective_request,
                provider_key=provider_key,
                account_ref=account_ref,
            )
            self._record_projected_snapshot(
                session,
                provider_key=provider_key,
                account_ref=account_ref,
                environment=effective_request.environment,
                source_snapshot=latest_snapshot,
                created_by=effective_request.created_by,
                origin_type="broker-adapter",
                origin_id=order_record.id,
            )

            session.commit()
            session.refresh(intent)
            return self._order_intent_summary(intent, session=session)

    def sync_broker_state(
        self,
        payload: BrokerSyncRunCreate | dict[str, Any],
    ) -> BrokerSyncRunSummary:
        request = BrokerSyncRunCreate.model_validate(payload)
        broker_adapter = request.broker_adapter or self.settings.default_broker_adapter
        adapter = self.adapters.get(broker_adapter)
        if adapter is None:
            raise ValueError(f"Unsupported broker adapter: {broker_adapter}")

        started_at = datetime.now(tz=UTC)
        sync_result = adapter.sync_state(
            BrokerSyncRequest(
                provider_key=request.provider_key,
                account_ref=request.account_ref,
                environment=request.environment,
                full_sync=request.full_sync,
            )
        )
        completed_at = datetime.now(tz=UTC)

        with self.session_factory() as session:
            provider = self._ensure_provider_profile(session, request.provider_key)
            provider.health_status = "healthy"
            capability_hint: dict[str, Any] | None = None
            if isinstance(sync_result.account_state.raw_payload, dict):
                hint = sync_result.account_state.raw_payload.get("capability_hint")
                if isinstance(hint, dict):
                    capability_hint = hint

            snapshot = BrokerAccountSnapshotModel(
                provider_key=sync_result.account_state.provider_key,
                account_ref=sync_result.account_state.account_ref,
                environment=sync_result.account_state.environment,
                equity=sync_result.account_state.equity,
                cash=sync_result.account_state.cash,
                buying_power=sync_result.account_state.buying_power,
                gross_exposure=sync_result.account_state.gross_exposure,
                net_exposure=sync_result.account_state.net_exposure,
                positions_count=sync_result.account_state.positions_count,
                open_orders_count=sync_result.account_state.open_orders_count,
                source_captured_at=sync_result.account_state.source_captured_at,
                source_age_seconds=sync_result.account_state.source_age_seconds,
                payload=sync_result.account_state.raw_payload,
                created_by=request.created_by,
                origin_type=request.origin_type,
                origin_id=request.origin_id,
                status="captured",
            )
            session.add(snapshot)
            session.flush()

            if capability_hint is not None:
                self._upsert_broker_capability_model(
                    session,
                    provider_key=request.provider_key,
                    account_ref=request.account_ref,
                    environment=request.environment,
                    broker_adapter=broker_adapter,
                    payload=capability_hint,
                    created_by=request.created_by,
                    origin_type=request.origin_type,
                    origin_id=request.origin_id,
                )

            sync_run = BrokerSyncRunModel(
                provider_key=request.provider_key,
                account_ref=request.account_ref,
                environment=request.environment,
                broker_adapter=broker_adapter,
                sync_scope="full" if request.full_sync else "incremental",
                account_snapshot_id=snapshot.id,
                notes=[],
                raw_payload=sync_result.raw_payload,
                started_at=started_at,
                completed_at=completed_at,
                created_by=request.created_by,
                origin_type=request.origin_type,
                origin_id=request.origin_id,
                status="synchronized",
            )
            session.add(sync_run)
            session.flush()

            notes = list(sync_result.notes)
            managed_order_ids: set[str] = set()
            synced_orders_count = 0
            unmanaged_orders_count = 0
            for order_state in sync_result.orders:
                order_record = self._upsert_order_from_sync(
                    session,
                    order_state=order_state,
                    provider_key=request.provider_key,
                    account_ref=request.account_ref,
                    environment=request.environment,
                    sync_run_id=sync_run.id,
                    created_by=request.created_by,
                    origin_type=request.origin_type,
                    origin_id=request.origin_id,
                )
                if order_record is None:
                    unmanaged_orders_count += 1
                    notes.append(
                        f"Unmanaged external order skipped: {order_state.symbol} / {order_state.broker_order_id}"
                    )
                    continue
                managed_order_ids.add(order_record.id)
                synced_orders_count += 1

            managed_position_ids: set[str] = set()
            synced_positions_count = 0
            unmanaged_positions_count = 0
            for position_state in sync_result.positions:
                position_record = self._upsert_position_from_sync(
                    session,
                    position_state=position_state,
                    provider_key=request.provider_key,
                    account_ref=request.account_ref,
                    environment=request.environment,
                    sync_run_id=sync_run.id,
                    created_by=request.created_by,
                    origin_type=request.origin_type,
                    origin_id=request.origin_id,
                )
                if position_record is None:
                    unmanaged_positions_count += 1
                    notes.append(f"Unmanaged external position skipped: {position_state.symbol}")
                    continue
                managed_position_ids.add(position_record.id)
                synced_positions_count += 1

            missing_internal_orders_count = 0
            missing_internal_positions_count = 0
            if request.full_sync:
                missing_internal_orders_count = self._mark_missing_internal_orders(
                    session,
                    provider_key=request.provider_key,
                    account_ref=request.account_ref,
                    environment=request.environment,
                    synced_order_ids=managed_order_ids,
                    sync_run_id=sync_run.id,
                )
                missing_internal_positions_count = self._mark_missing_internal_positions(
                    session,
                    provider_key=request.provider_key,
                    account_ref=request.account_ref,
                    environment=request.environment,
                    synced_position_ids=managed_position_ids,
                    sync_run_id=sync_run.id,
                )

            sync_run.synced_orders_count = synced_orders_count
            sync_run.synced_positions_count = synced_positions_count
            sync_run.unmanaged_orders_count = unmanaged_orders_count
            sync_run.unmanaged_positions_count = unmanaged_positions_count
            sync_run.missing_internal_orders_count = missing_internal_orders_count
            sync_run.missing_internal_positions_count = missing_internal_positions_count
            sync_run.notes = notes
            if (
                unmanaged_orders_count
                or unmanaged_positions_count
                or missing_internal_orders_count
                or missing_internal_positions_count
                or notes
            ):
                sync_run.status = "warning"

            session.commit()
            session.refresh(sync_run)
            return self._broker_sync_run_summary(sync_run)

    def list_broker_sync_runs(
        self,
        *,
        limit: int = 20,
        provider_key: str | None = None,
    ) -> list[BrokerSyncRunSummary]:
        with self.session_factory() as session:
            query = select(BrokerSyncRunModel).order_by(BrokerSyncRunModel.started_at.desc()).limit(limit)
            if provider_key:
                query = query.where(BrokerSyncRunModel.provider_key == provider_key)
            rows = session.scalars(query).all()
            return [self._broker_sync_run_summary(row) for row in rows]

    def cancel_order(
        self,
        order_record_id: str,
        payload: OrderCancelCreate | dict[str, Any],
    ) -> OrderRecordSummary:
        request = OrderCancelCreate.model_validate(payload)
        with self.session_factory() as session:
            order_record = session.get(OrderRecordModel, order_record_id)
            if order_record is None:
                raise ValueError(f"Order record not found: {order_record_id}")

            if order_record.status not in {"accepted", "submitted", "partially_filled"}:
                raise ValueError(f"Order `{order_record_id}` cannot be canceled from status `{order_record.status}`.")

            intent = session.get(OrderIntentModel, order_record.order_intent_id)
            if intent is None:
                raise ValueError(f"Order intent not found for order `{order_record_id}`.")

            adapter = self.adapters.get(intent.broker_adapter)
            if adapter is None:
                raise ValueError(f"Unsupported broker adapter: {intent.broker_adapter}")

            current_state = self._broker_order_state_from_record(order_record)
            cancel_result = adapter.cancel_order(
                BrokerCancelRequest(
                    provider_key=order_record.provider_key,
                    account_ref=order_record.account_ref,
                    environment=order_record.environment,
                    broker_order_id=order_record.broker_order_id,
                    client_order_id=order_record.client_order_id,
                    reason=request.reason,
                ),
                current_state,
            )

            order_record.status = cancel_result.order_status
            order_record.broker_updated_at = cancel_result.broker_updated_at
            order_record.raw_payload = cancel_result.raw_payload
            intent.status = cancel_result.order_status
            intent.decision_reason = request.reason

            latest_snapshot = self._resolve_snapshot(
                session,
                provider_key=order_record.provider_key,
                account_ref=order_record.account_ref,
                environment=order_record.environment,
                account_snapshot_id=None,
            )
            self._record_projected_snapshot(
                session,
                provider_key=order_record.provider_key,
                account_ref=order_record.account_ref,
                environment=order_record.environment,
                source_snapshot=latest_snapshot,
                created_by=request.created_by,
                origin_type=request.origin_type,
                origin_id=order_record.id,
            )

            session.commit()
            session.refresh(order_record)
            return self._order_record_summary(order_record, session=session)

    def replace_order(
        self,
        order_record_id: str,
        payload: OrderReplaceCreate | dict[str, Any],
    ) -> OrderRecordSummary:
        request = OrderReplaceCreate.model_validate(payload)
        with self.session_factory() as session:
            order_record = session.get(OrderRecordModel, order_record_id)
            if order_record is None:
                raise ValueError(f"Order record not found: {order_record_id}")

            if order_record.status not in {"accepted", "submitted", "partially_filled"}:
                raise ValueError(f"Order `{order_record_id}` cannot be replaced from status `{order_record.status}`.")

            intent = session.get(OrderIntentModel, order_record.order_intent_id)
            if intent is None:
                raise ValueError(f"Order intent not found for order `{order_record_id}`.")

            strategy = session.get(StrategySpecModel, order_record.strategy_spec_id)
            if strategy is None:
                raise ValueError(f"Strategy spec not found: {order_record.strategy_spec_id}")

            adapter = self.adapters.get(intent.broker_adapter)
            if adapter is None:
                raise ValueError(f"Unsupported broker adapter: {intent.broker_adapter}")

            policy = self._resolve_allocation_policy(
                session,
                policy_key=None,
                strategy_spec_id=order_record.strategy_spec_id,
                environment=order_record.environment,
                provider_key=order_record.provider_key,
                account_ref=order_record.account_ref,
            )
            readiness = self.get_execution_readiness()
            latest_snapshot = self._resolve_snapshot(
                session,
                provider_key=order_record.provider_key,
                account_ref=order_record.account_ref,
                environment=order_record.environment,
                account_snapshot_id=None,
            )
            symbol_positions = self._active_positions_for_symbol(
                session,
                provider_key=order_record.provider_key,
                account_ref=order_record.account_ref,
                environment=order_record.environment,
                symbol=order_record.symbol,
            )
            current_position = next(
                (
                    position
                    for position in symbol_positions
                    if position.strategy_spec_id == order_record.strategy_spec_id and position.status == "active"
                ),
                None,
            )
            active_positions = self._active_positions(
                session,
                provider_key=order_record.provider_key,
                account_ref=order_record.account_ref,
                environment=order_record.environment,
            )
            open_orders_count = max(
                0,
                self._count_open_orders(
                    session,
                    provider_key=order_record.provider_key,
                    account_ref=order_record.account_ref,
                    environment=order_record.environment,
                )
                - 1,
            )
            replacement_request = OrderIntentCreate(
                strategy_spec_id=order_record.strategy_spec_id,
                symbol=order_record.symbol,
                side=order_record.side,
                quantity=request.quantity,
                reference_price=request.reference_price,
                instrument_id=order_record.instrument_id,
                instrument_key=order_record.instrument_key,
                asset_type=order_record.asset_type,
                position_effect=order_record.position_effect,
                order_type=request.order_type or order_record.order_type,
                time_in_force=request.time_in_force or order_record.time_in_force,
                provider_key=order_record.provider_key,
                account_ref=order_record.account_ref,
                environment=order_record.environment,
                broker_adapter=intent.broker_adapter,
                allocation_policy_key=None,
                limit_price=request.limit_price,
                stop_price=request.stop_price,
                rationale=request.rationale,
                created_by=request.created_by,
                origin_type=request.origin_type,
                origin_id=request.origin_id,
            )
            instrument = (
                session.get(InstrumentDefinitionModel, order_record.instrument_id)
                if order_record.instrument_id
                else None
            )
            broker_capability = self._effective_broker_capability(
                session,
                provider_key=order_record.provider_key,
                account_ref=order_record.account_ref,
                environment=order_record.environment,
                broker_adapter=intent.broker_adapter,
            )
            replacement_legs = self._resolve_order_legs(
                session,
                request=replacement_request,
                instrument=instrument,
            )
            requested_notional = self._parent_requested_notional(
                request=replacement_request,
                instrument=instrument,
                order_legs=replacement_legs,
            )
            related_symbol_conflicts = self._related_symbol_conflicts(
                session,
                provider_key=order_record.provider_key,
                account_ref=order_record.account_ref,
                environment=order_record.environment,
                strategy_spec_id=order_record.strategy_spec_id,
                request_symbol=replacement_request.symbol,
                order_legs=replacement_legs,
                instrument=instrument,
            )
            simulation_error: str | None = None
            try:
                capital_profile = self._build_order_capital_profile(
                    session,
                    provider_key=order_record.provider_key,
                    account_ref=order_record.account_ref,
                    environment=order_record.environment,
                    request=replacement_request,
                    active_positions=active_positions,
                    order_legs=replacement_legs,
                    allow_short=policy.allow_short,
                )
            except ValueError as exc:
                simulation_error = str(exc)
                capital_profile = OrderCapitalProfile(
                    current_maintenance_requirement=0.0,
                    projected_maintenance_requirement=0.0,
                    current_gross_exposure=0.0,
                    projected_gross_exposure=0.0,
                    net_cash_delta=0.0,
                    liquidity_release=0.0,
                    liquidity_need=0.0,
                    effective_notional=requested_notional,
                )
            decision_reason = simulation_error or self._validate_order_request(
                readiness=readiness,
                strategy=strategy,
                policy=policy,
                request=replacement_request,
                instrument=instrument,
                broker_capability=broker_capability,
                requested_notional=requested_notional,
                latest_snapshot=latest_snapshot,
                active_positions=active_positions,
                open_orders_count=open_orders_count,
                current_position=current_position,
                symbol_positions=symbol_positions,
                related_symbol_conflicts=related_symbol_conflicts,
                order_legs=replacement_legs,
                broker_adapter=intent.broker_adapter,
                capital_profile=capital_profile,
            )

            replacement_intent = OrderIntentModel(
                strategy_spec_id=order_record.strategy_spec_id,
                allocation_policy_id=policy.id,
                provider_key=order_record.provider_key,
                account_ref=order_record.account_ref,
                environment=order_record.environment,
                broker_adapter=intent.broker_adapter,
                symbol=order_record.symbol,
                instrument_id=order_record.instrument_id,
                instrument_key=order_record.instrument_key,
                underlying_symbol=order_record.underlying_symbol,
                asset_type=order_record.asset_type,
                position_effect=order_record.position_effect,
                side=order_record.side,
                order_type=replacement_request.order_type,
                time_in_force=replacement_request.time_in_force,
                quantity=replacement_request.quantity,
                reference_price=replacement_request.reference_price,
                requested_notional=requested_notional,
                limit_price=replacement_request.limit_price,
                stop_price=replacement_request.stop_price,
                requested_at=datetime.now(tz=UTC),
                decision_reason=decision_reason,
                rationale=replacement_request.rationale,
                signal_payload={},
                created_by=request.created_by,
                origin_type=request.origin_type,
                origin_id=request.origin_id,
                status="rejected" if decision_reason else "accepted",
            )
            session.add(replacement_intent)
            session.flush()
            replacement_leg_rows = self._persist_order_legs(
                session,
                order_intent_id=replacement_intent.id,
                resolved_legs=replacement_legs,
                created_by=request.created_by,
                origin_type=request.origin_type,
                origin_id=request.origin_id,
            )
            replacement_client_order_id = self._client_order_id(replacement_intent.id)

            if decision_reason:
                session.commit()
                raise ValueError(decision_reason)

            replace_result = adapter.replace_order(
                BrokerReplaceRequest(
                    provider_key=order_record.provider_key,
                    account_ref=order_record.account_ref,
                    environment=order_record.environment,
                    broker_order_id=order_record.broker_order_id,
                    client_order_id=replacement_client_order_id,
                    symbol=order_record.symbol,
                    instrument_id=order_record.instrument_id,
                    instrument_key=order_record.instrument_key,
                    underlying_symbol=order_record.underlying_symbol,
                    asset_type=order_record.asset_type,
                    position_effect=order_record.position_effect,
                    side=order_record.side,
                    order_type=replacement_request.order_type,
                    time_in_force=replacement_request.time_in_force,
                    quantity=replacement_request.quantity,
                    reference_price=replacement_request.reference_price,
                    requested_notional=requested_notional,
                    contract_multiplier=self._contract_multiplier(instrument, replacement_request.asset_type),
                    leverage_ratio=self._leverage_ratio(instrument, replacement_request.asset_type),
                    limit_price=replacement_request.limit_price,
                    stop_price=replacement_request.stop_price,
                ),
                self._broker_order_state_from_record(order_record),
            )

            order_record.status = replace_result.previous_order_status
            order_record.broker_updated_at = replace_result.previous_broker_updated_at
            order_record.raw_payload = replace_result.previous_raw_payload

            replacement_order = OrderRecordModel(
                order_intent_id=replacement_intent.id,
                strategy_spec_id=order_record.strategy_spec_id,
                provider_key=order_record.provider_key,
                account_ref=order_record.account_ref,
                environment=order_record.environment,
                broker_order_id=replace_result.replacement_order.broker_order_id,
                client_order_id=replace_result.replacement_order.client_order_id,
                symbol=replace_result.replacement_order.symbol,
                instrument_id=replace_result.replacement_order.instrument_id,
                instrument_key=replace_result.replacement_order.instrument_key,
                underlying_symbol=replace_result.replacement_order.underlying_symbol,
                asset_type=replace_result.replacement_order.asset_type,
                position_effect=replace_result.replacement_order.position_effect,
                side=replace_result.replacement_order.side,
                order_type=replace_result.replacement_order.order_type,
                time_in_force=replace_result.replacement_order.time_in_force,
                quantity=replace_result.replacement_order.quantity,
                filled_quantity=replace_result.replacement_order.filled_quantity,
                requested_notional=replace_result.replacement_order.requested_notional,
                avg_fill_price=replace_result.replacement_order.avg_fill_price,
                limit_price=replace_result.replacement_order.limit_price,
                stop_price=replace_result.replacement_order.stop_price,
                parent_order_record_id=order_record.id,
                submitted_at=datetime.now(tz=UTC),
                broker_updated_at=replace_result.replacement_order.broker_updated_at,
                raw_payload=replace_result.replacement_order.raw_payload,
                created_by=request.created_by,
                origin_type=request.origin_type,
                origin_id=request.origin_id,
                status=replace_result.replacement_order.status,
            )
            session.add(replacement_order)
            session.flush()
            for leg in replacement_leg_rows:
                leg.order_record_id = replacement_order.id
            replacement_intent.status = replace_result.replacement_order.status
            replacement_intent.decision_reason = "Replacement accepted by execution policy and submitted to broker."

            latest_snapshot = self._resolve_snapshot(
                session,
                provider_key=order_record.provider_key,
                account_ref=order_record.account_ref,
                environment=order_record.environment,
                account_snapshot_id=None,
            )
            self._record_projected_snapshot(
                session,
                provider_key=order_record.provider_key,
                account_ref=order_record.account_ref,
                environment=order_record.environment,
                source_snapshot=latest_snapshot,
                created_by=request.created_by,
                origin_type=request.origin_type,
                origin_id=replacement_order.id,
            )

            session.commit()
            session.refresh(replacement_order)
            return self._order_record_summary(replacement_order, session=session)

    def list_order_intents(
        self,
        *,
        limit: int = 20,
        statuses: Sequence[str] | None = None,
    ) -> list[OrderIntentSummary]:
        with self.session_factory() as session:
            query = select(OrderIntentModel).order_by(OrderIntentModel.created_at.desc()).limit(limit)
            if statuses:
                query = query.where(OrderIntentModel.status.in_(list(statuses)))
            rows = session.scalars(query).all()
            return [self._order_intent_summary(row, session=session) for row in rows]

    def list_order_records(
        self,
        *,
        limit: int = 20,
        statuses: Sequence[str] | None = None,
    ) -> list[OrderRecordSummary]:
        with self.session_factory() as session:
            query = select(OrderRecordModel).order_by(OrderRecordModel.created_at.desc()).limit(limit)
            if statuses:
                query = query.where(OrderRecordModel.status.in_(list(statuses)))
            rows = session.scalars(query).all()
            return [self._order_record_summary(row, session=session) for row in rows]

    def list_positions(
        self,
        *,
        limit: int = 20,
        active_only: bool = True,
    ) -> list[PositionRecordSummary]:
        with self.session_factory() as session:
            query = select(PositionRecordModel).order_by(PositionRecordModel.updated_at.desc()).limit(limit)
            if active_only:
                query = query.where(PositionRecordModel.status == "active")
            rows = session.scalars(query).all()
            return [self._position_summary(row) for row in rows]

    def record_option_lifecycle_event(
        self,
        payload: OptionLifecycleEventCreate | dict[str, Any],
    ) -> OptionLifecycleEventSummary:
        request = OptionLifecycleEventCreate.model_validate(payload)
        occurred_at = request.occurred_at or datetime.now(tz=UTC)

        with self.session_factory() as session:
            position = self._resolve_option_position_for_event(session, request=request)
            instrument = self._resolve_instrument_by_identity(
                session,
                instrument_id=request.instrument_id or (position.instrument_id if position is not None else None),
                instrument_key=request.instrument_key or (position.instrument_key if position is not None else None),
            )
            if instrument is None:
                raise ValueError("Option lifecycle event references an unknown instrument.")
            if instrument.instrument_type != "option":
                raise ValueError("Option lifecycle events require an option instrument.")

            quantity = request.quantity
            if quantity is None:
                quantity = position.quantity if position is not None else 0.0
            if quantity <= 0:
                raise ValueError("Option lifecycle event quantity must be positive.")

            state_applied = False
            review_required = False
            applied_position_id = position.id if position is not None else None
            resulting_symbol: str | None = None
            resulting_instrument_key: str | None = None
            event_price = request.event_price
            cash_flow = request.cash_flow
            notes = request.notes

            if request.event_type == "expiration" and position is not None and position.status == "active":
                event_price = 0.0 if event_price is None else event_price
                self._apply_option_terminal_event(
                    position=position,
                    instrument=instrument,
                    quantity=quantity,
                    event_price=event_price,
                    occurred_at=occurred_at,
                    event_label="expiration",
                    terminal_status="expired",
                )
                state_applied = True
            elif request.event_type in {"exercise", "assignment"} and position is not None and position.status == "active":
                try:
                    resulting_position, underlying_instrument, derived_cash_flow, auto_note = self._apply_option_conversion_event(
                        session,
                        request=request,
                        position=position,
                        instrument=instrument,
                        quantity=quantity,
                        occurred_at=occurred_at,
                    )
                    state_applied = True
                    applied_position_id = resulting_position.id if resulting_position is not None else position.id
                    resulting_symbol = underlying_instrument.symbol
                    resulting_instrument_key = underlying_instrument.instrument_key
                    event_price = 0.0 if event_price is None else event_price
                    cash_flow = derived_cash_flow if cash_flow is None else cash_flow
                    if notes is None:
                        notes = auto_note
                except ValueError as exc:
                    review_required = True
                    notes = notes or str(exc)
                    self._ensure_option_review_incident(
                        session,
                        request=request,
                        instrument=instrument,
                        occurred_at=occurred_at,
                    )
            else:
                review_required = True
                notes = notes or (
                    "This option lifecycle event was recorded durably but still needs explicit review because "
                    "automatic state application is not implemented for this event path yet."
                )
                self._ensure_option_review_incident(
                    session,
                    request=request,
                    instrument=instrument,
                    occurred_at=occurred_at,
                )

            event = OptionLifecycleEventModel(
                event_type=request.event_type,
                provider_key=request.provider_key,
                account_ref=request.account_ref,
                environment=request.environment,
                symbol=request.symbol.upper(),
                underlying_symbol=instrument.underlying_symbol,
                position_id=position.id if position is not None else request.position_id,
                strategy_spec_id=request.strategy_spec_id or (position.strategy_spec_id if position is not None else None),
                instrument_id=instrument.id,
                instrument_key=instrument.instrument_key,
                quantity=quantity,
                event_price=event_price,
                cash_flow=cash_flow,
                state_applied=state_applied,
                review_required=review_required,
                applied_position_id=applied_position_id,
                resulting_symbol=resulting_symbol,
                resulting_instrument_key=resulting_instrument_key,
                notes=notes,
                metadata_payload=request.metadata_payload,
                occurred_at=occurred_at,
                created_by=request.created_by,
                origin_type=request.origin_type,
                origin_id=request.origin_id,
                status="applied" if state_applied else "review_required",
            )
            session.add(event)
            session.commit()
            session.refresh(event)
            return self._option_lifecycle_event_summary(event)

    def list_option_lifecycle_events(
        self,
        *,
        limit: int = 20,
        event_types: Sequence[str] | None = None,
    ) -> list[OptionLifecycleEventSummary]:
        with self.session_factory() as session:
            query = select(OptionLifecycleEventModel).order_by(OptionLifecycleEventModel.occurred_at.desc()).limit(limit)
            if event_types:
                query = query.where(OptionLifecycleEventModel.event_type.in_(list(event_types)))
            rows = session.scalars(query).all()
            return [self._option_lifecycle_event_summary(row) for row in rows]

    def _resolve_option_position_for_event(
        self,
        session: Session,
        *,
        request: OptionLifecycleEventCreate,
    ) -> PositionRecordModel | None:
        if request.position_id:
            return session.get(PositionRecordModel, request.position_id)

        query = (
            select(PositionRecordModel)
            .where(
                PositionRecordModel.provider_key == request.provider_key,
                PositionRecordModel.account_ref == request.account_ref,
                PositionRecordModel.environment == request.environment,
                PositionRecordModel.status == "active",
            )
            .order_by(PositionRecordModel.updated_at.desc())
        )
        if request.instrument_id:
            query = query.where(PositionRecordModel.instrument_id == request.instrument_id)
        elif request.instrument_key:
            query = query.where(PositionRecordModel.instrument_key == request.instrument_key)
        else:
            return None

        rows = session.scalars(query).all()
        return rows[0] if len(rows) == 1 else None

    def get_execution_readiness(self) -> ExecutionReadinessSummary:
        with self.session_factory() as session:
            latest_market = session.scalar(
                select(MarketCalendarStateModel)
                .where(MarketCalendarStateModel.market_calendar == self.settings.market_calendar)
                .order_by(MarketCalendarStateModel.created_at.desc())
            )
            latest_snapshot = session.scalar(
                select(BrokerAccountSnapshotModel).order_by(BrokerAccountSnapshotModel.created_at.desc())
            )
            health_provider = None
            if latest_snapshot is not None:
                health_provider = session.scalar(
                    select(ProviderProfileModel).where(
                        ProviderProfileModel.provider_key == latest_snapshot.provider_key
                    )
                )
            if health_provider is None:
                health_provider = session.scalar(
                    select(ProviderProfileModel).where(ProviderProfileModel.is_primary.is_(True))
                )
            latest_reconciliation = session.scalar(
                select(ReconciliationRunModel).order_by(ReconciliationRunModel.checked_at.desc())
            )
            open_provider_incidents = session.scalars(
                select(ProviderIncidentModel).where(ProviderIncidentModel.status.in_(OPEN_PROVIDER_INCIDENT_STATUSES))
            ).all()
            active_trading_overrides = session.scalars(
                select(OperatorOverrideModel).where(
                    OperatorOverrideModel.scope == "trading",
                    OperatorOverrideModel.is_active.is_(True),
                )
            ).all()
            production_count = int(
                session.scalar(
                    select(func.count())
                    .select_from(StrategySpecModel)
                    .where(StrategySpecModel.current_stage == "production")
                )
                or 0
            )
            latest_configured_sync = session.scalar(
                select(BrokerSyncRunModel)
                .where(
                    BrokerSyncRunModel.provider_key == self.settings.default_broker_provider_key,
                    BrokerSyncRunModel.account_ref == self.settings.default_broker_account_ref,
                    BrokerSyncRunModel.environment == self.settings.default_broker_environment,
                    BrokerSyncRunModel.broker_adapter == self.settings.default_broker_adapter,
                )
                .order_by(BrokerSyncRunModel.completed_at.desc(), BrokerSyncRunModel.created_at.desc())
            )
            configured_capability = self._resolve_broker_capability(
                session,
                provider_key=self.settings.default_broker_provider_key,
                account_ref=self.settings.default_broker_account_ref,
                environment=self.settings.default_broker_environment,
                broker_adapter=self.settings.default_broker_adapter,
            )

        blocked_reasons: list[str] = []
        warnings: list[str] = []

        if production_count <= 0:
            blocked_reasons.append("No production strategy is currently approved.")

        if active_trading_overrides:
            blocked_reasons.append("Trading is paused by an active override.")

        if latest_market is None:
            blocked_reasons.append("No market session state has been recorded yet.")
        elif not latest_market.trading_allowed:
            blocked_reasons.append(f"Market session `{latest_market.session_label}` does not allow trading.")

        provider_health = health_provider.health_status if health_provider is not None else None
        if open_provider_incidents:
            blocked_reasons.append("One or more provider incidents remain open.")
        elif provider_health in {"degraded", "slow"}:
            warnings.append(f"Primary provider health is `{provider_health}`.")
        elif provider_health in {"outage", "down"}:
            blocked_reasons.append(f"Primary provider health is `{provider_health}`.")
        elif provider_health in {None, "unknown"}:
            warnings.append("Primary provider health is still unknown.")

        broker_snapshot_age_seconds: int | None = None
        if latest_snapshot is None:
            blocked_reasons.append("No broker account snapshot has been captured.")
        else:
            snapshot_captured_at = _coerce_utc(latest_snapshot.source_captured_at)
            broker_snapshot_age_seconds = max(
                latest_snapshot.source_age_seconds,
                int((datetime.now(tz=UTC) - snapshot_captured_at).total_seconds()),
            )
            if broker_snapshot_age_seconds > 3600:
                blocked_reasons.append("The latest broker account snapshot is older than 1 hour.")
            elif broker_snapshot_age_seconds > 900:
                warnings.append("The latest broker account snapshot is older than 15 minutes.")

        if latest_reconciliation is None:
            blocked_reasons.append("No broker reconciliation run has been recorded.")
        elif latest_reconciliation.status == "blocked":
            blocked_reasons.append(
                latest_reconciliation.blocking_reason or "The latest reconciliation run is blocked."
            )
        elif latest_reconciliation.status == "warning":
            warnings.append("The latest reconciliation run reported warning-level divergence.")

        if self.settings.default_broker_environment == "live":
            if latest_configured_sync is None or latest_configured_sync.status != "synchronized":
                blocked_reasons.append(
                    "No successful broker sync has seeded the configured live account yet. Run broker sync before any live-capital activation."
                )
            if configured_capability is None:
                blocked_reasons.append(
                    "No live broker capability record has been seeded yet. Run broker sync before any live-capital activation."
                )
            elif not configured_capability.supports_live_trading:
                blocked_reasons.append(
                    "The configured broker capability does not confirm live-trading support for this account."
                )
            if latest_snapshot is not None and latest_snapshot.environment != "live":
                blocked_reasons.append(
                    "The latest broker account snapshot does not match the configured live environment."
                )

        readiness_status = "blocked" if blocked_reasons else ("degraded" if warnings else "ready")
        return ExecutionReadinessSummary(
            status=readiness_status,
            trading_allowed=not blocked_reasons,
            market_calendar=self.settings.market_calendar,
            market_session_label=latest_market.session_label if latest_market is not None else None,
            market_open=latest_market.is_market_open if latest_market is not None else False,
            active_production_strategies=production_count,
            blocked_reasons=blocked_reasons,
            warnings=warnings,
            active_trading_overrides=len(active_trading_overrides),
            open_provider_incidents=len(open_provider_incidents),
            latest_provider_health=provider_health,
            latest_market_state_at=_coerce_utc(latest_market.created_at) if latest_market is not None else None,
            latest_account_snapshot_at=_coerce_utc(latest_snapshot.source_captured_at) if latest_snapshot is not None else None,
            latest_reconciliation_at=_coerce_utc(latest_reconciliation.checked_at)
            if latest_reconciliation is not None
            else None,
            broker_snapshot_age_seconds=broker_snapshot_age_seconds,
            reconciliation_status=latest_reconciliation.status if latest_reconciliation is not None else None,
            reconciliation_halt_triggered=latest_reconciliation.halt_triggered if latest_reconciliation is not None else False,
        )

    def _build_market_session_payload(
        self,
        now: datetime,
        *,
        market_calendar: str,
        market_timezone: str,
    ) -> dict[str, Any]:
        timezone = ZoneInfo(market_timezone)
        local_now = now.astimezone(timezone)
        calendar_key = market_calendar.upper()
        if calendar_key in {"CRYPTO_24X7", "BINANCE_24X7", "24X7"}:
            return {
                "market_calendar": market_calendar,
                "market_timezone": market_timezone,
                "session_label": "continuous",
                "is_market_open": True,
                "trading_allowed": True,
                "next_open_at": None,
                "next_close_at": None,
            }
        if calendar_key == "XNYS":
            return self._build_xnys_session_payload(local_now, market_calendar, market_timezone)
        if calendar_key in {"XSHG", "XSHE"}:
            return self._build_cn_equities_session_payload(local_now, market_calendar, market_timezone)
        return {
            "market_calendar": market_calendar,
            "market_timezone": market_timezone,
            "session_label": "unknown_calendar",
            "is_market_open": False,
            "trading_allowed": False,
            "next_open_at": None,
            "next_close_at": None,
        }

    def _build_xnys_session_payload(
        self,
        local_now: datetime,
        market_calendar: str,
        market_timezone: str,
    ) -> dict[str, Any]:
        timezone = ZoneInfo(market_timezone)
        today_open = datetime.combine(local_now.date(), time(9, 30), tzinfo=timezone)
        today_close = datetime.combine(local_now.date(), time(16, 0), tzinfo=timezone)
        weekday = local_now.weekday()

        if weekday >= 5:
            next_open = self._next_weekday_open(local_now, timezone)
            next_close = datetime.combine(next_open.date(), time(16, 0), tzinfo=timezone)
            session_label = "weekend"
            is_market_open = False
            trading_allowed = False
        elif local_now < today_open:
            next_open = today_open
            next_close = today_close
            session_label = "pre_market"
            is_market_open = False
            trading_allowed = False
        elif local_now < today_close:
            next_open = self._next_weekday_open(local_now + timedelta(days=1), timezone)
            next_close = today_close
            session_label = "regular"
            is_market_open = True
            trading_allowed = True
        else:
            next_open = self._next_weekday_open(local_now + timedelta(days=1), timezone)
            next_close = datetime.combine(next_open.date(), time(16, 0), tzinfo=timezone)
            session_label = "after_hours"
            is_market_open = False
            trading_allowed = False

        return {
            "market_calendar": market_calendar,
            "market_timezone": market_timezone,
            "session_label": session_label,
            "is_market_open": is_market_open,
            "trading_allowed": trading_allowed,
            "next_open_at": next_open.astimezone(UTC) if next_open is not None else None,
            "next_close_at": next_close.astimezone(UTC) if next_close is not None else None,
        }

    def _build_cn_equities_session_payload(
        self,
        local_now: datetime,
        market_calendar: str,
        market_timezone: str,
    ) -> dict[str, Any]:
        timezone = ZoneInfo(market_timezone)
        morning_open = datetime.combine(local_now.date(), time(9, 30), tzinfo=timezone)
        morning_close = datetime.combine(local_now.date(), time(11, 30), tzinfo=timezone)
        afternoon_open = datetime.combine(local_now.date(), time(13, 0), tzinfo=timezone)
        afternoon_close = datetime.combine(local_now.date(), time(15, 0), tzinfo=timezone)
        weekday = local_now.weekday()

        if weekday >= 5:
            next_open = self._next_weekday_time(local_now, timezone, time(9, 30))
            next_close = datetime.combine(next_open.date(), time(11, 30), tzinfo=timezone)
            session_label = "weekend"
            is_market_open = False
            trading_allowed = False
        elif local_now < morning_open:
            next_open = morning_open
            next_close = morning_close
            session_label = "pre_open"
            is_market_open = False
            trading_allowed = False
        elif local_now < morning_close:
            next_open = afternoon_open
            next_close = morning_close
            session_label = "morning_continuous"
            is_market_open = True
            trading_allowed = True
        elif local_now < afternoon_open:
            next_open = afternoon_open
            next_close = afternoon_close
            session_label = "midday_break"
            is_market_open = False
            trading_allowed = False
        elif local_now < afternoon_close:
            next_open = self._next_weekday_time(local_now + timedelta(days=1), timezone, time(9, 30))
            next_close = afternoon_close
            session_label = "afternoon_continuous"
            is_market_open = True
            trading_allowed = True
        else:
            next_open = self._next_weekday_time(local_now + timedelta(days=1), timezone, time(9, 30))
            next_close = datetime.combine(next_open.date(), time(11, 30), tzinfo=timezone)
            session_label = "after_close"
            is_market_open = False
            trading_allowed = False

        return {
            "market_calendar": market_calendar,
            "market_timezone": market_timezone,
            "session_label": session_label,
            "is_market_open": is_market_open,
            "trading_allowed": trading_allowed,
            "next_open_at": next_open.astimezone(UTC) if next_open is not None else None,
            "next_close_at": next_close.astimezone(UTC) if next_close is not None else None,
        }

    def _next_weekday_open(self, start_local: datetime, timezone: ZoneInfo) -> datetime:
        return self._next_weekday_time(start_local, timezone, time(9, 30))

    def _next_weekday_time(
        self,
        start_local: datetime,
        timezone: ZoneInfo,
        target_time: time,
    ) -> datetime:
        probe = start_local
        while True:
            probe_date = probe.date()
            if probe.weekday() < 5:
                return datetime.combine(probe_date, target_time, tzinfo=timezone)
            probe = (probe + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

    def _resolve_snapshot(
        self,
        session: Session,
        *,
        provider_key: str,
        account_ref: str,
        environment: str,
        account_snapshot_id: str | None,
    ) -> BrokerAccountSnapshotModel | None:
        if account_snapshot_id:
            snapshot = session.get(BrokerAccountSnapshotModel, account_snapshot_id)
            if snapshot is None:
                raise ValueError(f"Broker account snapshot not found: {account_snapshot_id}")
            return snapshot
        return session.scalar(
            select(BrokerAccountSnapshotModel)
            .where(
                BrokerAccountSnapshotModel.provider_key == provider_key,
                BrokerAccountSnapshotModel.account_ref == account_ref,
                BrokerAccountSnapshotModel.environment == environment,
            )
            .order_by(BrokerAccountSnapshotModel.created_at.desc())
        )

    def _evaluate_reconciliation(
        self,
        *,
        snapshot: BrokerAccountSnapshotModel | None,
        equity_delta_pct: float,
        position_delta_count: int,
        order_delta_count: int,
        equity_warning_pct: float,
        equity_block_pct: float,
        notes: list[str],
    ) -> tuple[str, str | None]:
        if snapshot is None:
            reason = "No broker account snapshot is available for reconciliation."
            notes.append(reason)
            return ("blocked", reason)
        if position_delta_count > 0:
            reason = f"Position divergence detected ({position_delta_count})."
            notes.append(reason)
            return ("blocked", reason)
        if order_delta_count > 0:
            reason = f"Open-order divergence detected ({order_delta_count})."
            notes.append(reason)
            return ("blocked", reason)
        if equity_delta_pct >= equity_block_pct:
            reason = f"Equity divergence {equity_delta_pct:.4f}% exceeds the block threshold."
            notes.append(reason)
            return ("blocked", reason)
        if equity_delta_pct >= equity_warning_pct:
            notes.append(f"Equity divergence {equity_delta_pct:.4f}% exceeds the warning threshold.")
            return ("warning", None)
        notes.append("Broker and internal execution state are within tolerance.")
        return ("matched", None)

    def _ensure_trading_halt(
        self,
        session: Session,
        *,
        provider_key: str,
        reason: str,
        created_by: str,
        origin_type: str,
        origin_id: str | None,
    ) -> bool:
        existing_override = session.scalar(
            select(OperatorOverrideModel).where(
                OperatorOverrideModel.scope == "trading",
                OperatorOverrideModel.action == "pause",
                OperatorOverrideModel.is_active.is_(True),
            )
        )
        if existing_override is None:
            session.add(
                OperatorOverrideModel(
                    scope="trading",
                    action="pause",
                    reason=f"Reconciliation halt: {reason}",
                    activated_by=created_by,
                    created_by=created_by,
                    origin_type=origin_type,
                    origin_id=origin_id,
                    status="active",
                    is_active=True,
                )
            )

        incident_title = f"Trading reconciliation blocked for {provider_key}"
        existing_incident = session.scalar(
            select(IncidentModel).where(
                IncidentModel.title == incident_title,
                IncidentModel.status.in_(("open", "investigating", "mitigated")),
            )
        )
        if existing_incident is None:
            session.add(
                IncidentModel(
                    title=incident_title,
                    summary=reason,
                    severity="SEV-1",
                    created_by=created_by,
                    origin_type=origin_type,
                    origin_id=origin_id,
                    status="open",
                )
            )
        return True

    def _ensure_provider_profile(self, session: Session, provider_key: str) -> ProviderProfileModel:
        profile = session.scalar(select(ProviderProfileModel).where(ProviderProfileModel.provider_key == provider_key))
        if profile is not None:
            return profile

        profile = ProviderProfileModel(
            provider_key=provider_key,
            display_name=provider_key.replace("-", " ").title(),
            api_style="broker-adapter",
            health_status="unknown",
            is_primary=False,
            capability_snapshot={},
            created_by="execution-service",
            origin_type="execution-service",
            origin_id=provider_key,
            status="active",
        )
        session.add(profile)
        session.flush()
        return profile

    def _resolve_or_register_instrument(
        self,
        session: Session,
        request: OrderIntentCreate,
    ) -> InstrumentDefinitionModel | None:
        instrument: InstrumentDefinitionModel | None = None
        if request.instrument_id:
            instrument = session.get(InstrumentDefinitionModel, request.instrument_id)
            if instrument is None:
                raise ValueError(f"Instrument definition not found: {request.instrument_id}")
            return instrument

        if request.instrument_key:
            instrument = session.scalar(
                select(InstrumentDefinitionModel).where(InstrumentDefinitionModel.instrument_key == request.instrument_key)
            )
            if instrument is None and request.asset_type.lower() == "option":
                raise ValueError(f"Instrument definition not found: {request.instrument_key}")
            if instrument is not None:
                return instrument

        asset_type = request.asset_type.lower()
        if asset_type == "option":
            return None

        symbol = request.symbol.upper()
        instrument_key = self._canonical_instrument_key(
            instrument_type=asset_type,
            symbol=symbol,
            underlying_symbol=None,
            expiration_date=None,
            option_right=None,
            strike_price=None,
        )
        instrument = session.scalar(
            select(InstrumentDefinitionModel).where(InstrumentDefinitionModel.instrument_key == instrument_key)
        )
        if instrument is not None:
            return instrument

        instrument = InstrumentDefinitionModel(
            instrument_key=instrument_key,
            symbol=symbol,
            display_symbol=symbol,
            instrument_type=asset_type,
            currency="USD",
            contract_multiplier=1.0,
            leverage_ratio=1.0,
            inverse_exposure=False,
            is_marginable=True,
            is_shortable=request.environment == "paper",
            metadata_payload={"autoregistered": True},
            created_by=request.created_by,
            origin_type="execution-autoregister",
            origin_id=request.origin_id or request.symbol.upper(),
            status="active",
        )
        session.add(instrument)
        session.flush()
        return instrument

    def _resolve_broker_capability(
        self,
        session: Session,
        *,
        provider_key: str,
        account_ref: str,
        environment: str,
        broker_adapter: str,
    ) -> BrokerCapabilityModel | None:
        rows = session.scalars(
            select(BrokerCapabilityModel)
            .where(
                BrokerCapabilityModel.provider_key == provider_key,
                BrokerCapabilityModel.environment == environment,
                BrokerCapabilityModel.broker_adapter == broker_adapter,
                BrokerCapabilityModel.status == "active",
                or_(BrokerCapabilityModel.account_ref == account_ref, BrokerCapabilityModel.account_ref.is_(None)),
            )
            .order_by(BrokerCapabilityModel.account_ref.desc())
        ).all()
        return rows[0] if rows else None

    def _effective_broker_capability(
        self,
        session: Session,
        *,
        provider_key: str,
        account_ref: str,
        environment: str,
        broker_adapter: str,
    ) -> dict[str, Any]:
        capability = self._resolve_broker_capability(
            session,
            provider_key=provider_key,
            account_ref=account_ref,
            environment=environment,
            broker_adapter=broker_adapter,
        )
        defaults = {
            "capability_key": f"default:{provider_key}:{broker_adapter}:{environment}",
            "provider_key": provider_key,
            "broker_adapter": broker_adapter,
            "account_ref": account_ref,
            "environment": environment,
        }
        defaults.update(broker_capability_defaults(broker_adapter, environment))
        if capability is None:
            return defaults

        defaults.update(
            {
                "capability_key": capability.capability_key,
                "account_ref": capability.account_ref,
                "account_mode": capability.account_mode,
                "supports_equities": capability.supports_equities,
                "supports_etfs": capability.supports_etfs,
                "supports_fractional": capability.supports_fractional,
                "supports_short": capability.supports_short,
                "supports_margin": capability.supports_margin,
                "supports_options": capability.supports_options,
                "supports_multi_leg_options": capability.supports_multi_leg_options,
                "supports_option_exercise": capability.supports_option_exercise,
                "supports_option_assignment_events": capability.supports_option_assignment_events,
                "supports_live_trading": capability.supports_live_trading,
                "supports_paper_trading": capability.supports_paper_trading,
                "notes": capability.notes,
            }
        )
        return defaults

    def _canonical_instrument_key(
        self,
        *,
        instrument_type: str,
        symbol: str,
        underlying_symbol: str | None,
        expiration_date: str | None,
        option_right: str | None,
        strike_price: float | None,
    ) -> str:
        normalized_type = instrument_type.lower()
        if normalized_type == "option":
            strike = f"{strike_price:.8f}" if strike_price is not None else "unknown"
            right = (option_right or "unknown").lower()
            expiry = expiration_date or "unknown"
            return f"option:{(underlying_symbol or symbol).upper()}:{expiry}:{right}:{strike}"
        return f"{normalized_type}:{symbol.upper()}"

    def _display_symbol_for_instrument(
        self,
        *,
        instrument_type: str,
        symbol: str,
        underlying_symbol: str | None,
        expiration_date: str | None,
        option_right: str | None,
        strike_price: float | None,
    ) -> str:
        if instrument_type == "option":
            strike = f"{strike_price:.2f}" if strike_price is not None else "?"
            right = (option_right or "?").upper()
            expiry = expiration_date or "?"
            return f"{(underlying_symbol or symbol).upper()} {expiry} {right} {strike}"
        return symbol.upper()

    def _resolve_position_instrument(
        self,
        session: Session,
        position: PositionRecordModel,
    ) -> InstrumentDefinitionModel | None:
        if position.instrument_id:
            return session.get(InstrumentDefinitionModel, position.instrument_id)
        if position.instrument_key:
            return session.scalar(
                select(InstrumentDefinitionModel).where(InstrumentDefinitionModel.instrument_key == position.instrument_key)
            )
        return None

    def _resolve_instrument_by_identity(
        self,
        session: Session,
        *,
        instrument_id: str | None,
        instrument_key: str | None,
    ) -> InstrumentDefinitionModel | None:
        if instrument_id:
            return session.get(InstrumentDefinitionModel, instrument_id)
        if instrument_key:
            return session.scalar(
                select(InstrumentDefinitionModel).where(InstrumentDefinitionModel.instrument_key == instrument_key)
            )
        return None

    def _resolve_order_legs(
        self,
        session: Session,
        *,
        request: OrderIntentCreate,
        instrument: InstrumentDefinitionModel | None,
    ) -> list[ResolvedOrderLeg]:
        if not request.legs:
            return [
                ResolvedOrderLeg(
                    leg_index=1,
                    symbol=request.symbol.upper(),
                    instrument_id=instrument.id if instrument is not None else request.instrument_id,
                    instrument_key=instrument.instrument_key if instrument is not None else request.instrument_key,
                    underlying_symbol=instrument.underlying_symbol if instrument is not None else None,
                    asset_type=request.asset_type.lower(),
                    side=request.side,
                    position_effect=request.position_effect,
                    quantity=request.quantity,
                    ratio_quantity=1.0,
                    reference_price=request.reference_price,
                    requested_notional=self._requested_notional(
                        quantity=request.quantity,
                        price=request.reference_price,
                        instrument=instrument,
                        asset_type=request.asset_type,
                    ),
                )
            ]

        resolved: list[ResolvedOrderLeg] = []
        for leg_index, leg in enumerate(request.legs, start=1):
            if leg.quantity <= 0 or leg.reference_price <= 0:
                raise ValueError("Order legs require positive quantity and reference_price.")
            leg_instrument = self._resolve_instrument_by_identity(
                session,
                instrument_id=leg.instrument_id,
                instrument_key=leg.instrument_key,
            )
            leg_asset_type = leg.asset_type.lower()
            leg_symbol = leg.symbol.upper()
            if leg_instrument is not None:
                leg_asset_type = leg_instrument.instrument_type
                leg_symbol = leg_instrument.symbol.upper()
            elif leg_asset_type == "option":
                raise ValueError("Option order legs require a registered canonical instrument.")

            resolved.append(
                ResolvedOrderLeg(
                    leg_index=leg_index,
                    symbol=leg_symbol,
                    instrument_id=leg_instrument.id if leg_instrument is not None else leg.instrument_id,
                    instrument_key=leg_instrument.instrument_key if leg_instrument is not None else leg.instrument_key,
                    underlying_symbol=leg_instrument.underlying_symbol if leg_instrument is not None else None,
                    asset_type=leg_asset_type,
                    side=leg.side,
                    position_effect=leg.position_effect,
                    quantity=leg.quantity,
                    ratio_quantity=leg.ratio_quantity,
                    reference_price=leg.reference_price,
                    requested_notional=self._requested_notional(
                        quantity=leg.quantity,
                        price=leg.reference_price,
                        instrument=leg_instrument,
                        asset_type=leg_asset_type,
                    ),
                )
            )
        return resolved

    def _persist_order_legs(
        self,
        session: Session,
        *,
        order_intent_id: str,
        resolved_legs: Sequence[ResolvedOrderLeg],
        created_by: str,
        origin_type: str,
        origin_id: str | None,
    ) -> list[OrderLegModel]:
        rows: list[OrderLegModel] = []
        for leg in resolved_legs:
            row = OrderLegModel(
                order_intent_id=order_intent_id,
                order_record_id=None,
                leg_index=leg.leg_index,
                symbol=leg.symbol,
                instrument_id=leg.instrument_id,
                instrument_key=leg.instrument_key,
                underlying_symbol=leg.underlying_symbol,
                asset_type=leg.asset_type,
                side=leg.side,
                position_effect=leg.position_effect,
                quantity=leg.quantity,
                ratio_quantity=leg.ratio_quantity,
                reference_price=leg.reference_price,
                requested_notional=leg.requested_notional,
                created_by=created_by,
                origin_type=origin_type,
                origin_id=origin_id,
                status="active",
            )
            session.add(row)
            rows.append(row)
        session.flush()
        return rows

    def _apply_option_terminal_event(
        self,
        *,
        position: PositionRecordModel,
        instrument: InstrumentDefinitionModel,
        quantity: float,
        event_price: float,
        occurred_at: datetime,
        event_label: str,
        terminal_status: str,
    ) -> None:
        if quantity > position.quantity:
            raise ValueError("Option lifecycle event quantity exceeds the active position quantity.")

        multiplier = self._contract_multiplier(instrument, position.asset_type)
        if position.direction == "short":
            realized_increment = (position.avg_entry_price - event_price) * quantity * multiplier
        else:
            realized_increment = (event_price - position.avg_entry_price) * quantity * multiplier

        remaining_quantity = max(0.0, position.quantity - quantity)
        payload = dict(position.raw_payload or {})
        payload["option_event"] = event_label
        payload["option_event_at"] = occurred_at.isoformat()
        payload["option_event_price"] = event_price

        position.realized_pnl += realized_increment
        position.quantity = remaining_quantity
        position.market_price = event_price
        position.last_synced_at = occurred_at
        position.raw_payload = payload

        if remaining_quantity <= 0:
            position.status = terminal_status
            position.closed_at = occurred_at
            position.notional_value = 0.0
            position.unrealized_pnl = 0.0
            return

        position.notional_value = self._position_market_value(
            quantity=remaining_quantity,
            market_price=event_price,
            contract_multiplier=multiplier,
        )

    def _apply_option_conversion_event(
        self,
        session: Session,
        *,
        request: OptionLifecycleEventCreate,
        position: PositionRecordModel,
        instrument: InstrumentDefinitionModel,
        quantity: float,
        occurred_at: datetime,
    ) -> tuple[PositionRecordModel | None, InstrumentDefinitionModel, float, str]:
        if instrument.underlying_symbol is None:
            raise ValueError("Automatic option state application requires an underlying symbol.")
        if instrument.strike_price is None:
            raise ValueError("Automatic option state application requires a strike price.")
        if request.event_type == "exercise" and position.direction != "long":
            raise ValueError("Only long option positions can be auto-applied as exercise events.")
        if request.event_type == "assignment" and position.direction != "short":
            raise ValueError("Only short option positions can be auto-applied as assignment events.")

        broker_adapter = self._resolve_account_broker_adapter(
            session,
            provider_key=request.provider_key,
            account_ref=request.account_ref,
            environment=request.environment,
        )
        capability = self._effective_broker_capability(
            session,
            provider_key=request.provider_key,
            account_ref=request.account_ref,
            environment=request.environment,
            broker_adapter=broker_adapter,
        )
        if request.event_type == "exercise" and not capability["supports_option_exercise"]:
            raise ValueError("Broker capability does not support automatic option exercise application.")
        if request.event_type == "assignment" and not capability["supports_option_assignment_events"]:
            raise ValueError("Broker capability does not support automatic option assignment application.")
        if not capability["supports_equities"]:
            raise ValueError("Broker capability does not support automatic underlying equity state application.")

        underlying_instrument = self._resolve_or_autoregister_underlying_instrument(
            session,
            underlying_symbol=instrument.underlying_symbol,
            created_by=request.created_by,
            origin_type=request.origin_type,
            origin_id=request.origin_id or instrument.instrument_key,
        )
        underlying_positions = self._active_positions_for_symbol(
            session,
            provider_key=request.provider_key,
            account_ref=request.account_ref,
            environment=request.environment,
            symbol=underlying_instrument.symbol,
        )
        conflicting_positions = [
            active_position
            for active_position in underlying_positions
            if active_position.strategy_spec_id != position.strategy_spec_id and active_position.status == "active"
        ]
        if conflicting_positions:
            raise ValueError(
                "Automatic option state application is blocked because the underlying symbol is already controlled "
                "by another strategy."
            )

        current_underlying_position = next(
            (
                active_position
                for active_position in underlying_positions
                if active_position.strategy_spec_id == position.strategy_spec_id and active_position.status == "active"
            ),
            None,
        )
        current_underlying_instrument = (
            self._resolve_position_instrument(session, current_underlying_position)
            if current_underlying_position is not None
            else underlying_instrument
        )
        current_underlying_state = (
            PositionState(
                strategy_spec_id=current_underlying_position.strategy_spec_id,
                symbol=current_underlying_position.symbol,
                asset_type=current_underlying_position.asset_type,
                direction=current_underlying_position.direction,
                quantity=current_underlying_position.quantity,
                avg_entry_price=current_underlying_position.avg_entry_price,
                realized_pnl=current_underlying_position.realized_pnl,
                instrument_id=current_underlying_position.instrument_id,
                instrument_key=current_underlying_position.instrument_key,
                underlying_symbol=current_underlying_position.underlying_symbol,
                contract_multiplier=self._contract_multiplier(
                    current_underlying_instrument,
                    current_underlying_position.asset_type,
                ),
                leverage_ratio=self._leverage_ratio(
                    current_underlying_instrument,
                    current_underlying_position.asset_type,
                ),
                market_price=current_underlying_position.market_price,
                raw_payload=dict(current_underlying_position.raw_payload or {}),
            )
            if current_underlying_position is not None
            else None
        )

        contract_multiplier = self._contract_multiplier(instrument, position.asset_type)
        underlying_quantity = quantity * contract_multiplier
        underlying_side = self._underlying_side_for_option_event(
            option_right=instrument.option_right,
            event_type=request.event_type,
        )
        allow_short = bool(capability["supports_short"] and capability["supports_margin"])

        paper_result = PaperBrokerAdapter().execute_order(
            BrokerExecutionRequest(
                order_intent_id=f"option-event:{request.event_type}",
                client_order_id=f"option-event:{request.event_type}:{position.id}",
                strategy_spec_id=position.strategy_spec_id,
                provider_key=request.provider_key,
                account_ref=request.account_ref,
                environment=request.environment,
                symbol=underlying_instrument.symbol,
                instrument_id=underlying_instrument.id,
                instrument_key=underlying_instrument.instrument_key,
                underlying_symbol=None,
                asset_type=underlying_instrument.instrument_type,
                position_effect="open" if underlying_side == "buy" else "close",
                side=underlying_side,
                order_type="market",
                time_in_force="day",
                quantity=underlying_quantity,
                reference_price=instrument.strike_price,
                requested_notional=round(underlying_quantity * instrument.strike_price, 8),
                limit_price=None,
                stop_price=None,
                allow_short=allow_short,
                contract_multiplier=1.0,
                leverage_ratio=self._leverage_ratio(underlying_instrument, underlying_instrument.instrument_type),
            ),
            current_underlying_state,
        )
        underlying_market_price = float(
            request.metadata_payload.get("underlying_market_price", instrument.strike_price)
        )
        if paper_result.resulting_position is not None:
            payload = dict(paper_result.resulting_position.raw_payload or {})
            payload.update(
                {
                    "option_event": request.event_type,
                    "option_event_at": occurred_at.isoformat(),
                    "source_option_symbol": instrument.symbol,
                    "source_option_position_id": position.id,
                }
            )
            paper_result.resulting_position.market_price = underlying_market_price
            paper_result.resulting_position.raw_payload = payload

        self._apply_option_terminal_event(
            position=position,
            instrument=instrument,
            quantity=quantity,
            event_price=0.0 if request.event_price is None else request.event_price,
            occurred_at=occurred_at,
            event_label=request.event_type,
            terminal_status="exercised" if request.event_type == "exercise" else "assigned",
        )
        synthetic_request = OrderIntentCreate(
            strategy_spec_id=position.strategy_spec_id,
            symbol=underlying_instrument.symbol,
            side=underlying_side,
            quantity=underlying_quantity,
            reference_price=instrument.strike_price,
            instrument_id=underlying_instrument.id,
            instrument_key=underlying_instrument.instrument_key,
            asset_type=underlying_instrument.instrument_type,
            position_effect="open" if underlying_side == "buy" else "close",
            provider_key=request.provider_key,
            account_ref=request.account_ref,
            environment=request.environment,
            broker_adapter=broker_adapter,
            rationale=f"Option {request.event_type} auto-state application.",
            created_by=request.created_by,
            origin_type=request.origin_type,
            origin_id=request.origin_id or position.id,
        )
        resulting_position = self._apply_position_update(
            session,
            current_position=current_underlying_position,
            result=paper_result,
            request=synthetic_request,
            provider_key=request.provider_key,
            account_ref=request.account_ref,
        )
        gross_cash_flow = round(underlying_quantity * instrument.strike_price, 8)
        derived_cash_flow = -gross_cash_flow if underlying_side == "buy" else gross_cash_flow
        auto_note = (
            f"Applied option {request.event_type} automatically into underlying {underlying_instrument.symbol} "
            f"via a {underlying_side} transformation at strike {instrument.strike_price:.2f}."
        )
        return resulting_position, underlying_instrument, derived_cash_flow, auto_note
        position.unrealized_pnl = self._compute_unrealized_pnl(
            direction=position.direction,
            quantity=remaining_quantity,
            avg_entry_price=position.avg_entry_price,
            market_price=event_price,
            contract_multiplier=multiplier,
        )

    def _ensure_option_review_incident(
        self,
        session: Session,
        *,
        request: OptionLifecycleEventCreate,
        instrument: InstrumentDefinitionModel,
        occurred_at: datetime,
    ) -> None:
        title = f"Option lifecycle review required: {request.event_type} {instrument.display_symbol}"
        existing = session.scalar(
            select(IncidentModel).where(
                IncidentModel.title == title,
                IncidentModel.status.in_(("open", "investigating", "mitigated")),
            )
        )
        if existing is not None:
            return

        session.add(
            IncidentModel(
                title=title,
                summary=(
                    "A non-expiration option lifecycle event was recorded and needs explicit review before the "
                    "execution state can be considered fully reconciled."
                ),
                severity="SEV-2",
                created_by=request.created_by,
                origin_type=request.origin_type,
                origin_id=request.origin_id or instrument.instrument_key,
                status="open",
            )
        )

    def _resolve_account_broker_adapter(
        self,
        session: Session,
        *,
        provider_key: str,
        account_ref: str,
        environment: str,
    ) -> str:
        rows = session.scalars(
            select(BrokerCapabilityModel)
            .where(
                BrokerCapabilityModel.provider_key == provider_key,
                BrokerCapabilityModel.environment == environment,
                BrokerCapabilityModel.status == "active",
                or_(BrokerCapabilityModel.account_ref == account_ref, BrokerCapabilityModel.account_ref.is_(None)),
            )
            .order_by(BrokerCapabilityModel.account_ref.desc(), BrokerCapabilityModel.updated_at.desc())
        ).all()
        if rows:
            return rows[0].broker_adapter
        return self.settings.default_broker_adapter

    def _resolve_or_autoregister_underlying_instrument(
        self,
        session: Session,
        *,
        underlying_symbol: str,
        created_by: str,
        origin_type: str,
        origin_id: str | None,
    ) -> InstrumentDefinitionModel:
        instrument = session.scalar(
            select(InstrumentDefinitionModel).where(
                InstrumentDefinitionModel.instrument_key == self._canonical_instrument_key(
                    instrument_type="equity",
                    symbol=underlying_symbol,
                    underlying_symbol=None,
                    expiration_date=None,
                    option_right=None,
                    strike_price=None,
                )
            )
        )
        if instrument is not None:
            return instrument

        instrument = session.scalar(
            select(InstrumentDefinitionModel)
            .where(
                InstrumentDefinitionModel.symbol == underlying_symbol.upper(),
                InstrumentDefinitionModel.instrument_type != "option",
            )
            .order_by(InstrumentDefinitionModel.updated_at.desc())
        )
        if instrument is not None:
            return instrument

        instrument = InstrumentDefinitionModel(
            instrument_key=self._canonical_instrument_key(
                instrument_type="equity",
                symbol=underlying_symbol,
                underlying_symbol=None,
                expiration_date=None,
                option_right=None,
                strike_price=None,
            ),
            symbol=underlying_symbol.upper(),
            display_symbol=underlying_symbol.upper(),
            instrument_type="equity",
            currency="USD",
            contract_multiplier=1.0,
            leverage_ratio=1.0,
            inverse_exposure=False,
            is_marginable=True,
            is_shortable=True,
            metadata_payload={"autoregistered_from_option_underlying": True},
            created_by=created_by,
            origin_type=origin_type,
            origin_id=origin_id,
            status="active",
        )
        session.add(instrument)
        session.flush()
        return instrument

    def _underlying_side_for_option_event(self, *, option_right: str | None, event_type: str) -> str:
        normalized_right = (option_right or "").lower()
        if normalized_right not in {"call", "put"}:
            raise ValueError("Automatic option state application requires a call or put right.")
        if event_type == "exercise":
            return "buy" if normalized_right == "call" else "sell"
        if event_type == "assignment":
            return "sell" if normalized_right == "call" else "buy"
        raise ValueError(f"Unsupported option lifecycle event type: {event_type}")

    def _contract_multiplier(
        self,
        instrument: InstrumentDefinitionModel | None,
        asset_type: str,
    ) -> float:
        if asset_type == "option" and instrument is not None:
            return max(1.0, instrument.contract_multiplier)
        return 1.0

    def _leverage_ratio(
        self,
        instrument: InstrumentDefinitionModel | None,
        asset_type: str,
    ) -> float:
        if asset_type in {"leveraged_etf", "inverse_etf"} and instrument is not None:
            return max(1.0, instrument.leverage_ratio)
        return 1.0

    def _requested_notional(
        self,
        *,
        quantity: float,
        price: float,
        instrument: InstrumentDefinitionModel | None,
        asset_type: str,
    ) -> float:
        return round(quantity * price * self._contract_multiplier(instrument, asset_type), 8)

    def _parent_requested_notional(
        self,
        *,
        request: OrderIntentCreate,
        instrument: InstrumentDefinitionModel | None,
        order_legs: Sequence[ResolvedOrderLeg],
    ) -> float:
        if instrument is not None:
            multiplier = self._contract_multiplier(instrument, request.asset_type)
        elif request.asset_type.lower() == "option":
            multiplier = 1.0
            for leg in order_legs:
                base_points = leg.quantity * leg.reference_price
                if base_points > 0:
                    multiplier = max(1.0, round(leg.requested_notional / base_points, 8))
                    break
        else:
            multiplier = 1.0
        return round(request.quantity * request.reference_price * multiplier, 8)

    def _risk_weighted_notional(
        self,
        *,
        notional: float,
        instrument: InstrumentDefinitionModel | None,
        asset_type: str,
    ) -> float:
        return round(notional * self._leverage_ratio(instrument, asset_type), 8)

    def _position_market_value(
        self,
        *,
        quantity: float,
        market_price: float,
        contract_multiplier: float,
    ) -> float:
        return quantity * market_price * contract_multiplier

    def _resolve_allocation_policy(
        self,
        session: Session,
        *,
        policy_key: str | None,
        strategy_spec_id: str,
        environment: str,
        provider_key: str,
        account_ref: str,
    ) -> AllocationPolicyModel:
        if policy_key:
            policy = session.scalar(
                select(AllocationPolicyModel).where(
                    AllocationPolicyModel.policy_key == policy_key,
                    AllocationPolicyModel.status == "active",
                )
            )
            if policy is None:
                raise ValueError(f"Allocation policy not found: {policy_key}")
            return policy

        policy = session.scalar(
            select(AllocationPolicyModel).where(
                AllocationPolicyModel.strategy_spec_id == strategy_spec_id,
                AllocationPolicyModel.environment == environment,
                AllocationPolicyModel.status == "active",
            )
        )
        if policy is not None:
            return policy

        policy = session.scalar(
            select(AllocationPolicyModel).where(
                AllocationPolicyModel.policy_key == self.settings.default_allocation_policy_key,
                AllocationPolicyModel.environment == environment,
                AllocationPolicyModel.status == "active",
            )
        )
        if policy is not None:
            return policy

        policy = session.scalar(
            select(AllocationPolicyModel).where(
                AllocationPolicyModel.environment == environment,
                AllocationPolicyModel.scope == "global",
                AllocationPolicyModel.status == "active",
                or_(AllocationPolicyModel.provider_key == provider_key, AllocationPolicyModel.provider_key.is_(None)),
                or_(AllocationPolicyModel.account_ref == account_ref, AllocationPolicyModel.account_ref.is_(None)),
            )
        )
        if policy is None:
            raise ValueError("No active allocation policy is configured for this execution environment.")
        return policy

    def _related_symbol_conflicts(
        self,
        session: Session,
        *,
        provider_key: str,
        account_ref: str,
        environment: str,
        strategy_spec_id: str,
        request_symbol: str,
        order_legs: Sequence[ResolvedOrderLeg],
        instrument: InstrumentDefinitionModel | None,
    ) -> list[PositionRecordModel]:
        related_symbols = {request_symbol.upper()}
        if instrument is not None and instrument.underlying_symbol:
            related_symbols.add(instrument.underlying_symbol.upper())
        for leg in order_legs:
            related_symbols.add(leg.symbol.upper())
            if leg.underlying_symbol:
                related_symbols.add(leg.underlying_symbol.upper())
        return session.scalars(
            select(PositionRecordModel).where(
                PositionRecordModel.provider_key == provider_key,
                PositionRecordModel.account_ref == account_ref,
                PositionRecordModel.environment == environment,
                PositionRecordModel.status == "active",
                PositionRecordModel.strategy_spec_id != strategy_spec_id,
                PositionRecordModel.symbol.in_(sorted(related_symbols)),
            )
        ).all()

    def _borrow_constraint_reason(
        self,
        *,
        request: OrderIntentCreate,
        instrument: InstrumentDefinitionModel | None,
        current_position: PositionRecordModel | None,
    ) -> str | None:
        if instrument is None:
            return None
        if request.asset_type == "option" or request.side != "sell":
            return None
        if current_position is not None and current_position.direction == "long" and request.quantity <= current_position.quantity:
            return None
        if not instrument.is_shortable:
            return "The referenced instrument is not marked as shortable."

        metadata = instrument.metadata_payload or {}
        borrow_status = str(metadata.get("borrow_status") or "").strip().lower()
        locate_required = bool(metadata.get("locate_required"))
        locate_confirmed = bool((request.signal_payload or {}).get("locate_confirmed"))

        if borrow_status in {"blocked", "unavailable", "none"}:
            return "Borrow availability is blocked for this instrument, so short exposure cannot be opened."
        if borrow_status in {"hard_to_borrow", "htb"} and not locate_confirmed:
            return "This instrument is hard to borrow. A confirmed locate is required before opening short exposure."
        if locate_required and not locate_confirmed:
            return "This instrument requires a borrow locate before opening short exposure."
        return None

    def _position_state_from_model(
        self,
        session: Session,
        position: PositionRecordModel,
    ) -> PositionState:
        instrument = self._resolve_position_instrument(session, position)
        return PositionState(
            strategy_spec_id=position.strategy_spec_id,
            symbol=position.symbol,
            asset_type=position.asset_type,
            direction=position.direction,
            quantity=position.quantity,
            avg_entry_price=position.avg_entry_price,
            realized_pnl=position.realized_pnl,
            instrument_id=position.instrument_id,
            instrument_key=position.instrument_key,
            underlying_symbol=position.underlying_symbol,
            contract_multiplier=self._contract_multiplier(instrument, position.asset_type),
            leverage_ratio=self._leverage_ratio(instrument, position.asset_type),
            market_price=position.market_price,
            raw_payload=dict(position.raw_payload or {}),
        )

    def _build_leg_execution_request(
        self,
        *,
        strategy_spec_id: str,
        provider_key: str,
        account_ref: str,
        environment: str,
        created_by_request: OrderIntentCreate,
        leg: ResolvedOrderLeg,
        instrument: InstrumentDefinitionModel | None,
        allow_short: bool,
        client_order_id: str,
    ) -> BrokerExecutionRequest:
        leg_allows_short = allow_short or (
            leg.asset_type == "option" and leg.side == "sell" and leg.position_effect in {"open", "increase"}
        )
        return BrokerExecutionRequest(
            order_intent_id=f"sim:{strategy_spec_id}:{leg.leg_index}",
            client_order_id=client_order_id,
            strategy_spec_id=strategy_spec_id,
            provider_key=provider_key,
            account_ref=account_ref,
            environment=environment,
            symbol=leg.symbol,
            instrument_id=leg.instrument_id,
            instrument_key=leg.instrument_key,
            underlying_symbol=leg.underlying_symbol,
            asset_type=leg.asset_type,
            position_effect=leg.position_effect,
            side=leg.side,
            order_type=created_by_request.order_type,
            time_in_force=created_by_request.time_in_force,
            quantity=leg.quantity,
            reference_price=leg.reference_price,
            requested_notional=leg.requested_notional,
            limit_price=None,
            stop_price=None,
            allow_short=leg_allows_short,
            contract_multiplier=self._contract_multiplier(instrument, leg.asset_type),
            leverage_ratio=self._leverage_ratio(instrument, leg.asset_type),
            legs=(),
        )

    def _simulate_projected_positions(
        self,
        session: Session,
        *,
        provider_key: str,
        account_ref: str,
        environment: str,
        strategy_spec_id: str,
        request: OrderIntentCreate,
        active_positions: Sequence[PositionRecordModel],
        order_legs: Sequence[ResolvedOrderLeg],
        allow_short: bool,
    ) -> list[PositionState]:
        simulated: dict[tuple[str, str, str | None], PositionState] = {
            (
                position.strategy_spec_id,
                position.symbol.upper(),
                position.instrument_key,
            ): self._position_state_from_model(session, position)
            for position in active_positions
            if position.status == "active"
        }
        paper_adapter = PaperBrokerAdapter()

        for leg in order_legs:
            leg_instrument = self._resolve_instrument_by_identity(
                session,
                instrument_id=leg.instrument_id,
                instrument_key=leg.instrument_key,
            )
            key = (strategy_spec_id, leg.symbol.upper(), leg.instrument_key)
            current_state = simulated.get(key)
            result = paper_adapter.execute_order(
                self._build_leg_execution_request(
                    strategy_spec_id=strategy_spec_id,
                    provider_key=provider_key,
                    account_ref=account_ref,
                    environment=environment,
                    created_by_request=request,
                    leg=leg,
                    instrument=leg_instrument,
                    allow_short=allow_short,
                    client_order_id=f"sim-{request.strategy_spec_id}-{leg.leg_index}",
                ),
                current_state,
            )
            if result.resulting_position is None or result.resulting_position.quantity <= 0:
                simulated.pop(key, None)
                continue
            simulated[key] = result.resulting_position

        return list(simulated.values())

    def _build_order_capital_profile(
        self,
        session: Session,
        *,
        provider_key: str,
        account_ref: str,
        environment: str,
        request: OrderIntentCreate,
        active_positions: Sequence[PositionRecordModel],
        order_legs: Sequence[ResolvedOrderLeg],
        allow_short: bool,
    ) -> OrderCapitalProfile:
        current_states = [self._position_state_from_model(session, position) for position in active_positions if position.status == "active"]
        projected_states = self._simulate_projected_positions(
            session,
            provider_key=provider_key,
            account_ref=account_ref,
            environment=environment,
            strategy_spec_id=request.strategy_spec_id,
            request=request,
            active_positions=active_positions,
            order_legs=order_legs,
            allow_short=allow_short,
        )
        current_requirement = self._maintenance_requirement_from_states(session, current_states)
        projected_requirement = self._maintenance_requirement_from_states(session, projected_states)
        current_gross_exposure = self._gross_exposure_from_states(current_states)
        projected_gross_exposure = self._gross_exposure_from_states(projected_states)
        net_cash_delta = round(
            sum(
                leg.requested_notional if leg.side == "sell" else -leg.requested_notional
                for leg in order_legs
            ),
            8,
        )
        liquidity_release = max(0.0, round(current_requirement - projected_requirement, 8))
        liquidity_need = max(0.0, round((-net_cash_delta) - liquidity_release, 8))
        effective_notional = max(
            0.0,
            round(projected_requirement - current_requirement, 8),
            liquidity_need,
        )
        return OrderCapitalProfile(
            current_maintenance_requirement=current_requirement,
            projected_maintenance_requirement=projected_requirement,
            current_gross_exposure=current_gross_exposure,
            projected_gross_exposure=projected_gross_exposure,
            net_cash_delta=net_cash_delta,
            liquidity_release=liquidity_release,
            liquidity_need=liquidity_need,
            effective_notional=effective_notional,
        )

    def _execute_paper_multi_leg_fill(
        self,
        session: Session,
        *,
        request: OrderIntentCreate,
        provider_key: str,
        account_ref: str,
        order_legs: Sequence[ResolvedOrderLeg],
        allow_short: bool,
        client_order_id: str,
    ) -> BrokerExecutionResult:
        adapter = PaperBrokerAdapter()
        leg_payloads: list[dict[str, Any]] = []
        for leg in order_legs:
            current_model = next(
                (
                    position
                    for position in self._active_positions_for_symbol(
                        session,
                        provider_key=provider_key,
                        account_ref=account_ref,
                        environment=request.environment,
                        symbol=leg.symbol,
                    )
                    if position.strategy_spec_id == request.strategy_spec_id and position.status == "active"
                ),
                None,
            )
            current_state = self._position_state_from_model(session, current_model) if current_model is not None else None
            leg_instrument = self._resolve_instrument_by_identity(
                session,
                instrument_id=leg.instrument_id,
                instrument_key=leg.instrument_key,
            )
            result = adapter.execute_order(
                self._build_leg_execution_request(
                    strategy_spec_id=request.strategy_spec_id,
                    provider_key=provider_key,
                    account_ref=account_ref,
                    environment=request.environment,
                    created_by_request=request,
                    leg=leg,
                    instrument=leg_instrument,
                    allow_short=allow_short,
                    client_order_id=f"qe-{request.strategy_spec_id}-{leg.leg_index}",
                ),
                current_state,
            )
            leg_request = request.model_copy(
                update={
                    "symbol": leg.symbol,
                    "instrument_id": leg.instrument_id,
                    "instrument_key": leg.instrument_key,
                    "asset_type": leg.asset_type,
                    "position_effect": leg.position_effect,
                    "side": leg.side,
                    "quantity": leg.quantity,
                    "reference_price": leg.reference_price,
                }
            )
            self._apply_position_update(
                session,
                current_position=current_model,
                result=result,
                request=leg_request,
                provider_key=provider_key,
                account_ref=account_ref,
            )
            leg_payloads.append(
                {
                    "leg_index": leg.leg_index,
                    "symbol": leg.symbol,
                    "side": leg.side,
                    "position_effect": leg.position_effect,
                    "quantity": leg.quantity,
                    "avg_fill_price": result.avg_fill_price,
                    "status": result.order_status,
                }
            )

        now = datetime.now(tz=UTC)
        return BrokerExecutionResult(
            broker_order_id=f"paper-mleg-{uuid4()}",
            client_order_id=client_order_id,
            order_status="filled",
            filled_quantity=request.quantity,
            avg_fill_price=request.reference_price,
            broker_updated_at=now,
            raw_payload={
                "adapter": "paper_sim",
                "mode": "multi_leg_fill",
                "filled_at": now.isoformat(),
                "legs": leg_payloads,
            },
            resulting_position=None,
        )

    def _maintenance_requirement_from_states(
        self,
        session: Session,
        positions: Sequence[PositionState],
    ) -> float:
        if not positions:
            return 0.0
        non_option_requirement = 0.0
        option_positions: list[tuple[PositionState, InstrumentDefinitionModel | None]] = []
        for position in positions:
            if position.asset_type == "option":
                option_positions.append(
                    (
                        position,
                        self._resolve_instrument_by_identity(
                            session,
                            instrument_id=position.instrument_id,
                            instrument_key=position.instrument_key,
                        ),
                    )
                )
                continue
            if position.direction != "short":
                continue
            market_price = position.market_price or position.avg_entry_price
            market_value = abs(position.quantity * market_price)
            instrument = self._resolve_instrument_by_identity(
                session,
                instrument_id=position.instrument_id,
                instrument_key=position.instrument_key,
            )
            non_option_requirement += market_value * self._maintenance_margin_pct(instrument, position.asset_type)
        return round(non_option_requirement + self._option_requirement_from_states(positions, option_positions), 8)

    def _gross_exposure_from_states(
        self,
        positions: Sequence[PositionState],
    ) -> float:
        return round(
            sum(
                self._position_market_value(
                    quantity=position.quantity,
                    market_price=position.market_price or position.avg_entry_price,
                    contract_multiplier=position.contract_multiplier,
                )
                for position in positions
                if position.quantity > 0
            ),
            8,
        )

    def _maintenance_margin_pct(
        self,
        instrument: InstrumentDefinitionModel | None,
        asset_type: str,
    ) -> float:
        metadata = instrument.metadata_payload if instrument is not None else {}
        if metadata and metadata.get("maintenance_margin_pct") is not None:
            return max(0.0, float(metadata["maintenance_margin_pct"]))
        if asset_type in {"leveraged_etf", "inverse_etf"}:
            leverage_ratio = self._leverage_ratio(instrument, asset_type)
            return max(0.5, min(1.0, 0.3 * leverage_ratio))
        return 0.3

    def _option_requirement_from_states(
        self,
        positions: Sequence[PositionState],
        option_positions: Sequence[tuple[PositionState, InstrumentDefinitionModel | None]],
    ) -> float:
        if not option_positions:
            return 0.0
        underlying_long_qty: dict[str, float] = {}
        for position in positions:
            if position.asset_type == "option" or position.direction != "long":
                continue
            underlying_long_qty[position.symbol.upper()] = underlying_long_qty.get(position.symbol.upper(), 0.0) + position.quantity

        grouped: dict[tuple[str, str], list[tuple[PositionState, InstrumentDefinitionModel]]] = {}
        for position, instrument in option_positions:
            if instrument is None or instrument.underlying_symbol is None or instrument.expiration_date is None:
                continue
            group_key = (instrument.underlying_symbol.upper(), instrument.expiration_date.isoformat())
            grouped.setdefault(group_key, []).append((position, instrument))

        requirement = 0.0
        for (underlying_symbol, _expiry), items in grouped.items():
            remaining_covered_contracts = int(underlying_long_qty.get(underlying_symbol, 0.0) // 100.0)
            components: list[tuple[PositionState, InstrumentDefinitionModel, float]] = []
            for position, instrument in sorted(items, key=lambda item: (item[1].option_right or "", item[1].strike_price or 0.0)):
                effective_quantity = position.quantity
                if position.direction == "short" and (instrument.option_right or "").lower() == "call" and remaining_covered_contracts > 0:
                    covered = min(remaining_covered_contracts, int(position.quantity))
                    effective_quantity = max(0.0, position.quantity - covered)
                    remaining_covered_contracts -= covered
                if effective_quantity <= 0:
                    continue
                components.append((position, instrument, effective_quantity))
            if not components:
                continue
            price_points = self._option_price_points(components)
            min_profit = min(self._option_group_profit_at_price(components, price) for price in price_points)
            requirement += max(0.0, -min_profit)
        return round(requirement, 8)

    def _option_price_points(
        self,
        components: Sequence[tuple[PositionState, InstrumentDefinitionModel, float]],
    ) -> list[float]:
        strikes = [float(instrument.strike_price or 0.0) for _, instrument, _ in components]
        ceiling = max(strikes or [0.0]) * 2.0 + 10.0
        points = {0.0, ceiling}
        for strike in strikes:
            points.add(strike)
            points.add(max(0.0, strike - 0.01))
            points.add(strike + 0.01)
        return sorted(points)

    def _option_group_profit_at_price(
        self,
        components: Sequence[tuple[PositionState, InstrumentDefinitionModel, float]],
        underlying_price: float,
    ) -> float:
        profit = 0.0
        for position, instrument, effective_quantity in components:
            if (instrument.option_right or "").lower() == "call":
                intrinsic = max(0.0, underlying_price - float(instrument.strike_price or 0.0))
            else:
                intrinsic = max(0.0, float(instrument.strike_price or 0.0) - underlying_price)
            per_contract = intrinsic - position.avg_entry_price
            if position.direction == "short":
                per_contract = -per_contract
            profit += per_contract * effective_quantity * self._contract_multiplier(instrument, "option")
        return round(profit, 8)

    def _validate_order_request(
        self,
        *,
        readiness: ExecutionReadinessSummary,
        strategy: StrategySpecModel,
        policy: AllocationPolicyModel,
        request: OrderIntentCreate,
        instrument: InstrumentDefinitionModel | None,
        broker_capability: dict[str, Any],
        requested_notional: float,
        latest_snapshot: BrokerAccountSnapshotModel | None,
        active_positions: list[PositionRecordModel],
        open_orders_count: int,
        current_position: PositionRecordModel | None,
        symbol_positions: list[PositionRecordModel],
        related_symbol_conflicts: Sequence[PositionRecordModel],
        order_legs: Sequence[ResolvedOrderLeg],
        broker_adapter: str,
        capital_profile: OrderCapitalProfile,
    ) -> str | None:
        if readiness.status == "blocked":
            return readiness.blocked_reasons[0] if readiness.blocked_reasons else "Execution readiness is blocked."
        if strategy.current_stage != "production":
            return "Only production strategies may submit orders through the governed execution path."
        if request.quantity <= 0 or request.reference_price <= 0:
            return "Quantity and reference price must both be positive."
        if not policy.allow_fractional and float(request.quantity).is_integer() is False:
            return "Fractional quantity is not allowed by the active allocation policy."
        if not broker_capability["supports_fractional"] and float(request.quantity).is_integer() is False:
            return "The active broker capability does not support fractional quantity."

        asset_type = request.asset_type.lower()
        weighted_requested_notional = self._risk_weighted_notional(
            notional=max(requested_notional, capital_profile.effective_notional),
            instrument=instrument,
            asset_type=asset_type,
        )
        expands_exposure = True
        if request.side == "sell" and current_position is not None and current_position.direction == "long":
            expands_exposure = request.quantity > current_position.quantity
        elif request.side == "buy" and current_position is not None and current_position.direction == "short":
            expands_exposure = request.quantity > current_position.quantity

        if asset_type == "option":
            if instrument is None and len(order_legs) <= 1:
                return "Option orders require a registered canonical instrument."
            if request.position_effect == "auto":
                return "Option orders must specify position_effect explicitly."
            if not broker_capability["supports_options"]:
                return "The active broker capability does not support options trading."
            expands_exposure = request.position_effect in {"open", "increase"}
            if len(order_legs) > 1 and not broker_capability["supports_multi_leg_options"]:
                return "The active broker capability does not support multi-leg option execution."
            if len(order_legs) > 1:
                underlying_symbols = {
                    (leg.underlying_symbol or leg.symbol).upper()
                    for leg in order_legs
                }
                if len(underlying_symbols) != 1:
                    return "Multi-leg option execution requires all legs to share one underlying symbol."
        elif asset_type in {"equity", "crypto", "custom"}:
            if not broker_capability["supports_equities"]:
                return "The active broker capability does not support this equity-like product."
        elif asset_type in {"etf", "leveraged_etf", "inverse_etf"}:
            if not broker_capability["supports_etfs"]:
                return "The active broker capability does not support ETF products."
        else:
            return f"Unsupported asset_type for governed execution: {request.asset_type}"
        if len(order_legs) > 1 and asset_type != "option":
            return "Multi-leg order structures are only modeled for option instruments right now."

        if asset_type == "option" and instrument is not None and instrument.status != "active":
            return "The referenced option instrument is not active."
        if latest_snapshot is None:
            return "No broker account snapshot is available for allocation validation."

        equity = max(latest_snapshot.equity, 0.0)
        if equity <= 0:
            return "Broker equity is not positive, so order sizing cannot be validated."

        max_strategy_notional = equity * policy.max_strategy_notional_pct
        if expands_exposure and weighted_requested_notional > max_strategy_notional:
            return (
                f"Requested notional {weighted_requested_notional:.2f} exceeds the strategy cap "
                f"{max_strategy_notional:.2f}."
            )

        if related_symbol_conflicts:
            return (
                "A related symbol for this order is already held by another strategy in the same broker account. "
                "Cross-strategy symbol netting is blocked until sleeve attribution is implemented."
            )

        if request.side == "sell" and current_position is None and not policy.allow_short:
            return "Cannot open a short position because the active allocation policy disables shorting."
        if (
            request.side == "sell"
            and asset_type != "option"
            and current_position is None
            and policy.allow_short
            and not broker_capability["supports_short"]
        ):
            return "The active broker capability does not support short selling."
        if request.side == "sell" and current_position is not None and current_position.direction == "short" and not policy.allow_short:
            return "Cannot increase a short position because the active allocation policy disables shorting."
        if (
            request.side == "sell"
            and asset_type != "option"
            and current_position is not None
            and current_position.direction == "short"
            and policy.allow_short
            and not broker_capability["supports_short"]
        ):
            return "The active broker capability does not support short selling."

        if request.side == "sell" and current_position is not None and request.quantity > current_position.quantity and not policy.allow_short:
            return "Sell quantity exceeds the active long position and shorting is disabled."
        if (
            request.side == "sell"
            and asset_type != "option"
            and current_position is not None
            and request.quantity > current_position.quantity
            and policy.allow_short
            and not broker_capability["supports_short"]
        ):
            return "The active broker capability does not support short selling."
        if asset_type == "option" and request.side == "sell" and current_position is not None and request.quantity > current_position.quantity:
            return "Option sell quantity exceeds the active long contracts."

        if request.side == "sell" and policy.allow_short and not broker_capability["supports_margin"] and asset_type != "option":
            if current_position is None or current_position.direction == "short" or request.quantity > current_position.quantity:
                return "Opening short exposure requires a margin-capable broker/account mode."

        borrow_reason = self._borrow_constraint_reason(
            request=request,
            instrument=instrument,
            current_position=current_position,
        )
        if borrow_reason is not None:
            return borrow_reason

        projected_gross = capital_profile.projected_gross_exposure

        max_gross = equity * policy.max_gross_exposure_pct
        weighted_projected_gross = self._risk_weighted_notional(
            notional=projected_gross,
            instrument=instrument,
            asset_type=asset_type,
        )
        if weighted_projected_gross > max_gross:
            return f"Projected gross exposure {weighted_projected_gross:.2f} exceeds the portfolio cap {max_gross:.2f}."

        margin_account = broker_capability["supports_margin"] or broker_capability["account_mode"] in {
            "margin",
            "portfolio_margin",
        }
        available_funds = max(latest_snapshot.buying_power, 0.0) if margin_account else max(latest_snapshot.cash, 0.0)
        if capital_profile.liquidity_need > available_funds:
            if margin_account:
                return "Requested exposure exceeds broker buying power after reserve and roll-release adjustments."
            return "Requested exposure exceeds available cash after reserve and roll-release adjustments."
        if expands_exposure and capital_profile.projected_maintenance_requirement > equity:
            if capital_profile.projected_maintenance_requirement > capital_profile.current_maintenance_requirement + 1e-6:
                return (
                    f"Projected maintenance requirement {capital_profile.projected_maintenance_requirement:.2f} "
                    f"exceeds account equity {equity:.2f}."
                )
        if asset_type == "option" and request.side == "buy" and request.position_effect in {"open", "increase"} and not broker_capability["supports_paper_trading"] and request.environment == "paper":
            return "The active broker capability does not support paper trading for this options path."

        active_position_count = sum(1 for position in active_positions if position.status == "active")
        if current_position is None and active_position_count >= policy.max_open_positions:
            return "The active position count has reached the allocation-policy limit."

        if open_orders_count >= policy.max_open_orders:
            return "The open-order count has reached the allocation-policy limit."

        return None

    def _count_open_orders(
        self,
        session: Session,
        *,
        provider_key: str,
        account_ref: str,
        environment: str,
    ) -> int:
        return int(
            session.scalar(
                select(func.count())
                .select_from(OrderRecordModel)
                .where(
                    OrderRecordModel.provider_key == provider_key,
                    OrderRecordModel.account_ref == account_ref,
                    OrderRecordModel.environment == environment,
                    OrderRecordModel.status.in_(("accepted", "submitted", "partially_filled")),
                )
            )
            or 0
        )

    def _active_position_model(
        self,
        session: Session,
        *,
        provider_key: str,
        account_ref: str,
        environment: str,
        symbol: str,
    ) -> PositionRecordModel | None:
        return session.scalar(
            select(PositionRecordModel).where(
                PositionRecordModel.provider_key == provider_key,
                PositionRecordModel.account_ref == account_ref,
                PositionRecordModel.environment == environment,
                PositionRecordModel.symbol == symbol.upper(),
                PositionRecordModel.status == "active",
            )
        )

    def _active_positions_for_symbol(
        self,
        session: Session,
        *,
        provider_key: str,
        account_ref: str,
        environment: str,
        symbol: str,
    ) -> list[PositionRecordModel]:
        return session.scalars(
            select(PositionRecordModel).where(
                PositionRecordModel.provider_key == provider_key,
                PositionRecordModel.account_ref == account_ref,
                PositionRecordModel.environment == environment,
                PositionRecordModel.symbol == symbol.upper(),
                PositionRecordModel.status == "active",
            )
        ).all()

    def _active_positions(
        self,
        session: Session,
        *,
        provider_key: str,
        account_ref: str,
        environment: str,
    ) -> list[PositionRecordModel]:
        return session.scalars(
            select(PositionRecordModel).where(
                PositionRecordModel.provider_key == provider_key,
                PositionRecordModel.account_ref == account_ref,
                PositionRecordModel.environment == environment,
                PositionRecordModel.status == "active",
            )
        ).all()

    def _client_order_id(self, intent_id: str) -> str:
        return f"qe-{intent_id}"

    def _intent_id_from_client_order_id(self, client_order_id: str | None) -> str | None:
        if client_order_id is None or not client_order_id.startswith("qe-"):
            return None
        intent_id = client_order_id[3:]
        return intent_id or None

    def _broker_order_state_from_record(self, row: OrderRecordModel) -> BrokerOrderState:
        return BrokerOrderState(
            broker_order_id=row.broker_order_id,
            client_order_id=row.client_order_id,
            symbol=row.symbol,
            instrument_id=row.instrument_id,
            instrument_key=row.instrument_key,
            underlying_symbol=row.underlying_symbol,
            asset_type=row.asset_type,
            position_effect=row.position_effect,
            side=row.side,
            order_type=row.order_type,
            time_in_force=row.time_in_force,
            quantity=row.quantity,
            filled_quantity=row.filled_quantity,
            requested_notional=row.requested_notional,
            avg_fill_price=row.avg_fill_price,
            limit_price=row.limit_price,
            stop_price=row.stop_price,
            status=row.status,
            broker_updated_at=_coerce_utc(row.broker_updated_at or row.submitted_at),
            raw_payload=row.raw_payload,
        )

    def _upsert_order_from_sync(
        self,
        session: Session,
        *,
        order_state: BrokerOrderState,
        provider_key: str,
        account_ref: str,
        environment: str,
        sync_run_id: str,
        created_by: str,
        origin_type: str,
        origin_id: str | None,
    ) -> OrderRecordModel | None:
        order_record = session.scalar(
            select(OrderRecordModel).where(OrderRecordModel.broker_order_id == order_state.broker_order_id)
        )
        if order_record is None and order_state.client_order_id:
            order_record = session.scalar(
                select(OrderRecordModel).where(OrderRecordModel.client_order_id == order_state.client_order_id)
            )

        intent: OrderIntentModel | None = None
        if order_record is None:
            intent_id = self._intent_id_from_client_order_id(order_state.client_order_id)
            if intent_id is None:
                return None
            intent = session.get(OrderIntentModel, intent_id)
            if intent is None:
                return None
            order_record = OrderRecordModel(
                order_intent_id=intent.id,
                strategy_spec_id=intent.strategy_spec_id,
                provider_key=provider_key,
                account_ref=account_ref,
                environment=environment,
                broker_order_id=order_state.broker_order_id,
                client_order_id=order_state.client_order_id,
                symbol=order_state.symbol.upper(),
                instrument_id=intent.instrument_id,
                instrument_key=intent.instrument_key,
                underlying_symbol=intent.underlying_symbol,
                asset_type=order_state.asset_type,
                position_effect=intent.position_effect if order_state.position_effect == "auto" else order_state.position_effect,
                side=order_state.side,
                order_type=order_state.order_type,
                time_in_force=order_state.time_in_force,
                quantity=order_state.quantity,
                filled_quantity=order_state.filled_quantity,
                requested_notional=order_state.requested_notional,
                avg_fill_price=order_state.avg_fill_price,
                limit_price=order_state.limit_price,
                stop_price=order_state.stop_price,
                submitted_at=order_state.broker_updated_at,
                broker_updated_at=order_state.broker_updated_at,
                raw_payload=order_state.raw_payload,
                last_sync_run_id=sync_run_id,
                created_by=created_by,
                origin_type=origin_type,
                origin_id=origin_id,
                status=order_state.status,
            )
            session.add(order_record)
        else:
            intent = session.get(OrderIntentModel, order_record.order_intent_id)
            order_record.client_order_id = order_state.client_order_id
            order_record.symbol = order_state.symbol.upper()
            order_record.instrument_id = order_record.instrument_id or (intent.instrument_id if intent is not None else None)
            order_record.instrument_key = order_record.instrument_key or (intent.instrument_key if intent is not None else None)
            order_record.underlying_symbol = order_record.underlying_symbol or (
                intent.underlying_symbol if intent is not None else None
            )
            order_record.asset_type = self._merge_synced_asset_type(
                current_asset_type=order_record.asset_type,
                synced_asset_type=order_state.asset_type,
                raw_payload=order_state.raw_payload,
            )
            if order_state.position_effect != "auto":
                order_record.position_effect = order_state.position_effect
            order_record.side = order_state.side
            order_record.order_type = order_state.order_type
            order_record.time_in_force = order_state.time_in_force
            order_record.quantity = order_state.quantity
            order_record.filled_quantity = order_state.filled_quantity
            order_record.requested_notional = order_state.requested_notional
            order_record.avg_fill_price = order_state.avg_fill_price
            order_record.limit_price = order_state.limit_price
            order_record.stop_price = order_state.stop_price
            order_record.broker_updated_at = order_state.broker_updated_at
            order_record.raw_payload = order_state.raw_payload
            order_record.last_sync_run_id = sync_run_id
            order_record.status = order_state.status

        if intent is not None:
            intent.status = order_state.status
            if order_state.status in {"filled", "partially_filled"}:
                intent.decision_reason = "Broker sync confirmed execution state."
            elif order_state.status in {"canceled", "replaced", "sync_missing"}:
                intent.decision_reason = f"Broker sync updated order status to `{order_state.status}`."
        session.flush()
        return order_record

    def _resolve_position_strategy_spec_id(
        self,
        session: Session,
        *,
        provider_key: str,
        account_ref: str,
        environment: str,
        symbol: str,
    ) -> str | None:
        active_positions = self._active_positions_for_symbol(
            session,
            provider_key=provider_key,
            account_ref=account_ref,
            environment=environment,
            symbol=symbol,
        )
        strategy_ids = {position.strategy_spec_id for position in active_positions}
        if len(strategy_ids) == 1:
            return next(iter(strategy_ids))
        if len(strategy_ids) > 1:
            return None

        recent_orders = session.scalars(
            select(OrderRecordModel)
            .where(
                OrderRecordModel.provider_key == provider_key,
                OrderRecordModel.account_ref == account_ref,
                OrderRecordModel.environment == environment,
                OrderRecordModel.symbol == symbol.upper(),
            )
            .order_by(OrderRecordModel.broker_updated_at.desc(), OrderRecordModel.created_at.desc())
        ).all()
        order_strategy_ids = {order.strategy_spec_id for order in recent_orders}
        if len(order_strategy_ids) == 1:
            return next(iter(order_strategy_ids))
        return None

    def _upsert_position_from_sync(
        self,
        session: Session,
        *,
        position_state: PositionState,
        provider_key: str,
        account_ref: str,
        environment: str,
        sync_run_id: str,
        created_by: str,
        origin_type: str,
        origin_id: str | None,
    ) -> PositionRecordModel | None:
        current_time = datetime.now(tz=UTC)
        existing_positions = self._active_positions_for_symbol(
            session,
            provider_key=provider_key,
            account_ref=account_ref,
            environment=environment,
            symbol=position_state.symbol,
        )

        position_record: PositionRecordModel | None = None
        if len(existing_positions) == 1:
            position_record = existing_positions[0]
        elif len(existing_positions) > 1:
            return None

        strategy_spec_id = (
            position_record.strategy_spec_id
            if position_record is not None
            else self._resolve_position_strategy_spec_id(
                session,
                provider_key=provider_key,
                account_ref=account_ref,
                environment=environment,
                symbol=position_state.symbol,
            )
        )
        if strategy_spec_id is None:
            return None

        market_price = position_state.market_price or position_state.avg_entry_price
        notional_value = self._position_market_value(
            quantity=position_state.quantity,
            market_price=market_price,
            contract_multiplier=position_state.contract_multiplier,
        )
        unrealized_pnl = self._compute_unrealized_pnl(
            direction=position_state.direction,
            quantity=position_state.quantity,
            avg_entry_price=position_state.avg_entry_price,
            market_price=market_price,
            contract_multiplier=position_state.contract_multiplier,
        )
        raw_payload = position_state.raw_payload or {}

        if position_record is not None:
            position_record.instrument_id = position_state.instrument_id
            position_record.instrument_key = position_state.instrument_key
            position_record.underlying_symbol = position_state.underlying_symbol
            position_record.asset_type = self._merge_synced_asset_type(
                current_asset_type=position_record.asset_type,
                synced_asset_type=position_state.asset_type,
                raw_payload=position_state.raw_payload,
            )
            position_record.direction = position_state.direction
            position_record.quantity = position_state.quantity
            position_record.avg_entry_price = position_state.avg_entry_price
            position_record.market_price = market_price
            position_record.notional_value = notional_value
            if self._sync_realized_pnl_known(position_state.raw_payload):
                position_record.realized_pnl = position_state.realized_pnl
            position_record.unrealized_pnl = unrealized_pnl
            position_record.last_synced_at = current_time
            position_record.last_sync_run_id = sync_run_id
            position_record.raw_payload = raw_payload
            position_record.status = "active" if position_state.quantity > 0 else "closed"
            if position_state.quantity <= 0:
                position_record.closed_at = current_time
            return position_record

        position_record = PositionRecordModel(
            strategy_spec_id=strategy_spec_id,
            provider_key=provider_key,
            account_ref=account_ref,
            environment=environment,
            symbol=position_state.symbol.upper(),
            instrument_id=position_state.instrument_id,
            instrument_key=position_state.instrument_key,
            underlying_symbol=position_state.underlying_symbol,
            asset_type=position_state.asset_type,
            direction=position_state.direction,
            quantity=position_state.quantity,
            avg_entry_price=position_state.avg_entry_price,
            market_price=market_price,
            notional_value=notional_value,
            realized_pnl=position_state.realized_pnl,
            unrealized_pnl=unrealized_pnl,
            opened_at=current_time,
            last_synced_at=current_time,
            last_sync_run_id=sync_run_id,
            raw_payload=raw_payload,
            created_by=created_by,
            origin_type=origin_type,
            origin_id=origin_id,
            status="active" if position_state.quantity > 0 else "closed",
        )
        if position_state.quantity <= 0:
            position_record.closed_at = current_time
        session.add(position_record)
        session.flush()
        return position_record

    def _mark_missing_internal_orders(
        self,
        session: Session,
        *,
        provider_key: str,
        account_ref: str,
        environment: str,
        synced_order_ids: set[str],
        sync_run_id: str,
    ) -> int:
        current_time = datetime.now(tz=UTC)
        missing = session.scalars(
            select(OrderRecordModel).where(
                OrderRecordModel.provider_key == provider_key,
                OrderRecordModel.account_ref == account_ref,
                OrderRecordModel.environment == environment,
                OrderRecordModel.status.in_(("accepted", "submitted", "partially_filled")),
            )
        ).all()
        affected = 0
        for order in missing:
            if order.id in synced_order_ids:
                continue
            payload = dict(order.raw_payload or {})
            payload["sync_missing"] = True
            payload["sync_missing_at"] = current_time.isoformat()
            order.status = "sync_missing"
            order.broker_updated_at = current_time
            order.last_sync_run_id = sync_run_id
            order.raw_payload = payload
            intent = session.get(OrderIntentModel, order.order_intent_id)
            if intent is not None:
                intent.status = "sync_missing"
                intent.decision_reason = "Broker sync could not find this open order remotely."
            affected += 1
        return affected

    def _mark_missing_internal_positions(
        self,
        session: Session,
        *,
        provider_key: str,
        account_ref: str,
        environment: str,
        synced_position_ids: set[str],
        sync_run_id: str,
    ) -> int:
        current_time = datetime.now(tz=UTC)
        missing = self._active_positions(
            session,
            provider_key=provider_key,
            account_ref=account_ref,
            environment=environment,
        )
        affected = 0
        for position in missing:
            if position.id in synced_position_ids:
                continue
            payload = dict(position.raw_payload or {})
            payload["sync_missing"] = True
            payload["sync_missing_at"] = current_time.isoformat()
            position.status = "sync_missing"
            position.quantity = 0.0
            position.notional_value = 0.0
            position.unrealized_pnl = 0.0
            position.closed_at = current_time
            position.last_synced_at = current_time
            position.last_sync_run_id = sync_run_id
            position.raw_payload = payload
            affected += 1
        return affected

    def _apply_position_update(
        self,
        session: Session,
        *,
        current_position: PositionRecordModel | None,
        result,
        request: OrderIntentCreate,
        provider_key: str,
        account_ref: str,
    ) -> PositionRecordModel | None:
        if result.resulting_position is None:
            return current_position

        current_time = datetime.now(tz=UTC)
        market_price = (
            result.resulting_position.market_price
            or result.avg_fill_price
            or request.reference_price
        )
        raw_payload = result.resulting_position.raw_payload or {"adapter_mode": "paper_sim"}
        if current_position is not None:
            current_position.instrument_id = result.resulting_position.instrument_id
            current_position.instrument_key = result.resulting_position.instrument_key
            current_position.underlying_symbol = result.resulting_position.underlying_symbol
            current_position.asset_type = result.resulting_position.asset_type
            current_position.direction = result.resulting_position.direction
            current_position.quantity = result.resulting_position.quantity
            current_position.avg_entry_price = result.resulting_position.avg_entry_price
            current_position.market_price = market_price
            current_position.realized_pnl = result.resulting_position.realized_pnl
            current_position.notional_value = self._position_market_value(
                quantity=result.resulting_position.quantity,
                market_price=market_price,
                contract_multiplier=result.resulting_position.contract_multiplier,
            )
            current_position.unrealized_pnl = self._compute_unrealized_pnl(
                direction=result.resulting_position.direction,
                quantity=result.resulting_position.quantity,
                avg_entry_price=result.resulting_position.avg_entry_price,
                market_price=market_price,
                contract_multiplier=result.resulting_position.contract_multiplier,
            )
            current_position.last_synced_at = current_time
            current_position.raw_payload = raw_payload
            if result.closed_position or result.resulting_position.quantity <= 0:
                current_position.status = "closed"
                current_position.closed_at = current_time
                current_position.notional_value = 0.0
                current_position.unrealized_pnl = 0.0
            return current_position

        position_record = PositionRecordModel(
            strategy_spec_id=request.strategy_spec_id,
            provider_key=provider_key,
            account_ref=account_ref,
            environment=request.environment,
            symbol=request.symbol.upper(),
            instrument_id=result.resulting_position.instrument_id or request.instrument_id,
            instrument_key=result.resulting_position.instrument_key or request.instrument_key,
            underlying_symbol=result.resulting_position.underlying_symbol,
            asset_type=result.resulting_position.asset_type,
            direction=result.resulting_position.direction,
            quantity=result.resulting_position.quantity,
            avg_entry_price=result.resulting_position.avg_entry_price,
            market_price=market_price,
            notional_value=self._position_market_value(
                quantity=result.resulting_position.quantity,
                market_price=market_price,
                contract_multiplier=result.resulting_position.contract_multiplier,
            ),
            realized_pnl=result.resulting_position.realized_pnl,
            unrealized_pnl=self._compute_unrealized_pnl(
                direction=result.resulting_position.direction,
                quantity=result.resulting_position.quantity,
                avg_entry_price=result.resulting_position.avg_entry_price,
                market_price=market_price,
                contract_multiplier=result.resulting_position.contract_multiplier,
            ),
            opened_at=current_time,
            last_synced_at=current_time,
            raw_payload=raw_payload,
            created_by=request.created_by,
            origin_type=request.origin_type,
            origin_id=request.origin_id,
            status="active",
        )
        session.add(position_record)
        session.flush()
        return position_record

    def _record_projected_snapshot(
        self,
        session: Session,
        *,
        provider_key: str,
        account_ref: str,
        environment: str,
        source_snapshot: BrokerAccountSnapshotModel | None,
        created_by: str,
        origin_type: str,
        origin_id: str | None,
    ) -> None:
        session.flush()
        positions = self._active_positions(
            session,
            provider_key=provider_key,
            account_ref=account_ref,
            environment=environment,
        )
        all_positions = session.scalars(
            select(PositionRecordModel).where(
                PositionRecordModel.provider_key == provider_key,
                PositionRecordModel.account_ref == account_ref,
                PositionRecordModel.environment == environment,
            )
        ).all()
        gross_exposure = sum(position.notional_value for position in positions if position.status == "active")
        net_exposure = sum(
            position.notional_value if position.direction == "long" else -position.notional_value
            for position in positions
            if position.status == "active"
        )
        realized_pnl = sum(position.realized_pnl for position in all_positions)
        base_equity = source_snapshot.equity if source_snapshot is not None else 0.0
        projected_equity = base_equity + realized_pnl
        projected_cash = max(0.0, projected_equity - gross_exposure)
        projected_buying_power = max(0.0, projected_equity - gross_exposure)
        snapshot = BrokerAccountSnapshotModel(
            provider_key=provider_key,
            account_ref=account_ref,
            environment=environment,
            equity=projected_equity,
            cash=projected_cash,
            buying_power=projected_buying_power,
            gross_exposure=gross_exposure,
            net_exposure=net_exposure,
            positions_count=sum(1 for position in positions if position.status == "active"),
            open_orders_count=self._count_open_orders(
                session,
                provider_key=provider_key,
                account_ref=account_ref,
                environment=environment,
            ),
            source_captured_at=datetime.now(tz=UTC),
            source_age_seconds=0,
            payload={"source": "paper_adapter_projection"},
            created_by=created_by,
            origin_type=origin_type,
            origin_id=origin_id,
            status="captured",
        )
        session.add(snapshot)

    def _compute_unrealized_pnl(
        self,
        *,
        direction: str,
        quantity: float,
        avg_entry_price: float,
        market_price: float,
        contract_multiplier: float = 1.0,
    ) -> float:
        if direction == "short":
            return (avg_entry_price - market_price) * quantity * contract_multiplier
        return (market_price - avg_entry_price) * quantity * contract_multiplier

    def _upsert_broker_capability_model(
        self,
        session: Session,
        *,
        provider_key: str,
        account_ref: str,
        environment: str,
        broker_adapter: str,
        payload: dict[str, Any],
        created_by: str,
        origin_type: str,
        origin_id: str | None,
    ) -> None:
        capability_key = str(payload.get("capability_key") or f"{provider_key}:{broker_adapter}:{environment}")
        capability = session.scalar(
            select(BrokerCapabilityModel).where(BrokerCapabilityModel.capability_key == capability_key)
        )
        if capability is None:
            capability = BrokerCapabilityModel(
                capability_key=capability_key,
                created_by=created_by,
                origin_type=origin_type,
                origin_id=origin_id,
                status="active",
            )
            session.add(capability)

        capability.provider_key = provider_key
        capability.broker_adapter = broker_adapter
        capability.account_ref = str(payload.get("account_ref") or account_ref)
        capability.environment = environment
        capability.account_mode = str(payload.get("account_mode") or ("paper" if environment == "paper" else "cash"))
        capability.supports_equities = bool(payload.get("supports_equities", True))
        capability.supports_etfs = bool(payload.get("supports_etfs", True))
        capability.supports_fractional = bool(payload.get("supports_fractional", False))
        capability.supports_short = bool(payload.get("supports_short", False))
        capability.supports_margin = bool(payload.get("supports_margin", False))
        capability.supports_options = bool(payload.get("supports_options", False))
        capability.supports_multi_leg_options = bool(payload.get("supports_multi_leg_options", False))
        capability.supports_option_exercise = bool(payload.get("supports_option_exercise", False))
        capability.supports_option_assignment_events = bool(payload.get("supports_option_assignment_events", False))
        capability.supports_live_trading = bool(payload.get("supports_live_trading", environment != "paper"))
        capability.supports_paper_trading = bool(payload.get("supports_paper_trading", environment == "paper"))
        capability.notes = payload.get("notes")
        capability.status = "active"

    def _merge_synced_asset_type(
        self,
        *,
        current_asset_type: str | None,
        synced_asset_type: str,
        raw_payload: dict[str, Any] | None,
    ) -> str:
        if synced_asset_type != "equity":
            return synced_asset_type
        if not current_asset_type:
            return synced_asset_type
        if isinstance(raw_payload, dict) and raw_payload.get("asset_type_exact") is False:
            if current_asset_type in {"etf", "leveraged_etf", "inverse_etf"}:
                return current_asset_type
        return synced_asset_type

    def _sync_realized_pnl_known(self, raw_payload: dict[str, Any] | None) -> bool:
        if not isinstance(raw_payload, dict):
            return True
        return bool(raw_payload.get("sync_realized_pnl_known", True))

    def _instrument_summary(self, row: InstrumentDefinitionModel) -> InstrumentDefinitionSummary:
        return InstrumentDefinitionSummary(
            id=row.id,
            instrument_key=row.instrument_key,
            symbol=row.symbol,
            display_symbol=row.display_symbol,
            instrument_type=row.instrument_type,
            venue=row.venue,
            currency=row.currency,
            underlying_symbol=row.underlying_symbol,
            option_right=row.option_right,
            option_style=row.option_style,
            expiration_date=row.expiration_date,
            strike_price=row.strike_price,
            contract_multiplier=row.contract_multiplier,
            leverage_ratio=row.leverage_ratio,
            inverse_exposure=row.inverse_exposure,
            is_marginable=row.is_marginable,
            is_shortable=row.is_shortable,
            metadata_payload=row.metadata_payload,
            status=row.status,
            updated_at=row.updated_at,
        )

    def _broker_capability_summary(self, row: BrokerCapabilityModel) -> BrokerCapabilitySummary:
        return BrokerCapabilitySummary(
            id=row.id,
            capability_key=row.capability_key,
            provider_key=row.provider_key,
            broker_adapter=row.broker_adapter,
            account_ref=row.account_ref,
            environment=row.environment,
            account_mode=row.account_mode,
            supports_equities=row.supports_equities,
            supports_etfs=row.supports_etfs,
            supports_fractional=row.supports_fractional,
            supports_short=row.supports_short,
            supports_margin=row.supports_margin,
            supports_options=row.supports_options,
            supports_multi_leg_options=row.supports_multi_leg_options,
            supports_option_exercise=row.supports_option_exercise,
            supports_option_assignment_events=row.supports_option_assignment_events,
            supports_live_trading=row.supports_live_trading,
            supports_paper_trading=row.supports_paper_trading,
            notes=row.notes,
            status=row.status,
            updated_at=row.updated_at,
        )

    def _allocation_policy_summary(self, row: AllocationPolicyModel) -> AllocationPolicySummary:
        return AllocationPolicySummary(
            id=row.id,
            policy_key=row.policy_key,
            environment=row.environment,
            scope=row.scope,
            strategy_spec_id=row.strategy_spec_id,
            provider_key=row.provider_key,
            account_ref=row.account_ref,
            max_strategy_notional_pct=row.max_strategy_notional_pct,
            max_gross_exposure_pct=row.max_gross_exposure_pct,
            max_open_positions=row.max_open_positions,
            max_open_orders=row.max_open_orders,
            allow_short=row.allow_short,
            allow_fractional=row.allow_fractional,
            notes=row.notes,
            status=row.status,
            updated_at=row.updated_at,
        )

    def _load_order_legs(
        self,
        session: Session,
        *,
        order_intent_id: str | None = None,
        order_record_id: str | None = None,
    ) -> list[OrderLegSummary]:
        query = select(OrderLegModel).order_by(OrderLegModel.leg_index.asc(), OrderLegModel.created_at.asc())
        if order_record_id is not None:
            query = query.where(OrderLegModel.order_record_id == order_record_id)
        elif order_intent_id is not None:
            query = query.where(OrderLegModel.order_intent_id == order_intent_id)
        else:
            return []
        rows = session.scalars(query).all()
        return [self._order_leg_summary(row) for row in rows]

    def _order_intent_summary(self, row: OrderIntentModel, *, session: Session) -> OrderIntentSummary:
        legs = self._load_order_legs(session, order_intent_id=row.id)
        return OrderIntentSummary(
            id=row.id,
            strategy_spec_id=row.strategy_spec_id,
            allocation_policy_id=row.allocation_policy_id,
            provider_key=row.provider_key,
            account_ref=row.account_ref,
            environment=row.environment,
            broker_adapter=row.broker_adapter,
            symbol=row.symbol,
            instrument_id=row.instrument_id,
            instrument_key=row.instrument_key,
            underlying_symbol=row.underlying_symbol,
            asset_type=row.asset_type,
            position_effect=row.position_effect,
            side=row.side,
            order_type=row.order_type,
            time_in_force=row.time_in_force,
            quantity=row.quantity,
            reference_price=row.reference_price,
            requested_notional=row.requested_notional,
            decision_reason=row.decision_reason,
            rationale=row.rationale,
            leg_count=len(legs),
            legs=legs,
            status=row.status,
            created_at=row.created_at,
        )

    def _broker_sync_run_summary(self, row: BrokerSyncRunModel) -> BrokerSyncRunSummary:
        return BrokerSyncRunSummary(
            id=row.id,
            provider_key=row.provider_key,
            account_ref=row.account_ref,
            environment=row.environment,
            broker_adapter=row.broker_adapter,
            sync_scope=row.sync_scope,
            account_snapshot_id=row.account_snapshot_id,
            synced_orders_count=row.synced_orders_count,
            synced_positions_count=row.synced_positions_count,
            unmanaged_orders_count=row.unmanaged_orders_count,
            unmanaged_positions_count=row.unmanaged_positions_count,
            missing_internal_orders_count=row.missing_internal_orders_count,
            missing_internal_positions_count=row.missing_internal_positions_count,
            notes=row.notes,
            status=row.status,
            started_at=row.started_at,
            completed_at=row.completed_at,
            created_at=row.created_at,
        )

    def _order_record_summary(self, row: OrderRecordModel, *, session: Session) -> OrderRecordSummary:
        legs = self._load_order_legs(session, order_record_id=row.id)
        return OrderRecordSummary(
            id=row.id,
            order_intent_id=row.order_intent_id,
            strategy_spec_id=row.strategy_spec_id,
            provider_key=row.provider_key,
            account_ref=row.account_ref,
            environment=row.environment,
            broker_order_id=row.broker_order_id,
            client_order_id=row.client_order_id,
            parent_order_record_id=row.parent_order_record_id,
            last_sync_run_id=row.last_sync_run_id,
            symbol=row.symbol,
            instrument_id=row.instrument_id,
            instrument_key=row.instrument_key,
            underlying_symbol=row.underlying_symbol,
            asset_type=row.asset_type,
            position_effect=row.position_effect,
            side=row.side,
            order_type=row.order_type,
            time_in_force=row.time_in_force,
            quantity=row.quantity,
            filled_quantity=row.filled_quantity,
            requested_notional=row.requested_notional,
            avg_fill_price=row.avg_fill_price,
            leg_count=len(legs),
            legs=legs,
            status=row.status,
            submitted_at=row.submitted_at,
            broker_updated_at=row.broker_updated_at,
            created_at=row.created_at,
        )

    def _position_summary(self, row: PositionRecordModel) -> PositionRecordSummary:
        return PositionRecordSummary(
            id=row.id,
            strategy_spec_id=row.strategy_spec_id,
            provider_key=row.provider_key,
            account_ref=row.account_ref,
            environment=row.environment,
            symbol=row.symbol,
            instrument_id=row.instrument_id,
            instrument_key=row.instrument_key,
            underlying_symbol=row.underlying_symbol,
            asset_type=row.asset_type,
            direction=row.direction,
            quantity=row.quantity,
            avg_entry_price=row.avg_entry_price,
            market_price=row.market_price,
            notional_value=row.notional_value,
            realized_pnl=row.realized_pnl,
            unrealized_pnl=row.unrealized_pnl,
            status=row.status,
            opened_at=row.opened_at,
            closed_at=row.closed_at,
            last_synced_at=row.last_synced_at,
            last_sync_run_id=row.last_sync_run_id,
            created_at=row.created_at,
        )

    def _market_state_summary(self, row: MarketCalendarStateModel) -> MarketSessionStateSummary:
        return MarketSessionStateSummary(
            id=row.id,
            market_calendar=row.market_calendar,
            market_timezone=row.market_timezone,
            session_label=row.session_label,
            is_market_open=row.is_market_open,
            trading_allowed=row.trading_allowed,
            next_open_at=row.next_open_at,
            next_close_at=row.next_close_at,
            created_at=row.created_at,
        )

    def _account_snapshot_summary(self, row: BrokerAccountSnapshotModel) -> BrokerAccountSnapshotSummary:
        return BrokerAccountSnapshotSummary(
            id=row.id,
            provider_key=row.provider_key,
            account_ref=row.account_ref,
            environment=row.environment,
            equity=row.equity,
            cash=row.cash,
            buying_power=row.buying_power,
            gross_exposure=row.gross_exposure,
            net_exposure=row.net_exposure,
            positions_count=row.positions_count,
            open_orders_count=row.open_orders_count,
            source_captured_at=row.source_captured_at,
            source_age_seconds=row.source_age_seconds,
            payload=row.payload,
            created_at=row.created_at,
        )

    def _reconciliation_summary(self, row: ReconciliationRunModel) -> ReconciliationRunSummary:
        return ReconciliationRunSummary(
            id=row.id,
            provider_key=row.provider_key,
            account_ref=row.account_ref,
            account_snapshot_id=row.account_snapshot_id,
            environment=row.environment,
            internal_equity=row.internal_equity,
            broker_equity=row.broker_equity,
            equity_delta_abs=row.equity_delta_abs,
            equity_delta_pct=row.equity_delta_pct,
            internal_positions_count=row.internal_positions_count,
            broker_positions_count=row.broker_positions_count,
            internal_open_orders_count=row.internal_open_orders_count,
            broker_open_orders_count=row.broker_open_orders_count,
            position_delta_count=row.position_delta_count,
            order_delta_count=row.order_delta_count,
            blocking_reason=row.blocking_reason,
            notes=row.notes,
            halt_triggered=row.halt_triggered,
            status=row.status,
            checked_at=row.checked_at,
            created_at=row.created_at,
        )

    def _provider_incident_summary(self, row: ProviderIncidentModel) -> ProviderIncidentSummary:
        return ProviderIncidentSummary(
            id=row.id,
            provider_key=row.provider_key,
            title=row.title,
            summary=row.summary,
            severity=row.severity,
            status=row.status,
            detected_at=row.detected_at,
            resolved_at=row.resolved_at,
            created_at=row.created_at,
        )

    def _order_leg_summary(self, row: OrderLegModel) -> OrderLegSummary:
        return OrderLegSummary(
            id=row.id,
            order_intent_id=row.order_intent_id,
            order_record_id=row.order_record_id,
            leg_index=row.leg_index,
            symbol=row.symbol,
            instrument_id=row.instrument_id,
            instrument_key=row.instrument_key,
            underlying_symbol=row.underlying_symbol,
            asset_type=row.asset_type,
            side=row.side,
            position_effect=row.position_effect,
            quantity=row.quantity,
            ratio_quantity=row.ratio_quantity,
            reference_price=row.reference_price,
            requested_notional=row.requested_notional,
            status=row.status,
            created_at=row.created_at,
        )

    def _option_lifecycle_event_summary(self, row: OptionLifecycleEventModel) -> OptionLifecycleEventSummary:
        return OptionLifecycleEventSummary(
            id=row.id,
            event_type=row.event_type,
            provider_key=row.provider_key,
            account_ref=row.account_ref,
            environment=row.environment,
            symbol=row.symbol,
            underlying_symbol=row.underlying_symbol,
            position_id=row.position_id,
            strategy_spec_id=row.strategy_spec_id,
            instrument_id=row.instrument_id,
            instrument_key=row.instrument_key,
            quantity=row.quantity,
            event_price=row.event_price,
            cash_flow=row.cash_flow,
            state_applied=row.state_applied,
            review_required=row.review_required,
            applied_position_id=row.applied_position_id,
            resulting_symbol=row.resulting_symbol,
            resulting_instrument_key=row.resulting_instrument_key,
            notes=row.notes,
            metadata_payload=row.metadata_payload,
            occurred_at=row.occurred_at,
            status=row.status,
            created_at=row.created_at,
        )


def _coerce_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
