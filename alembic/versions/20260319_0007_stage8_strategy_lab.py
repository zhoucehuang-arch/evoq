"""stage8 strategy lab

Revision ID: 20260319_0007
Revises: 20260319_0006
Create Date: 2026-03-19 02:20:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "20260319_0007"
down_revision = "20260319_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "strat_hypothesis",
        sa.Column("source_insight_id", sa.String(length=36), nullable=True),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("thesis", sa.Text(), nullable=False),
        sa.Column("target_market", sa.String(length=120), nullable=False),
        sa.Column("mechanism", sa.Text(), nullable=False),
        sa.Column("risk_hypothesis", sa.Text(), nullable=True),
        sa.Column("evaluation_plan", sa.JSON(), nullable=False),
        sa.Column("invalidation_conditions", sa.JSON(), nullable=False),
        sa.Column("current_stage", sa.String(length=80), nullable=False),
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
        sa.ForeignKeyConstraint(["source_insight_id"], ["mem_insight.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_strat_hypothesis_source_insight_id"), "strat_hypothesis", ["source_insight_id"], unique=False)
    op.create_index(op.f("ix_strat_hypothesis_target_market"), "strat_hypothesis", ["target_market"], unique=False)
    op.create_index(op.f("ix_strat_hypothesis_current_stage"), "strat_hypothesis", ["current_stage"], unique=False)
    op.create_index(op.f("ix_strat_hypothesis_status"), "strat_hypothesis", ["status"], unique=False)
    op.create_index(op.f("ix_strat_hypothesis_trace_id"), "strat_hypothesis", ["trace_id"], unique=False)
    op.create_index(op.f("ix_strat_hypothesis_run_id"), "strat_hypothesis", ["run_id"], unique=False)

    op.create_table(
        "strat_strategy_spec",
        sa.Column("hypothesis_id", sa.String(length=36), nullable=False),
        sa.Column("spec_code", sa.String(length=120), nullable=False),
        sa.Column("version_label", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("target_market", sa.String(length=120), nullable=False),
        sa.Column("signal_logic", sa.Text(), nullable=False),
        sa.Column("risk_rules", sa.JSON(), nullable=False),
        sa.Column("data_requirements", sa.JSON(), nullable=False),
        sa.Column("invalidation_conditions", sa.JSON(), nullable=False),
        sa.Column("execution_constraints", sa.JSON(), nullable=False),
        sa.Column("current_stage", sa.String(length=80), nullable=False),
        sa.Column("latest_backtest_gate", sa.String(length=80), nullable=True),
        sa.Column("latest_paper_gate", sa.String(length=80), nullable=True),
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
        sa.ForeignKeyConstraint(["hypothesis_id"], ["strat_hypothesis.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("spec_code"),
    )
    op.create_index(op.f("ix_strat_strategy_spec_hypothesis_id"), "strat_strategy_spec", ["hypothesis_id"], unique=False)
    op.create_index(op.f("ix_strat_strategy_spec_target_market"), "strat_strategy_spec", ["target_market"], unique=False)
    op.create_index(op.f("ix_strat_strategy_spec_current_stage"), "strat_strategy_spec", ["current_stage"], unique=False)
    op.create_index(op.f("ix_strat_strategy_spec_latest_backtest_gate"), "strat_strategy_spec", ["latest_backtest_gate"], unique=False)
    op.create_index(op.f("ix_strat_strategy_spec_latest_paper_gate"), "strat_strategy_spec", ["latest_paper_gate"], unique=False)
    op.create_index(op.f("ix_strat_strategy_spec_status"), "strat_strategy_spec", ["status"], unique=False)
    op.create_index(op.f("ix_strat_strategy_spec_trace_id"), "strat_strategy_spec", ["trace_id"], unique=False)
    op.create_index(op.f("ix_strat_strategy_spec_run_id"), "strat_strategy_spec", ["run_id"], unique=False)

    op.create_table(
        "strat_backtest_run",
        sa.Column("strategy_spec_id", sa.String(length=36), nullable=False),
        sa.Column("dataset_range", sa.String(length=240), nullable=True),
        sa.Column("sample_size", sa.Integer(), nullable=False),
        sa.Column("metrics_json", sa.JSON(), nullable=False),
        sa.Column("artifact_path", sa.String(length=500), nullable=True),
        sa.Column("gate_result", sa.String(length=80), nullable=False),
        sa.Column("gate_notes", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
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
        sa.ForeignKeyConstraint(["strategy_spec_id"], ["strat_strategy_spec.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_strat_backtest_run_strategy_spec_id"), "strat_backtest_run", ["strategy_spec_id"], unique=False)
    op.create_index(op.f("ix_strat_backtest_run_gate_result"), "strat_backtest_run", ["gate_result"], unique=False)
    op.create_index(op.f("ix_strat_backtest_run_status"), "strat_backtest_run", ["status"], unique=False)
    op.create_index(op.f("ix_strat_backtest_run_trace_id"), "strat_backtest_run", ["trace_id"], unique=False)
    op.create_index(op.f("ix_strat_backtest_run_run_id"), "strat_backtest_run", ["run_id"], unique=False)

    op.create_table(
        "strat_paper_run",
        sa.Column("strategy_spec_id", sa.String(length=36), nullable=False),
        sa.Column("deployment_label", sa.String(length=120), nullable=False),
        sa.Column("monitoring_days", sa.Integer(), nullable=False),
        sa.Column("metrics_json", sa.JSON(), nullable=False),
        sa.Column("capital_allocated", sa.Float(), nullable=True),
        sa.Column("gate_result", sa.String(length=80), nullable=False),
        sa.Column("gate_notes", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
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
        sa.ForeignKeyConstraint(["strategy_spec_id"], ["strat_strategy_spec.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_strat_paper_run_strategy_spec_id"), "strat_paper_run", ["strategy_spec_id"], unique=False)
    op.create_index(op.f("ix_strat_paper_run_gate_result"), "strat_paper_run", ["gate_result"], unique=False)
    op.create_index(op.f("ix_strat_paper_run_status"), "strat_paper_run", ["status"], unique=False)
    op.create_index(op.f("ix_strat_paper_run_trace_id"), "strat_paper_run", ["trace_id"], unique=False)
    op.create_index(op.f("ix_strat_paper_run_run_id"), "strat_paper_run", ["run_id"], unique=False)

    op.create_table(
        "strat_promotion_decision",
        sa.Column("strategy_spec_id", sa.String(length=36), nullable=False),
        sa.Column("paper_run_id", sa.String(length=36), nullable=True),
        sa.Column("target_stage", sa.String(length=80), nullable=False),
        sa.Column("decision", sa.String(length=80), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("evidence_refs", sa.JSON(), nullable=False),
        sa.Column("decided_by", sa.String(length=120), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
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
        sa.ForeignKeyConstraint(["paper_run_id"], ["strat_paper_run.id"]),
        sa.ForeignKeyConstraint(["strategy_spec_id"], ["strat_strategy_spec.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_strat_promotion_decision_strategy_spec_id"), "strat_promotion_decision", ["strategy_spec_id"], unique=False)
    op.create_index(op.f("ix_strat_promotion_decision_paper_run_id"), "strat_promotion_decision", ["paper_run_id"], unique=False)
    op.create_index(op.f("ix_strat_promotion_decision_target_stage"), "strat_promotion_decision", ["target_stage"], unique=False)
    op.create_index(op.f("ix_strat_promotion_decision_decision"), "strat_promotion_decision", ["decision"], unique=False)
    op.create_index(op.f("ix_strat_promotion_decision_status"), "strat_promotion_decision", ["status"], unique=False)
    op.create_index(op.f("ix_strat_promotion_decision_trace_id"), "strat_promotion_decision", ["trace_id"], unique=False)
    op.create_index(op.f("ix_strat_promotion_decision_run_id"), "strat_promotion_decision", ["run_id"], unique=False)

    op.create_table(
        "strat_withdrawal_decision",
        sa.Column("strategy_spec_id", sa.String(length=36), nullable=False),
        sa.Column("replacement_strategy_spec_id", sa.String(length=36), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("evidence_refs", sa.JSON(), nullable=False),
        sa.Column("decided_by", sa.String(length=120), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
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
        sa.ForeignKeyConstraint(["replacement_strategy_spec_id"], ["strat_strategy_spec.id"]),
        sa.ForeignKeyConstraint(["strategy_spec_id"], ["strat_strategy_spec.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_strat_withdrawal_decision_strategy_spec_id"), "strat_withdrawal_decision", ["strategy_spec_id"], unique=False)
    op.create_index(op.f("ix_strat_withdrawal_decision_replacement_strategy_spec_id"), "strat_withdrawal_decision", ["replacement_strategy_spec_id"], unique=False)
    op.create_index(op.f("ix_strat_withdrawal_decision_status"), "strat_withdrawal_decision", ["status"], unique=False)
    op.create_index(op.f("ix_strat_withdrawal_decision_trace_id"), "strat_withdrawal_decision", ["trace_id"], unique=False)
    op.create_index(op.f("ix_strat_withdrawal_decision_run_id"), "strat_withdrawal_decision", ["run_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_strat_withdrawal_decision_run_id"), table_name="strat_withdrawal_decision")
    op.drop_index(op.f("ix_strat_withdrawal_decision_trace_id"), table_name="strat_withdrawal_decision")
    op.drop_index(op.f("ix_strat_withdrawal_decision_status"), table_name="strat_withdrawal_decision")
    op.drop_index(op.f("ix_strat_withdrawal_decision_replacement_strategy_spec_id"), table_name="strat_withdrawal_decision")
    op.drop_index(op.f("ix_strat_withdrawal_decision_strategy_spec_id"), table_name="strat_withdrawal_decision")
    op.drop_table("strat_withdrawal_decision")

    op.drop_index(op.f("ix_strat_promotion_decision_run_id"), table_name="strat_promotion_decision")
    op.drop_index(op.f("ix_strat_promotion_decision_trace_id"), table_name="strat_promotion_decision")
    op.drop_index(op.f("ix_strat_promotion_decision_status"), table_name="strat_promotion_decision")
    op.drop_index(op.f("ix_strat_promotion_decision_decision"), table_name="strat_promotion_decision")
    op.drop_index(op.f("ix_strat_promotion_decision_target_stage"), table_name="strat_promotion_decision")
    op.drop_index(op.f("ix_strat_promotion_decision_paper_run_id"), table_name="strat_promotion_decision")
    op.drop_index(op.f("ix_strat_promotion_decision_strategy_spec_id"), table_name="strat_promotion_decision")
    op.drop_table("strat_promotion_decision")

    op.drop_index(op.f("ix_strat_paper_run_run_id"), table_name="strat_paper_run")
    op.drop_index(op.f("ix_strat_paper_run_trace_id"), table_name="strat_paper_run")
    op.drop_index(op.f("ix_strat_paper_run_status"), table_name="strat_paper_run")
    op.drop_index(op.f("ix_strat_paper_run_gate_result"), table_name="strat_paper_run")
    op.drop_index(op.f("ix_strat_paper_run_strategy_spec_id"), table_name="strat_paper_run")
    op.drop_table("strat_paper_run")

    op.drop_index(op.f("ix_strat_backtest_run_run_id"), table_name="strat_backtest_run")
    op.drop_index(op.f("ix_strat_backtest_run_trace_id"), table_name="strat_backtest_run")
    op.drop_index(op.f("ix_strat_backtest_run_status"), table_name="strat_backtest_run")
    op.drop_index(op.f("ix_strat_backtest_run_gate_result"), table_name="strat_backtest_run")
    op.drop_index(op.f("ix_strat_backtest_run_strategy_spec_id"), table_name="strat_backtest_run")
    op.drop_table("strat_backtest_run")

    op.drop_index(op.f("ix_strat_strategy_spec_run_id"), table_name="strat_strategy_spec")
    op.drop_index(op.f("ix_strat_strategy_spec_trace_id"), table_name="strat_strategy_spec")
    op.drop_index(op.f("ix_strat_strategy_spec_status"), table_name="strat_strategy_spec")
    op.drop_index(op.f("ix_strat_strategy_spec_latest_paper_gate"), table_name="strat_strategy_spec")
    op.drop_index(op.f("ix_strat_strategy_spec_latest_backtest_gate"), table_name="strat_strategy_spec")
    op.drop_index(op.f("ix_strat_strategy_spec_current_stage"), table_name="strat_strategy_spec")
    op.drop_index(op.f("ix_strat_strategy_spec_target_market"), table_name="strat_strategy_spec")
    op.drop_index(op.f("ix_strat_strategy_spec_hypothesis_id"), table_name="strat_strategy_spec")
    op.drop_table("strat_strategy_spec")

    op.drop_index(op.f("ix_strat_hypothesis_run_id"), table_name="strat_hypothesis")
    op.drop_index(op.f("ix_strat_hypothesis_trace_id"), table_name="strat_hypothesis")
    op.drop_index(op.f("ix_strat_hypothesis_status"), table_name="strat_hypothesis")
    op.drop_index(op.f("ix_strat_hypothesis_current_stage"), table_name="strat_hypothesis")
    op.drop_index(op.f("ix_strat_hypothesis_target_market"), table_name="strat_hypothesis")
    op.drop_index(op.f("ix_strat_hypothesis_source_insight_id"), table_name="strat_hypothesis")
    op.drop_table("strat_hypothesis")
