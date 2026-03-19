import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from quant_evo_nextgen.config import Settings
from quant_evo_nextgen.db.session import Database
from quant_evo_nextgen.services.codex_fabric import CodexFabricService
from quant_evo_nextgen.services.dashboard import DashboardService
from quant_evo_nextgen.services.learning import LearningService
from quant_evo_nextgen.services.repo_state import RepoStateService
from quant_evo_nextgen.services.state_store import StateStore
from quant_evo_nextgen.services.supervisor import SupervisorService


def test_learning_service_ingests_completed_research_codex_runs_without_duplicates(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _seed_repo_state(tmp_path)
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'learning.db'}")
    database.create_schema()

    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'learning.db'}",
        openai_api_key="relay-key",
        openai_base_url="https://relay.example.com/v1",
    )
    state_store = StateStore(database.session_factory)
    state_store.bootstrap_reference_data(settings)
    workflow_run = state_store.start_workflow_run(
        workflow_code="WF-LRN-002",
        owner_role="supervisor",
        summary="Research intake for learning ingestion test.",
    )
    codex_fabric_service = CodexFabricService(database.session_factory, settings)
    learning_service = LearningService(database.session_factory)

    _mock_completed_research_run(monkeypatch)
    queued = codex_fabric_service.queue_run(
        {
            "codex_run_id": "research-run-1",
            "workflow_run_id": workflow_run.id,
            "supervisor_loop_key": "research-intake",
            "worker_class": "analysis_worker",
            "objective": "Run a bounded research intake sweep.",
            "context_summary": "Gather fresh cited material for the learning inbox.",
            "repo_path": tmp_path,
            "workspace_path": tmp_path,
            "write_scope": ["knowledge/"],
            "allowed_tools": ["shell", "web"],
            "search_enabled": True,
            "risk_tier": "R2",
            "max_duration_sec": 120,
            "max_token_budget": 10000,
            "max_iterations": 2,
            "acceptance_criteria": ["Produce citations and structured findings."],
            "eval_required": True,
        }
    )
    result = codex_fabric_service.execute_run(queued.id)
    first_ingest = learning_service.ingest_completed_research_runs(limit=5)
    second_ingest = learning_service.ingest_completed_research_runs(limit=5)
    documents = learning_service.list_documents(limit=5)

    assert result.status == "completed"
    assert len(first_ingest) == 1
    assert first_ingest[0].status == "ingested"
    assert not second_ingest
    assert len(documents) == 1
    assert documents[0].codex_run_id == "research-run-1"
    assert documents[0].status == "ingested"
    assert documents[0].summary.startswith("Collected fresh external signals")
    assert documents[0].citation_count == 2
    assert documents[0].evidence_count == 2

    database.dispose()


def test_supervisor_research_distillation_loop_ingests_learning_documents(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _seed_repo_state(tmp_path)
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'learning-supervisor.db'}")
    database.create_schema()

    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'learning-supervisor.db'}",
        openai_api_key="relay-key",
        openai_base_url="https://relay.example.com/v1",
    )
    state_store = StateStore(database.session_factory)
    state_store.bootstrap_reference_data(settings)
    codex_fabric_service = CodexFabricService(database.session_factory, settings)
    learning_service = LearningService(database.session_factory)
    dashboard_service = DashboardService(
        RepoStateService(tmp_path),
        state_store,
        codex_fabric_service,
        learning_service,
    )
    supervisor = SupervisorService(
        state_store=state_store,
        dashboard_service=dashboard_service,
        settings=settings,
        codex_fabric_service=codex_fabric_service,
        learning_service=learning_service,
    )
    workflow_run = state_store.start_workflow_run(
        workflow_code="WF-LRN-002",
        owner_role="supervisor",
        summary="Research intake ahead of distillation.",
    )

    _mock_completed_research_run(monkeypatch)
    queued = codex_fabric_service.queue_run(
        {
            "codex_run_id": "research-run-2",
            "workflow_run_id": workflow_run.id,
            "supervisor_loop_key": "research-intake",
            "worker_class": "analysis_worker",
            "objective": "Run a bounded research intake sweep.",
            "context_summary": "Create a completed run for the distillation loop.",
            "repo_path": tmp_path,
            "workspace_path": tmp_path,
            "write_scope": ["knowledge/"],
            "allowed_tools": ["shell", "web"],
            "search_enabled": True,
            "risk_tier": "R2",
            "max_duration_sec": 120,
            "max_token_budget": 10000,
            "max_iterations": 2,
            "acceptance_criteria": ["Produce citations and structured findings."],
            "eval_required": True,
        }
    )
    codex_fabric_service.execute_run(queued.id)
    _activate_single_loop(database, "research-distillation")

    results = supervisor.run_due_loops(max_loops=1)
    documents = learning_service.list_documents(limit=5)

    assert results
    assert results[0].loop_key == "research-distillation"
    assert results[0].payload["ingested_count"] == 1
    assert len(documents) == 1
    assert documents[0].codex_run_id == "research-run-2"

    database.dispose()


