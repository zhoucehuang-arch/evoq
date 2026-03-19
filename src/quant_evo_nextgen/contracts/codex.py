from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


WorkerClass = Literal[
    "analysis_worker",
    "implementation_worker",
    "review_worker",
    "strategy_worker",
    "ops_worker",
]

ExecutionMode = Literal["local_exec", "local_review", "local_apply"]
CodexOutcome = Literal["completed", "blocked", "failed", "needs_review", "needs_eval", "rejected"]


class CodexRunRequest(BaseModel):
    codex_run_id: str
    goal_id: str | None = None
    task_id: str | None = None
    workflow_run_id: str | None = None
    supervisor_loop_key: str | None = None
    worker_class: WorkerClass
    objective: str
    context_summary: str
    repo_path: Path
    workspace_path: Path
    write_scope: list[str] = Field(default_factory=list)
    allowed_tools: list[str] = Field(default_factory=list)
    search_enabled: bool = False
    risk_tier: str = "R2"
    max_duration_sec: int = 1800
    max_token_budget: int = 120000
    max_iterations: int = 4
    output_schema_path: Path | None = None
    acceptance_criteria: list[str] = Field(default_factory=list)
    prompt_appendix: str | None = None
    model: str | None = None
    execution_mode: ExecutionMode = "local_exec"
    review_required: bool = False
    eval_required: bool = False
    base_branch: str | None = None
    comparison_ref: str | None = None
    related_artifacts: list[str] = Field(default_factory=list)
    memory_refs: list[str] = Field(default_factory=list)
    citation_requirements: list[str] = Field(default_factory=list)


class CodexStructuredOutput(BaseModel):
    summary: str
    outcome: CodexOutcome
    files_changed: list[str] = Field(default_factory=list)
    tests_run: list[str] = Field(default_factory=list)
    test_results: list[str] = Field(default_factory=list)
    artifacts_produced: list[str] = Field(default_factory=list)
    followup_tasks: list[str] = Field(default_factory=list)
    risks_found: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    confidence: float | None = None


class CodexRunSummary(BaseModel):
    id: str
    status: str
    workflow_run_id: str | None = None
    supervisor_loop_key: str | None = None
    worker_class: WorkerClass
    execution_mode: str
    strategy_mode: str
    objective: str
    risk_tier: str
    current_attempt: int
    max_iterations: int
    queued_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    last_error: str | None = None
    workspace_path: str


class CodexAttemptSummary(BaseModel):
    id: str
    codex_run_id: str
    attempt_no: int
    phase: str
    status: str
    summary: str | None = None
    exit_code: int | None = None
    started_at: datetime
    ended_at: datetime | None = None
    prompt_path: str | None = None
    output_path: str | None = None
    handoff_path: str | None = None


class CodexArtifactSummary(BaseModel):
    id: str
    codex_run_id: str
    codex_attempt_id: str | None = None
    artifact_type: str
    label: str
    storage_path: str
    content_type: str | None = None
    metadata_payload: dict[str, Any] = Field(default_factory=dict)
