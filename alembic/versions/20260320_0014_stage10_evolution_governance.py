"""stage10 evolution governance

Revision ID: 20260320_0014
Revises: 20260320_0013
Create Date: 2026-03-20 12:30:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "20260320_0014"
down_revision = "20260320_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "evo_improvement_proposal",
        sa.Column("goal_id", sa.String(length=36), nullable=True),
        sa.Column("workflow_run_id", sa.String(length=36), nullable=True),
        sa.Column("codex_run_id", sa.String(length=36), nullable=True),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("target_surface", sa.String(length=80), nullable=False),
        sa.Column("proposal_kind", sa.String(length=80), nullable=False),
        sa.Column("change_scope", sa.JSON(), nullable=False),
        sa.Column("expected_benefit", sa.JSON(), nullable=False),
        sa.Column("evaluation_summary", sa.JSON(), nullable=False),
        sa.Column("risk_summary", sa.Text(), nullable=True),
        sa.Column("canary_plan", sa.JSON(), nullable=False),
        sa.Column("rollback_plan", sa.JSON(), nullable=False),
        sa.Column("objective_drift_checks", sa.JSON(), nullable=False),
        sa.Column("proposal_state", sa.String(length=80), nullable=False),
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
        sa.ForeignKeyConstraint(["goal_id"], ["gov_goal.id"]),
        sa.ForeignKeyConstraint(["workflow_run_id"], ["wf_workflow_run.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_evo_improvement_proposal_goal_id"),
        "evo_improvement_proposal",
        ["goal_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_evo_improvement_proposal_workflow_run_id"),
        "evo_improvement_proposal",
        ["workflow_run_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_evo_improvement_proposal_codex_run_id"),
        "evo_improvement_proposal",
        ["codex_run_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_evo_improvement_proposal_target_surface"),
        "evo_improvement_proposal",
        ["target_surface"],
        unique=False,
    )
    op.create_index(
        op.f("ix_evo_improvement_proposal_proposal_kind"),
        "evo_improvement_proposal",
        ["proposal_kind"],
        unique=False,
    )
    op.create_index(
        op.f("ix_evo_improvement_proposal_proposal_state"),
        "evo_improvement_proposal",
        ["proposal_state"],
        unique=False,
    )
    op.create_index(op.f("ix_evo_improvement_proposal_status"), "evo_improvement_proposal", ["status"], unique=False)
    op.create_index(
        op.f("ix_evo_improvement_proposal_trace_id"),
        "evo_improvement_proposal",
        ["trace_id"],
        unique=False,
    )
    op.create_index(op.f("ix_evo_improvement_proposal_run_id"), "evo_improvement_proposal", ["run_id"], unique=False)

    op.create_table(
        "evo_canary_run",
        sa.Column("proposal_id", sa.String(length=36), nullable=False),
        sa.Column("lane_type", sa.String(length=40), nullable=False),
        sa.Column("environment", sa.String(length=40), nullable=False),
        sa.Column("traffic_pct", sa.Float(), nullable=False),
        sa.Column("success_metrics", sa.JSON(), nullable=False),
        sa.Column("objective_drift_score", sa.Float(), nullable=True),
        sa.Column("objective_drift_summary", sa.Text(), nullable=True),
        sa.Column("rollback_ready", sa.Boolean(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["proposal_id"], ["evo_improvement_proposal.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_evo_canary_run_proposal_id"), "evo_canary_run", ["proposal_id"], unique=False)
    op.create_index(op.f("ix_evo_canary_run_lane_type"), "evo_canary_run", ["lane_type"], unique=False)
    op.create_index(op.f("ix_evo_canary_run_environment"), "evo_canary_run", ["environment"], unique=False)
    op.create_index(op.f("ix_evo_canary_run_status"), "evo_canary_run", ["status"], unique=False)
    op.create_index(op.f("ix_evo_canary_run_trace_id"), "evo_canary_run", ["trace_id"], unique=False)
    op.create_index(op.f("ix_evo_canary_run_run_id"), "evo_canary_run", ["run_id"], unique=False)

    op.create_table(
        "evo_promotion_decision",
        sa.Column("proposal_id", sa.String(length=36), nullable=False),
        sa.Column("decision", sa.String(length=40), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("decided_by", sa.String(length=120), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decision_payload", sa.JSON(), nullable=False),
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
        sa.ForeignKeyConstraint(["proposal_id"], ["evo_improvement_proposal.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_evo_promotion_decision_proposal_id"),
        "evo_promotion_decision",
        ["proposal_id"],
        unique=False,
    )
    op.create_index(op.f("ix_evo_promotion_decision_decision"), "evo_promotion_decision", ["decision"], unique=False)
    op.create_index(
        op.f("ix_evo_promotion_decision_decided_at"),
        "evo_promotion_decision",
        ["decided_at"],
        unique=False,
    )
    op.create_index(op.f("ix_evo_promotion_decision_status"), "evo_promotion_decision", ["status"], unique=False)
    op.create_index(
        op.f("ix_evo_promotion_decision_trace_id"),
        "evo_promotion_decision",
        ["trace_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_evo_promotion_decision_run_id"),
        "evo_promotion_decision",
        ["run_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_evo_promotion_decision_run_id"), table_name="evo_promotion_decision")
    op.drop_index(op.f("ix_evo_promotion_decision_trace_id"), table_name="evo_promotion_decision")
    op.drop_index(op.f("ix_evo_promotion_decision_status"), table_name="evo_promotion_decision")
    op.drop_index(op.f("ix_evo_promotion_decision_decided_at"), table_name="evo_promotion_decision")
    op.drop_index(op.f("ix_evo_promotion_decision_decision"), table_name="evo_promotion_decision")
    op.drop_index(op.f("ix_evo_promotion_decision_proposal_id"), table_name="evo_promotion_decision")
    op.drop_table("evo_promotion_decision")

    op.drop_index(op.f("ix_evo_canary_run_run_id"), table_name="evo_canary_run")
    op.drop_index(op.f("ix_evo_canary_run_trace_id"), table_name="evo_canary_run")
    op.drop_index(op.f("ix_evo_canary_run_status"), table_name="evo_canary_run")
    op.drop_index(op.f("ix_evo_canary_run_environment"), table_name="evo_canary_run")
    op.drop_index(op.f("ix_evo_canary_run_lane_type"), table_name="evo_canary_run")
    op.drop_index(op.f("ix_evo_canary_run_proposal_id"), table_name="evo_canary_run")
    op.drop_table("evo_canary_run")

    op.drop_index(op.f("ix_evo_improvement_proposal_run_id"), table_name="evo_improvement_proposal")
    op.drop_index(op.f("ix_evo_improvement_proposal_trace_id"), table_name="evo_improvement_proposal")
    op.drop_index(op.f("ix_evo_improvement_proposal_status"), table_name="evo_improvement_proposal")
    op.drop_index(
        op.f("ix_evo_improvement_proposal_proposal_state"),
        table_name="evo_improvement_proposal",
    )
    op.drop_index(
        op.f("ix_evo_improvement_proposal_proposal_kind"),
        table_name="evo_improvement_proposal",
    )
    op.drop_index(
        op.f("ix_evo_improvement_proposal_target_surface"),
        table_name="evo_improvement_proposal",
    )
    op.drop_index(op.f("ix_evo_improvement_proposal_codex_run_id"), table_name="evo_improvement_proposal")
    op.drop_index(
        op.f("ix_evo_improvement_proposal_workflow_run_id"),
        table_name="evo_improvement_proposal",
    )
    op.drop_index(op.f("ix_evo_improvement_proposal_goal_id"), table_name="evo_improvement_proposal")
    op.drop_table("evo_improvement_proposal")
