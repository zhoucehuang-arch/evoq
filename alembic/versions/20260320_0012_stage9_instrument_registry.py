"""stage9 instrument registry and broker capability model

Revision ID: 20260320_0012
Revises: 20260320_0011
Create Date: 2026-03-20 03:40:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "20260320_0012"
down_revision = "20260320_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "exec_instrument_definition",
        sa.Column("instrument_key", sa.String(length=200), nullable=False),
        sa.Column("symbol", sa.String(length=80), nullable=False),
        sa.Column("display_symbol", sa.String(length=160), nullable=False),
        sa.Column("instrument_type", sa.String(length=40), nullable=False),
        sa.Column("venue", sa.String(length=80), nullable=True),
        sa.Column("currency", sa.String(length=16), nullable=False),
        sa.Column("underlying_symbol", sa.String(length=80), nullable=True),
        sa.Column("option_right", sa.String(length=16), nullable=True),
        sa.Column("option_style", sa.String(length=16), nullable=True),
        sa.Column("expiration_date", sa.Date(), nullable=True),
        sa.Column("strike_price", sa.Float(), nullable=True),
        sa.Column("contract_multiplier", sa.Float(), nullable=False),
        sa.Column("leverage_ratio", sa.Float(), nullable=False),
        sa.Column("inverse_exposure", sa.Boolean(), nullable=False),
        sa.Column("is_marginable", sa.Boolean(), nullable=False),
        sa.Column("is_shortable", sa.Boolean(), nullable=False),
        sa.Column("metadata_payload", sa.JSON(), nullable=False),
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
    op.create_index(op.f("ix_exec_instrument_definition_instrument_key"), "exec_instrument_definition", ["instrument_key"], unique=True)
    op.create_index(op.f("ix_exec_instrument_definition_symbol"), "exec_instrument_definition", ["symbol"], unique=False)
    op.create_index(op.f("ix_exec_instrument_definition_instrument_type"), "exec_instrument_definition", ["instrument_type"], unique=False)
    op.create_index(op.f("ix_exec_instrument_definition_underlying_symbol"), "exec_instrument_definition", ["underlying_symbol"], unique=False)
    op.create_index(op.f("ix_exec_instrument_definition_status"), "exec_instrument_definition", ["status"], unique=False)
    op.create_index(op.f("ix_exec_instrument_definition_trace_id"), "exec_instrument_definition", ["trace_id"], unique=False)
    op.create_index(op.f("ix_exec_instrument_definition_run_id"), "exec_instrument_definition", ["run_id"], unique=False)

    op.create_table(
        "exec_broker_capability",
        sa.Column("capability_key", sa.String(length=160), nullable=False),
        sa.Column("provider_key", sa.String(length=120), nullable=False),
        sa.Column("broker_adapter", sa.String(length=80), nullable=False),
        sa.Column("account_ref", sa.String(length=120), nullable=True),
        sa.Column("environment", sa.String(length=40), nullable=False),
        sa.Column("account_mode", sa.String(length=40), nullable=False),
        sa.Column("supports_equities", sa.Boolean(), nullable=False),
        sa.Column("supports_etfs", sa.Boolean(), nullable=False),
        sa.Column("supports_fractional", sa.Boolean(), nullable=False),
        sa.Column("supports_short", sa.Boolean(), nullable=False),
        sa.Column("supports_margin", sa.Boolean(), nullable=False),
        sa.Column("supports_options", sa.Boolean(), nullable=False),
        sa.Column("supports_multi_leg_options", sa.Boolean(), nullable=False),
        sa.Column("supports_option_exercise", sa.Boolean(), nullable=False),
        sa.Column("supports_option_assignment_events", sa.Boolean(), nullable=False),
        sa.Column("supports_live_trading", sa.Boolean(), nullable=False),
        sa.Column("supports_paper_trading", sa.Boolean(), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_exec_broker_capability_capability_key"), "exec_broker_capability", ["capability_key"], unique=True)
    op.create_index(op.f("ix_exec_broker_capability_provider_key"), "exec_broker_capability", ["provider_key"], unique=False)
    op.create_index(op.f("ix_exec_broker_capability_broker_adapter"), "exec_broker_capability", ["broker_adapter"], unique=False)
    op.create_index(op.f("ix_exec_broker_capability_account_ref"), "exec_broker_capability", ["account_ref"], unique=False)
    op.create_index(op.f("ix_exec_broker_capability_environment"), "exec_broker_capability", ["environment"], unique=False)
    op.create_index(op.f("ix_exec_broker_capability_status"), "exec_broker_capability", ["status"], unique=False)
    op.create_index(op.f("ix_exec_broker_capability_trace_id"), "exec_broker_capability", ["trace_id"], unique=False)
    op.create_index(op.f("ix_exec_broker_capability_run_id"), "exec_broker_capability", ["run_id"], unique=False)

    with op.batch_alter_table("exec_order_intent") as batch_op:
        batch_op.add_column(sa.Column("instrument_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("instrument_key", sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column("underlying_symbol", sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column("position_effect", sa.String(length=20), server_default="auto", nullable=False))
        batch_op.create_index(op.f("ix_exec_order_intent_instrument_id"), ["instrument_id"], unique=False)
        batch_op.create_index(op.f("ix_exec_order_intent_instrument_key"), ["instrument_key"], unique=False)
        batch_op.create_index(op.f("ix_exec_order_intent_underlying_symbol"), ["underlying_symbol"], unique=False)

    with op.batch_alter_table("exec_order_record") as batch_op:
        batch_op.add_column(sa.Column("instrument_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("instrument_key", sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column("underlying_symbol", sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column("position_effect", sa.String(length=20), server_default="auto", nullable=False))
        batch_op.create_index(op.f("ix_exec_order_record_instrument_id"), ["instrument_id"], unique=False)
        batch_op.create_index(op.f("ix_exec_order_record_instrument_key"), ["instrument_key"], unique=False)
        batch_op.create_index(op.f("ix_exec_order_record_underlying_symbol"), ["underlying_symbol"], unique=False)

    with op.batch_alter_table("exec_position_record") as batch_op:
        batch_op.add_column(sa.Column("instrument_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("instrument_key", sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column("underlying_symbol", sa.String(length=80), nullable=True))
        batch_op.create_index(op.f("ix_exec_position_record_instrument_id"), ["instrument_id"], unique=False)
        batch_op.create_index(op.f("ix_exec_position_record_instrument_key"), ["instrument_key"], unique=False)
        batch_op.create_index(op.f("ix_exec_position_record_underlying_symbol"), ["underlying_symbol"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("exec_position_record") as batch_op:
        batch_op.drop_index(op.f("ix_exec_position_record_underlying_symbol"))
        batch_op.drop_index(op.f("ix_exec_position_record_instrument_key"))
        batch_op.drop_index(op.f("ix_exec_position_record_instrument_id"))
        batch_op.drop_column("underlying_symbol")
        batch_op.drop_column("instrument_key")
        batch_op.drop_column("instrument_id")

    with op.batch_alter_table("exec_order_record") as batch_op:
        batch_op.drop_index(op.f("ix_exec_order_record_underlying_symbol"))
        batch_op.drop_index(op.f("ix_exec_order_record_instrument_key"))
        batch_op.drop_index(op.f("ix_exec_order_record_instrument_id"))
        batch_op.drop_column("position_effect")
        batch_op.drop_column("underlying_symbol")
        batch_op.drop_column("instrument_key")
        batch_op.drop_column("instrument_id")

    with op.batch_alter_table("exec_order_intent") as batch_op:
        batch_op.drop_index(op.f("ix_exec_order_intent_underlying_symbol"))
        batch_op.drop_index(op.f("ix_exec_order_intent_instrument_key"))
        batch_op.drop_index(op.f("ix_exec_order_intent_instrument_id"))
        batch_op.drop_column("position_effect")
        batch_op.drop_column("underlying_symbol")
        batch_op.drop_column("instrument_key")
        batch_op.drop_column("instrument_id")

    op.drop_index(op.f("ix_exec_broker_capability_run_id"), table_name="exec_broker_capability")
    op.drop_index(op.f("ix_exec_broker_capability_trace_id"), table_name="exec_broker_capability")
    op.drop_index(op.f("ix_exec_broker_capability_status"), table_name="exec_broker_capability")
    op.drop_index(op.f("ix_exec_broker_capability_environment"), table_name="exec_broker_capability")
    op.drop_index(op.f("ix_exec_broker_capability_account_ref"), table_name="exec_broker_capability")
    op.drop_index(op.f("ix_exec_broker_capability_broker_adapter"), table_name="exec_broker_capability")
    op.drop_index(op.f("ix_exec_broker_capability_provider_key"), table_name="exec_broker_capability")
    op.drop_index(op.f("ix_exec_broker_capability_capability_key"), table_name="exec_broker_capability")
    op.drop_table("exec_broker_capability")

    op.drop_index(op.f("ix_exec_instrument_definition_run_id"), table_name="exec_instrument_definition")
    op.drop_index(op.f("ix_exec_instrument_definition_trace_id"), table_name="exec_instrument_definition")
    op.drop_index(op.f("ix_exec_instrument_definition_status"), table_name="exec_instrument_definition")
    op.drop_index(op.f("ix_exec_instrument_definition_underlying_symbol"), table_name="exec_instrument_definition")
    op.drop_index(op.f("ix_exec_instrument_definition_instrument_type"), table_name="exec_instrument_definition")
    op.drop_index(op.f("ix_exec_instrument_definition_symbol"), table_name="exec_instrument_definition")
    op.drop_index(op.f("ix_exec_instrument_definition_instrument_key"), table_name="exec_instrument_definition")
    op.drop_table("exec_instrument_definition")
