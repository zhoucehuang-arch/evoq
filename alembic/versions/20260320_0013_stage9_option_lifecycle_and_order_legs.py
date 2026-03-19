"""stage9 option lifecycle events and order legs

Revision ID: 20260320_0013
Revises: 20260320_0012
Create Date: 2026-03-20 10:20:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "20260320_0013"
down_revision = "20260320_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "exec_order_leg",
        sa.Column("order_intent_id", sa.String(length=36), nullable=True),
        sa.Column("order_record_id", sa.String(length=36), nullable=True),
        sa.Column("leg_index", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=80), nullable=False),
        sa.Column("instrument_id", sa.String(length=36), nullable=True),
        sa.Column("instrument_key", sa.String(length=200), nullable=True),
        sa.Column("underlying_symbol", sa.String(length=80), nullable=True),
        sa.Column("asset_type", sa.String(length=40), nullable=False),
        sa.Column("side", sa.String(length=20), nullable=False),
        sa.Column("position_effect", sa.String(length=20), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("ratio_quantity", sa.Float(), nullable=False),
        sa.Column("reference_price", sa.Float(), nullable=False),
        sa.Column("requested_notional", sa.Float(), nullable=False),
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
        sa.ForeignKeyConstraint(["order_record_id"], ["exec_order_record.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_exec_order_leg_order_intent_id"), "exec_order_leg", ["order_intent_id"], unique=False)
    op.create_index(op.f("ix_exec_order_leg_order_record_id"), "exec_order_leg", ["order_record_id"], unique=False)
    op.create_index(op.f("ix_exec_order_leg_leg_index"), "exec_order_leg", ["leg_index"], unique=False)
    op.create_index(op.f("ix_exec_order_leg_symbol"), "exec_order_leg", ["symbol"], unique=False)
    op.create_index(op.f("ix_exec_order_leg_instrument_id"), "exec_order_leg", ["instrument_id"], unique=False)
    op.create_index(op.f("ix_exec_order_leg_instrument_key"), "exec_order_leg", ["instrument_key"], unique=False)
    op.create_index(op.f("ix_exec_order_leg_underlying_symbol"), "exec_order_leg", ["underlying_symbol"], unique=False)
    op.create_index(op.f("ix_exec_order_leg_status"), "exec_order_leg", ["status"], unique=False)
    op.create_index(op.f("ix_exec_order_leg_trace_id"), "exec_order_leg", ["trace_id"], unique=False)
    op.create_index(op.f("ix_exec_order_leg_run_id"), "exec_order_leg", ["run_id"], unique=False)

    op.create_table(
        "exec_option_lifecycle_event",
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("provider_key", sa.String(length=120), nullable=False),
        sa.Column("account_ref", sa.String(length=120), nullable=False),
        sa.Column("environment", sa.String(length=40), nullable=False),
        sa.Column("symbol", sa.String(length=80), nullable=False),
        sa.Column("underlying_symbol", sa.String(length=80), nullable=True),
        sa.Column("position_id", sa.String(length=36), nullable=True),
        sa.Column("strategy_spec_id", sa.String(length=36), nullable=True),
        sa.Column("instrument_id", sa.String(length=36), nullable=True),
        sa.Column("instrument_key", sa.String(length=200), nullable=True),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("event_price", sa.Float(), nullable=True),
        sa.Column("cash_flow", sa.Float(), nullable=True),
        sa.Column("state_applied", sa.Boolean(), nullable=False),
        sa.Column("review_required", sa.Boolean(), nullable=False),
        sa.Column("applied_position_id", sa.String(length=36), nullable=True),
        sa.Column("resulting_symbol", sa.String(length=80), nullable=True),
        sa.Column("resulting_instrument_key", sa.String(length=200), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("metadata_payload", sa.JSON(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
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
        sa.ForeignKeyConstraint(["position_id"], ["exec_position_record.id"]),
        sa.ForeignKeyConstraint(["strategy_spec_id"], ["strat_strategy_spec.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_exec_option_lifecycle_event_event_type"), "exec_option_lifecycle_event", ["event_type"], unique=False)
    op.create_index(op.f("ix_exec_option_lifecycle_event_provider_key"), "exec_option_lifecycle_event", ["provider_key"], unique=False)
    op.create_index(op.f("ix_exec_option_lifecycle_event_account_ref"), "exec_option_lifecycle_event", ["account_ref"], unique=False)
    op.create_index(op.f("ix_exec_option_lifecycle_event_environment"), "exec_option_lifecycle_event", ["environment"], unique=False)
    op.create_index(op.f("ix_exec_option_lifecycle_event_symbol"), "exec_option_lifecycle_event", ["symbol"], unique=False)
    op.create_index(op.f("ix_exec_option_lifecycle_event_underlying_symbol"), "exec_option_lifecycle_event", ["underlying_symbol"], unique=False)
    op.create_index(op.f("ix_exec_option_lifecycle_event_position_id"), "exec_option_lifecycle_event", ["position_id"], unique=False)
    op.create_index(op.f("ix_exec_option_lifecycle_event_strategy_spec_id"), "exec_option_lifecycle_event", ["strategy_spec_id"], unique=False)
    op.create_index(op.f("ix_exec_option_lifecycle_event_instrument_id"), "exec_option_lifecycle_event", ["instrument_id"], unique=False)
    op.create_index(op.f("ix_exec_option_lifecycle_event_instrument_key"), "exec_option_lifecycle_event", ["instrument_key"], unique=False)
    op.create_index(op.f("ix_exec_option_lifecycle_event_applied_position_id"), "exec_option_lifecycle_event", ["applied_position_id"], unique=False)
    op.create_index(op.f("ix_exec_option_lifecycle_event_resulting_symbol"), "exec_option_lifecycle_event", ["resulting_symbol"], unique=False)
    op.create_index(op.f("ix_exec_option_lifecycle_event_resulting_instrument_key"), "exec_option_lifecycle_event", ["resulting_instrument_key"], unique=False)
    op.create_index(op.f("ix_exec_option_lifecycle_event_occurred_at"), "exec_option_lifecycle_event", ["occurred_at"], unique=False)
    op.create_index(op.f("ix_exec_option_lifecycle_event_status"), "exec_option_lifecycle_event", ["status"], unique=False)
    op.create_index(op.f("ix_exec_option_lifecycle_event_trace_id"), "exec_option_lifecycle_event", ["trace_id"], unique=False)
    op.create_index(op.f("ix_exec_option_lifecycle_event_run_id"), "exec_option_lifecycle_event", ["run_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_exec_option_lifecycle_event_run_id"), table_name="exec_option_lifecycle_event")
    op.drop_index(op.f("ix_exec_option_lifecycle_event_trace_id"), table_name="exec_option_lifecycle_event")
    op.drop_index(op.f("ix_exec_option_lifecycle_event_status"), table_name="exec_option_lifecycle_event")
    op.drop_index(op.f("ix_exec_option_lifecycle_event_occurred_at"), table_name="exec_option_lifecycle_event")
    op.drop_index(op.f("ix_exec_option_lifecycle_event_resulting_instrument_key"), table_name="exec_option_lifecycle_event")
    op.drop_index(op.f("ix_exec_option_lifecycle_event_resulting_symbol"), table_name="exec_option_lifecycle_event")
    op.drop_index(op.f("ix_exec_option_lifecycle_event_applied_position_id"), table_name="exec_option_lifecycle_event")
    op.drop_index(op.f("ix_exec_option_lifecycle_event_instrument_key"), table_name="exec_option_lifecycle_event")
    op.drop_index(op.f("ix_exec_option_lifecycle_event_instrument_id"), table_name="exec_option_lifecycle_event")
    op.drop_index(op.f("ix_exec_option_lifecycle_event_strategy_spec_id"), table_name="exec_option_lifecycle_event")
    op.drop_index(op.f("ix_exec_option_lifecycle_event_position_id"), table_name="exec_option_lifecycle_event")
    op.drop_index(op.f("ix_exec_option_lifecycle_event_underlying_symbol"), table_name="exec_option_lifecycle_event")
    op.drop_index(op.f("ix_exec_option_lifecycle_event_symbol"), table_name="exec_option_lifecycle_event")
    op.drop_index(op.f("ix_exec_option_lifecycle_event_environment"), table_name="exec_option_lifecycle_event")
    op.drop_index(op.f("ix_exec_option_lifecycle_event_account_ref"), table_name="exec_option_lifecycle_event")
    op.drop_index(op.f("ix_exec_option_lifecycle_event_provider_key"), table_name="exec_option_lifecycle_event")
    op.drop_index(op.f("ix_exec_option_lifecycle_event_event_type"), table_name="exec_option_lifecycle_event")
    op.drop_table("exec_option_lifecycle_event")

    op.drop_index(op.f("ix_exec_order_leg_run_id"), table_name="exec_order_leg")
    op.drop_index(op.f("ix_exec_order_leg_trace_id"), table_name="exec_order_leg")
    op.drop_index(op.f("ix_exec_order_leg_status"), table_name="exec_order_leg")
    op.drop_index(op.f("ix_exec_order_leg_underlying_symbol"), table_name="exec_order_leg")
    op.drop_index(op.f("ix_exec_order_leg_instrument_key"), table_name="exec_order_leg")
    op.drop_index(op.f("ix_exec_order_leg_instrument_id"), table_name="exec_order_leg")
    op.drop_index(op.f("ix_exec_order_leg_symbol"), table_name="exec_order_leg")
    op.drop_index(op.f("ix_exec_order_leg_leg_index"), table_name="exec_order_leg")
    op.drop_index(op.f("ix_exec_order_leg_order_record_id"), table_name="exec_order_leg")
    op.drop_index(op.f("ix_exec_order_leg_order_intent_id"), table_name="exec_order_leg")
    op.drop_table("exec_order_leg")