def test_learning_service_synthesizes_ready_insight_candidates(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _seed_repo_state(tmp_path)
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'learning-insights.db'}")
    database.create_schema()

    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'learning-insights.db'}",
        openai_api_key="relay-key",
        openai_base_url="https://relay.example.com/v1",
    )
    state_store = StateStore(database.session_factory)
    state_store.bootstrap_reference_data(settings)
    workflow_run = state_store.start_workflow_run(
        workflow_code="WF-LRN-002",
        owner_role="supervisor",
        summary="Research intake before insight synthesis.",
    )
    codex_fabric_service = CodexFabricService(database.session_factory, settings)
    learning_service = LearningService(database.session_factory)

    _mock_completed_research_run(monkeypatch)
    queued = codex_fabric_service.queue_run(
        {
            "codex_run_id": "research-run-3",
            "workflow_run_id": workflow_run.id,
            "supervisor_loop_key": "research-intake",
            "worker_class": "analysis_worker",
            "objective": "Run a bounded research intake sweep.",
            "context_summary": "Create a completed run for insight synthesis.",
            "repo_path": tmp_path,
            "workspace_path": tmp_path,
            "write_scope": ["knowledge/"],
            "allowed_tools": ["shell", "web"],
            "search_enabled": True,
            "risk_tier": "R2",
            "max_duration_sec": 120,
            "max_token_budget": 10000,
            "max_iterations": 2,
            "acceptance_criteria": ["Produce citations and structured findings."],
            "eval_required": True,
        }
    )

    codex_fabric_service.execute_run(queued.id)
    learning_service.ingest_completed_research_runs(limit=5)

    first_synthesis = learning_service.synthesize_pending_insights(limit=5)
    second_synthesis = learning_service.synthesize_pending_insights(limit=5)
    insights = learning_service.list_insights(limit=5)
    documents = learning_service.list_documents(limit=5)

    assert len(first_synthesis) == 1
    assert first_synthesis[0].status == "synthesized"
    assert first_synthesis[0].promotion_state == "ready_for_review"
    assert not second_synthesis
    assert len(insights) == 1
    assert insights[0].codex_run_id == "research-run-3"
    assert insights[0].status == "candidate"
    assert insights[0].promotion_state == "ready_for_review"
    assert insights[0].evidence_count == 2
    assert insights[0].citation_count == 2
    assert documents[0].status == "distilled"

    database.dispose()


