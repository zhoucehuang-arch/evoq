from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from quant_evo_nextgen.db.base import Base, utc_now


def generate_id() -> str:
    return str(uuid4())


class TimestampMixin:
    created_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[Any] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


class LineageMixin:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    created_by: Mapped[str] = mapped_column(String(120), default="system", nullable=False)
    origin_type: Mapped[str] = mapped_column(String(80), default="system", nullable=False)
    origin_id: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(80), default="active", nullable=False, index=True)
    trace_id: Mapped[str | None] = mapped_column(String(120), index=True)
    run_id: Mapped[str | None] = mapped_column(String(120), index=True)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float)


class SystemPolicyModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "gov_system_policy"

    policy_key: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    value_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    is_mutable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class AutonomyModeModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "gov_autonomy_mode"

    mode: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    rationale: Mapped[str | None] = mapped_column(Text)
    activated_by: Mapped[str] = mapped_column(String(120), default="system", nullable=False)
    activated_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)


class GoalModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "gov_goal"

    title: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    mission_domain: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    success_metrics: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    failure_metrics: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    budget_scope: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    time_horizon: Mapped[str | None] = mapped_column(String(120))

    revisions: Mapped[list["GoalRevisionModel"]] = relationship(back_populates="goal", cascade="all, delete-orphan")
    plans: Mapped[list["PlanModel"]] = relationship(back_populates="goal", cascade="all, delete-orphan")
    tasks: Mapped[list["TaskModel"]] = relationship(back_populates="goal")
    workflow_runs: Mapped[list["WorkflowRunModel"]] = relationship(back_populates="goal")


class GoalRevisionModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "gov_goal_revision"

    goal_id: Mapped[str] = mapped_column(ForeignKey("gov_goal.id"), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    revision_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    goal: Mapped[GoalModel] = relationship(back_populates="revisions")


class ApprovalRequestModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "gov_approval_request"

    approval_type: Mapped[str] = mapped_column(String(80), nullable=False)
    subject_type: Mapped[str] = mapped_column(String(80), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    requested_by: Mapped[str] = mapped_column(String(120), nullable=False)
    requested_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    deadline: Mapped[Any | None] = mapped_column(DateTime(timezone=True))
    decision_status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False, index=True)
    rationale: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    decisions: Mapped[list["ApprovalDecisionModel"]] = relationship(
        back_populates="approval_request",
        cascade="all, delete-orphan",
    )


class ApprovalDecisionModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "gov_approval_decision"

    approval_request_id: Mapped[str] = mapped_column(
        ForeignKey("gov_approval_request.id"),
        nullable=False,
        index=True,
    )
    decision: Mapped[str] = mapped_column(String(40), nullable=False)
    decided_by: Mapped[str] = mapped_column(String(120), nullable=False)
    decided_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)

    approval_request: Mapped[ApprovalRequestModel] = relationship(back_populates="decisions")


class OperatorOverrideModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "gov_operator_override"

    scope: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    activated_by: Mapped[str] = mapped_column(String(120), nullable=False)
    activated_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    expires_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)


class ManualTakeoverSessionModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "gov_manual_takeover_session"

    scope: Mapped[str] = mapped_column(String(80), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    initiated_by: Mapped[str] = mapped_column(String(120), nullable=False)
    started_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    ended_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class OwnerPreferenceModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "gov_owner_preference"

    preference_key: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    scope: Mapped[str] = mapped_column(String(80), default="owner", nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    value_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    updated_by: Mapped[str] = mapped_column(String(120), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)


class RuntimeConfigProposalModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "gov_runtime_config_proposal"

    target_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    target_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    requested_by: Mapped[str] = mapped_column(String(120), nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text)
    change_summary: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approval_request_id: Mapped[str | None] = mapped_column(
        ForeignKey("gov_approval_request.id"),
        index=True,
    )
    current_value_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    proposed_value_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class RuntimeConfigRevisionModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "gov_runtime_config_revision"

    proposal_id: Mapped[str | None] = mapped_column(
        ForeignKey("gov_runtime_config_proposal.id"),
        index=True,
    )
    target_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    target_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    change_summary: Mapped[str] = mapped_column(Text, nullable=False)
    previous_value_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    applied_value_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    applied_by: Mapped[str] = mapped_column(String(120), nullable=False)
    applied_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)


class EvolutionImprovementProposalModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "evo_improvement_proposal"

    goal_id: Mapped[str | None] = mapped_column(ForeignKey("gov_goal.id"), index=True)
    workflow_run_id: Mapped[str | None] = mapped_column(ForeignKey("wf_workflow_run.id"), index=True)
    codex_run_id: Mapped[str | None] = mapped_column(ForeignKey("exec_codex_run.id"), index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    target_surface: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    proposal_kind: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    change_scope: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    expected_benefit: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    evaluation_summary: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    risk_summary: Mapped[str | None] = mapped_column(Text)
    canary_plan: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    rollback_plan: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    objective_drift_checks: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    proposal_state: Mapped[str] = mapped_column(String(80), default="candidate", nullable=False, index=True)


class EvolutionCanaryRunModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "evo_canary_run"

    proposal_id: Mapped[str] = mapped_column(ForeignKey("evo_improvement_proposal.id"), nullable=False, index=True)
    lane_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    environment: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    traffic_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    success_metrics: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    objective_drift_score: Mapped[float | None] = mapped_column(Float)
    objective_drift_summary: Mapped[str | None] = mapped_column(Text)
    rollback_ready: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    started_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True))


class EvolutionPromotionDecisionModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "evo_promotion_decision"

    proposal_id: Mapped[str] = mapped_column(ForeignKey("evo_improvement_proposal.id"), nullable=False, index=True)
    decision: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    decided_by: Mapped[str] = mapped_column(String(120), nullable=False)
    decided_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    decision_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class PlanModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "wf_plan"

    goal_id: Mapped[str] = mapped_column(ForeignKey("gov_goal.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    goal: Mapped[GoalModel] = relationship(back_populates="plans")
    tasks: Mapped[list["TaskModel"]] = relationship(back_populates="plan", cascade="all, delete-orphan")


class TaskModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "wf_task"

    goal_id: Mapped[str | None] = mapped_column(ForeignKey("gov_goal.id"), index=True)
    plan_id: Mapped[str | None] = mapped_column(ForeignKey("wf_plan.id"), index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    owner_role: Mapped[str] = mapped_column(String(80), nullable=False)
    input_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    output_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=1800, nullable=False)
    retry_policy: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    goal: Mapped[GoalModel | None] = relationship(back_populates="tasks")
    plan: Mapped[PlanModel | None] = relationship(back_populates="tasks")
    workflow_runs: Mapped[list["WorkflowRunModel"]] = relationship(back_populates="task")


class WorkflowDefinitionModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "wf_workflow_definition"

    workflow_code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    family: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    risk_tier: Mapped[str] = mapped_column(String(20), nullable=False)
    approval_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    runs: Mapped[list["WorkflowRunModel"]] = relationship(back_populates="workflow_definition")


class WorkflowRunModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "wf_workflow_run"

    workflow_definition_id: Mapped[str] = mapped_column(
        ForeignKey("wf_workflow_definition.id"),
        nullable=False,
        index=True,
    )
    goal_id: Mapped[str | None] = mapped_column(ForeignKey("gov_goal.id"), index=True)
    task_id: Mapped[str | None] = mapped_column(ForeignKey("wf_task.id"), index=True)
    owner_role: Mapped[str] = mapped_column(String(80), nullable=False)
    input_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    result_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    started_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    ended_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True))

    workflow_definition: Mapped[WorkflowDefinitionModel] = relationship(back_populates="runs")
    goal: Mapped[GoalModel | None] = relationship(back_populates="workflow_runs")
    task: Mapped[TaskModel | None] = relationship(back_populates="workflow_runs")
    events: Mapped[list["WorkflowEventModel"]] = relationship(
        back_populates="workflow_run",
        cascade="all, delete-orphan",
    )


class WorkflowEventModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "wf_workflow_event"

    workflow_run_id: Mapped[str] = mapped_column(ForeignKey("wf_workflow_run.id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    event_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    workflow_run: Mapped[WorkflowRunModel] = relationship(back_populates="events")


class SupervisorLoopModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "wf_supervisor_loop"

    loop_key: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    workflow_code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    domain: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    handler_key: Mapped[str] = mapped_column(String(120), nullable=False)
    cadence_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    execution_mode: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    budget_scope: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    stop_conditions: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    next_due_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True), index=True)
    last_started_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True))
    last_completed_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True))
    last_status: Mapped[str] = mapped_column(String(40), default="idle", nullable=False, index=True)
    last_error: Mapped[str | None] = mapped_column(Text)
    failure_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_failure_streak: Mapped[int] = mapped_column(Integer, default=3, nullable=False)


class DecisionCardModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "wf_decision_card"

    subject_type: Mapped[str] = mapped_column(String(80), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    outcome: Mapped[str] = mapped_column(String(80), nullable=False)
    evidence_refs: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)


class HeartbeatModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "obs_heartbeat"

    node_role: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    deployment_topology: Mapped[str] = mapped_column(String(80), nullable=False)
    mode: Mapped[str] = mapped_column(String(80), nullable=False)
    risk_state: Mapped[str] = mapped_column(String(80), nullable=False)
    summary_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    recorded_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)


class IncidentModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "obs_incident"

    title: Mapped[str] = mapped_column(String(240), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    detected_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    resolved_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True))
    related_workflow_run_id: Mapped[str | None] = mapped_column(ForeignKey("wf_workflow_run.id"))


class ProviderProfileModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "obs_provider_profile"

    provider_key: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    base_url: Mapped[str | None] = mapped_column(String(500))
    api_style: Mapped[str] = mapped_column(String(80), nullable=False)
    health_status: Mapped[str] = mapped_column(String(40), default="unknown", nullable=False, index=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    capability_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class ProviderIncidentModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "obs_provider_incident"

    provider_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    detected_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    resolved_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True))


class SourcePolicyModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "mem_source_policy"

    source_key: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    ingest_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    trust_floor: Mapped[float] = mapped_column(Float, default=0.4, nullable=False)
    freshness_ttl_hours: Mapped[int] = mapped_column(Integer, default=48, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)


class SourceHealthModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "mem_source_health"

    source_key: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    health_status: Mapped[str] = mapped_column(String(40), default="unknown", nullable=False, index=True)
    trust_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    freshness_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    last_validated_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True))


class DocumentModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "mem_document"

    codex_run_id: Mapped[str | None] = mapped_column(ForeignKey("exec_codex_run.id"), unique=True, index=True)
    workflow_run_id: Mapped[str | None] = mapped_column(ForeignKey("wf_workflow_run.id"), index=True)
    supervisor_loop_key: Mapped[str | None] = mapped_column(String(120), index=True)
    source_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    storage_path: Mapped[str | None] = mapped_column(String(500))
    citations_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    followup_tasks: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    risks_found: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    ingested_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)


class EvidenceItemModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "mem_evidence_item"

    document_id: Mapped[str] = mapped_column(ForeignKey("mem_document.id"), nullable=False, index=True)
    codex_run_id: Mapped[str | None] = mapped_column(ForeignKey("exec_codex_run.id"), index=True)
    evidence_type: Mapped[str] = mapped_column(String(80), default="external_citation", nullable=False, index=True)
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    citation_ref: Mapped[str | None] = mapped_column(String(500))
    topic: Mapped[str | None] = mapped_column(String(120), index=True)
    recorded_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)


class InsightModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "mem_insight"

    document_id: Mapped[str] = mapped_column(ForeignKey("mem_document.id"), nullable=False, unique=True, index=True)
    codex_run_id: Mapped[str | None] = mapped_column(ForeignKey("exec_codex_run.id"), index=True)
    workflow_run_id: Mapped[str | None] = mapped_column(ForeignKey("wf_workflow_run.id"), index=True)
    supervisor_loop_key: Mapped[str | None] = mapped_column(String(120), index=True)
    topic_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_evidence_refs: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    citation_refs: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    challenge_notes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    followup_tasks: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    promotion_state: Mapped[str] = mapped_column(String(80), default="candidate", nullable=False, index=True)
    quarantine_reason: Mapped[str | None] = mapped_column(Text)
    recorded_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    last_validated_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True))


class HypothesisModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "strat_hypothesis"

    source_insight_id: Mapped[str | None] = mapped_column(ForeignKey("mem_insight.id"), index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    thesis: Mapped[str] = mapped_column(Text, nullable=False)
    target_market: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    mechanism: Mapped[str] = mapped_column(Text, nullable=False)
    risk_hypothesis: Mapped[str | None] = mapped_column(Text)
    evaluation_plan: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    invalidation_conditions: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    current_stage: Mapped[str] = mapped_column(String(80), default="hypothesis", nullable=False, index=True)


class StrategySpecModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "strat_strategy_spec"

    hypothesis_id: Mapped[str] = mapped_column(ForeignKey("strat_hypothesis.id"), nullable=False, index=True)
    spec_code: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    version_label: Mapped[str] = mapped_column(String(80), default="v1", nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    target_market: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    signal_logic: Mapped[str] = mapped_column(Text, nullable=False)
    risk_rules: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    data_requirements: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    invalidation_conditions: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    execution_constraints: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    current_stage: Mapped[str] = mapped_column(String(80), default="specified", nullable=False, index=True)
    latest_backtest_gate: Mapped[str | None] = mapped_column(String(80), index=True)
    latest_paper_gate: Mapped[str | None] = mapped_column(String(80), index=True)


class BacktestRunModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "strat_backtest_run"

    strategy_spec_id: Mapped[str] = mapped_column(ForeignKey("strat_strategy_spec.id"), nullable=False, index=True)
    dataset_range: Mapped[str | None] = mapped_column(String(240))
    sample_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metrics_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    artifact_path: Mapped[str | None] = mapped_column(String(500))
    gate_result: Mapped[str] = mapped_column(String(80), default="needs_review", nullable=False, index=True)
    gate_notes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    started_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True))


class PaperRunModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "strat_paper_run"

    strategy_spec_id: Mapped[str] = mapped_column(ForeignKey("strat_strategy_spec.id"), nullable=False, index=True)
    deployment_label: Mapped[str] = mapped_column(String(120), nullable=False)
    monitoring_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metrics_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    capital_allocated: Mapped[float | None] = mapped_column(Float)
    gate_result: Mapped[str] = mapped_column(String(80), default="monitoring", nullable=False, index=True)
    gate_notes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    started_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True))


class PromotionDecisionModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "strat_promotion_decision"

    strategy_spec_id: Mapped[str] = mapped_column(ForeignKey("strat_strategy_spec.id"), nullable=False, index=True)
    paper_run_id: Mapped[str | None] = mapped_column(ForeignKey("strat_paper_run.id"), index=True)
    target_stage: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    decision: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_refs: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    decided_by: Mapped[str] = mapped_column(String(120), nullable=False)
    decided_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class WithdrawalDecisionModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "strat_withdrawal_decision"

    strategy_spec_id: Mapped[str] = mapped_column(ForeignKey("strat_strategy_spec.id"), nullable=False, index=True)
    replacement_strategy_spec_id: Mapped[str | None] = mapped_column(
        ForeignKey("strat_strategy_spec.id"),
        index=True,
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_refs: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    decided_by: Mapped[str] = mapped_column(String(120), nullable=False)
    decided_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class MarketCalendarStateModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "exec_market_calendar_state"

    market_calendar: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    market_timezone: Mapped[str] = mapped_column(String(80), nullable=False)
    session_label: Mapped[str] = mapped_column(String(80), nullable=False)
    is_market_open: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    trading_allowed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    next_open_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True))
    next_close_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True))


class BrokerAccountSnapshotModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "exec_broker_account_snapshot"

    provider_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    account_ref: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    environment: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    equity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    cash: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    buying_power: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    gross_exposure: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    net_exposure: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    positions_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    open_orders_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source_captured_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    source_age_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class ReconciliationRunModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "exec_reconciliation_run"

    provider_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    account_ref: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    account_snapshot_id: Mapped[str | None] = mapped_column(
        ForeignKey("exec_broker_account_snapshot.id"),
        index=True,
    )
    environment: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    internal_equity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    broker_equity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    equity_delta_abs: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    equity_delta_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    internal_positions_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    broker_positions_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    internal_open_orders_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    broker_open_orders_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    position_delta_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    order_delta_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    blocking_reason: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    checked_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    halt_triggered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class BrokerSyncRunModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "exec_broker_sync_run"

    provider_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    account_ref: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    environment: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    broker_adapter: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    sync_scope: Mapped[str] = mapped_column(String(40), default="full", nullable=False)
    account_snapshot_id: Mapped[str | None] = mapped_column(
        ForeignKey("exec_broker_account_snapshot.id"),
        index=True,
    )
    synced_orders_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    synced_positions_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unmanaged_orders_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unmanaged_positions_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    missing_internal_orders_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    missing_internal_positions_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    started_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True))


class InstrumentDefinitionModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "exec_instrument_definition"

    instrument_key: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    display_symbol: Mapped[str] = mapped_column(String(160), nullable=False)
    instrument_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    venue: Mapped[str | None] = mapped_column(String(80))
    currency: Mapped[str] = mapped_column(String(16), default="USD", nullable=False)
    underlying_symbol: Mapped[str | None] = mapped_column(String(80), index=True)
    option_right: Mapped[str | None] = mapped_column(String(16))
    option_style: Mapped[str | None] = mapped_column(String(16))
    expiration_date: Mapped[Any | None] = mapped_column(Date)
    strike_price: Mapped[float | None] = mapped_column(Float)
    contract_multiplier: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    leverage_ratio: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    inverse_exposure: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_marginable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_shortable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metadata_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class BrokerCapabilityModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "exec_broker_capability"

    capability_key: Mapped[str] = mapped_column(String(160), unique=True, nullable=False, index=True)
    provider_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    broker_adapter: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    account_ref: Mapped[str | None] = mapped_column(String(120), index=True)
    environment: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    account_mode: Mapped[str] = mapped_column(String(40), default="cash", nullable=False)
    supports_equities: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    supports_etfs: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    supports_fractional: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    supports_short: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_margin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_options: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_multi_leg_options: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_option_exercise: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_option_assignment_events: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_live_trading: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_paper_trading: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)


class AllocationPolicyModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "exec_allocation_policy"

    policy_key: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    environment: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    scope: Mapped[str] = mapped_column(String(40), default="global", nullable=False, index=True)
    strategy_spec_id: Mapped[str | None] = mapped_column(ForeignKey("strat_strategy_spec.id"), index=True)
    provider_key: Mapped[str | None] = mapped_column(String(120), index=True)
    account_ref: Mapped[str | None] = mapped_column(String(120), index=True)
    max_strategy_notional_pct: Mapped[float] = mapped_column(Float, default=0.05, nullable=False)
    max_gross_exposure_pct: Mapped[float] = mapped_column(Float, default=0.8, nullable=False)
    max_open_positions: Mapped[int] = mapped_column(Integer, default=8, nullable=False)
    max_open_orders: Mapped[int] = mapped_column(Integer, default=8, nullable=False)
    allow_short: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allow_fractional: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)


class OrderIntentModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "exec_order_intent"

    strategy_spec_id: Mapped[str] = mapped_column(ForeignKey("strat_strategy_spec.id"), nullable=False, index=True)
    allocation_policy_id: Mapped[str | None] = mapped_column(ForeignKey("exec_allocation_policy.id"), index=True)
    provider_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    account_ref: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    environment: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    broker_adapter: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    instrument_id: Mapped[str | None] = mapped_column(String(36), index=True)
    instrument_key: Mapped[str | None] = mapped_column(String(200), index=True)
    underlying_symbol: Mapped[str | None] = mapped_column(String(80), index=True)
    asset_type: Mapped[str] = mapped_column(String(40), default="equity", nullable=False)
    position_effect: Mapped[str] = mapped_column(String(20), default="auto", nullable=False)
    side: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    order_type: Mapped[str] = mapped_column(String(20), default="market", nullable=False)
    time_in_force: Mapped[str] = mapped_column(String(20), default="day", nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    reference_price: Mapped[float] = mapped_column(Float, nullable=False)
    requested_notional: Mapped[float] = mapped_column(Float, nullable=False)
    limit_price: Mapped[float | None] = mapped_column(Float)
    stop_price: Mapped[float | None] = mapped_column(Float)
    requested_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    decision_reason: Mapped[str | None] = mapped_column(Text)
    rationale: Mapped[str | None] = mapped_column(Text)
    signal_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class OrderRecordModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "exec_order_record"

    order_intent_id: Mapped[str] = mapped_column(ForeignKey("exec_order_intent.id"), nullable=False, index=True)
    strategy_spec_id: Mapped[str] = mapped_column(ForeignKey("strat_strategy_spec.id"), nullable=False, index=True)
    provider_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    account_ref: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    environment: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    broker_order_id: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    client_order_id: Mapped[str | None] = mapped_column(String(160), index=True)
    symbol: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    instrument_id: Mapped[str | None] = mapped_column(String(36), index=True)
    instrument_key: Mapped[str | None] = mapped_column(String(200), index=True)
    underlying_symbol: Mapped[str | None] = mapped_column(String(80), index=True)
    asset_type: Mapped[str] = mapped_column(String(40), default="equity", nullable=False)
    position_effect: Mapped[str] = mapped_column(String(20), default="auto", nullable=False)
    side: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    order_type: Mapped[str] = mapped_column(String(20), nullable=False)
    time_in_force: Mapped[str] = mapped_column(String(20), default="day", nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    filled_quantity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    requested_notional: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    avg_fill_price: Mapped[float | None] = mapped_column(Float)
    limit_price: Mapped[float | None] = mapped_column(Float)
    stop_price: Mapped[float | None] = mapped_column(Float)
    parent_order_record_id: Mapped[str | None] = mapped_column(ForeignKey("exec_order_record.id"), index=True)
    last_sync_run_id: Mapped[str | None] = mapped_column(ForeignKey("exec_broker_sync_run.id"), index=True)
    submitted_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    broker_updated_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True))
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class OrderLegModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "exec_order_leg"

    order_intent_id: Mapped[str | None] = mapped_column(ForeignKey("exec_order_intent.id"), index=True)
    order_record_id: Mapped[str | None] = mapped_column(ForeignKey("exec_order_record.id"), index=True)
    leg_index: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    instrument_id: Mapped[str | None] = mapped_column(String(36), index=True)
    instrument_key: Mapped[str | None] = mapped_column(String(200), index=True)
    underlying_symbol: Mapped[str | None] = mapped_column(String(80), index=True)
    asset_type: Mapped[str] = mapped_column(String(40), default="option", nullable=False)
    side: Mapped[str] = mapped_column(String(20), nullable=False)
    position_effect: Mapped[str] = mapped_column(String(20), default="auto", nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    ratio_quantity: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    reference_price: Mapped[float] = mapped_column(Float, nullable=False)
    requested_notional: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)


class PositionRecordModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "exec_position_record"

    strategy_spec_id: Mapped[str] = mapped_column(ForeignKey("strat_strategy_spec.id"), nullable=False, index=True)
    provider_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    account_ref: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    environment: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    instrument_id: Mapped[str | None] = mapped_column(String(36), index=True)
    instrument_key: Mapped[str | None] = mapped_column(String(200), index=True)
    underlying_symbol: Mapped[str | None] = mapped_column(String(80), index=True)
    asset_type: Mapped[str] = mapped_column(String(40), default="equity", nullable=False)
    direction: Mapped[str] = mapped_column(String(20), default="long", nullable=False, index=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    avg_entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    market_price: Mapped[float | None] = mapped_column(Float)
    notional_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    realized_pnl: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    unrealized_pnl: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    opened_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    closed_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True))
    last_synced_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_sync_run_id: Mapped[str | None] = mapped_column(ForeignKey("exec_broker_sync_run.id"), index=True)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class OptionLifecycleEventModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "exec_option_lifecycle_event"

    event_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    provider_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    account_ref: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    environment: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    underlying_symbol: Mapped[str | None] = mapped_column(String(80), index=True)
    position_id: Mapped[str | None] = mapped_column(ForeignKey("exec_position_record.id"), index=True)
    strategy_spec_id: Mapped[str | None] = mapped_column(ForeignKey("strat_strategy_spec.id"), index=True)
    instrument_id: Mapped[str | None] = mapped_column(String(36), index=True)
    instrument_key: Mapped[str | None] = mapped_column(String(200), index=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    event_price: Mapped[float | None] = mapped_column(Float)
    cash_flow: Mapped[float | None] = mapped_column(Float)
    state_applied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    review_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    applied_position_id: Mapped[str | None] = mapped_column(String(36), index=True)
    resulting_symbol: Mapped[str | None] = mapped_column(String(80), index=True)
    resulting_instrument_key: Mapped[str | None] = mapped_column(String(200), index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    metadata_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    occurred_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)


class DrillRunModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "ops_drill_run"

    drill_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    started_by: Mapped[str] = mapped_column(String(120), nullable=False)
    started_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    result_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class RecoveryCheckpointModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "ops_recovery_checkpoint"

    checkpoint_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    storage_uri: Mapped[str] = mapped_column(String(500), nullable=False)
    captured_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    metadata_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class CodexRunModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "exec_codex_run"

    goal_id: Mapped[str | None] = mapped_column(ForeignKey("gov_goal.id"), index=True)
    task_id: Mapped[str | None] = mapped_column(ForeignKey("wf_task.id"), index=True)
    workflow_run_id: Mapped[str | None] = mapped_column(ForeignKey("wf_workflow_run.id"), index=True)
    supervisor_loop_key: Mapped[str | None] = mapped_column(String(120), index=True)
    worker_class: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    execution_mode: Mapped[str] = mapped_column(String(40), default="local_exec", nullable=False, index=True)
    strategy_mode: Mapped[str] = mapped_column(String(40), default="ralph_style", nullable=False, index=True)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    context_summary: Mapped[str] = mapped_column(Text, nullable=False)
    repo_path: Mapped[str] = mapped_column(String(500), nullable=False)
    workspace_path: Mapped[str] = mapped_column(String(500), nullable=False)
    write_scope: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    allowed_tools: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    search_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    risk_tier: Mapped[str] = mapped_column(String(20), nullable=False, default="R2")
    max_duration_sec: Mapped[int] = mapped_column(Integer, default=1800, nullable=False)
    max_token_budget: Mapped[int] = mapped_column(Integer, default=120000, nullable=False)
    max_iterations: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    review_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    eval_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ralph_state_path: Mapped[str | None] = mapped_column(String(500))
    output_schema_path: Mapped[str | None] = mapped_column(String(500))
    request_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    result_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    queued_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    started_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True))
    last_heartbeat_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    current_attempt: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    attempts: Mapped[list["CodexAttemptModel"]] = relationship(
        back_populates="codex_run",
        cascade="all, delete-orphan",
    )
    artifacts: Mapped[list["CodexArtifactModel"]] = relationship(
        back_populates="codex_run",
        cascade="all, delete-orphan",
    )


class CodexAttemptModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "exec_codex_attempt"

    codex_run_id: Mapped[str] = mapped_column(ForeignKey("exec_codex_run.id"), nullable=False, index=True)
    attempt_no: Mapped[int] = mapped_column(Integer, nullable=False)
    phase: Mapped[str] = mapped_column(String(40), default="implement", nullable=False, index=True)
    prompt_path: Mapped[str | None] = mapped_column(String(500))
    output_path: Mapped[str | None] = mapped_column(String(500))
    handoff_path: Mapped[str | None] = mapped_column(String(500))
    command_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    env_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    result_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    exit_code: Mapped[int | None] = mapped_column(Integer)
    started_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    ended_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True))

    codex_run: Mapped[CodexRunModel] = relationship(back_populates="attempts")
    artifacts: Mapped[list["CodexArtifactModel"]] = relationship(
        back_populates="codex_attempt",
        cascade="all, delete-orphan",
    )


class CodexArtifactModel(Base, LineageMixin, TimestampMixin):
    __tablename__ = "exec_codex_artifact"

    codex_run_id: Mapped[str] = mapped_column(ForeignKey("exec_codex_run.id"), nullable=False, index=True)
    codex_attempt_id: Mapped[str | None] = mapped_column(ForeignKey("exec_codex_attempt.id"), index=True)
    artifact_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(120))
    metadata_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    codex_run: Mapped[CodexRunModel] = relationship(back_populates="artifacts")
    codex_attempt: Mapped[CodexAttemptModel | None] = relationship(back_populates="artifacts")
