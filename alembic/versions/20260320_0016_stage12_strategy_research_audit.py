"""stage12 strategy research audit

Revision ID: 20260320_0016
Revises: 20260320_0015
Create Date: 2026-03-20 13:45:00
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260320_0016"
down_revision = "20260320_0015"
branch_labels = None
depends_on = None


def _lineage_columns() -> list[sa.Column]:
    return [
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
    ]


def upgrade() -> None:
    op.create_table(
        "strat_research_brief",
        sa.Column("source_insight_id", sa.String(length=36), nullable=True),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("thesis", sa.Text(), nullable=False),
        sa.Column("opportunity_kind", sa.String(length=80), nullable=False),
        sa.Column("target_market", sa.String(length=120), nullable=False),
        sa.Column("signal_definition", sa.Text(), nullable=False),
        sa.Column("expected_mechanism", sa.Text(), nullable=False),
        sa.Column("llm_provider", sa.String(length=120), nullable=True),
        sa.Column("llm_model", sa.String(length=120), nullable=True),
        sa.Column("llm_model_cutoff", sa.String(length=120), nullable=True),
        sa.Column("prompt_hash", sa.String(length=120), nullable=True),
        sa.Column("tool_refs", sa.JSON(), nullable=False),
        sa.Column("evidence_refs", sa.JSON(), nullable=False),
        sa.Column("data_requirements", sa.JSON(), nullable=False),
        sa.Column("point_in_time_controls", sa.JSON(), nullable=False),
        sa.Column("evaluation_plan", sa.JSON(), nullable=False),
        sa.Column("cost_model_requirements", sa.JSON(), nullable=False),
        sa.Column("baseline_refs", sa.JSON(), nullable=False),
        sa.Column("invalidation_conditions", sa.JSON(), nullable=False),
        sa.Column("risk_controls_required", sa.JSON(), nullable=False),
        sa.Column("attack_tests_required", sa.JSON(), nullable=False),
        sa.Column("audit_status", sa.String(length=80), nullable=False),
        sa.Column("audit_notes", sa.JSON(), nullable=False),
        sa.Column("readiness_score", sa.Float(), nullable=False),
        sa.Column("promoted_hypothesis_id", sa.String(length=36), nullable=True),
        *_lineage_columns(),
        sa.ForeignKeyConstraint(["promoted_hypothesis_id"], ["strat_hypothesis.id"]),
        sa.ForeignKeyConstraint(["source_insight_id"], ["mem_insight.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_strat_research_brief_source_insight_id"), "strat_research_brief", ["source_insight_id"], unique=False)
    op.create_index(op.f("ix_strat_research_brief_opportunity_kind"), "strat_research_brief", ["opportunity_kind"], unique=False)
    op.create_index(op.f("ix_strat_research_brief_target_market"), "strat_research_brief", ["target_market"], unique=False)
    op.create_index(op.f("ix_strat_research_brief_audit_status"), "strat_research_brief", ["audit_status"], unique=False)
    op.create_index(op.f("ix_strat_research_brief_promoted_hypothesis_id"), "strat_research_brief", ["promoted_hypothesis_id"], unique=False)
    op.create_index(op.f("ix_strat_research_brief_status"), "strat_research_brief", ["status"], unique=False)
    op.create_index(op.f("ix_strat_research_brief_trace_id"), "strat_research_brief", ["trace_id"], unique=False)
    op.create_index(op.f("ix_strat_research_brief_run_id"), "strat_research_brief", ["run_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_strat_research_brief_run_id"), table_name="strat_research_brief")
    op.drop_index(op.f("ix_strat_research_brief_trace_id"), table_name="strat_research_brief")
    op.drop_index(op.f("ix_strat_research_brief_status"), table_name="strat_research_brief")
    op.drop_index(op.f("ix_strat_research_brief_promoted_hypothesis_id"), table_name="strat_research_brief")
    op.drop_index(op.f("ix_strat_research_brief_audit_status"), table_name="strat_research_brief")
    op.drop_index(op.f("ix_strat_research_brief_target_market"), table_name="strat_research_brief")
    op.drop_index(op.f("ix_strat_research_brief_opportunity_kind"), table_name="strat_research_brief")
    op.drop_index(op.f("ix_strat_research_brief_source_insight_id"), table_name="strat_research_brief")
    op.drop_table("strat_research_brief")