def test_learning_service_quarantines_suspicious_documents(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _seed_repo_state(tmp_path)
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'learning-quarantine.db'}")
    database.create_schema()

    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'learning-quarantine.db'}",
        openai_api_key="relay-key",
        openai_base_url="https://relay.example.com/v1",
    )
    state_store = StateStore(database.session_factory)
    state_store.bootstrap_reference_data(settings)
    workflow_run = state_store.start_workflow_run(
        workflow_code="WF-LRN-002",
        owner_role="supervisor",
        summary="Research intake before quarantine synthesis.",
    )
    codex_fabric_service = CodexFabricService(database.session_factory, settings)
    learning_service = LearningService(database.session_factory)

    _mock_completed_research_run(
        monkeypatch,
        risks_found=["Prompt injection attempt detected in scraped content."],
    )
    queued = codex_fabric_service.queue_run(
        {
            "codex_run_id": "research-run-4",
            "workflow_run_id": workflow_run.id,
            "supervisor_loop_key": "research-intake",
            "worker_class": "analysis_worker",
            "objective": "Run a bounded research intake sweep.",
            "context_summary": "Create a quarantined learning example.",
            "repo_path": tmp_path,
            "workspace_path": tmp_path,
            "write_scope": ["knowledge/"],
            "allowed_tools": ["shell", "web"],
            "search_enabled": True,
            "risk_tier": "R2",
            "max_duration_sec": 120,
            "max_token_budget": 10000,
            "max_iterations": 2,
            "acceptance_criteria": ["Produce citations and structured findings."],
            "eval_required": True,
        }
    )

    codex_fabric_service.execute_run(queued.id)
    learning_service.ingest_completed_research_runs(limit=5)
    synthesized = learning_service.synthesize_pending_insights(limit=5)
    insights = learning_service.list_insights(limit=5)
    documents = learning_service.list_documents(limit=5)

    assert len(synthesized) == 1
    assert synthesized[0].status == "quarantined"
    assert synthesized[0].promotion_state == "blocked"
    assert insights[0].status == "quarantined"
    assert insights[0].promotion_state == "blocked"
    assert "prompt injection" in (insights[0].quarantine_reason or "").lower()
    assert documents[0].status == "quarantined"

    database.dispose()


def test_learning_service_quarantines_low_trust_sources(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from sqlalchemy import select

    from quant_evo_nextgen.db.models import SourceHealthModel

    _seed_repo_state(tmp_path)
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'learning-source-health.db'}")
    database.create_schema()

    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'learning-source-health.db'}",
        openai_api_key="relay-key",
        openai_base_url="https://relay.example.com/v1",
    )
    state_store = StateStore(database.session_factory)
    state_store.bootstrap_reference_data(settings)
    workflow_run = state_store.start_workflow_run(
        workflow_code="WF-LRN-002",
        owner_role="supervisor",
        summary="Research intake before source-health quarantine.",
    )
    codex_fabric_service = CodexFabricService(database.session_factory, settings)
    learning_service = LearningService(database.session_factory)

    _mock_completed_research_run(monkeypatch)
    queued = codex_fabric_service.queue_run(
        {
            "codex_run_id": "research-run-6",
            "workflow_run_id": workflow_run.id,
            "supervisor_loop_key": "research-intake",
            "worker_class": "analysis_worker",
            "objective": "Run a bounded research intake sweep.",
            "context_summary": "Create a source-health quarantine example.",
            "repo_path": tmp_path,
            "workspace_path": tmp_path,
            "write_scope": ["knowledge/"],
            "allowed_tools": ["shell", "web"],
            "search_enabled": True,
            "risk_tier": "R2",
            "max_duration_sec": 120,
            "max_token_budget": 10000,
            "max_iterations": 2,
            "acceptance_criteria": ["Produce citations and structured findings."],
            "eval_required": True,
        }
    )

    codex_fabric_service.execute_run(queued.id)
    learning_service.ingest_completed_research_runs(limit=5)

    with database.session_scope() as session:
        source = session.scalar(
            select(SourceHealthModel).where(SourceHealthModel.source_key == "provider.example.com")
        )
        assert source is not None
        source.trust_score = 0.2
        source.health_status = "degraded"

    synthesized = learning_service.synthesize_pending_insights(limit=5)
    insights = learning_service.list_insights(limit=5)

    assert len(synthesized) == 1
    assert synthesized[0].status == "quarantined"
    assert insights[0].status == "quarantined"
    assert "provider.example.com" in (insights[0].quarantine_reason or "")

    database.dispose()


