"""stage6 supervisor codex linkage

Revision ID: 20260318_0004
Revises: 20260318_0003
Create Date: 2026-03-18 23:58:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "20260318_0004"
down_revision = "20260318_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("exec_codex_run", sa.Column("supervisor_loop_key", sa.String(length=120), nullable=True))
    op.create_index(
        op.f("ix_exec_codex_run_supervisor_loop_key"),
        "exec_codex_run",
        ["supervisor_loop_key"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_exec_codex_run_supervisor_loop_key"), table_name="exec_codex_run")
    op.drop_column("exec_codex_run", "supervisor_loop_key")
