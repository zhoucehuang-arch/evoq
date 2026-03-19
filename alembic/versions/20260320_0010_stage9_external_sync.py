"""stage9 external sync and order recovery

Revision ID: 20260320_0010
Revises: 20260319_0009
Create Date: 2026-03-20 01:15:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "20260320_0010"
down_revision = "20260319_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "exec_broker_sync_run",
        sa.Column("provider_key", sa.String(length=120), nullable=False),
        sa.Column("account_ref", sa.String(length=120), nullable=False),
        sa.Column("environment", sa.String(length=40), nullable=False),
        sa.Column("broker_adapter", sa.String(length=80), nullable=False),
        sa.Column("sync_scope", sa.String(length=40), nullable=False),
        sa.Column("account_snapshot_id", sa.String(length=36), nullable=True),
        sa.Column("synced_orders_count", sa.Integer(), nullable=False),
        sa.Column("synced_positions_count", sa.Integer(), nullable=False),
        sa.Column("unmanaged_orders_count", sa.Integer(), nullable=False),
        sa.Column("unmanaged_positions_count", sa.Integer(), nullable=False),
        sa.Column("missing_internal_orders_count", sa.Integer(), nullable=False),
        sa.Column("missing_internal_positions_count", sa.Integer(), nullable=False),
        sa.Column("notes", sa.JSON(), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
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
    op.create_index(op.f("ix_exec_broker_sync_run_provider_key"), "exec_broker_sync_run", ["provider_key"], unique=False)
    op.create_index(op.f("ix_exec_broker_sync_run_account_ref"), "exec_broker_sync_run", ["account_ref"], unique=False)
    op.create_index(op.f("ix_exec_broker_sync_run_environment"), "exec_broker_sync_run", ["environment"], unique=False)
    op.create_index(op.f("ix_exec_broker_sync_run_broker_adapter"), "exec_broker_sync_run", ["broker_adapter"], unique=False)
    op.create_index(op.f("ix_exec_broker_sync_run_account_snapshot_id"), "exec_broker_sync_run", ["account_snapshot_id"], unique=False)
    op.create_index(op.f("ix_exec_broker_sync_run_status"), "exec_broker_sync_run", ["status"], unique=False)
    op.create_index(op.f("ix_exec_broker_sync_run_trace_id"), "exec_broker_sync_run", ["trace_id"], unique=False)
    op.create_index(op.f("ix_exec_broker_sync_run_run_id"), "exec_broker_sync_run", ["run_id"], unique=False)

    with op.batch_alter_table("exec_order_record") as batch_op:
        batch_op.add_column(sa.Column("client_order_id", sa.String(length=160), nullable=True))
        batch_op.add_column(sa.Column("time_in_force", sa.String(length=20), server_default="day", nullable=False))
        batch_op.add_column(sa.Column("parent_order_record_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("last_sync_run_id", sa.String(length=36), nullable=True))
        batch_op.create_index(op.f("ix_exec_order_record_client_order_id"), ["client_order_id"], unique=False)
        batch_op.create_index(op.f("ix_exec_order_record_parent_order_record_id"), ["parent_order_record_id"], unique=False)
        batch_op.create_index(op.f("ix_exec_order_record_last_sync_run_id"), ["last_sync_run_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_exec_order_record_parent_order_record_id",
            "exec_order_record",
            ["parent_order_record_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_exec_order_record_last_sync_run_id",
            "exec_broker_sync_run",
            ["last_sync_run_id"],
            ["id"],
        )

    with op.batch_alter_table("exec_position_record") as batch_op:
        batch_op.add_column(sa.Column("last_sync_run_id", sa.String(length=36), nullable=True))
        batch_op.create_index(op.f("ix_exec_position_record_last_sync_run_id"), ["last_sync_run_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_exec_position_record_last_sync_run_id",
            "exec_broker_sync_run",
            ["last_sync_run_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("exec_position_record") as batch_op:
        batch_op.drop_constraint("fk_exec_position_record_last_sync_run_id", type_="foreignkey")
        batch_op.drop_index(op.f("ix_exec_position_record_last_sync_run_id"))
        batch_op.drop_column("last_sync_run_id")

    with op.batch_alter_table("exec_order_record") as batch_op:
        batch_op.drop_constraint("fk_exec_order_record_last_sync_run_id", type_="foreignkey")
        batch_op.drop_constraint("fk_exec_order_record_parent_order_record_id", type_="foreignkey")
        batch_op.drop_index(op.f("ix_exec_order_record_last_sync_run_id"))
        batch_op.drop_index(op.f("ix_exec_order_record_parent_order_record_id"))
        batch_op.drop_index(op.f("ix_exec_order_record_client_order_id"))
        batch_op.drop_column("last_sync_run_id")
        batch_op.drop_column("parent_order_record_id")
        batch_op.drop_column("time_in_force")
        batch_op.drop_column("client_order_id")

    op.drop_index(op.f("ix_exec_broker_sync_run_run_id"), table_name="exec_broker_sync_run")
    op.drop_index(op.f("ix_exec_broker_sync_run_trace_id"), table_name="exec_broker_sync_run")
    op.drop_index(op.f("ix_exec_broker_sync_run_status"), table_name="exec_broker_sync_run")
    op.drop_index(op.f("ix_exec_broker_sync_run_account_snapshot_id"), table_name="exec_broker_sync_run")
    op.drop_index(op.f("ix_exec_broker_sync_run_broker_adapter"), table_name="exec_broker_sync_run")
    op.drop_index(op.f("ix_exec_broker_sync_run_environment"), table_name="exec_broker_sync_run")
    op.drop_index(op.f("ix_exec_broker_sync_run_account_ref"), table_name="exec_broker_sync_run")
    op.drop_index(op.f("ix_exec_broker_sync_run_provider_key"), table_name="exec_broker_sync_run")
    op.drop_table("exec_broker_sync_run")
