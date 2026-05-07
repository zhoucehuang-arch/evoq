from __future__ import annotations

from datetime import UTC, datetime
from typing import Callable

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from quant_evo_nextgen.config import Settings
from quant_evo_nextgen.contracts.state import ExecutionReadinessSummary
from quant_evo_nextgen.db.models import (
    BrokerAccountSnapshotModel,
    BrokerCapabilityModel,
    BrokerSyncRunModel,
    MarketCalendarStateModel,
    MarketQuoteSnapshotModel,
    OperatorOverrideModel,
    ProviderIncidentModel,
    ProviderProfileModel,
    ReconciliationRunModel,
    StrategySpecModel,
)


OPEN_PROVIDER_INCIDENT_STATUSES = ("open", "investigating", "mitigated")


class ExecutionReadinessEvaluator:
    def __init__(self, session_factory: Callable[[], Session], settings: Settings) -> None:
        self.session_factory = session_factory
        self.settings = settings

    def build(self) -> ExecutionReadinessSummary:
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
            configured_capability = self._resolve_broker_capability(session)
            latest_quote = session.scalar(
                select(MarketQuoteSnapshotModel).order_by(
                    MarketQuoteSnapshotModel.as_of.desc(),
                    MarketQuoteSnapshotModel.created_at.desc(),
                )
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

        if latest_quote is not None:
            quote_age_seconds = int((datetime.now(tz=UTC) - _coerce_utc(latest_quote.as_of)).total_seconds())
            if quote_age_seconds > 172800:
                blocked_reasons.append(
                    f"Latest market data quote for {latest_quote.symbol} is stale by more than 48 hours."
                )
            elif quote_age_seconds > 86400:
                warnings.append(f"Latest market data quote for {latest_quote.symbol} is older than 24 hours.")

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

    def _resolve_broker_capability(self, session: Session) -> BrokerCapabilityModel | None:
        rows = session.scalars(
            select(BrokerCapabilityModel)
            .where(
                BrokerCapabilityModel.provider_key == self.settings.default_broker_provider_key,
                BrokerCapabilityModel.environment == self.settings.default_broker_environment,
                BrokerCapabilityModel.broker_adapter == self.settings.default_broker_adapter,
                BrokerCapabilityModel.status == "active",
                or_(
                    BrokerCapabilityModel.account_ref == self.settings.default_broker_account_ref,
                    BrokerCapabilityModel.account_ref.is_(None),
                ),
            )
            .order_by(BrokerCapabilityModel.account_ref.desc())
        ).all()
        return rows[0] if rows else None


def _coerce_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
