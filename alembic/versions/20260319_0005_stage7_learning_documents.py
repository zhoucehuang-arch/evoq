"""stage7 learning documents

Revision ID: 20260319_0005
Revises: 20260318_0004
Create Date: 2026-03-19 00:20:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "20260319_0005"
down_revision = "20260318_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mem_document",
        sa.Column("codex_run_id", sa.String(length=36), nullable=True),
        sa.Column("workflow_run_id", sa.String(length=36), nullable=True),
        sa.Column("supervisor_loop_key", sa.String(length=120), nullable=True),
        sa.Column("source_key", sa.String(length=120), nullable=False),
        sa.Column("source_type", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("storage_path", sa.String(length=500), nullable=True),
        sa.Column("citations_json", sa.JSON(), nullable=False),
        sa.Column("followup_tasks", sa.JSON(), nullable=False),
        sa.Column("risks_found", sa.JSON(), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
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
        sa.ForeignKeyConstraint(["workflow_run_id"], ["wf_workflow_run.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("codex_run_id"),
    )
    op.create_index(op.f("ix_mem_document_codex_run_id"), "mem_document", ["codex_run_id"], unique=False)
    op.create_index(op.f("ix_mem_document_workflow_run_id"), "mem_document", ["workflow_run_id"], unique=False)
    op.create_index(op.f("ix_mem_document_supervisor_loop_key"), "mem_document", ["supervisor_loop_key"], unique=False)
    op.create_index(op.f("ix_mem_document_source_key"), "mem_document", ["source_key"], unique=False)
    op.create_index(op.f("ix_mem_document_source_type"), "mem_document", ["source_type"], unique=False)
    op.create_index(op.f("ix_mem_document_ingested_at"), "mem_document", ["ingested_at"], unique=False)
    op.create_index(op.f("ix_mem_document_status"), "mem_document", ["status"], unique=False)
    op.create_index(op.f("ix_mem_document_trace_id"), "mem_document", ["trace_id"], unique=False)
    op.create_index(op.f("ix_mem_document_run_id"), "mem_document", ["run_id"], unique=False)

    op.create_table(
        "mem_evidence_item",
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("codex_run_id", sa.String(length=36), nullable=True),
        sa.Column("evidence_type", sa.String(length=80), nullable=False),
        sa.Column("claim_text", sa.Text(), nullable=False),
        sa.Column("citation_ref", sa.String(length=500), nullable=True),
        sa.Column("topic", sa.String(length=120), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_mem_evidence_item_document_id"), "mem_evidence_item", ["document_id"], unique=False)
    op.create_index(op.f("ix_mem_evidence_item_codex_run_id"), "mem_evidence_item", ["codex_run_id"], unique=False)
    op.create_index(op.f("ix_mem_evidence_item_evidence_type"), "mem_evidence_item", ["evidence_type"], unique=False)
    op.create_index(op.f("ix_mem_evidence_item_topic"), "mem_evidence_item", ["topic"], unique=False)
    op.create_index(op.f("ix_mem_evidence_item_recorded_at"), "mem_evidence_item", ["recorded_at"], unique=False)
    op.create_index(op.f("ix_mem_evidence_item_status"), "mem_evidence_item", ["status"], unique=False)
    op.create_index(op.f("ix_mem_evidence_item_trace_id"), "mem_evidence_item", ["trace_id"], unique=False)
    op.create_index(op.f("ix_mem_evidence_item_run_id"), "mem_evidence_item", ["run_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_mem_evidence_item_run_id"), table_name="mem_evidence_item")
    op.drop_index(op.f("ix_mem_evidence_item_trace_id"), table_name="mem_evidence_item")
    op.drop_index(op.f("ix_mem_evidence_item_status"), table_name="mem_evidence_item")
    op.drop_index(op.f("ix_mem_evidence_item_recorded_at"), table_name="mem_evidence_item")
    op.drop_index(op.f("ix_mem_evidence_item_topic"), table_name="mem_evidence_item")
    op.drop_index(op.f("ix_mem_evidence_item_evidence_type"), table_name="mem_evidence_item")
    op.drop_index(op.f("ix_mem_evidence_item_codex_run_id"), table_name="mem_evidence_item")
    op.drop_index(op.f("ix_mem_evidence_item_document_id"), table_name="mem_evidence_item")
    op.drop_table("mem_evidence_item")

    op.drop_index(op.f("ix_mem_document_run_id"), table_name="mem_document")
    op.drop_index(op.f("ix_mem_document_trace_id"), table_name="mem_document")
    op.drop_index(op.f("ix_mem_document_status"), table_name="mem_document")
    op.drop_index(op.f("ix_mem_document_ingested_at"), table_name="mem_document")
    op.drop_index(op.f("ix_mem_document_source_type"), table_name="mem_document")
    op.drop_index(op.f("ix_mem_document_source_key"), table_name="mem_document")
    op.drop_index(op.f("ix_mem_document_supervisor_loop_key"), table_name="mem_document")
    op.drop_index(op.f("ix_mem_document_workflow_run_id"), table_name="mem_document")
    op.drop_index(op.f("ix_mem_document_codex_run_id"), table_name="mem_document")
    op.drop_table("mem_document")
