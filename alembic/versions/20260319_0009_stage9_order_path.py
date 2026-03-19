"""stage9 order path

Revision ID: 20260319_0009
Revises: 20260319_0008
Create Date: 2026-03-19 23:58:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "20260319_0009"
down_revision = "20260319_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "exec_allocation_policy",
        sa.Column("policy_key", sa.String(length=120), nullable=False),
        sa.Column("environment", sa.String(length=40), nullable=False),
        sa.Column("scope", sa.String(length=40), nullable=False),
        sa.Column("strategy_spec_id", sa.String(length=36), nullable=True),
        sa.Column("provider_key", sa.String(length=120), nullable=True),
        sa.Column("account_ref", sa.String(length=120), nullable=True),
        sa.Column("max_strategy_notional_pct", sa.Float(), nullable=False),
        sa.Column("max_gross_exposure_pct", sa.Float(), nullable=False),
        sa.Column("max_open_positions", sa.Integer(), nullable=False),
        sa.Column("max_open_orders", sa.Integer(), nullable=False),
        sa.Column("allow_short", sa.Boolean(), nullable=False),
        sa.Column("allow_fractional", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["strategy_spec_id"], ["strat_strategy_spec.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("policy_key"),
    )
    op.create_index(op.f("ix_exec_allocation_policy_environment"), "exec_allocation_policy", ["environment"], unique=False)
    op.create_index(op.f("ix_exec_allocation_policy_scope"), "exec_allocation_policy", ["scope"], unique=False)
    op.create_index(op.f("ix_exec_allocation_policy_strategy_spec_id"), "exec_allocation_policy", ["strategy_spec_id"], unique=False)
    op.create_index(op.f("ix_exec_allocation_policy_provider_key"), "exec_allocation_policy", ["provider_key"], unique=False)
    op.create_index(op.f("ix_exec_allocation_policy_account_ref"), "exec_allocation_policy", ["account_ref"], unique=False)
    op.create_index(op.f("ix_exec_allocation_policy_status"), "exec_allocation_policy", ["status"], unique=False)
    op.create_index(op.f("ix_exec_allocation_policy_trace_id"), "exec_allocation_policy", ["trace_id"], unique=False)
    op.create_index(op.f("ix_exec_allocation_policy_run_id"), "exec_allocation_policy", ["run_id"], unique=False)

    op.create_table(
        "exec_order_intent",
        sa.Column("strategy_spec_id", sa.String(length=36), nullable=False),
        sa.Column("allocation_policy_id", sa.String(length=36), nullable=True),
        sa.Column("provider_key", sa.String(length=120), nullable=False),
        sa.Column("account_ref", sa.String(length=120), nullable=False),
        sa.Column("environment", sa.String(length=40), nullable=False),
        sa.Column("broker_adapter", sa.String(length=80), nullable=False),
        sa.Column("symbol", sa.String(length=40), nullable=False),
        sa.Column("asset_type", sa.String(length=40), nullable=False),
        sa.Column("side", sa.String(length=20), nullable=False),
        sa.Column("order_type", sa.String(length=20), nullable=False),
        sa.Column("time_in_force", sa.String(length=20), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("reference_price", sa.Float(), nullable=False),
        sa.Column("requested_notional", sa.Float(), nullable=False),
        sa.Column("limit_price", sa.Float(), nullable=True),
        sa.Column("stop_price", sa.Float(), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("signal_payload", sa.JSON(), nullable=False),
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
        sa.ForeignKeyConstraint(["allocation_policy_id"], ["exec_allocation_policy.id"]),
        sa.ForeignKeyConstraint(["strategy_spec_id"], ["strat_strategy_spec.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_exec_order_intent_strategy_spec_id"), "exec_order_intent", ["strategy_spec_id"], unique=False)
    op.create_index(op.f("ix_exec_order_intent_allocation_policy_id"), "exec_order_intent", ["allocation_policy_id"], unique=False)
    op.create_index(op.f("ix_exec_order_intent_provider_key"), "exec_order_intent", ["provider_key"], unique=False)
    op.create_index(op.f("ix_exec_order_intent_account_ref"), "exec_order_intent", ["account_ref"], unique=False)
    op.create_index(op.f("ix_exec_order_intent_environment"), "exec_order_intent", ["environment"], unique=False)
    op.create_index(op.f("ix_exec_order_intent_broker_adapter"), "exec_order_intent", ["broker_adapter"], unique=False)
    op.create_index(op.f("ix_exec_order_intent_symbol"), "exec_order_intent", ["symbol"], unique=False)
    op.create_index(op.f("ix_exec_order_intent_side"), "exec_order_intent", ["side"], unique=False)
    op.create_index(op.f("ix_exec_order_intent_status"), "exec_order_intent", ["status"], unique=False)
    op.create_index(op.f("ix_exec_order_intent_trace_id"), "exec_order_intent", ["trace_id"], unique=False)
    op.create_index(op.f("ix_exec_order_intent_run_id"), "exec_order_intent", ["run_id"], unique=False)

    op.create_table(
        "exec_order_record",
        sa.Column("order_intent_id", sa.String(length=36), nullable=False),
        sa.Column("strategy_spec_id", sa.String(length=36), nullable=False),
        sa.Column("provider_key", sa.String(length=120), nullable=False),
        sa.Column("account_ref", sa.String(length=120), nullable=False),
        sa.Column("environment", sa.String(length=40), nullable=False),
        sa.Column("broker_order_id", sa.String(length=160), nullable=False),
        sa.Column("symbol", sa.String(length=40), nullable=False),
        sa.Column("asset_type", sa.String(length=40), nullable=False),
        sa.Column("side", sa.String(length=20), nullable=False),
        sa.Column("order_type", sa.String(length=20), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("filled_quantity", sa.Float(), nullable=False),
        sa.Column("requested_notional", sa.Float(), nullable=False),
        sa.Column("avg_fill_price", sa.Float(), nullable=True),
        sa.Column("limit_price", sa.Float(), nullable=True),
        sa.Column("stop_price", sa.Float(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("broker_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
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
        sa.ForeignKeyConstraint(["order_intent_id"], ["exec_order_intent.id"]),
        sa.ForeignKeyConstraint(["strategy_spec_id"], ["strat_strategy_spec.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("broker_order_id"),
    )
    op.create_index(op.f("ix_exec_order_record_order_intent_id"), "exec_order_record", ["order_intent_id"], unique=False)
    op.create_index(op.f("ix_exec_order_record_strategy_spec_id"), "exec_order_record", ["strategy_spec_id"], unique=False)
    op.create_index(op.f("ix_exec_order_record_provider_key"), "exec_order_record", ["provider_key"], unique=False)
    op.create_index(op.f("ix_exec_order_record_account_ref"), "exec_order_record", ["account_ref"], unique=False)
    op.create_index(op.f("ix_exec_order_record_environment"), "exec_order_record", ["environment"], unique=False)
    op.create_index(op.f("ix_exec_order_record_symbol"), "exec_order_record", ["symbol"], unique=False)
    op.create_index(op.f("ix_exec_order_record_side"), "exec_order_record", ["side"], unique=False)
    op.create_index(op.f("ix_exec_order_record_status"), "exec_order_record", ["status"], unique=False)
    op.create_index(op.f("ix_exec_order_record_trace_id"), "exec_order_record", ["trace_id"], unique=False)
    op.create_index(op.f("ix_exec_order_record_run_id"), "exec_order_record", ["run_id"], unique=False)

    op.create_table(
        "exec_position_record",
        sa.Column("strategy_spec_id", sa.String(length=36), nullable=False),
        sa.Column("provider_key", sa.String(length=120), nullable=False),
        sa.Column("account_ref", sa.String(length=120), nullable=False),
        sa.Column("environment", sa.String(length=40), nullable=False),
        sa.Column("symbol", sa.String(length=40), nullable=False),
        sa.Column("asset_type", sa.String(length=40), nullable=False),
        sa.Column("direction", sa.String(length=20), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("avg_entry_price", sa.Float(), nullable=False),
        sa.Column("market_price", sa.Float(), nullable=True),
        sa.Column("notional_value", sa.Float(), nullable=False),
        sa.Column("realized_pnl", sa.Float(), nullable=False),
        sa.Column("unrealized_pnl", sa.Float(), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
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
        sa.ForeignKeyConstraint(["strategy_spec_id"], ["strat_strategy_spec.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_exec_position_record_strategy_spec_id"), "exec_position_record", ["strategy_spec_id"], unique=False)
    op.create_index(op.f("ix_exec_position_record_provider_key"), "exec_position_record", ["provider_key"], unique=False)
    op.create_index(op.f("ix_exec_position_record_account_ref"), "exec_position_record", ["account_ref"], unique=False)
    op.create_index(op.f("ix_exec_position_record_environment"), "exec_position_record", ["environment"], unique=False)
    op.create_index(op.f("ix_exec_position_record_symbol"), "exec_position_record", ["symbol"], unique=False)
    op.create_index(op.f("ix_exec_position_record_direction"), "exec_position_record", ["direction"], unique=False)
    op.create_index(op.f("ix_exec_position_record_status"), "exec_position_record", ["status"], unique=False)
    op.create_index(op.f("ix_exec_position_record_trace_id"), "exec_position_record", ["trace_id"], unique=False)
    op.create_index(op.f("ix_exec_position_record_run_id"), "exec_position_record", ["run_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_exec_position_record_run_id"), table_name="exec_position_record")
    op.drop_index(op.f("ix_exec_position_record_trace_id"), table_name="exec_position_record")
    op.drop_index(op.f("ix_exec_position_record_status"), table_name="exec_position_record")
    op.drop_index(op.f("ix_exec_position_record_direction"), table_name="exec_position_record")
    op.drop_index(op.f("ix_exec_position_record_symbol"), table_name="exec_position_record")
    op.drop_index(op.f("ix_exec_position_record_environment"), table_name="exec_position_record")
    op.drop_index(op.f("ix_exec_position_record_account_ref"), table_name="exec_position_record")
    op.drop_index(op.f("ix_exec_position_record_provider_key"), table_name="exec_position_record")
    op.drop_index(op.f("ix_exec_position_record_strategy_spec_id"), table_name="exec_position_record")
    op.drop_table("exec_position_record")

    op.drop_index(op.f("ix_exec_order_record_run_id"), table_name="exec_order_record")
    op.drop_index(op.f("ix_exec_order_record_trace_id"), table_name="exec_order_record")
    op.drop_index(op.f("ix_exec_order_record_status"), table_name="exec_order_record")
    op.drop_index(op.f("ix_exec_order_record_side"), table_name="exec_order_record")
    op.drop_index(op.f("ix_exec_order_record_symbol"), table_name="exec_order_record")
    op.drop_index(op.f("ix_exec_order_record_environment"), table_name="exec_order_record")
    op.drop_index(op.f("ix_exec_order_record_account_ref"), table_name="exec_order_record")
    op.drop_index(op.f("ix_exec_order_record_provider_key"), table_name="exec_order_record")
    op.drop_index(op.f("ix_exec_order_record_strategy_spec_id"), table_name="exec_order_record")
    op.drop_index(op.f("ix_exec_order_record_order_intent_id"), table_name="exec_order_record")
    op.drop_table("exec_order_record")

    op.drop_index(op.f("ix_exec_order_intent_run_id"), table_name="exec_order_intent")
    op.drop_index(op.f("ix_exec_order_intent_trace_id"), table_name="exec_order_intent")
    op.drop_index(op.f("ix_exec_order_intent_status"), table_name="exec_order_intent")
    op.drop_index(op.f("ix_exec_order_intent_side"), table_name="exec_order_intent")
    op.drop_index(op.f("ix_exec_order_intent_symbol"), table_name="exec_order_intent")
    op.drop_index(op.f("ix_exec_order_intent_broker_adapter"), table_name="exec_order_intent")
    op.drop_index(op.f("ix_exec_order_intent_environment"), table_name="exec_order_intent")
    op.drop_index(op.f("ix_exec_order_intent_account_ref"), table_name="exec_order_intent")
    op.drop_index(op.f("ix_exec_order_intent_provider_key"), table_name="exec_order_intent")
    op.drop_index(op.f("ix_exec_order_intent_allocation_policy_id"), table_name="exec_order_intent")
    op.drop_index(op.f("ix_exec_order_intent_strategy_spec_id"), table_name="exec_order_intent")
    op.drop_table("exec_order_intent")

    op.drop_index(op.f("ix_exec_allocation_policy_run_id"), table_name="exec_allocation_policy")
    op.drop_index(op.f("ix_exec_allocation_policy_trace_id"), table_name="exec_allocation_policy")
    op.drop_index(op.f("ix_exec_allocation_policy_status"), table_name="exec_allocation_policy")
    op.drop_index(op.f("ix_exec_allocation_policy_account_ref"), table_name="exec_allocation_policy")
    op.drop_index(op.f("ix_exec_allocation_policy_provider_key"), table_name="exec_allocation_policy")
    op.drop_index(op.f("ix_exec_allocation_policy_strategy_spec_id"), table_name="exec_allocation_policy")
    op.drop_index(op.f("ix_exec_allocation_policy_scope"), table_name="exec_allocation_policy")
    op.drop_index(op.f("ix_exec_allocation_policy_environment"), table_name="exec_allocation_policy")
    op.drop_table("exec_allocation_policy")
