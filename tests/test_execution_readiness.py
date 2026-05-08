from __future__ import annotations

from datetime import UTC, datetime

from quant_evo_nextgen.config import Settings
from quant_evo_nextgen.db.models import (
    BrokerAccountSnapshotModel,
    MarketCalendarStateModel,
    MarketQuoteSnapshotModel,
    OperatorOverrideModel,
    ProviderProfileModel,
    ReconciliationRunModel,
    StrategySpecModel,
)
from quant_evo_nextgen.db.session import Database
from quant_evo_nextgen.services.execution_readiness import ExecutionReadinessEvaluator


def test_execution_readiness_blocks_empty_database(sqlite_database: Database, test_settings: Settings) -> None:
    summary = ExecutionReadinessEvaluator(sqlite_database.session_factory, test_settings).build()

    assert summary.status == "blocked"
    assert summary.trading_allowed is False
    assert "No production strategy is currently approved." in summary.blocked_reasons
    assert "No broker account snapshot has been captured." in summary.blocked_reasons
    assert "No broker reconciliation run has been recorded." in summary.blocked_reasons


def test_execution_readiness_ready_when_required_paper_evidence_is_fresh(
    sqlite_database: Database,
    test_settings: Settings,
) -> None:
    now = datetime.now(tz=UTC)
    with sqlite_database.session_scope() as session:
        session.add_all(
            [
                ProviderProfileModel(
                    provider_key="paper-sim",
                    display_name="Paper Sim",
                    api_style="internal",
                    health_status="healthy",
                    is_primary=True,
                    capability_snapshot={},
                ),
                MarketCalendarStateModel(
                    market_calendar=test_settings.market_calendar,
                    market_timezone=test_settings.market_timezone,
                    session_label="regular",
                    is_market_open=True,
                    trading_allowed=True,
                ),
                StrategySpecModel(
                    hypothesis_id="hypothesis-1",
                    spec_code="ready-spec",
                    title="Ready strategy",
                    target_market="us_equities",
                    signal_logic="Deterministic signal.",
                    current_stage="production",
                ),
                BrokerAccountSnapshotModel(
                    provider_key="paper-sim",
                    account_ref="paper-main",
                    environment="paper",
                    equity=100_000,
                    cash=100_000,
                    buying_power=100_000,
                    gross_exposure=0,
                    net_exposure=0,
                    positions_count=0,
                    open_orders_count=0,
                    source_captured_at=now,
                    source_age_seconds=0,
                    payload={},
                ),
                ReconciliationRunModel(
                    provider_key="paper-sim",
                    account_ref="paper-main",
                    environment="paper",
                    internal_equity=100_000,
                    broker_equity=100_000,
                    equity_delta_abs=0,
                    equity_delta_pct=0,
                    internal_positions_count=0,
                    broker_positions_count=0,
                    internal_open_orders_count=0,
                    broker_open_orders_count=0,
                    position_delta_count=0,
                    order_delta_count=0,
                    status="synchronized",
                    checked_at=now,
                    halt_triggered=False,
                ),
                MarketQuoteSnapshotModel(
                    provider_key="local-replay",
                    symbol="AAPL",
                    last=200.0,
                    as_of=now,
                    is_realtime=False,
                    payload={},
                ),
            ]
        )

    summary = ExecutionReadinessEvaluator(sqlite_database.session_factory, test_settings).build()

    assert summary.status == "ready"
    assert summary.trading_allowed is True
    assert summary.active_production_strategies == 1
    assert summary.blocked_reasons == []


def test_execution_readiness_trading_override_blocks_otherwise_ready_state(
    sqlite_database: Database,
    test_settings: Settings,
) -> None:
    now = datetime.now(tz=UTC)
    with sqlite_database.session_scope() as session:
        session.add_all(
            [
                ProviderProfileModel(
                    provider_key="paper-sim",
                    display_name="Paper Sim",
                    api_style="internal",
                    health_status="healthy",
                    is_primary=True,
                    capability_snapshot={},
                ),
                MarketCalendarStateModel(
                    market_calendar=test_settings.market_calendar,
                    market_timezone=test_settings.market_timezone,
                    session_label="regular",
                    is_market_open=True,
                    trading_allowed=True,
                ),
                StrategySpecModel(
                    hypothesis_id="hypothesis-1",
                    spec_code="paused-spec",
                    title="Paused strategy",
                    target_market="us_equities",
                    signal_logic="Deterministic signal.",
                    current_stage="production",
                ),
                BrokerAccountSnapshotModel(
                    provider_key="paper-sim",
                    account_ref="paper-main",
                    environment="paper",
                    equity=100_000,
                    cash=100_000,
                    buying_power=100_000,
                    gross_exposure=0,
                    net_exposure=0,
                    positions_count=0,
                    open_orders_count=0,
                    source_captured_at=now,
                    source_age_seconds=0,
                    payload={},
                ),
                ReconciliationRunModel(
                    provider_key="paper-sim",
                    account_ref="paper-main",
                    environment="paper",
                    internal_equity=100_000,
                    broker_equity=100_000,
                    equity_delta_abs=0,
                    equity_delta_pct=0,
                    internal_positions_count=0,
                    broker_positions_count=0,
                    internal_open_orders_count=0,
                    broker_open_orders_count=0,
                    position_delta_count=0,
                    order_delta_count=0,
                    status="synchronized",
                    checked_at=now,
                    halt_triggered=False,
                ),
                OperatorOverrideModel(
                    scope="trading",
                    action="pause",
                    reason="Operator pause.",
                    activated_by="tester",
                    is_active=True,
                ),
            ]
        )

    summary = ExecutionReadinessEvaluator(sqlite_database.session_factory, test_settings).build()

    assert summary.status == "blocked"
    assert summary.trading_allowed is False
    assert "Trading is paused by an active override." in summary.blocked_reasons
