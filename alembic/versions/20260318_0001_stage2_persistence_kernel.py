"""stage2 persistence kernel

Revision ID: 20260318_0001
Revises:
Create Date: 2026-03-18 19:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "20260318_0001"
down_revision = None
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
    ]


def _timestamp_columns() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def _create_common_indexes(table_name: str, *extra_indexes: tuple[str, list[str]]) -> None:
    for suffix, columns in extra_indexes:
        op.create_index(op.f(f"ix_{table_name}_{suffix}"), table_name, columns, unique=False)
    op.create_index(op.f(f"ix_{table_name}_status"), table_name, ["status"], unique=False)
    op.create_index(op.f(f"ix_{table_name}_trace_id"), table_name, ["trace_id"], unique=False)
    op.create_index(op.f(f"ix_{table_name}_run_id"), table_name, ["run_id"], unique=False)


def _drop_common_indexes(table_name: str, *extra_suffixes: str) -> None:
    op.drop_index(op.f(f"ix_{table_name}_run_id"), table_name=table_name)
    op.drop_index(op.f(f"ix_{table_name}_trace_id"), table_name=table_name)
    op.drop_index(op.f(f"ix_{table_name}_status"), table_name=table_name)
    for suffix in reversed(extra_suffixes):
        op.drop_index(op.f(f"ix_{table_name}_{suffix}"), table_name=table_name)


def upgrade() -> None:
    op.create_table(
        "gov_system_policy",
        sa.Column("policy_key", sa.String(length=120), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("value_json", sa.JSON(), nullable=False),
        sa.Column("is_mutable", sa.Boolean(), nullable=False),
        *_lineage_columns(),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("policy_key"),
    )
    _create_common_indexes("gov_system_policy")

    op.create_table(
        "gov_autonomy_mode",
        sa.Column("mode", sa.String(length=60), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("activated_by", sa.String(length=120), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *_lineage_columns(),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_common_indexes("gov_autonomy_mode", ("mode", ["mode"]), ("is_active", ["is_active"]))

    op.create_table(
        "gov_goal",
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("mission_domain", sa.String(length=80), nullable=False),
        sa.Column("success_metrics", sa.JSON(), nullable=False),
        sa.Column("failure_metrics", sa.JSON(), nullable=False),
        sa.Column("budget_scope", sa.JSON(), nullable=False),
        sa.Column("time_horizon", sa.String(length=120), nullable=True),
        *_lineage_columns(),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_common_indexes("gov_goal", ("mission_domain", ["mission_domain"]))

    op.create_table(
        "gov_goal_revision",
        sa.Column("goal_id", sa.String(length=36), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("revision_payload", sa.JSON(), nullable=False),
        *_lineage_columns(),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["goal_id"], ["gov_goal.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_common_indexes("gov_goal_revision", ("goal_id", ["goal_id"]))

    op.create_table(
        "gov_approval_request",
        sa.Column("approval_type", sa.String(length=80), nullable=False),
        sa.Column("subject_type", sa.String(length=80), nullable=False),
        sa.Column("subject_id", sa.String(length=120), nullable=False),
        sa.Column("requested_by", sa.String(length=120), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decision_status", sa.String(length=40), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        *_lineage_columns(),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_common_indexes(
        "gov_approval_request",
        ("subject_id", ["subject_id"]),
        ("decision_status", ["decision_status"]),
    )

    op.create_table(
        "gov_approval_decision",
        sa.Column("approval_request_id", sa.String(length=36), nullable=False),
        sa.Column("decision", sa.String(length=40), nullable=False),
        sa.Column("decided_by", sa.String(length=120), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        *_lineage_columns(),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["approval_request_id"], ["gov_approval_request.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_common_indexes("gov_approval_decision", ("approval_request_id", ["approval_request_id"]))

    op.create_table(
        "gov_operator_override",
        sa.Column("scope", sa.String(length=80), nullable=False),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("activated_by", sa.String(length=120), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *_lineage_columns(),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_common_indexes("gov_operator_override", ("scope", ["scope"]), ("is_active", ["is_active"]))

    op.create_table(
        "gov_manual_takeover_session",
        sa.Column("scope", sa.String(length=80), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("initiated_by", sa.String(length=120), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *_lineage_columns(),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_common_indexes("gov_manual_takeover_session")

    op.create_table(
        "wf_plan",
        sa.Column("goal_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        *_lineage_columns(),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["goal_id"], ["gov_goal.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_common_indexes("wf_plan", ("goal_id", ["goal_id"]))

    op.create_table(
        "wf_task",
        sa.Column("goal_id", sa.String(length=36), nullable=True),
        sa.Column("plan_id", sa.String(length=36), nullable=True),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("owner_role", sa.String(length=80), nullable=False),
        sa.Column("input_payload", sa.JSON(), nullable=False),
        sa.Column("output_payload", sa.JSON(), nullable=False),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False),
        sa.Column("retry_policy", sa.JSON(), nullable=False),
        *_lineage_columns(),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["goal_id"], ["gov_goal.id"]),
        sa.ForeignKeyConstraint(["plan_id"], ["wf_plan.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_common_indexes("wf_task", ("goal_id", ["goal_id"]), ("plan_id", ["plan_id"]))

    op.create_table(
        "wf_workflow_definition",
        sa.Column("workflow_code", sa.String(length=80), nullable=False),
        sa.Column("family", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("risk_tier", sa.String(length=20), nullable=False),
        sa.Column("approval_required", sa.Boolean(), nullable=False),
        *_lineage_columns(),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workflow_code"),
    )
    _create_common_indexes("wf_workflow_definition", ("family", ["family"]))

    op.create_table(
        "wf_workflow_run",
        sa.Column("workflow_definition_id", sa.String(length=36), nullable=False),
        sa.Column("goal_id", sa.String(length=36), nullable=True),
        sa.Column("task_id", sa.String(length=36), nullable=True),
        sa.Column("owner_role", sa.String(length=80), nullable=False),
        sa.Column("input_payload", sa.JSON(), nullable=False),
        sa.Column("result_payload", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        *_lineage_columns(),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["workflow_definition_id"], ["wf_workflow_definition.id"]),
        sa.ForeignKeyConstraint(["goal_id"], ["gov_goal.id"]),
        sa.ForeignKeyConstraint(["task_id"], ["wf_task.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_common_indexes(
        "wf_workflow_run",
        ("workflow_definition_id", ["workflow_definition_id"]),
        ("goal_id", ["goal_id"]),
        ("task_id", ["task_id"]),
    )

    op.create_table(
        "wf_workflow_event",
        sa.Column("workflow_run_id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("event_at", sa.DateTime(timezone=True), nullable=False),
        *_lineage_columns(),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["workflow_run_id"], ["wf_workflow_run.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_common_indexes("wf_workflow_event", ("workflow_run_id", ["workflow_run_id"]))

    op.create_table(
        "wf_decision_card",
        sa.Column("subject_type", sa.String(length=80), nullable=False),
        sa.Column("subject_id", sa.String(length=120), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("outcome", sa.String(length=80), nullable=False),
        sa.Column("evidence_refs", sa.JSON(), nullable=False),
        *_lineage_columns(),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_common_indexes("wf_decision_card", ("subject_id", ["subject_id"]))

    op.create_table(
        "obs_heartbeat",
        sa.Column("node_role", sa.String(length=80), nullable=False),
        sa.Column("deployment_topology", sa.String(length=80), nullable=False),
        sa.Column("mode", sa.String(length=80), nullable=False),
        sa.Column("risk_state", sa.String(length=80), nullable=False),
        sa.Column("summary_payload", sa.JSON(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        *_lineage_columns(),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_common_indexes("obs_heartbeat", ("node_role", ["node_role"]), ("recorded_at", ["recorded_at"]))

    op.create_table(
        "obs_incident",
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("related_workflow_run_id", sa.String(length=36), nullable=True),
        *_lineage_columns(),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["related_workflow_run_id"], ["wf_workflow_run.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_common_indexes("obs_incident", ("severity", ["severity"]))

    op.create_table(
        "obs_provider_profile",
        sa.Column("provider_key", sa.String(length=120), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("base_url", sa.String(length=500), nullable=True),
        sa.Column("api_style", sa.String(length=80), nullable=False),
        sa.Column("health_status", sa.String(length=40), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.Column("capability_snapshot", sa.JSON(), nullable=False),
        *_lineage_columns(),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider_key"),
    )
    _create_common_indexes("obs_provider_profile", ("health_status", ["health_status"]))

    op.create_table(
        "obs_provider_incident",
        sa.Column("provider_key", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        *_lineage_columns(),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_common_indexes("obs_provider_incident", ("provider_key", ["provider_key"]))

    op.create_table(
        "mem_source_policy",
        sa.Column("source_key", sa.String(length=120), nullable=False),
        sa.Column("source_type", sa.String(length=80), nullable=False),
        sa.Column("ingest_enabled", sa.Boolean(), nullable=False),
        sa.Column("trust_floor", sa.Float(), nullable=False),
        sa.Column("freshness_ttl_hours", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        *_lineage_columns(),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_key"),
    )
    _create_common_indexes("mem_source_policy")

    op.create_table(
        "mem_source_health",
        sa.Column("source_key", sa.String(length=120), nullable=False),
        sa.Column("source_type", sa.String(length=80), nullable=False),
        sa.Column("health_status", sa.String(length=40), nullable=False),
        sa.Column("trust_score", sa.Float(), nullable=False),
        sa.Column("freshness_score", sa.Float(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("last_validated_at", sa.DateTime(timezone=True), nullable=True),
        *_lineage_columns(),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_key"),
    )
    _create_common_indexes("mem_source_health", ("health_status", ["health_status"]))

    op.create_table(
        "exec_market_calendar_state",
        sa.Column("market_calendar", sa.String(length=40), nullable=False),
        sa.Column("market_timezone", sa.String(length=80), nullable=False),
        sa.Column("session_label", sa.String(length=80), nullable=False),
        sa.Column("is_market_open", sa.Boolean(), nullable=False),
        sa.Column("trading_allowed", sa.Boolean(), nullable=False),
        sa.Column("next_open_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_close_at", sa.DateTime(timezone=True), nullable=True),
        *_lineage_columns(),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_common_indexes("exec_market_calendar_state", ("market_calendar", ["market_calendar"]))

    op.create_table(
        "ops_drill_run",
        sa.Column("drill_type", sa.String(length=80), nullable=False),
        sa.Column("started_by", sa.String(length=120), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("result_payload", sa.JSON(), nullable=False),
        *_lineage_columns(),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_common_indexes("ops_drill_run", ("drill_type", ["drill_type"]))

    op.create_table(
        "ops_recovery_checkpoint",
        sa.Column("checkpoint_type", sa.String(length=80), nullable=False),
        sa.Column("storage_uri", sa.String(length=500), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_payload", sa.JSON(), nullable=False),
        *_lineage_columns(),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_common_indexes("ops_recovery_checkpoint", ("checkpoint_type", ["checkpoint_type"]))


def downgrade() -> None:
    _drop_common_indexes("ops_recovery_checkpoint", "checkpoint_type")
    op.drop_table("ops_recovery_checkpoint")

    _drop_common_indexes("ops_drill_run", "drill_type")
    op.drop_table("ops_drill_run")

    _drop_common_indexes("exec_market_calendar_state", "market_calendar")
    op.drop_table("exec_market_calendar_state")

    _drop_common_indexes("mem_source_health", "health_status")
    op.drop_table("mem_source_health")

    _drop_common_indexes("mem_source_policy")
    op.drop_table("mem_source_policy")

    _drop_common_indexes("obs_provider_incident", "provider_key")
    op.drop_table("obs_provider_incident")

    _drop_common_indexes("obs_provider_profile", "health_status")
    op.drop_table("obs_provider_profile")

    _drop_common_indexes("obs_incident", "severity")
    op.drop_table("obs_incident")

    _drop_common_indexes("obs_heartbeat", "node_role", "recorded_at")
    op.drop_table("obs_heartbeat")

    _drop_common_indexes("wf_decision_card", "subject_id")
    op.drop_table("wf_decision_card")

    _drop_common_indexes("wf_workflow_event", "workflow_run_id")
    op.drop_table("wf_workflow_event")

    _drop_common_indexes("wf_workflow_run", "workflow_definition_id", "goal_id", "task_id")
    op.drop_table("wf_workflow_run")

    _drop_common_indexes("wf_workflow_definition", "family")
    op.drop_table("wf_workflow_definition")

    _drop_common_indexes("wf_task", "goal_id", "plan_id")
    op.drop_table("wf_task")

    _drop_common_indexes("wf_plan", "goal_id")
    op.drop_table("wf_plan")

    _drop_common_indexes("gov_manual_takeover_session")
    op.drop_table("gov_manual_takeover_session")

    _drop_common_indexes("gov_operator_override", "scope", "is_active")
    op.drop_table("gov_operator_override")

    _drop_common_indexes("gov_approval_decision", "approval_request_id")
    op.drop_table("gov_approval_decision")

    _drop_common_indexes("gov_approval_request", "subject_id", "decision_status")
    op.drop_table("gov_approval_request")

    _drop_common_indexes("gov_goal_revision", "goal_id")
    op.drop_table("gov_goal_revision")

    _drop_common_indexes("gov_goal", "mission_domain")
    op.drop_table("gov_goal")

    _drop_common_indexes("gov_autonomy_mode", "mode", "is_active")
    op.drop_table("gov_autonomy_mode")

    _drop_common_indexes("gov_system_policy")
    op.drop_table("gov_system_policy")
