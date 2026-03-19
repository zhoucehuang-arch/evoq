"""stage5 codex fabric

Revision ID: 20260318_0003
Revises: 20260318_0002
Create Date: 2026-03-18 23:30:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "20260318_0003"
down_revision = "20260318_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "exec_codex_run",
        sa.Column("goal_id", sa.String(length=36), nullable=True),
        sa.Column("task_id", sa.String(length=36), nullable=True),
        sa.Column("workflow_run_id", sa.String(length=36), nullable=True),
        sa.Column("worker_class", sa.String(length=80), nullable=False),
        sa.Column("execution_mode", sa.String(length=40), nullable=False),
        sa.Column("strategy_mode", sa.String(length=40), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("context_summary", sa.Text(), nullable=False),
        sa.Column("repo_path", sa.String(length=500), nullable=False),
        sa.Column("workspace_path", sa.String(length=500), nullable=False),
        sa.Column("write_scope", sa.JSON(), nullable=False),
        sa.Column("allowed_tools", sa.JSON(), nullable=False),
        sa.Column("search_enabled", sa.Boolean(), nullable=False),
        sa.Column("risk_tier", sa.String(length=20), nullable=False),
        sa.Column("max_duration_sec", sa.Integer(), nullable=False),
        sa.Column("max_token_budget", sa.Integer(), nullable=False),
        sa.Column("max_iterations", sa.Integer(), nullable=False),
        sa.Column("review_required", sa.Boolean(), nullable=False),
        sa.Column("eval_required", sa.Boolean(), nullable=False),
        sa.Column("ralph_state_path", sa.String(length=500), nullable=True),
        sa.Column("output_schema_path", sa.String(length=500), nullable=True),
        sa.Column("request_payload", sa.JSON(), nullable=False),
        sa.Column("result_payload", sa.JSON(), nullable=False),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("current_attempt", sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(["goal_id"], ["gov_goal.id"]),
        sa.ForeignKeyConstraint(["task_id"], ["wf_task.id"]),
        sa.ForeignKeyConstraint(["workflow_run_id"], ["wf_workflow_run.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_exec_codex_run_goal_id"), "exec_codex_run", ["goal_id"], unique=False)
    op.create_index(op.f("ix_exec_codex_run_task_id"), "exec_codex_run", ["task_id"], unique=False)
    op.create_index(op.f("ix_exec_codex_run_workflow_run_id"), "exec_codex_run", ["workflow_run_id"], unique=False)
    op.create_index(op.f("ix_exec_codex_run_worker_class"), "exec_codex_run", ["worker_class"], unique=False)
    op.create_index(op.f("ix_exec_codex_run_execution_mode"), "exec_codex_run", ["execution_mode"], unique=False)
    op.create_index(op.f("ix_exec_codex_run_strategy_mode"), "exec_codex_run", ["strategy_mode"], unique=False)
    op.create_index(op.f("ix_exec_codex_run_queued_at"), "exec_codex_run", ["queued_at"], unique=False)
    op.create_index(op.f("ix_exec_codex_run_status"), "exec_codex_run", ["status"], unique=False)
    op.create_index(op.f("ix_exec_codex_run_trace_id"), "exec_codex_run", ["trace_id"], unique=False)
    op.create_index(op.f("ix_exec_codex_run_run_id"), "exec_codex_run", ["run_id"], unique=False)

    op.create_table(
        "exec_codex_attempt",
        sa.Column("codex_run_id", sa.String(length=36), nullable=False),
        sa.Column("attempt_no", sa.Integer(), nullable=False),
        sa.Column("phase", sa.String(length=40), nullable=False),
        sa.Column("prompt_path", sa.String(length=500), nullable=True),
        sa.Column("output_path", sa.String(length=500), nullable=True),
        sa.Column("handoff_path", sa.String(length=500), nullable=True),
        sa.Column("command_json", sa.JSON(), nullable=False),
        sa.Column("env_snapshot", sa.JSON(), nullable=False),
        sa.Column("result_payload", sa.JSON(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("exit_code", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_exec_codex_attempt_codex_run_id"), "exec_codex_attempt", ["codex_run_id"], unique=False)
    op.create_index(op.f("ix_exec_codex_attempt_phase"), "exec_codex_attempt", ["phase"], unique=False)
    op.create_index(op.f("ix_exec_codex_attempt_status"), "exec_codex_attempt", ["status"], unique=False)
    op.create_index(op.f("ix_exec_codex_attempt_trace_id"), "exec_codex_attempt", ["trace_id"], unique=False)
    op.create_index(op.f("ix_exec_codex_attempt_run_id"), "exec_codex_attempt", ["run_id"], unique=False)

    op.create_table(
        "exec_codex_artifact",
        sa.Column("codex_run_id", sa.String(length=36), nullable=False),
        sa.Column("codex_attempt_id", sa.String(length=36), nullable=True),
        sa.Column("artifact_type", sa.String(length=80), nullable=False),
        sa.Column("label", sa.String(length=200), nullable=False),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=True),
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
        sa.ForeignKeyConstraint(["codex_attempt_id"], ["exec_codex_attempt.id"]),
        sa.ForeignKeyConstraint(["codex_run_id"], ["exec_codex_run.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_exec_codex_artifact_codex_run_id"), "exec_codex_artifact", ["codex_run_id"], unique=False)
    op.create_index(op.f("ix_exec_codex_artifact_codex_attempt_id"), "exec_codex_artifact", ["codex_attempt_id"], unique=False)
    op.create_index(op.f("ix_exec_codex_artifact_artifact_type"), "exec_codex_artifact", ["artifact_type"], unique=False)
    op.create_index(op.f("ix_exec_codex_artifact_status"), "exec_codex_artifact", ["status"], unique=False)
    op.create_index(op.f("ix_exec_codex_artifact_trace_id"), "exec_codex_artifact", ["trace_id"], unique=False)
    op.create_index(op.f("ix_exec_codex_artifact_run_id"), "exec_codex_artifact", ["run_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_exec_codex_artifact_run_id"), table_name="exec_codex_artifact")
    op.drop_index(op.f("ix_exec_codex_artifact_trace_id"), table_name="exec_codex_artifact")
    op.drop_index(op.f("ix_exec_codex_artifact_status"), table_name="exec_codex_artifact")
    op.drop_index(op.f("ix_exec_codex_artifact_artifact_type"), table_name="exec_codex_artifact")
    op.drop_index(op.f("ix_exec_codex_artifact_codex_attempt_id"), table_name="exec_codex_artifact")
    op.drop_index(op.f("ix_exec_codex_artifact_codex_run_id"), table_name="exec_codex_artifact")
    op.drop_table("exec_codex_artifact")

    op.drop_index(op.f("ix_exec_codex_attempt_run_id"), table_name="exec_codex_attempt")
    op.drop_index(op.f("ix_exec_codex_attempt_trace_id"), table_name="exec_codex_attempt")
    op.drop_index(op.f("ix_exec_codex_attempt_status"), table_name="exec_codex_attempt")
    op.drop_index(op.f("ix_exec_codex_attempt_phase"), table_name="exec_codex_attempt")
    op.drop_index(op.f("ix_exec_codex_attempt_codex_run_id"), table_name="exec_codex_attempt")
    op.drop_table("exec_codex_attempt")

    op.drop_index(op.f("ix_exec_codex_run_run_id"), table_name="exec_codex_run")
    op.drop_index(op.f("ix_exec_codex_run_trace_id"), table_name="exec_codex_run")
    op.drop_index(op.f("ix_exec_codex_run_status"), table_name="exec_codex_run")
    op.drop_index(op.f("ix_exec_codex_run_queued_at"), table_name="exec_codex_run")
    op.drop_index(op.f("ix_exec_codex_run_strategy_mode"), table_name="exec_codex_run")
    op.drop_index(op.f("ix_exec_codex_run_execution_mode"), table_name="exec_codex_run")
    op.drop_index(op.f("ix_exec_codex_run_worker_class"), table_name="exec_codex_run")
    op.drop_index(op.f("ix_exec_codex_run_workflow_run_id"), table_name="exec_codex_run")
    op.drop_index(op.f("ix_exec_codex_run_task_id"), table_name="exec_codex_run")
    op.drop_index(op.f("ix_exec_codex_run_goal_id"), table_name="exec_codex_run")
    op.drop_table("exec_codex_run")