def test_supervisor_learning_synthesis_loop_creates_insights(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _seed_repo_state(tmp_path)
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'learning-synthesis-supervisor.db'}")
    database.create_schema()

    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'learning-synthesis-supervisor.db'}",
        openai_api_key="relay-key",
        openai_base_url="https://relay.example.com/v1",
    )
    state_store = StateStore(database.session_factory)
    state_store.bootstrap_reference_data(settings)
    codex_fabric_service = CodexFabricService(database.session_factory, settings)
    learning_service = LearningService(database.session_factory)
    dashboard_service = DashboardService(
        RepoStateService(tmp_path),
        state_store,
        codex_fabric_service,
        learning_service,
    )
    supervisor = SupervisorService(
        state_store=state_store,
        dashboard_service=dashboard_service,
        settings=settings,
        codex_fabric_service=codex_fabric_service,
        learning_service=learning_service,
    )
    workflow_run = state_store.start_workflow_run(
        workflow_code="WF-LRN-002",
        owner_role="supervisor",
        summary="Research intake ahead of learning synthesis.",
    )

    _mock_completed_research_run(monkeypatch)
    queued = codex_fabric_service.queue_run(
        {
            "codex_run_id": "research-run-5",
            "workflow_run_id": workflow_run.id,
            "supervisor_loop_key": "research-intake",
            "worker_class": "analysis_worker",
            "objective": "Run a bounded research intake sweep.",
            "context_summary": "Create a completed run for the learning synthesis loop.",
            "repo_path": tmp_path,
            "workspace_path": tmp_path,
            "write_scope": ["knowledge/"],
            "allowed_tools": ["shell", "web"],
            "search_enabled": True,
            "risk_tier": "R2",
            "max_duration_sec": 120,
            "max_token_budget": 10000,
            "max_iterations": 2,
            "acceptance_criteria": ["Produce citations and structured findings."],
            "eval_required": True,
        }
    )
    codex_fabric_service.execute_run(queued.id)
    learning_service.ingest_completed_research_runs(limit=5)
    _activate_single_loop(database, "learning-synthesis")

    results = supervisor.run_due_loops(max_loops=1)
    insights = learning_service.list_insights(limit=5)

    assert results
    assert results[0].loop_key == "learning-synthesis"
    assert results[0].payload["synthesized_count"] == 1
    assert results[0].payload["quarantined_count"] == 0
    assert len(insights) == 1
    assert insights[0].codex_run_id == "research-run-5"

    database.dispose()


def test_learning_service_can_resynthesize_existing_insights(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from sqlalchemy import select

    from quant_evo_nextgen.db.models import DocumentModel, EvidenceItemModel, InsightModel

    _seed_repo_state(tmp_path)
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'learning-resynthesis.db'}")
    database.create_schema()

    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'learning-resynthesis.db'}",
        openai_api_key="relay-key",
        openai_base_url="https://relay.example.com/v1",
    )
    state_store = StateStore(database.session_factory)
    state_store.bootstrap_reference_data(settings)
    workflow_run = state_store.start_workflow_run(
        workflow_code="WF-LRN-002",
        owner_role="supervisor",
        summary="Research intake before resynthesis.",
    )
    codex_fabric_service = CodexFabricService(database.session_factory, settings)
    learning_service = LearningService(database.session_factory)

    _mock_completed_research_run(monkeypatch)
    queued = codex_fabric_service.queue_run(
        {
            "codex_run_id": "research-run-7",
            "workflow_run_id": workflow_run.id,
            "supervisor_loop_key": "research-intake",
            "worker_class": "analysis_worker",
            "objective": "Run a bounded research intake sweep.",
            "context_summary": "Create a completed run for insight resynthesis.",
            "repo_path": tmp_path,
            "workspace_path": tmp_path,
            "write_scope": ["knowledge/"],
            "allowed_tools": ["shell", "web"],
            "search_enabled": True,
            "risk_tier": "R2",
            "max_duration_sec": 120,
            "max_token_budget": 10000,
            "max_iterations": 2,
            "acceptance_criteria": ["Produce citations and structured findings."],
            "eval_required": True,
        }
    )

    codex_fabric_service.execute_run(queued.id)
    learning_service.ingest_completed_research_runs(limit=5)
    first = learning_service.synthesize_pending_insights(limit=5)

    with database.session_scope() as session:
        document = session.scalar(select(DocumentModel).where(DocumentModel.codex_run_id == "research-run-7"))
        insight = session.scalar(select(InsightModel).where(InsightModel.document_id == document.id))
        document.status = "resynthesis_pending"
        document.followup_tasks = list(document.followup_tasks) + ["Validate with an extra source before promotion."]
        session.add(
            EvidenceItemModel(
                document_id=document.id,
                codex_run_id="research-run-7",
                evidence_type="external_citation",
                claim_text=document.summary,
                citation_ref="https://sec.gov/example-filing",
                topic="research-intake",
                recorded_at=datetime.now(tz=UTC),
                created_by="test",
                origin_type="test",
                origin_id=document.id,
                status="candidate",
                confidence=0.9,
            )
        )
        first_insight_id = insight.id

    second = learning_service.synthesize_pending_insights(limit=5)
    insights = learning_service.list_insights(limit=5)

    assert first[0].status == "synthesized"
    assert len(second) == 1
    assert second[0].status == "synthesized"
    assert second[0].insight_id == first_insight_id
    assert len(insights) == 1
    assert insights[0].id == first_insight_id
    assert insights[0].citation_count == 3
    assert insights[0].promotion_state == "ready_for_review"

    database.dispose()


