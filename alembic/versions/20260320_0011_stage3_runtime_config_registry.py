"""stage3 runtime config registry and proposals

Revision ID: 20260320_0011
Revises: 20260320_0010
Create Date: 2026-03-20 03:10:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "20260320_0011"
down_revision = "20260320_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "gov_runtime_config_proposal",
        sa.Column("target_type", sa.String(length=40), nullable=False),
        sa.Column("target_key", sa.String(length=120), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("requested_by", sa.String(length=120), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("change_summary", sa.Text(), nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("requires_approval", sa.Boolean(), nullable=False),
        sa.Column("approval_request_id", sa.String(length=36), nullable=True),
        sa.Column("current_value_json", sa.JSON(), nullable=False),
        sa.Column("proposed_value_json", sa.JSON(), nullable=False),
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
        sa.ForeignKeyConstraint(["approval_request_id"], ["gov_approval_request.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_gov_runtime_config_proposal_target_type"),
        "gov_runtime_config_proposal",
        ["target_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_gov_runtime_config_proposal_target_key"),
        "gov_runtime_config_proposal",
        ["target_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_gov_runtime_config_proposal_category"),
        "gov_runtime_config_proposal",
        ["category"],
        unique=False,
    )
    op.create_index(
        op.f("ix_gov_runtime_config_proposal_approval_request_id"),
        "gov_runtime_config_proposal",
        ["approval_request_id"],
        unique=False,
    )
    op.create_index(op.f("ix_gov_runtime_config_proposal_status"), "gov_runtime_config_proposal", ["status"], unique=False)
    op.create_index(op.f("ix_gov_runtime_config_proposal_trace_id"), "gov_runtime_config_proposal", ["trace_id"], unique=False)
    op.create_index(op.f("ix_gov_runtime_config_proposal_run_id"), "gov_runtime_config_proposal", ["run_id"], unique=False)

    op.create_table(
        "gov_runtime_config_revision",
        sa.Column("proposal_id", sa.String(length=36), nullable=True),
        sa.Column("target_type", sa.String(length=40), nullable=False),
        sa.Column("target_key", sa.String(length=120), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("change_summary", sa.Text(), nullable=False),
        sa.Column("previous_value_json", sa.JSON(), nullable=False),
        sa.Column("applied_value_json", sa.JSON(), nullable=False),
        sa.Column("applied_by", sa.String(length=120), nullable=False),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=False),
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
        sa.ForeignKeyConstraint(["proposal_id"], ["gov_runtime_config_proposal.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_gov_runtime_config_revision_proposal_id"),
        "gov_runtime_config_revision",
        ["proposal_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_gov_runtime_config_revision_target_type"),
        "gov_runtime_config_revision",
        ["target_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_gov_runtime_config_revision_target_key"),
        "gov_runtime_config_revision",
        ["target_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_gov_runtime_config_revision_applied_at"),
        "gov_runtime_config_revision",
        ["applied_at"],
        unique=False,
    )
    op.create_index(op.f("ix_gov_runtime_config_revision_status"), "gov_runtime_config_revision", ["status"], unique=False)
    op.create_index(op.f("ix_gov_runtime_config_revision_trace_id"), "gov_runtime_config_revision", ["trace_id"], unique=False)
    op.create_index(op.f("ix_gov_runtime_config_revision_run_id"), "gov_runtime_config_revision", ["run_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_gov_runtime_config_revision_run_id"), table_name="gov_runtime_config_revision")
    op.drop_index(op.f("ix_gov_runtime_config_revision_trace_id"), table_name="gov_runtime_config_revision")
    op.drop_index(op.f("ix_gov_runtime_config_revision_status"), table_name="gov_runtime_config_revision")
    op.drop_index(op.f("ix_gov_runtime_config_revision_applied_at"), table_name="gov_runtime_config_revision")
    op.drop_index(op.f("ix_gov_runtime_config_revision_target_key"), table_name="gov_runtime_config_revision")
    op.drop_index(op.f("ix_gov_runtime_config_revision_target_type"), table_name="gov_runtime_config_revision")
    op.drop_index(op.f("ix_gov_runtime_config_revision_proposal_id"), table_name="gov_runtime_config_revision")
    op.drop_table("gov_runtime_config_revision")

    op.drop_index(op.f("ix_gov_runtime_config_proposal_run_id"), table_name="gov_runtime_config_proposal")
    op.drop_index(op.f("ix_gov_runtime_config_proposal_trace_id"), table_name="gov_runtime_config_proposal")
    op.drop_index(op.f("ix_gov_runtime_config_proposal_status"), table_name="gov_runtime_config_proposal")
    op.drop_index(op.f("ix_gov_runtime_config_proposal_approval_request_id"), table_name="gov_runtime_config_proposal")
    op.drop_index(op.f("ix_gov_runtime_config_proposal_category"), table_name="gov_runtime_config_proposal")
    op.drop_index(op.f("ix_gov_runtime_config_proposal_target_key"), table_name="gov_runtime_config_proposal")
    op.drop_index(op.f("ix_gov_runtime_config_proposal_target_type"), table_name="gov_runtime_config_proposal")
    op.drop_table("gov_runtime_config_proposal")
