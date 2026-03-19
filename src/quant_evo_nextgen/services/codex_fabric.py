from __future__ import annotations

import json
import os
import hashlib
import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from quant_evo_nextgen.config import Settings
from quant_evo_nextgen.contracts.codex import (
    CodexArtifactSummary,
    CodexAttemptSummary,
    CodexRunRequest,
    CodexRunSummary,
    CodexStructuredOutput,
)
from quant_evo_nextgen.db.models import CodexArtifactModel, CodexAttemptModel, CodexRunModel
from quant_evo_nextgen.services.codex import build_exec_command, build_exec_environment, ensure_paths_exist


ACTIVE_RUN_STATUSES = {"queued", "booting", "running", "reviewing"}
TERMINAL_RUN_STATUSES = {"completed", "blocked", "failed", "needs_review", "needs_eval", "rejected"}
DIRECT_WORKSPACE_MODE = "direct"
ISOLATED_COPY_WORKSPACE_MODE = "isolated_copy"
ISOLATION_IGNORED_DIRS = {".git", ".qe", ".next", "node_modules", "__pycache__", ".pytest_cache"}
ISOLATION_IGNORED_SUFFIXES = {".pyc", ".pyo", ".db", ".sqlite", ".sqlite3"}
ISOLATION_IGNORED_PREFIXES = (".tmp-", "tmp-")


@dataclass(slots=True)
class _AttemptExecution:
    phase: str
    attempt_no: int
    prompt_path: Path
    output_path: Path
    handoff_path: Path
    stdout_path: Path
    stderr_path: Path
    final_message_path: Path
    workspace_sync_path: Path
    command: list[str]
    env_snapshot: dict[str, Any]
    request: CodexRunRequest
    source_workspace_path: Path
    effective_workspace_path: Path
    workspace_mode: str
    baseline_path: Path | None
    sync_write_scope: list[str]