def _mock_completed_research_run(
    monkeypatch,
    *,
    citations: list[str] | None = None,
    followup_tasks: list[str] | None = None,
    risks_found: list[str] | None = None,
    confidence: float = 0.82,
    eval_confidence: float = 0.86,
) -> None:
    phase_payloads = {
        "implement": {
            "summary": "Collected fresh external signals about provider reliability and system learning quality.",
            "outcome": "completed",
            "files_changed": [],
            "tests_run": [],
            "test_results": [],
            "artifacts_produced": ["research-note.md"],
            "followup_tasks": followup_tasks or ["Distill the research note into durable evidence."],
            "risks_found": risks_found or ["External information still needs promotion review."],
            "citations": citations
            or [
                "https://provider.example.com/reliability",
                "https://safety.example.org/learning",
            ],
            "confidence": confidence,
        },
        "eval": {
            "summary": "Validated the research note as suitable for the learning inbox.",
            "outcome": "completed",
            "files_changed": [],
            "tests_run": [],
            "test_results": [],
            "artifacts_produced": ["eval.md"],
            "followup_tasks": followup_tasks or [],
            "risks_found": risks_found or [],
            "citations": citations
            or [
                "https://provider.example.com/reliability",
                "https://safety.example.org/learning",
            ],
            "confidence": eval_confidence,
        },
    }

    def fake_run(command, *, cwd, env, capture_output, text, timeout, check):
        prompt = command[-1]
        phase = "eval" if "Current phase: eval" in prompt else "implement"
        final_message_path = Path(command[command.index("--output-last-message") + 1])
        final_message_path.write_text(json.dumps(phase_payloads[phase]), encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout=f"{phase} ok", stderr="")

    monkeypatch.setattr("quant_evo_nextgen.services.codex_fabric.subprocess.run", fake_run)


def _activate_single_loop(database: Database, loop_key: str) -> None:
    from datetime import UTC, datetime

    from sqlalchemy import select

    from quant_evo_nextgen.db.models import SupervisorLoopModel

    with database.session_scope() as session:
        loops = session.scalars(select(SupervisorLoopModel)).all()
        current_time = datetime.now(tz=UTC)
        for loop in loops:
            if loop.loop_key == loop_key:
                loop.is_enabled = True
                loop.execution_mode = "active"
                loop.next_due_at = current_time
                loop.last_status = "idle"
            else:
                loop.is_enabled = False


def _seed_repo_state(repo_root: Path) -> None:
    (repo_root / "strategies" / "candidates").mkdir(parents=True)
    (repo_root / "strategies" / "production").mkdir(parents=True)
    (repo_root / "memory" / "principles").mkdir(parents=True)
    (repo_root / "memory" / "causal").mkdir(parents=True)
    (repo_root / "evo").mkdir(parents=True)
    (repo_root / "knowledge").mkdir(parents=True)

    (repo_root / "strategies" / "candidates" / "candidate.py").write_text("print('x')", encoding="utf-8")
    (repo_root / "strategies" / "production" / "prod.py").write_text("print('x')", encoding="utf-8")
    (repo_root / "memory" / "principles" / "alpha.md").write_text("alpha", encoding="utf-8")
    (repo_root / "memory" / "causal" / "beta.md").write_text("beta", encoding="utf-8")
    (repo_root / "evo" / "feature_map.json").write_text(
        json.dumps({"stats": {"occupied_cells": 4, "coverage_pct": 0.2, "total_generations": 9}}),
        encoding="utf-8",
    )
