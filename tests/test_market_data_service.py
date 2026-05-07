from __future__ import annotations

from datetime import UTC, datetime, timedelta

from quant_evo_nextgen.contracts.state import (
    FactorGenerationRequest,
    HistoricalBarCreate,
    MarketDataProviderUpsert,
    MarketDataReplayIngestCreate,
    MarketQuoteSnapshotCreate,
    WatchlistItemUpsert,
    WatchlistUpsert,
)
from quant_evo_nextgen.db.session import Database
from quant_evo_nextgen.services.market_data import MarketDataService


def test_market_data_service_tracks_provider_watchlist_quotes_and_freshness(tmp_path):
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'market-data.db'}")
    database.create_schema()
    service = MarketDataService(database.session_factory)
    now = datetime.now(tz=UTC)

    provider = service.upsert_provider(
        MarketDataProviderUpsert(
            provider_key="alpaca",
            display_name="Alpaca",
            provider_type="broker",
            market_coverage=["us_equities"],
            supports_realtime=True,
            entitlement_state="paper",
            health_status="healthy",
            freshness_sla_seconds=300,
            last_heartbeat_at=now,
        )
    )
    assert provider.provider_key == "alpaca"
    assert provider.supports_realtime is True

    watchlist = service.upsert_watchlist(
        WatchlistUpsert(
            watchlist_key="us-core",
            display_name="US Core",
            market_scope="us_equities",
            is_default=True,
        )
    )
    assert watchlist.watchlist_key == "us-core"

    item = service.upsert_watchlist_item(
        "us-core",
        WatchlistItemUpsert(symbol="AAPL", market="us_equities", venue="XNYS", priority=1),
    )
    assert item.symbol == "AAPL"

    quote = service.record_quote_snapshot(
        MarketQuoteSnapshotCreate(
            provider_key="alpaca",
            symbol="AAPL",
            market="us_equities",
            venue="XNYS",
            last=187.25,
            as_of=now - timedelta(seconds=30),
            is_realtime=True,
        )
    )
    assert quote.last == 187.25

    freshness = service.get_freshness(watchlist_key="us-core")
    assert freshness.fresh == 1
    assert freshness.stale == 0
    assert freshness.missing == 0
    assert freshness.items[0].provider_key == "alpaca"


def test_market_data_freshness_marks_missing_watchlist_symbol(tmp_path):
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'market-data-missing.db'}")
    database.create_schema()
    service = MarketDataService(database.session_factory)

    service.upsert_watchlist(WatchlistUpsert(watchlist_key="us-core", display_name="US Core"))
    service.upsert_watchlist_item("us-core", WatchlistItemUpsert(symbol="MSFT"))

    freshness = service.get_freshness(watchlist_key="us-core")

    assert freshness.fresh == 0
    assert freshness.stale == 0
    assert freshness.missing == 1
    assert freshness.items[0].status == "missing"


def test_market_data_service_ingests_replay_bars_and_generates_factor_lineage(tmp_path):
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'market-data-replay.db'}")
    database.create_schema()
    service = MarketDataService(database.session_factory)
    start = datetime(2026, 5, 4, tzinfo=UTC)

    run = service.ingest_replay_bars(
        MarketDataReplayIngestCreate(
            provider_key="local-replay",
            source_ref="unit-test-bars.json",
            bars=[
                HistoricalBarCreate(symbol="AAPL", bar_start=start, open=100, high=102, low=99, close=101, volume=1000),
                HistoricalBarCreate(
                    symbol="AAPL",
                    bar_start=start + timedelta(days=1),
                    open=101,
                    high=104,
                    low=100,
                    close=103,
                    volume=1100,
                ),
                HistoricalBarCreate(
                    symbol="AAPL",
                    bar_start=start + timedelta(days=2),
                    open=103,
                    high=107,
                    low=102,
                    close=106,
                    volume=1200,
                ),
                HistoricalBarCreate(symbol="MSFT", bar_start=start, open=50, high=51, low=49, close=50, volume=900),
                HistoricalBarCreate(
                    symbol="MSFT",
                    bar_start=start + timedelta(days=1),
                    open=50,
                    high=51,
                    low=48,
                    close=49,
                    volume=950,
                ),
                HistoricalBarCreate(
                    symbol="MSFT",
                    bar_start=start + timedelta(days=2),
                    open=49,
                    high=50,
                    low=47,
                    close=48,
                    volume=980,
                ),
            ],
        )
    )

    assert run.provider_key == "local-replay"
    assert run.adapter_key == "local_replay"
    assert run.bar_count == 6
    assert run.symbols == ["AAPL", "MSFT"]

    bars = service.list_historical_bars(symbol="AAPL")
    assert len(bars) == 3
    assert bars[0].close == 106
    assert bars[0].ingestion_run_id == run.id

    quotes = service.list_quote_snapshots(symbol="AAPL")
    assert quotes[0].last == 106
    assert quotes[0].is_realtime is False

    factors = service.generate_factor_snapshots(
        FactorGenerationRequest(provider_key="local-replay", lookback_bars=3)
    )

    assert [factor.symbol for factor in factors] == ["AAPL", "MSFT"]
    assert factors[0].rank == 1
    assert factors[0].value == 106 / 101 - 1
    assert factors[0].input_bar_ids == [bar.id for bar in reversed(bars)]
    assert factors[0].lineage_payload["provider_key"] == "local-replay"
    assert factors[0].lineage_payload["formula"] == "(latest_close / first_close) - 1"
    assert service.list_factor_snapshots(symbol="AAPL")[0].factor_code == "momentum_close_return"

    reversal = service.generate_factor_snapshots(
        FactorGenerationRequest(
            factor_code="reversal_close_return",
            factor_name="Close-to-close reversal score",
            provider_key="local-replay",
            lookback_bars=3,
            symbols=["AAPL"],
        )
    )
    volatility = service.generate_factor_snapshots(
        FactorGenerationRequest(
            factor_code="realized_volatility",
            factor_name="Realized close-to-close volatility",
            provider_key="local-replay",
            lookback_bars=3,
            symbols=["AAPL"],
        )
    )
    liquidity = service.generate_factor_snapshots(
        FactorGenerationRequest(
            factor_code="dollar_volume_liquidity",
            factor_name="Average dollar-volume liquidity",
            provider_key="local-replay",
            lookback_bars=3,
            symbols=["AAPL"],
        )
    )

    assert reversal[0].value == -(106 / 101 - 1)
    assert volatility[0].value >= 0
    assert liquidity[0].value > 100_000
