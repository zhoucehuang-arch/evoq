"""stage9 execution kernel

Revision ID: 20260319_0008
Revises: 20260319_0007
Create Date: 2026-03-19 23:35:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "20260319_0008"
down_revision = "20260319_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "exec_broker_account_snapshot",
        sa.Column("provider_key", sa.String(length=120), nullable=False),
        sa.Column("account_ref", sa.String(length=120), nullable=False),
        sa.Column("environment", sa.String(length=40), nullable=False),
        sa.Column("equity", sa.Float(), nullable=False),
        sa.Column("cash", sa.Float(), nullable=False),
        sa.Column("buying_power", sa.Float(), nullable=False),
        sa.Column("gross_exposure", sa.Float(), nullable=False),
        sa.Column("net_exposure", sa.Float(), nullable=False),
        sa.Column("positions_count", sa.Integer(), nullable=False),
        sa.Column("open_orders_count", sa.Integer(), nullable=False),
        sa.Column("source_captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_age_seconds", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_exec_broker_account_snapshot_provider_key"),
        "exec_broker_account_snapshot",
        ["provider_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_exec_broker_account_snapshot_account_ref"),
        "exec_broker_account_snapshot",
        ["account_ref"],
        unique=False,
    )
    op.create_index(
        op.f("ix_exec_broker_account_snapshot_environment"),
        "exec_broker_account_snapshot",
        ["environment"],
        unique=False,
    )
    op.create_index(
        op.f("ix_exec_broker_account_snapshot_status"),
        "exec_broker_account_snapshot",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_exec_broker_account_snapshot_trace_id"),
        "exec_broker_account_snapshot",
        ["trace_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_exec_broker_account_snapshot_run_id"),
        "exec_broker_account_snapshot",
        ["run_id"],
        unique=False,
    )

    op.create_table(
        "exec_reconciliation_run",
        sa.Column("provider_key", sa.String(length=120), nullable=False),
        sa.Column("account_ref", sa.String(length=120), nullable=False),
        sa.Column("account_snapshot_id", sa.String(length=36), nullable=True),
        sa.Column("environment", sa.String(length=40), nullable=False),
        sa.Column("internal_equity", sa.Float(), nullable=False),
        sa.Column("broker_equity", sa.Float(), nullable=False),
        sa.Column("equity_delta_abs", sa.Float(), nullable=False),
        sa.Column("equity_delta_pct", sa.Float(), nullable=False),
        sa.Column("internal_positions_count", sa.Integer(), nullable=False),
        sa.Column("broker_positions_count", sa.Integer(), nullable=False),
        sa.Column("internal_open_orders_count", sa.Integer(), nullable=False),
        sa.Column("broker_open_orders_count", sa.Integer(), nullable=False),
        sa.Column("position_delta_count", sa.Integer(), nullable=False),
        sa.Column("order_delta_count", sa.Integer(), nullable=False),
        sa.Column("blocking_reason", sa.Text(), nullable=True),
        sa.Column("notes", sa.JSON(), nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("halt_triggered", sa.Boolean(), nullable=False),
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
        sa.ForeignKeyConstraint(["account_snapshot_id"], ["exec_broker_account_snapshot.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_exec_reconciliation_run_provider_key"),
        "exec_reconciliation_run",
        ["provider_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_exec_reconciliation_run_account_ref"),
        "exec_reconciliation_run",
        ["account_ref"],
        unique=False,
    )
    op.create_index(
        op.f("ix_exec_reconciliation_run_account_snapshot_id"),
        "exec_reconciliation_run",
        ["account_snapshot_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_exec_reconciliation_run_environment"),
        "exec_reconciliation_run",
        ["environment"],
        unique=False,
    )
    op.create_index(
        op.f("ix_exec_reconciliation_run_status"),
        "exec_reconciliation_run",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_exec_reconciliation_run_trace_id"),
        "exec_reconciliation_run",
        ["trace_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_exec_reconciliation_run_run_id"),
        "exec_reconciliation_run",
        ["run_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_exec_reconciliation_run_run_id"), table_name="exec_reconciliation_run")
    op.drop_index(op.f("ix_exec_reconciliation_run_trace_id"), table_name="exec_reconciliation_run")
    op.drop_index(op.f("ix_exec_reconciliation_run_status"), table_name="exec_reconciliation_run")
    op.drop_index(op.f("ix_exec_reconciliation_run_environment"), table_name="exec_reconciliation_run")
    op.drop_index(op.f("ix_exec_reconciliation_run_account_snapshot_id"), table_name="exec_reconciliation_run")
    op.drop_index(op.f("ix_exec_reconciliation_run_account_ref"), table_name="exec_reconciliation_run")
    op.drop_index(op.f("ix_exec_reconciliation_run_provider_key"), table_name="exec_reconciliation_run")
    op.drop_table("exec_reconciliation_run")

    op.drop_index(op.f("ix_exec_broker_account_snapshot_run_id"), table_name="exec_broker_account_snapshot")
    op.drop_index(op.f("ix_exec_broker_account_snapshot_trace_id"), table_name="exec_broker_account_snapshot")
    op.drop_index(op.f("ix_exec_broker_account_snapshot_status"), table_name="exec_broker_account_snapshot")
    op.drop_index(op.f("ix_exec_broker_account_snapshot_environment"), table_name="exec_broker_account_snapshot")
    op.drop_index(op.f("ix_exec_broker_account_snapshot_account_ref"), table_name="exec_broker_account_snapshot")
    op.drop_index(op.f("ix_exec_broker_account_snapshot_provider_key"), table_name="exec_broker_account_snapshot")
    op.drop_table("exec_broker_account_snapshot")
