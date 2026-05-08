"""stage13 historical bars factor kernel

Revision ID: 20260320_0017
Revises: 20260320_0016
Create Date: 2026-03-20 14:30:00
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260320_0017"
down_revision = "20260320_0016"
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
        "md_ingestion_run",
        sa.Column("provider_key", sa.String(length=120), nullable=False),
        sa.Column("adapter_key", sa.String(length=120), nullable=False),
        sa.Column("source_ref", sa.String(length=500), nullable=True),
        sa.Column("market", sa.String(length=40), nullable=False),
        sa.Column("symbols", sa.JSON(), nullable=False),
        sa.Column("bar_count", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        *_lineage_columns(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_md_ingestion_run_provider_key"), "md_ingestion_run", ["provider_key"], unique=False)
    op.create_index(op.f("ix_md_ingestion_run_adapter_key"), "md_ingestion_run", ["adapter_key"], unique=False)
    op.create_index(op.f("ix_md_ingestion_run_market"), "md_ingestion_run", ["market"], unique=False)
    op.create_index(op.f("ix_md_ingestion_run_status"), "md_ingestion_run", ["status"], unique=False)
    op.create_index(op.f("ix_md_ingestion_run_trace_id"), "md_ingestion_run", ["trace_id"], unique=False)
    op.create_index(op.f("ix_md_ingestion_run_run_id"), "md_ingestion_run", ["run_id"], unique=False)

    op.create_table(
        "md_historical_bar",
        sa.Column("ingestion_run_id", sa.String(length=36), nullable=True),
        sa.Column("provider_key", sa.String(length=120), nullable=False),
        sa.Column("symbol", sa.String(length=80), nullable=False),
        sa.Column("market", sa.String(length=40), nullable=False),
        sa.Column("venue", sa.String(length=80), nullable=True),
        sa.Column("timeframe", sa.String(length=40), nullable=False),
        sa.Column("bar_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Float(), nullable=False),
        sa.Column("high", sa.Float(), nullable=False),
        sa.Column("low", sa.Float(), nullable=False),
        sa.Column("close", sa.Float(), nullable=False),
        sa.Column("volume", sa.Float(), nullable=True),
        sa.Column("adjusted_close", sa.Float(), nullable=True),
        sa.Column("is_adjusted", sa.Boolean(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        *_lineage_columns(),
        sa.ForeignKeyConstraint(["ingestion_run_id"], ["md_ingestion_run.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_md_historical_bar_ingestion_run_id"), "md_historical_bar", ["ingestion_run_id"], unique=False)
    op.create_index(op.f("ix_md_historical_bar_provider_key"), "md_historical_bar", ["provider_key"], unique=False)
    op.create_index(op.f("ix_md_historical_bar_symbol"), "md_historical_bar", ["symbol"], unique=False)
    op.create_index(op.f("ix_md_historical_bar_market"), "md_historical_bar", ["market"], unique=False)
    op.create_index(op.f("ix_md_historical_bar_venue"), "md_historical_bar", ["venue"], unique=False)
    op.create_index(op.f("ix_md_historical_bar_timeframe"), "md_historical_bar", ["timeframe"], unique=False)
    op.create_index(op.f("ix_md_historical_bar_bar_start"), "md_historical_bar", ["bar_start"], unique=False)
    op.create_index(op.f("ix_md_historical_bar_is_adjusted"), "md_historical_bar", ["is_adjusted"], unique=False)
    op.create_index(op.f("ix_md_historical_bar_status"), "md_historical_bar", ["status"], unique=False)
    op.create_index(op.f("ix_md_historical_bar_trace_id"), "md_historical_bar", ["trace_id"], unique=False)
    op.create_index(op.f("ix_md_historical_bar_run_id"), "md_historical_bar", ["run_id"], unique=False)

    op.create_table(
        "factor_snapshot",
        sa.Column("factor_code", sa.String(length=120), nullable=False),
        sa.Column("factor_name", sa.String(length=200), nullable=False),
        sa.Column("symbol", sa.String(length=80), nullable=False),
        sa.Column("market", sa.String(length=40), nullable=False),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("percentile", sa.Float(), nullable=True),
        sa.Column("lookback_bars", sa.Integer(), nullable=False),
        sa.Column("input_bar_ids", sa.JSON(), nullable=False),
        sa.Column("lineage_payload", sa.JSON(), nullable=False),
        *_lineage_columns(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_factor_snapshot_factor_code"), "factor_snapshot", ["factor_code"], unique=False)
    op.create_index(op.f("ix_factor_snapshot_symbol"), "factor_snapshot", ["symbol"], unique=False)
    op.create_index(op.f("ix_factor_snapshot_market"), "factor_snapshot", ["market"], unique=False)
    op.create_index(op.f("ix_factor_snapshot_as_of"), "factor_snapshot", ["as_of"], unique=False)
    op.create_index(op.f("ix_factor_snapshot_rank"), "factor_snapshot", ["rank"], unique=False)
    op.create_index(op.f("ix_factor_snapshot_status"), "factor_snapshot", ["status"], unique=False)
    op.create_index(op.f("ix_factor_snapshot_trace_id"), "factor_snapshot", ["trace_id"], unique=False)
    op.create_index(op.f("ix_factor_snapshot_run_id"), "factor_snapshot", ["run_id"], unique=False)


def downgrade() -> None:
    for index_name in (
        "ix_factor_snapshot_run_id",
        "ix_factor_snapshot_trace_id",
        "ix_factor_snapshot_status",
        "ix_factor_snapshot_rank",
        "ix_factor_snapshot_as_of",
        "ix_factor_snapshot_market",
        "ix_factor_snapshot_symbol",
        "ix_factor_snapshot_factor_code",
    ):
        op.drop_index(op.f(index_name), table_name="factor_snapshot")
    op.drop_table("factor_snapshot")

    for index_name in (
        "ix_md_historical_bar_run_id",
        "ix_md_historical_bar_trace_id",
        "ix_md_historical_bar_status",
        "ix_md_historical_bar_is_adjusted",
        "ix_md_historical_bar_bar_start",
        "ix_md_historical_bar_timeframe",
        "ix_md_historical_bar_venue",
        "ix_md_historical_bar_market",
        "ix_md_historical_bar_symbol",
        "ix_md_historical_bar_provider_key",
        "ix_md_historical_bar_ingestion_run_id",
    ):
        op.drop_index(op.f(index_name), table_name="md_historical_bar")
    op.drop_table("md_historical_bar")

    for index_name in (
        "ix_md_ingestion_run_run_id",
        "ix_md_ingestion_run_trace_id",
        "ix_md_ingestion_run_status",
        "ix_md_ingestion_run_market",
        "ix_md_ingestion_run_adapter_key",
        "ix_md_ingestion_run_provider_key",
    ):
        op.drop_index(op.f(index_name), table_name="md_ingestion_run")
    op.drop_table("md_ingestion_run")