class CodexFabricService:
    def __init__(self, session_factory: Callable[[], Session], settings: Settings) -> None:
        self.session_factory = session_factory
        self.settings = settings

    def queue_run(self, payload: CodexRunRequest | dict[str, Any]) -> CodexRunSummary:
        request = CodexRunRequest.model_validate(payload)
        ensure_paths_exist(request)
        run_root = self._run_root_for_request(request)
        run_root.mkdir(parents=True, exist_ok=True)
        self._write_json(run_root / "request.json", request.model_dump(mode="json"))

        with self.session_factory() as session:
            run = CodexRunModel(
                id=request.codex_run_id,
                goal_id=request.goal_id,
                task_id=request.task_id,
                workflow_run_id=request.workflow_run_id,
                supervisor_loop_key=request.supervisor_loop_key,
                worker_class=request.worker_class,
                execution_mode=request.execution_mode,
                strategy_mode="ralph_style",
                objective=request.objective,
                context_summary=request.context_summary,
                repo_path=str(request.repo_path),
                workspace_path=str(request.workspace_path),
                write_scope=request.write_scope,
                allowed_tools=request.allowed_tools,
                search_enabled=request.search_enabled,
                risk_tier=request.risk_tier,
                max_duration_sec=request.max_duration_sec,
                max_token_budget=request.max_token_budget,
                max_iterations=request.max_iterations,
                review_required=request.review_required,
                eval_required=request.eval_required,
                ralph_state_path=str(run_root),
                output_schema_path=str(request.output_schema_path) if request.output_schema_path else None,
                request_payload=request.model_dump(mode="json"),
                result_payload={},
                queued_at=datetime.now(tz=UTC),
                created_by="codex-fabric",
                origin_type="supervisor-loop" if request.supervisor_loop_key else "codex-request",
                origin_id=request.workflow_run_id or request.supervisor_loop_key or request.codex_run_id,
                tags=[f"supervisor-loop:{request.supervisor_loop_key}"] if request.supervisor_loop_key else [],
                status="queued",
            )
            session.add(run)
            session.commit()
            session.refresh(run)
            return self._run_summary(run)

    def list_runs(
        self,
        *,
        statuses: Sequence[str] | None = None,
        supervisor_loop_key: str | None = None,
        workflow_run_id: str | None = None,
        limit: int = 20,
    ) -> list[CodexRunSummary]:
        with self.session_factory() as session:
            query = select(CodexRunModel).order_by(CodexRunModel.queued_at.desc()).limit(limit)
            if statuses:
                query = query.where(CodexRunModel.status.in_(list(statuses)))
            if supervisor_loop_key:
                query = query.where(CodexRunModel.supervisor_loop_key == supervisor_loop_key)
            if workflow_run_id:
                query = query.where(CodexRunModel.workflow_run_id == workflow_run_id)
            runs = session.scalars(query).all()
            return [self._run_summary(run) for run in runs]

    def find_active_run(
        self,
        *,
        supervisor_loop_key: str | None = None,
        workflow_run_id: str | None = None,
    ) -> CodexRunSummary | None:
        with self.session_factory() as session:
            query = select(CodexRunModel).where(CodexRunModel.status.in_(list(ACTIVE_RUN_STATUSES)))
            if supervisor_loop_key is not None:
                query = query.where(CodexRunModel.supervisor_loop_key == supervisor_loop_key)
            if workflow_run_id is not None:
                query = query.where(CodexRunModel.workflow_run_id == workflow_run_id)
            query = query.order_by(CodexRunModel.queued_at.asc())
            run = session.scalar(query)
            return self._run_summary(run) if run is not None else None

    def list_attempts(self, codex_run_id: str) -> list[CodexAttemptSummary]:
        with self.session_factory() as session:
            attempts = session.scalars(
                select(CodexAttemptModel)
                .where(CodexAttemptModel.codex_run_id == codex_run_id)
                .order_by(CodexAttemptModel.attempt_no.asc())
            ).all()
            return [self._attempt_summary(attempt) for attempt in attempts]

    def list_artifacts(self, codex_run_id: str) -> list[CodexArtifactSummary]:
        with self.session_factory() as session:
            artifacts = session.scalars(
                select(CodexArtifactModel)
                .where(CodexArtifactModel.codex_run_id == codex_run_id)
                .order_by(CodexArtifactModel.created_at.asc())
            ).all()
            return [self._artifact_summary(artifact) for artifact in artifacts]

    def claim_next_run(self) -> CodexRunSummary | None:
        with self.session_factory() as session:
            run = self._claim_stale_run(session)
            recovered = run is not None
            if run is None:
                run = session.scalar(
                    select(CodexRunModel)
                    .where(CodexRunModel.status == "queued")
                    .order_by(CodexRunModel.queued_at.asc())
                )
            if run is None:
                return None

            now = datetime.now(tz=UTC)
            run.status = "booting"
            run.started_at = run.started_at or now
            run.last_heartbeat_at = now
            if recovered:
                run.last_error = self._merge_error(run.last_error, "Recovered stale Codex run lease.")
            session.commit()
            session.refresh(run)
            return self._run_summary(run)

    def run_next(self, *, max_runs: int = 1) -> list[CodexRunSummary]:
        completed: list[CodexRunSummary] = []
        for _ in range(max_runs):
            claimed = self.claim_next_run()
            if claimed is None:
                break
            completed.append(self.execute_run(claimed.id))
        return completed

    def execute_run(self, codex_run_id: str) -> CodexRunSummary:
        while True:
            with self.session_factory() as session:
                run = self._load_run(session, codex_run_id)
                if run.status in TERMINAL_RUN_STATUSES:
                    return self._run_summary(run)
                if run.current_attempt >= run.max_iterations:
                    run.status = "failed"
                    run.completed_at = datetime.now(tz=UTC)
                    run.last_error = "Reached maximum Ralph-style iterations."
                    session.commit()
                    session.refresh(run)
                    return self._run_summary(run)

                execution = self._prepare_attempt(run)
                attempt = CodexAttemptModel(
                    codex_run_id=run.id,
                    attempt_no=execution.attempt_no,
                    phase=execution.phase,
                    prompt_path=str(execution.prompt_path),
                    output_path=str(execution.output_path),
                    handoff_path=str(execution.handoff_path),
                    command_json=execution.command,
                    env_snapshot=execution.env_snapshot,
                    created_by="codex-fabric",
                    origin_type="codex-attempt",
                    origin_id=run.id,
                    status="running",
                )
                run.current_attempt = execution.attempt_no
                run.status = "running" if execution.phase == "implement" else "reviewing"
                run.last_heartbeat_at = datetime.now(tz=UTC)
                session.add(attempt)
                session.commit()
                attempt_id = attempt.id

            result_payload = self._execute_subprocess(execution)

            with self.session_factory() as session:
                run = self._load_run(session, codex_run_id)
                attempt = session.get(CodexAttemptModel, attempt_id)
                if attempt is None:
                    raise ValueError(f"Codex attempt not found: {attempt_id}")

                structured = self._load_structured_output(execution.final_message_path)
                if structured is not None:
                    result_payload["structured_output"] = structured.model_dump(mode="json")
                    attempt.summary = structured.summary

                attempt.status = result_payload["status"]
                attempt.result_payload = result_payload
                attempt.exit_code = result_payload.get("exit_code")
                attempt.ended_at = datetime.now(tz=UTC)
                run.last_heartbeat_at = attempt.ended_at
                run.last_error = result_payload.get("error")
                next_status = self._resolve_next_status(run, execution.phase, result_payload, structured)

                if structured is not None:
                    self._write_handoff(execution.handoff_path, structured, execution.phase)
                if next_status in TERMINAL_RUN_STATUSES:
                    workspace_sync_payload = self._finalize_workspace(execution, final_status=next_status)
                    if workspace_sync_payload is not None:
                        result_payload["workspace_sync"] = workspace_sync_payload
                self._record_attempt_artifacts(session, run, attempt, execution, result_payload, structured)
                self._append_progress(run, execution.phase, structured, result_payload)
                if structured is not None:
                    self._append_guardrails(run, structured)

                run.status = next_status
                run.result_payload = {
                    **run.result_payload,
                    "last_phase": execution.phase,
                    "last_attempt_no": execution.attempt_no,
                    "last_status": next_status,
                    "structured_output": structured.model_dump(mode="json") if structured else None,
                    "workspace_mode": execution.workspace_mode,
                    "effective_workspace_path": str(execution.effective_workspace_path),
                    "workspace_sync": result_payload.get("workspace_sync"),
                }

                if next_status in TERMINAL_RUN_STATUSES:
                    run.completed_at = datetime.now(tz=UTC)

                session.commit()
                session.refresh(run)

                if run.status in TERMINAL_RUN_STATUSES:
                    return self._run_summary(run)

    def _prepare_attempt(self, run: CodexRunModel) -> _AttemptExecution:
        request = CodexRunRequest.model_validate(run.request_payload)
        phase = self._next_phase(run)
        attempt_no = run.current_attempt + 1
        run_root = Path(run.ralph_state_path or self._run_root_for_request(request))
        run_root.mkdir(parents=True, exist_ok=True)
        attempts_dir = run_root / "attempts"
        attempts_dir.mkdir(parents=True, exist_ok=True)
        attempt_dir = attempts_dir / f"attempt-{attempt_no:03d}-{phase}"
        attempt_dir.mkdir(parents=True, exist_ok=True)

        schema_path = Path(run.output_schema_path) if run.output_schema_path else run_root / "structured-output.schema.json"
        if not schema_path.exists():
            self._write_json(schema_path, CodexStructuredOutput.model_json_schema())

        prompt_text = self._build_phase_prompt(run, request, phase, run_root)
        prompt_path = attempt_dir / "prompt.md"
        prompt_path.write_text(prompt_text, encoding="utf-8")

        output_path = attempt_dir / "stdout.ndjson"
        stderr_path = attempt_dir / "stderr.log"
        final_message_path = attempt_dir / "final-message.json"
        handoff_path = attempt_dir / "handoff.md"
        workspace_sync_path = attempt_dir / "workspace-sync.json"
        effective_workspace_path, workspace_mode, baseline_path = self._resolve_workspace_execution(
            request=request,
            run_root=run_root,
        )

        phase_request = self._phase_request(request, schema_path, phase).model_copy(
            update={"workspace_path": effective_workspace_path}
        )
        command = build_exec_command(
            phase_request,
            self.settings,
            output_last_message_path=final_message_path,
            prompt_override=prompt_text,
        )
        env_snapshot = self._redacted_env_snapshot(build_exec_environment(self.settings))
        return _AttemptExecution(
            phase=phase,
            attempt_no=attempt_no,
            prompt_path=prompt_path,
            output_path=output_path,
            handoff_path=handoff_path,
            stdout_path=output_path,
            stderr_path=stderr_path,
            final_message_path=final_message_path,
            workspace_sync_path=workspace_sync_path,
            command=command,
            env_snapshot=env_snapshot,
            request=phase_request,
            source_workspace_path=request.workspace_path,
            effective_workspace_path=effective_workspace_path,
            workspace_mode=workspace_mode,
            baseline_path=baseline_path,
            sync_write_scope=list(request.write_scope),
        )

    def _execute_subprocess(self, execution: _AttemptExecution) -> dict[str, Any]:
        env = os.environ.copy()
        env.update(build_exec_environment(self.settings))
        started_at = datetime.now(tz=UTC)
        try:
            completed = subprocess.run(
                execution.command,
                cwd=str(execution.request.workspace_path),
                env=env,
                capture_output=True,
                text=True,
                timeout=execution.request.max_duration_sec,
                check=False,
            )
            execution.stdout_path.write_text(completed.stdout or "", encoding="utf-8")
            execution.stderr_path.write_text(completed.stderr or "", encoding="utf-8")
            return {
                "status": "completed" if completed.returncode == 0 else "failed",
                "exit_code": completed.returncode,
                "stdout_path": str(execution.stdout_path),
                "stderr_path": str(execution.stderr_path),
                "started_at": started_at.isoformat(),
                "ended_at": datetime.now(tz=UTC).isoformat(),
            }
        except subprocess.TimeoutExpired as exc:
            execution.stdout_path.write_text(exc.stdout or "", encoding="utf-8")
            execution.stderr_path.write_text(exc.stderr or "", encoding="utf-8")
            return {
                "status": "failed",
                "error": f"Codex attempt timed out after {execution.request.max_duration_sec} seconds.",
                "exit_code": None,
                "stdout_path": str(execution.stdout_path),
                "stderr_path": str(execution.stderr_path),
                "started_at": started_at.isoformat(),
                "ended_at": datetime.now(tz=UTC).isoformat(),
            }
        except FileNotFoundError:
            return {
                "status": "failed",
                "error": f"Codex command not found: {self.settings.codex_command}",
                "exit_code": None,
                "stdout_path": str(execution.stdout_path),
                "stderr_path": str(execution.stderr_path),
                "started_at": started_at.isoformat(),
                "ended_at": datetime.now(tz=UTC).isoformat(),
            }

    def _build_phase_prompt(
        self,
        run: CodexRunModel,
        request: CodexRunRequest,
        phase: str,
        run_root: Path,
    ) -> str:
        progress_path = run_root / "progress.md"
        guardrails_path = run_root / "guardrails.md"
        latest_handoff_path = self._latest_handoff_path(run_root)
        progress_text = progress_path.read_text(encoding="utf-8") if progress_path.exists() else "No prior progress yet."
        guardrails_text = guardrails_path.read_text(encoding="utf-8") if guardrails_path.exists() else "No guardrails recorded yet."
        handoff_text = latest_handoff_path.read_text(encoding="utf-8") if latest_handoff_path is not None else "No prior handoff."

        phase_brief = {
            "implement": "Implement the task in a fresh session. If not fully done, leave a precise handoff.",
            "review": "Review the current workspace in read-only mode against the acceptance criteria and risks.",
            "eval": "Evaluate whether the change should advance, focusing on objective fit and regression risk.",
        }[phase]

        appendix = [
            "",
            "Ralph-style loop mode:",
            "- Treat this attempt as a fresh session.",
            "- Use files, not context carryover, as the durable memory.",
            "- Before claiming completion, verify against the acceptance criteria.",
            "- If incomplete, return a precise handoff through the structured output followup_tasks and risks_found fields.",
            f"- Progress file: {progress_path}",
            f"- Guardrails file: {guardrails_path}",
            f"- Latest handoff source: {latest_handoff_path if latest_handoff_path is not None else 'none'}",
            "",
            "Existing progress:",
            progress_text,
            "",
            "Existing guardrails:",
            guardrails_text,
            "",
            "Latest handoff:",
            handoff_text,
            "",
            f"Current phase: {phase}",
            phase_brief,
        ]

        phase_request = self._phase_request(request, request.output_schema_path, phase)
        if phase_request.prompt_appendix:
            appendix.append("")
            appendix.append(phase_request.prompt_appendix)
        return "\n".join(
            [
                f"Objective: {phase_request.objective}",
                f"Context: {phase_request.context_summary}",
                f"Risk tier: {phase_request.risk_tier}",
                f"Write scope: {', '.join(phase_request.write_scope) if phase_request.write_scope else 'read-only'}",
                "Acceptance criteria:",
                *[f"- {criterion}" for criterion in phase_request.acceptance_criteria],
                *appendix,
            ]
        )

    def _phase_request(self, request: CodexRunRequest, schema_path: Path | None, phase: str) -> CodexRunRequest:
        if phase == "implement":
            return request.model_copy(update={"output_schema_path": schema_path})
        if phase == "review":
            return request.model_copy(
                update={
                    "worker_class": "review_worker",
                    "execution_mode": "local_review",
                    "write_scope": [],
                    "output_schema_path": schema_path,
                    "objective": f"Review Codex run `{request.codex_run_id}` for correctness and regression risk.",
                    "context_summary": request.context_summary,
                    "prompt_appendix": "Do not modify files. Review the workspace and decide whether the change is safe to accept.",
                }
            )
        return request.model_copy(
            update={
                "worker_class": "analysis_worker",
                "execution_mode": "local_review",
                "write_scope": [],
                "output_schema_path": schema_path,
                "objective": f"Evaluate whether Codex run `{request.codex_run_id}` should advance toward promotion.",
                "context_summary": request.context_summary,
                "prompt_appendix": "Do not modify files. Evaluate objective fit, governance fit, and residual risk.",
            }
        )

    def _resolve_next_status(
        self,
        run: CodexRunModel,
        phase: str,
        result_payload: dict[str, Any],
        structured: CodexStructuredOutput | None,
    ) -> str:
        if result_payload["status"] == "failed" and structured is None:
            return "failed" if run.current_attempt >= run.max_iterations else "queued"

        if structured is None:
            return "failed"

        outcome = structured.outcome
        if phase == "implement":
            if outcome in {"blocked", "rejected"}:
                return outcome
            if outcome == "failed":
                return "failed" if run.current_attempt >= run.max_iterations else "queued"
            if run.review_required and outcome in {"completed", "needs_review", "needs_eval"}:
                return "reviewing"
            if run.eval_required and outcome in {"completed", "needs_eval"}:
                return "reviewing"
            return "completed" if outcome == "completed" else outcome

        if phase == "review":
            if outcome == "completed":
                return "reviewing" if run.eval_required else "completed"
            if outcome == "needs_eval" and run.eval_required:
                return "reviewing"
            return outcome

        if phase == "eval":
            return "completed" if outcome == "completed" else outcome

        return "failed"

    def _next_phase(self, run: CodexRunModel) -> str:
        attempts = sorted(run.attempts, key=lambda item: item.attempt_no)
        implement_done = any(
            attempt.phase == "implement"
            and attempt.status == "completed"
            and (attempt.result_payload.get("structured_output") or {}).get("outcome") in {"completed", "needs_review", "needs_eval"}
            for attempt in attempts
        )
        review_done = any(
            attempt.phase == "review"
            and attempt.status == "completed"
            and (
                (attempt.result_payload.get("structured_output") or {}).get("outcome") == "completed"
                or (
                    run.eval_required
                    and (attempt.result_payload.get("structured_output") or {}).get("outcome") == "needs_eval"
                )
            )
            for attempt in attempts
        )
        eval_done = any(
            attempt.phase == "eval"
            and attempt.status == "completed"
            and (attempt.result_payload.get("structured_output") or {}).get("outcome") == "completed"
            for attempt in attempts
        )

        if not implement_done:
            return "implement"
        if run.review_required and not review_done:
            return "review"
        if run.eval_required and not eval_done:
            return "eval"
        return "implement"

    def _record_attempt_artifacts(
        self,
        session: Session,
        run: CodexRunModel,
        attempt: CodexAttemptModel,
        execution: _AttemptExecution,
        result_payload: dict[str, Any],
        structured: CodexStructuredOutput | None,
    ) -> None:
        self._upsert_artifact(
            session,
            run_id=run.id,
            attempt_id=attempt.id,
            artifact_type="prompt",
            label=f"Prompt {execution.attempt_no}",
            path=execution.prompt_path,
            content_type="text/markdown",
            metadata={"phase": execution.phase},
        )
        self._upsert_artifact(
            session,
            run_id=run.id,
            attempt_id=attempt.id,
            artifact_type="stdout",
            label=f"Stdout {execution.attempt_no}",
            path=execution.stdout_path,
            content_type="application/x-ndjson",
            metadata={"phase": execution.phase, "exit_code": result_payload.get("exit_code")},
        )
        self._upsert_artifact(
            session,
            run_id=run.id,
            attempt_id=attempt.id,
            artifact_type="stderr",
            label=f"Stderr {execution.attempt_no}",
            path=execution.stderr_path,
            content_type="text/plain",
            metadata={"phase": execution.phase},
        )
        if execution.final_message_path.exists():
            self._upsert_artifact(
                session,
                run_id=run.id,
                attempt_id=attempt.id,
                artifact_type="final_message",
                label=f"Final message {execution.attempt_no}",
                path=execution.final_message_path,
                content_type="application/json" if structured else "text/plain",
                metadata={"phase": execution.phase},
            )
        if execution.handoff_path.exists():
            self._upsert_artifact(
                session,
                run_id=run.id,
                attempt_id=attempt.id,
                artifact_type="handoff",
                label=f"Handoff {execution.attempt_no}",
                path=execution.handoff_path,
                content_type="text/markdown",
                metadata={"phase": execution.phase},
            )
        if execution.workspace_sync_path.exists():
            self._upsert_artifact(
                session,
                run_id=run.id,
                attempt_id=attempt.id,
                artifact_type="workspace_sync",
                label=f"Workspace sync {execution.attempt_no}",
                path=execution.workspace_sync_path,
                content_type="application/json",
                metadata={"phase": execution.phase, "workspace_mode": execution.workspace_mode},
            )

    def _upsert_artifact(
        self,
        session: Session,
        *,
        run_id: str,
        attempt_id: str | None,
        artifact_type: str,
        label: str,
        path: Path,
        content_type: str,
        metadata: dict[str, Any],
    ) -> None:
        session.add(
            CodexArtifactModel(
                codex_run_id=run_id,
                codex_attempt_id=attempt_id,
                artifact_type=artifact_type,
                label=label,
                storage_path=str(path),
                content_type=content_type,
                metadata_payload=metadata,
                created_by="codex-fabric",
                origin_type="codex-artifact",
                origin_id=run_id,
                status="recorded",
            )
        )

    def _append_progress(
        self,
        run: CodexRunModel,
        phase: str,
        structured: CodexStructuredOutput | None,
        result_payload: dict[str, Any],
    ) -> None:
        run_root = Path(run.ralph_state_path)
        progress_path = run_root / "progress.md"
        lines = [
            f"## {datetime.now(tz=UTC).isoformat()} / {phase}",
            f"- status: {result_payload['status']}",
        ]
        if structured is not None:
            lines.append(f"- outcome: {structured.outcome}")
            lines.append(f"- summary: {structured.summary}")
        if result_payload.get("error"):
            lines.append(f"- error: {result_payload['error']}")
        with progress_path.open("a", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n\n")

    def _append_guardrails(self, run: CodexRunModel, structured: CodexStructuredOutput) -> None:
        if not structured.risks_found:
            return
        run_root = Path(run.ralph_state_path)
        guardrails_path = run_root / "guardrails.md"
        with guardrails_path.open("a", encoding="utf-8") as handle:
            for risk in structured.risks_found:
                handle.write(f"- {risk}\n")

    def _write_handoff(self, handoff_path: Path, structured: CodexStructuredOutput, phase: str) -> None:
        handoff = [
            f"# Handoff / {phase}",
            "",
            f"Summary: {structured.summary}",
            f"Outcome: {structured.outcome}",
            "",
            "Follow-up tasks:",
            *([f"- {task}" for task in structured.followup_tasks] or ["- none"]),
            "",
            "Risks found:",
            *([f"- {risk}" for risk in structured.risks_found] or ["- none"]),
        ]
        handoff_path.write_text("\n".join(handoff), encoding="utf-8")

    def _load_structured_output(self, final_message_path: Path) -> CodexStructuredOutput | None:
        if not final_message_path.exists():
            return None
        raw = final_message_path.read_text(encoding="utf-8").strip()
        if not raw:
            return None
        try:
            return CodexStructuredOutput.model_validate_json(raw)
        except Exception:
            try:
                return CodexStructuredOutput.model_validate(json.loads(raw))
            except Exception:
                return None

    def _latest_handoff_path(self, run_root: Path) -> Path | None:
        attempts_dir = run_root / "attempts"
        if not attempts_dir.exists():
            return None
        handoffs = sorted(attempts_dir.glob("attempt-*/handoff.md"))
        return handoffs[-1] if handoffs else None

    def _run_root_for_request(self, request: CodexRunRequest) -> Path:
        return request.workspace_path / ".qe" / "codex_runs" / request.codex_run_id

    def _resolve_workspace_execution(
        self,
        *,
        request: CodexRunRequest,
        run_root: Path,
    ) -> tuple[Path, str, Path | None]:
        workspace_mode = (self.settings.codex_workspace_mode or DIRECT_WORKSPACE_MODE).strip().lower()
        if workspace_mode != ISOLATED_COPY_WORKSPACE_MODE:
            return request.workspace_path, DIRECT_WORKSPACE_MODE, None

        isolated_workspace = run_root / "workspace"
        baseline_path = run_root / "workspace-baseline.json"
        if not isolated_workspace.exists():
            self._materialize_isolated_workspace(request.workspace_path, isolated_workspace)
        if not baseline_path.exists():
            self._write_json(baseline_path, self._workspace_manifest(isolated_workspace))
        return isolated_workspace, ISOLATED_COPY_WORKSPACE_MODE, baseline_path

    def _materialize_isolated_workspace(self, source_workspace: Path, isolated_workspace: Path) -> None:
        isolated_workspace.mkdir(parents=True, exist_ok=True)
        for root, dirnames, filenames in os.walk(source_workspace):
            root_path = Path(root)
            relative_root = root_path.relative_to(source_workspace)
            dirnames[:] = [dirname for dirname in dirnames if not self._should_ignore_dir(relative_root / dirname)]
            target_root = isolated_workspace / relative_root
            target_root.mkdir(parents=True, exist_ok=True)
            for filename in filenames:
                relative_path = relative_root / filename
                if self._should_ignore_file(relative_path):
                    continue
                source_path = root_path / filename
                target_path = isolated_workspace / relative_path
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, target_path)

    def _workspace_manifest(self, workspace_root: Path) -> dict[str, Any]:
        files: dict[str, str] = {}
        for root, dirnames, filenames in os.walk(workspace_root):
            root_path = Path(root)
            relative_root = root_path.relative_to(workspace_root)
            dirnames[:] = [dirname for dirname in dirnames if not self._should_ignore_dir(relative_root / dirname)]
            for filename in filenames:
                relative_path = relative_root / filename
                if self._should_ignore_file(relative_path):
                    continue
                files[relative_path.as_posix()] = self._sha256(workspace_root / relative_path)
        return {"files": files}

    def _finalize_workspace(self, execution: _AttemptExecution, *, final_status: str) -> dict[str, Any] | None:
        if execution.workspace_mode != ISOLATED_COPY_WORKSPACE_MODE:
            return None

        payload: dict[str, Any] = {
            "workspace_mode": execution.workspace_mode,
            "source_workspace_path": str(execution.source_workspace_path),
            "effective_workspace_path": str(execution.effective_workspace_path),
            "final_status": final_status,
            "applied": False,
            "copied_files": [],
            "deleted_files": [],
        }
        if final_status != "completed":
            payload["reason"] = "Run did not complete successfully, so isolated changes were not synced back."
            execution.workspace_sync_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            return payload

        current_manifest = self._workspace_manifest(execution.effective_workspace_path)
        baseline_files = {}
        if execution.baseline_path is not None and execution.baseline_path.exists():
            baseline_files = dict(json.loads(execution.baseline_path.read_text(encoding="utf-8")).get("files", {}))
        current_files = dict(current_manifest.get("files", {}))
        copied_files: list[str] = []
        deleted_files: list[str] = []

        scoped_paths = sorted({*baseline_files.keys(), *current_files.keys()})
        for relative in scoped_paths:
            if not self._path_in_write_scope(relative, execution.sync_write_scope):
                continue
            source_file = execution.effective_workspace_path / Path(relative)
            target_file = execution.source_workspace_path / Path(relative)
            current_hash = current_files.get(relative)
            baseline_hash = baseline_files.get(relative)
            if current_hash is None and baseline_hash is not None:
                if target_file.exists():
                    target_file.unlink()
                deleted_files.append(relative)
                continue
            if current_hash is None or current_hash == baseline_hash:
                continue
            target_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, target_file)
            copied_files.append(relative)

        payload["applied"] = True
        payload["copied_files"] = copied_files
        payload["deleted_files"] = deleted_files
        execution.workspace_sync_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return payload

    def _path_in_write_scope(self, relative_path: str, write_scope: Sequence[str]) -> bool:
        normalized_path = relative_path.replace("\\", "/").strip("/")
        if not write_scope:
            return False
        for scope in write_scope:
            normalized_scope = str(scope).replace("\\", "/").strip()
            if not normalized_scope:
                continue
            normalized_scope = normalized_scope.rstrip("/")
            if not normalized_scope:
                return True
            if normalized_path == normalized_scope or normalized_path.startswith(f"{normalized_scope}/"):
                return True
        return False

    def _should_ignore_dir(self, relative_path: Path) -> bool:
        return any(part in ISOLATION_IGNORED_DIRS for part in relative_path.parts if part)

    def _should_ignore_file(self, relative_path: Path) -> bool:
        if self._should_ignore_dir(relative_path.parent):
            return True
        if relative_path.suffix.lower() in ISOLATION_IGNORED_SUFFIXES:
            return True
        return any(relative_path.name.startswith(prefix) for prefix in ISOLATION_IGNORED_PREFIXES)

    def _sha256(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _claim_stale_run(self, session: Session) -> CodexRunModel | None:
        now = datetime.now(tz=UTC)
        active_runs = session.scalars(
            select(CodexRunModel)
            .where(CodexRunModel.status.in_(list(ACTIVE_RUN_STATUSES)))
            .order_by(CodexRunModel.queued_at.asc())
        ).all()
        for run in active_runs:
            reference_time = self._reference_time(run)
            stale_after_seconds = max(run.max_duration_sec, self.settings.codex_timeout_seconds) + 60
            if (now - reference_time).total_seconds() > stale_after_seconds:
                return run
        return None

    def _reference_time(self, run: CodexRunModel) -> datetime:
        timestamp = run.last_heartbeat_at or run.started_at or run.queued_at
        return self._coerce_utc(timestamp)

    def _load_run(self, session: Session, codex_run_id: str) -> CodexRunModel:
        run = session.scalar(
            select(CodexRunModel)
            .where(CodexRunModel.id == codex_run_id)
            .options(
                selectinload(CodexRunModel.attempts),
                selectinload(CodexRunModel.artifacts),
            )
        )
        if run is None:
            raise ValueError(f"Codex run not found: {codex_run_id}")
        return run

    def _run_summary(self, run: CodexRunModel) -> CodexRunSummary:
        return CodexRunSummary(
            id=run.id,
            status=run.status,
            workflow_run_id=run.workflow_run_id,
            supervisor_loop_key=run.supervisor_loop_key,
            worker_class=run.worker_class,
            execution_mode=run.execution_mode,
            strategy_mode=run.strategy_mode,
            objective=run.objective,
            risk_tier=run.risk_tier,
            current_attempt=run.current_attempt,
            max_iterations=run.max_iterations,
            queued_at=run.queued_at,
            started_at=run.started_at,
            completed_at=run.completed_at,
            last_error=run.last_error,
            workspace_path=run.workspace_path,
        )

    def _attempt_summary(self, attempt: CodexAttemptModel) -> CodexAttemptSummary:
        return CodexAttemptSummary(
            id=attempt.id,
            codex_run_id=attempt.codex_run_id,
            attempt_no=attempt.attempt_no,
            phase=attempt.phase,
            status=attempt.status,
            summary=attempt.summary,
            exit_code=attempt.exit_code,
            started_at=attempt.started_at,
            ended_at=attempt.ended_at,
            prompt_path=attempt.prompt_path,
            output_path=attempt.output_path,
            handoff_path=attempt.handoff_path,
        )

    def _artifact_summary(self, artifact: CodexArtifactModel) -> CodexArtifactSummary:
        return CodexArtifactSummary(
            id=artifact.id,
            codex_run_id=artifact.codex_run_id,
            codex_attempt_id=artifact.codex_attempt_id,
            artifact_type=artifact.artifact_type,
            label=artifact.label,
            storage_path=artifact.storage_path,
            content_type=artifact.content_type,
            metadata_payload=artifact.metadata_payload,
        )

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def _redacted_env_snapshot(self, env: dict[str, str]) -> dict[str, Any]:
        snapshot: dict[str, Any] = {}
        for key, value in env.items():
            if "KEY" in key or "TOKEN" in key or "SECRET" in key:
                snapshot[key] = "set"
            else:
                snapshot[key] = value
        return snapshot

    def _coerce_utc(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    def _merge_error(self, existing: str | None, message: str) -> str:
        if not existing:
            return message
        if message in existing:
            return existing
        return f"{existing} | {message}"
