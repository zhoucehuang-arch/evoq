from __future__ import annotations

from datetime import UTC, datetime
from typing import Callable

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from quant_evo_nextgen.contracts.state import (
    FactorGenerationRequest,
    FactorSnapshotSummary,
    HistoricalBarSummary,
    MarketDataFreshnessItem,
    MarketDataFreshnessSummary,
    MarketDataIngestionRunSummary,
    MarketDataProviderSummary,
    MarketDataProviderUpsert,
    MarketDataReplayIngestCreate,
    MarketQuoteSnapshotCreate,
    MarketQuoteSnapshotSummary,
    WatchlistItemSummary,
    WatchlistItemUpsert,
    WatchlistSummary,
    WatchlistUpsert,
)
from quant_evo_nextgen.db.base import utc_now
from quant_evo_nextgen.db.models import (
    FactorSnapshotModel,
    HistoricalBarModel,
    MarketDataIngestionRunModel,
    MarketDataProviderModel,
    MarketQuoteSnapshotModel,
    WatchlistItemModel,
    WatchlistModel,
)
from quant_evo_nextgen.services.factor_engine import evaluate_factor, factor_catalog, factor_decay_payload


class MarketDataService:
    """Owns provider readiness, watchlists, quote snapshots, and freshness checks."""

    def __init__(self, session_factory: Callable[[], Session]):
        self._session_factory = session_factory

    def upsert_provider(self, payload: MarketDataProviderUpsert) -> MarketDataProviderSummary:
        with self._session_factory() as session:
            provider = session.execute(
                select(MarketDataProviderModel).where(MarketDataProviderModel.provider_key == payload.provider_key)
            ).scalar_one_or_none()
            if provider is None:
                provider = MarketDataProviderModel(
                    provider_key=payload.provider_key,
                    created_by=payload.created_by,
                    origin_type=payload.origin_type,
                    origin_id=payload.origin_id,
                    status=payload.status,
                )
                session.add(provider)

            provider.display_name = payload.display_name
            provider.provider_type = payload.provider_type
            provider.market_coverage = payload.market_coverage
            provider.supports_realtime = payload.supports_realtime
            provider.supports_historical = payload.supports_historical
            provider.supports_fundamentals = payload.supports_fundamentals
            provider.supports_news = payload.supports_news
            provider.entitlement_state = payload.entitlement_state
            provider.health_status = payload.health_status
            provider.latency_ms = payload.latency_ms
            provider.freshness_sla_seconds = payload.freshness_sla_seconds
            provider.last_heartbeat_at = payload.last_heartbeat_at
            provider.notes = payload.notes
            provider.status = payload.status
            session.commit()
            session.refresh(provider)
            return self._provider_summary(provider)

    def list_providers(self, *, limit: int = 100) -> list[MarketDataProviderSummary]:
        with self._session_factory() as session:
            rows = session.execute(
                select(MarketDataProviderModel)
                .order_by(MarketDataProviderModel.provider_key.asc())
                .limit(limit)
            ).scalars()
            return [self._provider_summary(row) for row in rows]

    def upsert_watchlist(self, payload: WatchlistUpsert) -> WatchlistSummary:
        with self._session_factory() as session:
            watchlist = session.execute(
                select(WatchlistModel).where(WatchlistModel.watchlist_key == payload.watchlist_key)
            ).scalar_one_or_none()
            if watchlist is None:
                watchlist = WatchlistModel(
                    watchlist_key=payload.watchlist_key,
                    created_by=payload.created_by,
                    origin_type=payload.origin_type,
                    origin_id=payload.origin_id,
                    status=payload.status,
                )
                session.add(watchlist)

            if payload.is_default:
                existing_defaults = session.execute(
                    select(WatchlistModel).where(
                        WatchlistModel.market_scope == payload.market_scope,
                        WatchlistModel.is_default.is_(True),
                        WatchlistModel.watchlist_key != payload.watchlist_key,
                    )
                ).scalars()
                for existing in existing_defaults:
                    existing.is_default = False

            watchlist.display_name = payload.display_name
            watchlist.market_scope = payload.market_scope
            watchlist.description = payload.description
            watchlist.is_default = payload.is_default
            watchlist.status = payload.status
            session.commit()
            session.refresh(watchlist)
            return self._watchlist_summary(watchlist, session=session)

    def list_watchlists(self, *, limit: int = 100) -> list[WatchlistSummary]:
        with self._session_factory() as session:
            rows = session.execute(
                select(WatchlistModel)
                .order_by(
                    WatchlistModel.is_default.desc(),
                    WatchlistModel.market_scope.asc(),
                    WatchlistModel.watchlist_key.asc(),
                )
                .limit(limit)
            ).scalars()
            return [self._watchlist_summary(row, session=session) for row in rows]

    def upsert_watchlist_item(self, watchlist_key: str, payload: WatchlistItemUpsert) -> WatchlistItemSummary:
        with self._session_factory() as session:
            watchlist = self._get_or_create_watchlist(session, watchlist_key, market_scope=payload.market)
            item = session.execute(
                select(WatchlistItemModel).where(
                    WatchlistItemModel.watchlist_id == watchlist.id,
                    WatchlistItemModel.symbol == payload.symbol,
                    WatchlistItemModel.market == payload.market,
                )
            ).scalar_one_or_none()
            if item is None:
                item = WatchlistItemModel(
                    watchlist_id=watchlist.id,
                    symbol=payload.symbol,
                    created_by=payload.created_by,
                    origin_type=payload.origin_type,
                    origin_id=payload.origin_id,
                    status=payload.status,
                )
                session.add(item)

            item.instrument_key = payload.instrument_key
            item.market = payload.market
            item.venue = payload.venue
            item.currency = payload.currency
            item.priority = payload.priority
            item.metadata_payload = payload.metadata_payload
            item.status = payload.status
            session.commit()
            session.refresh(item)
            return self._watchlist_item_summary(item, watchlist_key=watchlist.watchlist_key)

    def list_watchlist_items(self, watchlist_key: str) -> list[WatchlistItemSummary]:
        with self._session_factory() as session:
            watchlist = session.execute(
                select(WatchlistModel).where(WatchlistModel.watchlist_key == watchlist_key)
            ).scalar_one_or_none()
            if watchlist is None:
                return []
            rows = session.execute(
                select(WatchlistItemModel)
                .where(WatchlistItemModel.watchlist_id == watchlist.id)
                .order_by(WatchlistItemModel.priority.asc(), WatchlistItemModel.symbol.asc())
            ).scalars()
            return [self._watchlist_item_summary(row, watchlist_key=watchlist.watchlist_key) for row in rows]

    def record_quote_snapshot(self, payload: MarketQuoteSnapshotCreate) -> MarketQuoteSnapshotSummary:
        with self._session_factory() as session:
            self._ensure_provider(session, payload.provider_key)
            snapshot = MarketQuoteSnapshotModel(
                provider_key=payload.provider_key,
                symbol=payload.symbol,
                market=payload.market,
                venue=payload.venue,
                bid=payload.bid,
                ask=payload.ask,
                last=payload.last,
                volume=payload.volume,
                as_of=payload.as_of or utc_now(),
                source_latency_ms=payload.source_latency_ms,
                is_realtime=payload.is_realtime,
                payload=payload.payload,
                created_by=payload.created_by,
                origin_type=payload.origin_type,
                origin_id=payload.origin_id,
                status=payload.status,
            )
            session.add(snapshot)
            session.commit()
            session.refresh(snapshot)
            return self._quote_summary(snapshot)

    def list_quote_snapshots(self, *, symbol: str | None = None, limit: int = 100) -> list[MarketQuoteSnapshotSummary]:
        with self._session_factory() as session:
            query = select(MarketQuoteSnapshotModel)
            if symbol:
                query = query.where(MarketQuoteSnapshotModel.symbol == symbol)
            rows = session.execute(
                query.order_by(
                    desc(MarketQuoteSnapshotModel.as_of),
                    desc(MarketQuoteSnapshotModel.created_at),
                ).limit(limit)
            ).scalars()
            return [self._quote_summary(row) for row in rows]

    def ingest_replay_bars(self, payload: MarketDataReplayIngestCreate) -> MarketDataIngestionRunSummary:
        with self._session_factory() as session:
            self._ensure_provider(session, payload.provider_key)
            symbols = sorted({bar.symbol.strip().upper() for bar in payload.bars if bar.symbol.strip()})
            run = MarketDataIngestionRunModel(
                provider_key=payload.provider_key,
                adapter_key=payload.adapter_key,
                source_ref=payload.source_ref,
                market=payload.market,
                symbols=symbols,
                bar_count=0,
                started_at=utc_now(),
                created_by=payload.created_by,
                origin_type=payload.origin_type,
                origin_id=payload.origin_id,
                status="running",
            )
            session.add(run)
            session.flush()

            latest_by_symbol: dict[tuple[str, str], HistoricalBarModel] = {}
            for item in payload.bars:
                symbol = item.symbol.strip().upper()
                if not symbol:
                    continue
                bar = HistoricalBarModel(
                    ingestion_run_id=run.id,
                    provider_key=payload.provider_key,
                    symbol=symbol,
                    market=item.market or payload.market,
                    venue=item.venue,
                    timeframe=item.timeframe or payload.timeframe,
                    bar_start=item.bar_start,
                    open=item.open,
                    high=item.high,
                    low=item.low,
                    close=item.close,
                    volume=item.volume,
                    adjusted_close=item.adjusted_close,
                    is_adjusted=item.is_adjusted,
                    payload=item.payload,
                    created_by=payload.created_by,
                    origin_type=payload.origin_type,
                    origin_id=payload.origin_id or run.id,
                    status="active",
                )
                session.add(bar)
                key = (symbol, bar.market)
                if key not in latest_by_symbol or item.bar_start > latest_by_symbol[key].bar_start:
                    latest_by_symbol[key] = bar

            session.flush()
            for bar in latest_by_symbol.values():
                session.add(
                    MarketQuoteSnapshotModel(
                        provider_key=payload.provider_key,
                        symbol=bar.symbol,
                        market=bar.market,
                        venue=bar.venue,
                        last=bar.adjusted_close if bar.is_adjusted and bar.adjusted_close is not None else bar.close,
                        volume=bar.volume,
                        as_of=bar.bar_start,
                        is_realtime=False,
                        payload={
                            "source": "replay_historical_bar",
                            "ingestion_run_id": run.id,
                            "historical_bar_id": bar.id,
                            "timeframe": bar.timeframe,
                        },
                        created_by=payload.created_by,
                        origin_type=payload.origin_type,
                        origin_id=run.id,
                        status="active",
                    )
                )

            run.bar_count = len(payload.bars)
            run.completed_at = utc_now()
            run.status = payload.status
            session.commit()
            session.refresh(run)
            return self._ingestion_run_summary(run)

    def list_ingestion_runs(self, *, limit: int = 50) -> list[MarketDataIngestionRunSummary]:
        with self._session_factory() as session:
            rows = session.execute(
                select(MarketDataIngestionRunModel)
                .order_by(desc(MarketDataIngestionRunModel.started_at), desc(MarketDataIngestionRunModel.created_at))
                .limit(limit)
            ).scalars()
            return [self._ingestion_run_summary(row) for row in rows]

    def list_historical_bars(
        self,
        *,
        symbol: str | None = None,
        market: str | None = None,
        timeframe: str | None = None,
        limit: int = 200,
    ) -> list[HistoricalBarSummary]:
        with self._session_factory() as session:
            query = select(HistoricalBarModel)
            if symbol:
                query = query.where(HistoricalBarModel.symbol == symbol.strip().upper())
            if market:
                query = query.where(HistoricalBarModel.market == market)
            if timeframe:
                query = query.where(HistoricalBarModel.timeframe == timeframe)
            rows = session.execute(
                query.order_by(desc(HistoricalBarModel.bar_start), HistoricalBarModel.symbol.asc()).limit(limit)
            ).scalars()
            return [self._historical_bar_summary(row) for row in rows]

    def generate_factor_snapshots(self, payload: FactorGenerationRequest) -> list[FactorSnapshotSummary]:
        with self._session_factory() as session:
            symbols = [symbol.strip().upper() for symbol in payload.symbols if symbol.strip()]
            if not symbols:
                symbol_rows = session.execute(
                    select(HistoricalBarModel.symbol)
                    .where(HistoricalBarModel.market == payload.market, HistoricalBarModel.timeframe == payload.timeframe)
                    .distinct()
                    .order_by(HistoricalBarModel.symbol.asc())
                ).all()
                symbols = [row[0] for row in symbol_rows]

            candidates: list[tuple[FactorSnapshotModel, float, FactorSnapshotModel | None]] = []
            for symbol in symbols:
                query = select(HistoricalBarModel).where(
                    HistoricalBarModel.symbol == symbol,
                    HistoricalBarModel.market == payload.market,
                    HistoricalBarModel.timeframe == payload.timeframe,
                )
                if payload.provider_key:
                    query = query.where(HistoricalBarModel.provider_key == payload.provider_key)
                if payload.as_of:
                    query = query.where(HistoricalBarModel.bar_start <= payload.as_of)

                bars = list(
                    session.execute(
                        query.order_by(desc(HistoricalBarModel.bar_start), desc(HistoricalBarModel.created_at)).limit(
                            payload.lookback_bars
                        )
                    ).scalars()
                )
                if len(bars) < payload.lookback_bars:
                    continue
                ordered_bars = list(reversed(bars))
                first_bar = ordered_bars[0]
                latest_bar = ordered_bars[-1]
                result = evaluate_factor(
                    payload.factor_code,
                    ordered_bars,
                    custom_expression=payload.custom_expression,
                )
                previous_snapshot = session.scalar(
                    select(FactorSnapshotModel)
                    .where(
                        FactorSnapshotModel.factor_code == payload.factor_code,
                        FactorSnapshotModel.symbol == symbol,
                        FactorSnapshotModel.market == payload.market,
                        FactorSnapshotModel.as_of <= latest_bar.bar_start,
                    )
                    .order_by(desc(FactorSnapshotModel.as_of), desc(FactorSnapshotModel.created_at))
                    .limit(1)
                )
                definition = factor_catalog().get(payload.factor_code)
                snapshot = FactorSnapshotModel(
                    factor_code=payload.factor_code,
                    factor_name=payload.factor_name or (definition.name if definition else "Custom linear factor"),
                    symbol=symbol,
                    market=payload.market,
                    as_of=latest_bar.bar_start,
                    value=result.value,
                    lookback_bars=payload.lookback_bars,
                    input_bar_ids=[bar.id for bar in ordered_bars],
                    lineage_payload={
                        "provider_key": payload.provider_key,
                        "timeframe": payload.timeframe,
                        "lookback_bars": payload.lookback_bars,
                        "start_bar_at": first_bar.bar_start.isoformat(),
                        "end_bar_at": latest_bar.bar_start.isoformat(),
                        "formula": result.formula,
                        "components": result.components,
                        "custom_expression": payload.custom_expression,
                    },
                    created_by=payload.created_by,
                    origin_type=payload.origin_type,
                    origin_id=payload.origin_id,
                    status=payload.status,
                )
                candidates.append((snapshot, result.value, previous_snapshot))

            ranked = sorted(candidates, key=lambda item: item[1], reverse=True)
            total = len(ranked)
            for index, (snapshot, _, previous_snapshot) in enumerate(ranked, start=1):
                snapshot.rank = index
                snapshot.percentile = 1.0 if total == 1 else 1.0 - ((index - 1) / (total - 1))
                snapshot.lineage_payload = {
                    **(snapshot.lineage_payload or {}),
                    "decay": factor_decay_payload(
                        current_value=snapshot.value,
                        previous_value=previous_snapshot.value if previous_snapshot else None,
                        previous_rank=previous_snapshot.rank if previous_snapshot else None,
                        current_rank=index,
                    ),
                }
                session.add(snapshot)

            session.commit()
            for snapshot, _, _ in ranked:
                session.refresh(snapshot)
            return [self._factor_snapshot_summary(snapshot) for snapshot, _, _ in ranked]

    def list_factor_snapshots(
        self,
        *,
        factor_code: str | None = None,
        symbol: str | None = None,
        limit: int = 100,
    ) -> list[FactorSnapshotSummary]:
        with self._session_factory() as session:
            query = select(FactorSnapshotModel)
            if factor_code:
                query = query.where(FactorSnapshotModel.factor_code == factor_code)
            if symbol:
                query = query.where(FactorSnapshotModel.symbol == symbol.strip().upper())
            rows = session.execute(
                query.order_by(
                    desc(FactorSnapshotModel.as_of),
                    FactorSnapshotModel.factor_code.asc(),
                    FactorSnapshotModel.rank.asc(),
                ).limit(limit)
            ).scalars()
            return [self._factor_snapshot_summary(row) for row in rows]

    def get_freshness(self, *, watchlist_key: str | None = None) -> MarketDataFreshnessSummary:
        generated_at = utc_now()
        with self._session_factory() as session:
            providers = {
                row.provider_key: row
                for row in session.execute(select(MarketDataProviderModel)).scalars()
            }
            targets = self._freshness_targets(session, watchlist_key=watchlist_key)
            items: list[MarketDataFreshnessItem] = []
            for symbol, market in targets:
                snapshot = session.execute(
                    select(MarketQuoteSnapshotModel)
                    .where(MarketQuoteSnapshotModel.symbol == symbol, MarketQuoteSnapshotModel.market == market)
                    .order_by(desc(MarketQuoteSnapshotModel.as_of), desc(MarketQuoteSnapshotModel.created_at))
                    .limit(1)
                ).scalar_one_or_none()
                items.append(self._freshness_item(symbol, market, snapshot, providers, generated_at))

            fresh = sum(1 for item in items if item.status == "fresh")
            stale = sum(1 for item in items if item.status == "stale")
            missing = sum(1 for item in items if item.status == "missing")
            return MarketDataFreshnessSummary(
                watchlist_key=watchlist_key,
                generated_at=generated_at,
                fresh=fresh,
                stale=stale,
                missing=missing,
                items=items,
            )

    def _freshness_targets(self, session: Session, *, watchlist_key: str | None) -> list[tuple[str, str]]:
        if watchlist_key:
            watchlist = session.execute(
                select(WatchlistModel).where(WatchlistModel.watchlist_key == watchlist_key)
            ).scalar_one_or_none()
            if watchlist is None:
                return []
            rows = session.execute(
                select(WatchlistItemModel.symbol, WatchlistItemModel.market)
                .where(WatchlistItemModel.watchlist_id == watchlist.id)
                .order_by(WatchlistItemModel.priority.asc(), WatchlistItemModel.symbol.asc())
            ).all()
            return [(symbol, market) for symbol, market in rows]

        rows = session.execute(
            select(MarketQuoteSnapshotModel.symbol, MarketQuoteSnapshotModel.market)
            .order_by(desc(MarketQuoteSnapshotModel.as_of))
            .limit(500)
        ).all()
        seen: set[tuple[str, str]] = set()
        targets: list[tuple[str, str]] = []
        for symbol, market in rows:
            key = (symbol, market)
            if key in seen:
                continue
            seen.add(key)
            targets.append(key)
        return targets

    def _freshness_item(
        self,
        symbol: str,
        market: str,
        snapshot: MarketQuoteSnapshotModel | None,
        providers: dict[str, MarketDataProviderModel],
        generated_at: datetime,
    ) -> MarketDataFreshnessItem:
        if snapshot is None:
            return MarketDataFreshnessItem(
                symbol=symbol,
                market=market,
                status="missing",
                reason="no_quote_snapshot",
            )

        provider = providers.get(snapshot.provider_key)
        quote_time = self._aware(snapshot.as_of)
        age_seconds = max(0, int((self._aware(generated_at) - quote_time).total_seconds()))
        sla_seconds = provider.freshness_sla_seconds if provider else 120
        status = "fresh" if age_seconds <= sla_seconds else "stale"
        return MarketDataFreshnessItem(
            symbol=symbol,
            market=market,
            provider_key=snapshot.provider_key,
            status=status,
            age_seconds=age_seconds,
            last_quote_at=snapshot.as_of,
            last_price=snapshot.last,
            provider_health=provider.health_status if provider else "unknown",
            reason=None if status == "fresh" else f"older_than_{sla_seconds}_seconds",
        )

    def _get_or_create_watchlist(self, session: Session, watchlist_key: str, *, market_scope: str) -> WatchlistModel:
        watchlist = session.execute(
            select(WatchlistModel).where(WatchlistModel.watchlist_key == watchlist_key)
        ).scalar_one_or_none()
        if watchlist is not None:
            return watchlist
        watchlist = WatchlistModel(
            watchlist_key=watchlist_key,
            display_name=watchlist_key,
            market_scope=market_scope,
            description=None,
            is_default=False,
            created_by="operator",
            origin_type="manual",
            status="active",
        )
        session.add(watchlist)
        session.flush()
        return watchlist

    def _ensure_provider(self, session: Session, provider_key: str) -> MarketDataProviderModel:
        provider = session.execute(
            select(MarketDataProviderModel).where(MarketDataProviderModel.provider_key == provider_key)
        ).scalar_one_or_none()
        if provider is not None:
            return provider
        provider = MarketDataProviderModel(
            provider_key=provider_key,
            display_name=provider_key,
            provider_type="custom",
            market_coverage=["us_equities"],
            supports_realtime=False,
            supports_historical=True,
            supports_fundamentals=False,
            supports_news=False,
            entitlement_state="unknown",
            health_status="unknown",
            freshness_sla_seconds=120,
            created_by="system",
            origin_type="market_data",
            status="active",
        )
        session.add(provider)
        session.flush()
        return provider

    def _provider_summary(self, row: MarketDataProviderModel) -> MarketDataProviderSummary:
        return MarketDataProviderSummary(
            id=row.id,
            provider_key=row.provider_key,
            display_name=row.display_name,
            provider_type=row.provider_type,
            market_coverage=row.market_coverage or [],
            supports_realtime=row.supports_realtime,
            supports_historical=row.supports_historical,
            supports_fundamentals=row.supports_fundamentals,
            supports_news=row.supports_news,
            entitlement_state=row.entitlement_state,
            health_status=row.health_status,
            latency_ms=row.latency_ms,
            freshness_sla_seconds=row.freshness_sla_seconds,
            last_heartbeat_at=row.last_heartbeat_at,
            notes=row.notes,
            updated_at=row.updated_at,
        )

    def _watchlist_summary(self, row: WatchlistModel, *, session: Session) -> WatchlistSummary:
        item_count = session.execute(
            select(func.count(WatchlistItemModel.id)).where(WatchlistItemModel.watchlist_id == row.id)
        ).scalar_one()
        return WatchlistSummary(
            id=row.id,
            watchlist_key=row.watchlist_key,
            display_name=row.display_name,
            market_scope=row.market_scope,
            description=row.description,
            is_default=row.is_default,
            item_count=item_count,
            updated_at=row.updated_at,
        )

    def _watchlist_item_summary(self, row: WatchlistItemModel, *, watchlist_key: str) -> WatchlistItemSummary:
        return WatchlistItemSummary(
            id=row.id,
            watchlist_key=watchlist_key,
            symbol=row.symbol,
            instrument_key=row.instrument_key,
            market=row.market,
            venue=row.venue,
            currency=row.currency,
            priority=row.priority,
            metadata_payload=row.metadata_payload or {},
            updated_at=row.updated_at,
        )

    def _quote_summary(self, row: MarketQuoteSnapshotModel) -> MarketQuoteSnapshotSummary:
        return MarketQuoteSnapshotSummary(
            id=row.id,
            provider_key=row.provider_key,
            symbol=row.symbol,
            market=row.market,
            venue=row.venue,
            bid=row.bid,
            ask=row.ask,
            last=row.last,
            volume=row.volume,
            as_of=row.as_of,
            source_latency_ms=row.source_latency_ms,
            is_realtime=row.is_realtime,
            created_at=row.created_at,
        )

    def _ingestion_run_summary(self, row: MarketDataIngestionRunModel) -> MarketDataIngestionRunSummary:
        return MarketDataIngestionRunSummary(
            id=row.id,
            provider_key=row.provider_key,
            adapter_key=row.adapter_key,
            source_ref=row.source_ref,
            market=row.market,
            symbols=row.symbols or [],
            bar_count=row.bar_count,
            started_at=row.started_at,
            completed_at=row.completed_at,
            error_message=row.error_message,
            status=row.status,
            created_at=row.created_at,
        )

    def _historical_bar_summary(self, row: HistoricalBarModel) -> HistoricalBarSummary:
        return HistoricalBarSummary(
            id=row.id,
            ingestion_run_id=row.ingestion_run_id,
            provider_key=row.provider_key,
            symbol=row.symbol,
            market=row.market,
            venue=row.venue,
            timeframe=row.timeframe,
            bar_start=row.bar_start,
            open=row.open,
            high=row.high,
            low=row.low,
            close=row.close,
            volume=row.volume,
            adjusted_close=row.adjusted_close,
            is_adjusted=row.is_adjusted,
            created_at=row.created_at,
        )

    def _factor_snapshot_summary(self, row: FactorSnapshotModel) -> FactorSnapshotSummary:
        return FactorSnapshotSummary(
            id=row.id,
            factor_code=row.factor_code,
            factor_name=row.factor_name,
            symbol=row.symbol,
            market=row.market,
            as_of=row.as_of,
            value=row.value,
            rank=row.rank,
            percentile=row.percentile,
            lookback_bars=row.lookback_bars,
            input_bar_ids=row.input_bar_ids or [],
            lineage_payload=row.lineage_payload or {},
            created_at=row.created_at,
        )

    def _aware(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
