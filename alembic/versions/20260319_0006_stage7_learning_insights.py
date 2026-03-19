"""stage7 learning insights

Revision ID: 20260319_0006
Revises: 20260319_0005
Create Date: 2026-03-19 01:10:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "20260319_0006"
down_revision = "20260319_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mem_insight",
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("codex_run_id", sa.String(length=36), nullable=True),
        sa.Column("workflow_run_id", sa.String(length=36), nullable=True),
        sa.Column("supervisor_loop_key", sa.String(length=120), nullable=True),
        sa.Column("topic_key", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("supporting_evidence_refs", sa.JSON(), nullable=False),
        sa.Column("citation_refs", sa.JSON(), nullable=False),
        sa.Column("challenge_notes", sa.JSON(), nullable=False),
        sa.Column("followup_tasks", sa.JSON(), nullable=False),
        sa.Column("promotion_state", sa.String(length=80), nullable=False),
        sa.Column("quarantine_reason", sa.Text(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_validated_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["codex_run_id"], ["exec_codex_run.id"]),
        sa.ForeignKeyConstraint(["document_id"], ["mem_document.id"]),
        sa.ForeignKeyConstraint(["workflow_run_id"], ["wf_workflow_run.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id"),
    )
    op.create_index(op.f("ix_mem_insight_document_id"), "mem_insight", ["document_id"], unique=False)
    op.create_index(op.f("ix_mem_insight_codex_run_id"), "mem_insight", ["codex_run_id"], unique=False)
    op.create_index(op.f("ix_mem_insight_workflow_run_id"), "mem_insight", ["workflow_run_id"], unique=False)
    op.create_index(op.f("ix_mem_insight_supervisor_loop_key"), "mem_insight", ["supervisor_loop_key"], unique=False)
    op.create_index(op.f("ix_mem_insight_topic_key"), "mem_insight", ["topic_key"], unique=False)
    op.create_index(op.f("ix_mem_insight_promotion_state"), "mem_insight", ["promotion_state"], unique=False)
    op.create_index(op.f("ix_mem_insight_recorded_at"), "mem_insight", ["recorded_at"], unique=False)
    op.create_index(op.f("ix_mem_insight_status"), "mem_insight", ["status"], unique=False)
    op.create_index(op.f("ix_mem_insight_trace_id"), "mem_insight", ["trace_id"], unique=False)
    op.create_index(op.f("ix_mem_insight_run_id"), "mem_insight", ["run_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_mem_insight_run_id"), table_name="mem_insight")
    op.drop_index(op.f("ix_mem_insight_trace_id"), table_name="mem_insight")
    op.drop_index(op.f("ix_mem_insight_status"), table_name="mem_insight")
    op.drop_index(op.f("ix_mem_insight_recorded_at"), table_name="mem_insight")
    op.drop_index(op.f("ix_mem_insight_promotion_state"), table_name="mem_insight")
    op.drop_index(op.f("ix_mem_insight_topic_key"), table_name="mem_insight")
    op.drop_index(op.f("ix_mem_insight_supervisor_loop_key"), table_name="mem_insight")
    op.drop_index(op.f("ix_mem_insight_workflow_run_id"), table_name="mem_insight")
    op.drop_index(op.f("ix_mem_insight_codex_run_id"), table_name="mem_insight")
    op.drop_index(op.f("ix_mem_insight_document_id"), table_name="mem_insight")
    op.drop_table("mem_insight")
