"""execution numeric precision

Revision ID: 20260508_0018
Revises: 20260320_0017
Create Date: 2026-05-08 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260508_0018"
down_revision = "20260320_0017"
branch_labels = None
depends_on = None


MONEY = sa.Numeric(24, 8, asdecimal=False)
PRICE = sa.Numeric(20, 8, asdecimal=False)
QUANTITY = sa.Numeric(24, 10, asdecimal=False)
RATIO = sa.Numeric(18, 8, asdecimal=False)


def _alter_columns(table_name: str, columns: list[tuple[str, sa.Numeric, bool]]) -> None:
    with op.batch_alter_table(table_name) as batch:
        for name, column_type, nullable in columns:
            batch.alter_column(
                name,
                existing_type=sa.Float(),
                type_=column_type,
                existing_nullable=nullable,
            )


def _revert_columns(table_name: str, columns: list[tuple[str, bool]]) -> None:
    with op.batch_alter_table(table_name) as batch:
        for name, nullable in columns:
            batch.alter_column(
                name,
                existing_type=sa.Numeric(),
                type_=sa.Float(),
                existing_nullable=nullable,
            )


def upgrade() -> None:
    _alter_columns(
        "exec_broker_account_snapshot",
        [
            ("equity", MONEY, False),
            ("cash", MONEY, False),
            ("buying_power", MONEY, False),
            ("gross_exposure", MONEY, False),
            ("net_exposure", MONEY, False),
        ],
    )
    _alter_columns(
        "exec_instrument_definition",
        [
            ("strike_price", PRICE, True),
            ("contract_multiplier", RATIO, False),
            ("leverage_ratio", RATIO, False),
        ],
    )
    _alter_columns(
        "exec_order_intent",
        [
            ("quantity", QUANTITY, False),
            ("reference_price", PRICE, False),
            ("requested_notional", MONEY, False),
            ("limit_price", PRICE, True),
            ("stop_price", PRICE, True),
        ],
    )
    _alter_columns(
        "exec_order_record",
        [
            ("quantity", QUANTITY, False),
            ("filled_quantity", QUANTITY, False),
            ("requested_notional", MONEY, False),
            ("avg_fill_price", PRICE, True),
            ("limit_price", PRICE, True),
            ("stop_price", PRICE, True),
        ],
    )
    _alter_columns(
        "exec_order_leg",
        [
            ("quantity", QUANTITY, False),
            ("ratio_quantity", RATIO, False),
            ("reference_price", PRICE, False),
            ("requested_notional", MONEY, False),
        ],
    )
    _alter_columns(
        "exec_position_record",
        [
            ("quantity", QUANTITY, False),
            ("avg_entry_price", PRICE, False),
            ("market_price", PRICE, True),
            ("notional_value", MONEY, False),
            ("realized_pnl", MONEY, False),
            ("unrealized_pnl", MONEY, False),
        ],
    )
    _alter_columns(
        "exec_option_lifecycle_event",
        [
            ("quantity", QUANTITY, False),
            ("event_price", PRICE, True),
            ("cash_flow", MONEY, True),
        ],
    )


def downgrade() -> None:
    _revert_columns(
        "exec_option_lifecycle_event",
        [("quantity", False), ("event_price", True), ("cash_flow", True)],
    )
    _revert_columns(
        "exec_position_record",
        [
            ("quantity", False),
            ("avg_entry_price", False),
            ("market_price", True),
            ("notional_value", False),
            ("realized_pnl", False),
            ("unrealized_pnl", False),
        ],
    )
    _revert_columns(
        "exec_order_leg",
        [
            ("quantity", False),
            ("ratio_quantity", False),
            ("reference_price", False),
            ("requested_notional", False),
        ],
    )
    _revert_columns(
        "exec_order_record",
        [
            ("quantity", False),
            ("filled_quantity", False),
            ("requested_notional", False),
            ("avg_fill_price", True),
            ("limit_price", True),
            ("stop_price", True),
        ],
    )
    _revert_columns(
        "exec_order_intent",
        [
            ("quantity", False),
            ("reference_price", False),
            ("requested_notional", False),
            ("limit_price", True),
            ("stop_price", True),
        ],
    )
    _revert_columns(
        "exec_instrument_definition",
        [("strike_price", True), ("contract_multiplier", False), ("leverage_ratio", False)],
    )
    _revert_columns(
        "exec_broker_account_snapshot",
        [
            ("equity", False),
            ("cash", False),
            ("buying_power", False),
            ("gross_exposure", False),
            ("net_exposure", False),
        ],
    )
