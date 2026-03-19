"""stage3 control plane and supervisor

Revision ID: 20260318_0002
Revises: 20260318_0001
Create Date: 2026-03-18 22:30:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "20260318_0002"
down_revision = "20260318_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "gov_owner_preference",
        sa.Column("preference_key", sa.String(length=120), nullable=False),
        sa.Column("scope", sa.String(length=80), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("value_json", sa.JSON(), nullable=False),
        sa.Column("updated_by", sa.String(length=120), nullable=False),
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
        sa.UniqueConstraint("preference_key"),
    )
    op.create_index(op.f("ix_gov_owner_preference_scope"), "gov_owner_preference", ["scope"], unique=False)
    op.create_index(op.f("ix_gov_owner_preference_status"), "gov_owner_preference", ["status"], unique=False)
    op.create_index(op.f("ix_gov_owner_preference_trace_id"), "gov_owner_preference", ["trace_id"], unique=False)
    op.create_index(op.f("ix_gov_owner_preference_run_id"), "gov_owner_preference", ["run_id"], unique=False)

    op.create_table(
        "wf_supervisor_loop",
        sa.Column("loop_key", sa.String(length=120), nullable=False),
        sa.Column("workflow_code", sa.String(length=80), nullable=False),
        sa.Column("domain", sa.String(length=80), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("handler_key", sa.String(length=120), nullable=False),
        sa.Column("cadence_seconds", sa.Integer(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("execution_mode", sa.String(length=40), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.Column("budget_scope", sa.JSON(), nullable=False),
        sa.Column("stop_conditions", sa.JSON(), nullable=False),
        sa.Column("next_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_status", sa.String(length=40), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("failure_streak", sa.Integer(), nullable=False),
        sa.Column("max_failure_streak", sa.Integer(), nullable=False),
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
        sa.UniqueConstraint("loop_key"),
    )
    op.create_index(op.f("ix_wf_supervisor_loop_workflow_code"), "wf_supervisor_loop", ["workflow_code"], unique=False)
    op.create_index(op.f("ix_wf_supervisor_loop_domain"), "wf_supervisor_loop", ["domain"], unique=False)
    op.create_index(op.f("ix_wf_supervisor_loop_execution_mode"), "wf_supervisor_loop", ["execution_mode"], unique=False)
    op.create_index(op.f("ix_wf_supervisor_loop_is_enabled"), "wf_supervisor_loop", ["is_enabled"], unique=False)
    op.create_index(op.f("ix_wf_supervisor_loop_next_due_at"), "wf_supervisor_loop", ["next_due_at"], unique=False)
    op.create_index(op.f("ix_wf_supervisor_loop_last_status"), "wf_supervisor_loop", ["last_status"], unique=False)
    op.create_index(op.f("ix_wf_supervisor_loop_status"), "wf_supervisor_loop", ["status"], unique=False)
    op.create_index(op.f("ix_wf_supervisor_loop_trace_id"), "wf_supervisor_loop", ["trace_id"], unique=False)
    op.create_index(op.f("ix_wf_supervisor_loop_run_id"), "wf_supervisor_loop", ["run_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_wf_supervisor_loop_run_id"), table_name="wf_supervisor_loop")
    op.drop_index(op.f("ix_wf_supervisor_loop_trace_id"), table_name="wf_supervisor_loop")
    op.drop_index(op.f("ix_wf_supervisor_loop_status"), table_name="wf_supervisor_loop")
    op.drop_index(op.f("ix_wf_supervisor_loop_last_status"), table_name="wf_supervisor_loop")
    op.drop_index(op.f("ix_wf_supervisor_loop_next_due_at"), table_name="wf_supervisor_loop")
    op.drop_index(op.f("ix_wf_supervisor_loop_is_enabled"), table_name="wf_supervisor_loop")
    op.drop_index(op.f("ix_wf_supervisor_loop_execution_mode"), table_name="wf_supervisor_loop")
    op.drop_index(op.f("ix_wf_supervisor_loop_domain"), table_name="wf_supervisor_loop")
    op.drop_index(op.f("ix_wf_supervisor_loop_workflow_code"), table_name="wf_supervisor_loop")
    op.drop_table("wf_supervisor_loop")

    op.drop_index(op.f("ix_gov_owner_preference_run_id"), table_name="gov_owner_preference")
    op.drop_index(op.f("ix_gov_owner_preference_trace_id"), table_name="gov_owner_preference")
    op.drop_index(op.f("ix_gov_owner_preference_status"), table_name="gov_owner_preference")
    op.drop_index(op.f("ix_gov_owner_preference_scope"), table_name="gov_owner_preference")
    op.drop_table("gov_owner_preference")
