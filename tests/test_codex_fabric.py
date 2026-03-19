import json
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

from quant_evo_nextgen.config import Settings
from quant_evo_nextgen.contracts.codex import CodexRunRequest
from quant_evo_nextgen.db.models import CodexRunModel
from quant_evo_nextgen.db.session import Database
from quant_evo_nextgen.services.codex_fabric import CodexFabricService


def test_codex_fabric_runs_implement_review_eval_loop(tmp_path: Path, monkeypatch) -> None:
    service, database = _build_service(tmp_path)
    request = _build_request(
        tmp_path,
        codex_run_id="codex-loop-1",
        review_required=True,
        eval_required=True,
    )

    phase_payloads = {
        "implement": {
            "summary": "Implementation completed and handed off for review.",
            "outcome": "needs_review",
            "files_changed": ["src/example.py"],
            "tests_run": ["py -m pytest tests/test_example.py"],
            "test_results": ["passed"],
            "artifacts_produced": ["patch.diff"],
            "followup_tasks": ["Review the new implementation."],
            "risks_found": ["Need explicit regression review."],
            "citations": [],
            "confidence": 0.77,
        },
        "review": {
            "summary": "Review passed and requested final evaluation.",
            "outcome": "needs_eval",
            "files_changed": [],
            "tests_run": ["py -m pytest tests/test_example.py"],
            "test_results": ["passed"],
            "artifacts_produced": ["review.md"],
            "followup_tasks": ["Run eval before promotion."],
            "risks_found": ["Residual production-risk check still required."],
            "citations": [],
            "confidence": 0.83,
        },
        "eval": {
            "summary": "Eval accepted the run for completion.",
            "outcome": "completed",
            "files_changed": [],
            "tests_run": ["py -m pytest tests/test_example.py"],
            "test_results": ["passed"],
            "artifacts_produced": ["eval.md"],
            "followup_tasks": [],
            "risks_found": [],
            "citations": [],
            "confidence": 0.9,
        },
    }
    seen_phases: list[str] = []

    def fake_run(command, *, cwd, env, capture_output, text, timeout, check):
        phase = _phase_from_command(command)
        seen_phases.append(phase)
        final_message_path = Path(command[command.index("--output-last-message") + 1])
        final_message_path.write_text(json.dumps(phase_payloads[phase]), encoding="utf-8")
        workspace_path = Path(cwd)
        assert workspace_path != tmp_path
        assert workspace_path.name == "workspace"
        if phase == "implement":
            (workspace_path / "src").mkdir(parents=True, exist_ok=True)
            (workspace_path / "src" / "example.py").write_text("print('isolated workspace change')\n", encoding="utf-8")
        assert env["CODEX_API_KEY"] == "relay-key"
        assert env["OPENAI_API_KEY"] == "relay-key"
        assert env["OPENAI_BASE_URL"] == "https://relay.example.com/v1"
        return subprocess.CompletedProcess(command, 0, stdout=f"{phase} ok", stderr="")

    monkeypatch.setattr("quant_evo_nextgen.services.codex_fabric.subprocess.run", fake_run)

    queued = service.queue_run(request)
    result = service.execute_run(queued.id)

    attempts = service.list_attempts(queued.id)
    artifacts = service.list_artifacts(queued.id)
    run_root = tmp_path / ".qe" / "codex_runs" / queued.id

    assert result.status == "completed"
    assert seen_phases == ["implement", "review", "eval"]
    assert [attempt.phase for attempt in attempts] == ["implement", "review", "eval"]
    assert len(artifacts) == 16
    assert (run_root / "progress.md").exists()
    assert (run_root / "guardrails.md").exists()
    assert "Need explicit regression review." in (run_root / "guardrails.md").read_text(encoding="utf-8")
    assert (
        run_root / "attempts" / "attempt-003-eval" / "handoff.md"
    ).read_text(encoding="utf-8").startswith("# Handoff / eval")
    assert (tmp_path / "src" / "example.py").read_text(encoding="utf-8") == "print('isolated workspace change')\n"
    assert (run_root / "attempts" / "attempt-003-eval" / "workspace-sync.json").exists()

    database.dispose()


def test_codex_fabric_retries_failed_attempt_until_success(tmp_path: Path, monkeypatch) -> None:
    service, database = _build_service(tmp_path)
    request = _build_request(tmp_path, codex_run_id="codex-retry-1", max_iterations=3)
    execution_count = 0

    def fake_run(command, *, cwd, env, capture_output, text, timeout, check):
        nonlocal execution_count
        execution_count += 1
        final_message_path = Path(command[command.index("--output-last-message") + 1])
        if execution_count == 2:
            final_message_path.write_text(
                json.dumps(
                    {
                        "summary": "Recovered after one retry.",
                        "outcome": "completed",
                        "files_changed": ["src/recovered.py"],
                        "tests_run": ["py -m pytest"],
                        "test_results": ["passed"],
                        "artifacts_produced": [],
                        "followup_tasks": [],
                        "risks_found": [],
                        "citations": [],
                        "confidence": 0.71,
                    }
                ),
                encoding="utf-8",
            )
            return subprocess.CompletedProcess(command, 0, stdout="retry ok", stderr="")
        return subprocess.CompletedProcess(command, 1, stdout="first failed", stderr="boom")

    monkeypatch.setattr("quant_evo_nextgen.services.codex_fabric.subprocess.run", fake_run)

    queued = service.queue_run(request)
    result = service.execute_run(queued.id)
    attempts = service.list_attempts(queued.id)

    assert result.status == "completed"
    assert execution_count == 2
    assert [attempt.status for attempt in attempts] == ["failed", "completed"]
    assert [attempt.phase for attempt in attempts] == ["implement", "implement"]

    database.dispose()


