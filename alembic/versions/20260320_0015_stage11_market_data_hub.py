"""stage11 market data hub

Revision ID: 20260320_0015
Revises: 20260320_0014
Create Date: 2026-03-20 13:15:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "20260320_0015"
down_revision = "20260320_0014"
branch_labels = None
depends_on = None


def _lineage_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=120), nullable=False),
        sa.Column("origin_type", sa.String(length=80), nullable=False),
        sa.Column("origin_id", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=80), nullable=False),
        sa.Column("trace_id", sa.String(length=120), nullable=True),
        sa.Column("run_id", sa.String(length=120), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "md_provider",
        sa.Column("provider_key", sa.String(length=120), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("provider_type", sa.String(length=40), nullable=False),
        sa.Column("market_coverage", sa.JSON(), nullable=False),
        sa.Column("supports_realtime", sa.Boolean(), nullable=False),
        sa.Column("supports_historical", sa.Boolean(), nullable=False),
        sa.Column("supports_fundamentals", sa.Boolean(), nullable=False),
        sa.Column("supports_news", sa.Boolean(), nullable=False),
        sa.Column("entitlement_state", sa.String(length=40), nullable=False),
        sa.Column("health_status", sa.String(length=40), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("freshness_sla_seconds", sa.Integer(), nullable=False),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        *_lineage_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider_key"),
    )
    op.create_index(op.f("ix_md_provider_provider_key"), "md_provider", ["provider_key"], unique=False)
    op.create_index(op.f("ix_md_provider_provider_type"), "md_provider", ["provider_type"], unique=False)
    op.create_index(op.f("ix_md_provider_entitlement_state"), "md_provider", ["entitlement_state"], unique=False)
    op.create_index(op.f("ix_md_provider_health_status"), "md_provider", ["health_status"], unique=False)
    op.create_index(op.f("ix_md_provider_status"), "md_provider", ["status"], unique=False)
    op.create_index(op.f("ix_md_provider_trace_id"), "md_provider", ["trace_id"], unique=False)
    op.create_index(op.f("ix_md_provider_run_id"), "md_provider", ["run_id"], unique=False)

    op.create_table(
        "md_watchlist",
        sa.Column("watchlist_key", sa.String(length=120), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("market_scope", sa.String(length=40), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        *_lineage_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("watchlist_key"),
    )
    op.create_index(op.f("ix_md_watchlist_watchlist_key"), "md_watchlist", ["watchlist_key"], unique=False)
    op.create_index(op.f("ix_md_watchlist_market_scope"), "md_watchlist", ["market_scope"], unique=False)
    op.create_index(op.f("ix_md_watchlist_status"), "md_watchlist", ["status"], unique=False)
    op.create_index(op.f("ix_md_watchlist_trace_id"), "md_watchlist", ["trace_id"], unique=False)
    op.create_index(op.f("ix_md_watchlist_run_id"), "md_watchlist", ["run_id"], unique=False)

    op.create_table(
        "md_watchlist_item",
        sa.Column("watchlist_id", sa.String(length=36), nullable=False),
        sa.Column("symbol", sa.String(length=80), nullable=False),
        sa.Column("instrument_key", sa.String(length=200), nullable=True),
        sa.Column("market", sa.String(length=40), nullable=False),
        sa.Column("venue", sa.String(length=80), nullable=True),
        sa.Column("currency", sa.String(length=16), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("metadata_payload", sa.JSON(), nullable=False),
        *_lineage_columns(),
        sa.ForeignKeyConstraint(["watchlist_id"], ["md_watchlist.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_md_watchlist_item_watchlist_id"), "md_watchlist_item", ["watchlist_id"], unique=False)
    op.create_index(op.f("ix_md_watchlist_item_symbol"), "md_watchlist_item", ["symbol"], unique=False)
    op.create_index(op.f("ix_md_watchlist_item_instrument_key"), "md_watchlist_item", ["instrument_key"], unique=False)
    op.create_index(op.f("ix_md_watchlist_item_market"), "md_watchlist_item", ["market"], unique=False)
    op.create_index(op.f("ix_md_watchlist_item_venue"), "md_watchlist_item", ["venue"], unique=False)
    op.create_index(op.f("ix_md_watchlist_item_status"), "md_watchlist_item", ["status"], unique=False)
    op.create_index(op.f("ix_md_watchlist_item_trace_id"), "md_watchlist_item", ["trace_id"], unique=False)
    op.create_index(op.f("ix_md_watchlist_item_run_id"), "md_watchlist_item", ["run_id"], unique=False)

    op.create_table(
        "md_quote_snapshot",
        sa.Column("provider_key", sa.String(length=120), nullable=False),
        sa.Column("symbol", sa.String(length=80), nullable=False),
        sa.Column("market", sa.String(length=40), nullable=False),
        sa.Column("venue", sa.String(length=80), nullable=True),
        sa.Column("bid", sa.Float(), nullable=True),
        sa.Column("ask", sa.Float(), nullable=True),
        sa.Column("last", sa.Float(), nullable=True),
        sa.Column("volume", sa.Float(), nullable=True),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_latency_ms", sa.Integer(), nullable=True),
        sa.Column("is_realtime", sa.Boolean(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        *_lineage_columns(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_md_quote_snapshot_provider_key"), "md_quote_snapshot", ["provider_key"], unique=False)
    op.create_index(op.f("ix_md_quote_snapshot_symbol"), "md_quote_snapshot", ["symbol"], unique=False)
    op.create_index(op.f("ix_md_quote_snapshot_market"), "md_quote_snapshot", ["market"], unique=False)
    op.create_index(op.f("ix_md_quote_snapshot_venue"), "md_quote_snapshot", ["venue"], unique=False)
    op.create_index(op.f("ix_md_quote_snapshot_as_of"), "md_quote_snapshot", ["as_of"], unique=False)
    op.create_index(op.f("ix_md_quote_snapshot_is_realtime"), "md_quote_snapshot", ["is_realtime"], unique=False)
    op.create_index(op.f("ix_md_quote_snapshot_status"), "md_quote_snapshot", ["status"], unique=False)
    op.create_index(op.f("ix_md_quote_snapshot_trace_id"), "md_quote_snapshot", ["trace_id"], unique=False)
    op.create_index(op.f("ix_md_quote_snapshot_run_id"), "md_quote_snapshot", ["run_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_md_quote_snapshot_run_id"), table_name="md_quote_snapshot")
    op.drop_index(op.f("ix_md_quote_snapshot_trace_id"), table_name="md_quote_snapshot")
    op.drop_index(op.f("ix_md_quote_snapshot_status"), table_name="md_quote_snapshot")
    op.drop_index(op.f("ix_md_quote_snapshot_is_realtime"), table_name="md_quote_snapshot")
    op.drop_index(op.f("ix_md_quote_snapshot_as_of"), table_name="md_quote_snapshot")
    op.drop_index(op.f("ix_md_quote_snapshot_venue"), table_name="md_quote_snapshot")
    op.drop_index(op.f("ix_md_quote_snapshot_market"), table_name="md_quote_snapshot")
    op.drop_index(op.f("ix_md_quote_snapshot_symbol"), table_name="md_quote_snapshot")
    op.drop_index(op.f("ix_md_quote_snapshot_provider_key"), table_name="md_quote_snapshot")
    op.drop_table("md_quote_snapshot")

    op.drop_index(op.f("ix_md_watchlist_item_run_id"), table_name="md_watchlist_item")
    op.drop_index(op.f("ix_md_watchlist_item_trace_id"), table_name="md_watchlist_item")
    op.drop_index(op.f("ix_md_watchlist_item_status"), table_name="md_watchlist_item")
    op.drop_index(op.f("ix_md_watchlist_item_venue"), table_name="md_watchlist_item")
    op.drop_index(op.f("ix_md_watchlist_item_market"), table_name="md_watchlist_item")
    op.drop_index(op.f("ix_md_watchlist_item_instrument_key"), table_name="md_watchlist_item")
    op.drop_index(op.f("ix_md_watchlist_item_symbol"), table_name="md_watchlist_item")
    op.drop_index(op.f("ix_md_watchlist_item_watchlist_id"), table_name="md_watchlist_item")
    op.drop_table("md_watchlist_item")

    op.drop_index(op.f("ix_md_watchlist_run_id"), table_name="md_watchlist")
    op.drop_index(op.f("ix_md_watchlist_trace_id"), table_name="md_watchlist")
    op.drop_index(op.f("ix_md_watchlist_status"), table_name="md_watchlist")
    op.drop_index(op.f("ix_md_watchlist_market_scope"), table_name="md_watchlist")
    op.drop_index(op.f("ix_md_watchlist_watchlist_key"), table_name="md_watchlist")
    op.drop_table("md_watchlist")

    op.drop_index(op.f("ix_md_provider_run_id"), table_name="md_provider")
    op.drop_index(op.f("ix_md_provider_trace_id"), table_name="md_provider")
    op.drop_index(op.f("ix_md_provider_status"), table_name="md_provider")
    op.drop_index(op.f("ix_md_provider_health_status"), table_name="md_provider")
    op.drop_index(op.f("ix_md_provider_entitlement_state"), table_name="md_provider")
    op.drop_index(op.f("ix_md_provider_provider_type"), table_name="md_provider")
    op.drop_index(op.f("ix_md_provider_provider_key"), table_name="md_provider")
    op.drop_table("md_provider")