def test_codex_fabric_does_not_sync_failed_isolated_changes(tmp_path: Path, monkeypatch) -> None:
    service, database = _build_service(tmp_path)
    request = _build_request(tmp_path, codex_run_id="codex-failed-sync-1", max_iterations=1)
    (tmp_path / "src").mkdir(parents=True, exist_ok=True)
    original_path = tmp_path / "src" / "failed.py"
    original_path.write_text("print('original')\n", encoding="utf-8")

    def fake_run(command, *, cwd, env, capture_output, text, timeout, check):
        workspace_path = Path(cwd)
        (workspace_path / "src" / "failed.py").write_text("print('isolated only')\n", encoding="utf-8")
        return subprocess.CompletedProcess(command, 1, stdout="failed", stderr="boom")

    monkeypatch.setattr("quant_evo_nextgen.services.codex_fabric.subprocess.run", fake_run)

    queued = service.queue_run(request)
    result = service.execute_run(queued.id)
    run_root = tmp_path / ".qe" / "codex_runs" / queued.id
    sync_payload = json.loads(
        (run_root / "attempts" / "attempt-001-implement" / "workspace-sync.json").read_text(encoding="utf-8")
    )

    assert result.status == "failed"
    assert original_path.read_text(encoding="utf-8") == "print('original')\n"
    assert sync_payload["applied"] is False
    assert sync_payload["final_status"] == "failed"

    database.dispose()


def test_codex_fabric_recovers_stale_active_runs_before_new_claims(tmp_path: Path) -> None:
    service, database = _build_service(tmp_path)
    stale_request = _build_request(tmp_path, codex_run_id="codex-stale-1")
    fresh_request = _build_request(tmp_path, codex_run_id="codex-fresh-1")

    stale_run = service.queue_run(stale_request)
    fresh_run = service.queue_run(fresh_request)

    with database.session_scope() as session:
        run = session.get(CodexRunModel, stale_run.id)
        assert run is not None
        run.status = "running"
        run.started_at = datetime.now(tz=UTC) - timedelta(hours=2)
        run.last_heartbeat_at = datetime.now(tz=UTC) - timedelta(hours=2)
        run.current_attempt = 1

    claimed = service.claim_next_run()

    assert claimed is not None
    assert claimed.id == stale_run.id
    assert claimed.status == "booting"

    with database.session_scope() as session:
        recovered = session.get(CodexRunModel, stale_run.id)
        queued = session.get(CodexRunModel, fresh_run.id)
        assert recovered is not None
        assert queued is not None
        assert recovered.last_error == "Recovered stale Codex run lease."
        assert queued.status == "queued"

    database.dispose()


def _build_service(tmp_path: Path) -> tuple[CodexFabricService, Database]:
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'codex-fabric.db'}")
    database.create_schema()
    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'codex-fabric.db'}",
        openai_api_key="relay-key",
        openai_base_url="https://relay.example.com/v1",
        codex_timeout_seconds=300,
    )
    return CodexFabricService(database.session_factory, settings), database


def _build_request(tmp_path: Path, **overrides) -> CodexRunRequest:
    tmp_path.mkdir(parents=True, exist_ok=True)
    payload = {
        "codex_run_id": "codex-run",
        "worker_class": "implementation_worker",
        "objective": "Implement and validate the requested change.",
        "context_summary": "Use the repo workspace and persist Ralph-style handoffs.",
        "repo_path": tmp_path,
        "workspace_path": tmp_path,
        "write_scope": ["src/"],
        "allowed_tools": ["shell"],
        "search_enabled": False,
        "risk_tier": "R2",
        "max_duration_sec": 120,
        "max_token_budget": 10000,
        "max_iterations": 4,
        "acceptance_criteria": ["Keep artifacts and structured output durable."],
        "review_required": False,
        "eval_required": False,
    }
    payload.update(overrides)
    return CodexRunRequest.model_validate(payload)


def _phase_from_command(command: list[str]) -> str:
    prompt = command[-1]
    for phase in ("implement", "review", "eval"):
        if f"Current phase: {phase}" in prompt:
            return phase
    raise AssertionError(f"Unable to detect phase from command: {command}")
