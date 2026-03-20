from datetime import UTC, datetime, timedelta
from pathlib import Path

from quant_evo_nextgen.config import Settings
from quant_evo_nextgen.db.models import CodexRunModel, EvolutionImprovementProposalModel
from quant_evo_nextgen.db.session import Database
from quant_evo_nextgen.services.codex_fabric import CodexFabricService
from quant_evo_nextgen.services.evolution import EvolutionService
from quant_evo_nextgen.services.evolution_capability import EvolutionCapabilityService
from quant_evo_nextgen.services.state_store import StateStore


def test_evolution_capability_review_does_not_false_positive_stall_on_bootstrap(tmp_path: Path) -> None:
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'evolution-capability-bootstrap.db'}")
    database.create_schema()
    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'evolution-capability-bootstrap.db'}",
        db_bootstrap_on_start=True,
    )
    state_store = StateStore(database.session_factory)
    state_store.bootstrap_reference_data(settings)

    review = EvolutionCapabilityService(state_store=state_store).build_review(
        now=datetime(2026, 3, 20, 12, 0, tzinfo=UTC)
    )

    assert review.stall_state == "healthy"
    assert review.stall_summary is None
    assert review.should_queue_replan is False
    assert len(review.scorecards) == 5
    assert {scorecard.capability_key for scorecard in review.scorecards} == {
        "research_continuity",
        "learning_quality",
        "strategy_discipline",
        "governed_evolution",
        "capital_guardrails",
    }


def test_evolution_capability_review_warns_when_reflection_runs_produce_no_proposals(tmp_path: Path) -> None:
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'evolution-capability-warning.db'}")
    database.create_schema()
    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'evolution-capability-warning.db'}",
        db_bootstrap_on_start=True,
        openai_api_key="relay-key",
        openai_base_url="https://relay.example.com/v1",
    )
    state_store = StateStore(database.session_factory)
    state_store.bootstrap_reference_data(settings)
    fixed_now = datetime(2026, 3, 20, 12, 0, tzinfo=UTC)
    _insert_completed_codex_runs(
        database=database,
        repo_root=tmp_path,
        now=fixed_now,
        count=3,
        supervisor_loop_key="strategy-evaluation",
    )

    review = EvolutionCapabilityService(
        state_store=state_store,
        evolution_service=EvolutionService(database.session_factory),
        codex_fabric_service=CodexFabricService(database.session_factory, settings),
    ).build_review(now=fixed_now)

    assert review.stall_state == "warning"
    assert review.should_queue_replan is True
    assert review.stall_summary is not None
    assert "Multiple bounded reflection runs" in review.stall_summary
    assert review.capability_gaps[0].gap_key == "evolution-stall"
    assert review.capability_gaps[0].severity == "warn"


def test_evolution_capability_review_marks_repeated_blocked_proposals_critical(tmp_path: Path) -> None:
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'evolution-capability-critical.db'}")
    database.create_schema()
    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'evolution-capability-critical.db'}",
        db_bootstrap_on_start=True,
    )
    state_store = StateStore(database.session_factory)
    state_store.bootstrap_reference_data(settings)
    evolution_service = EvolutionService(database.session_factory)
    fixed_now = datetime(2026, 3, 20, 12, 0, tzinfo=UTC)

    first = evolution_service.create_improvement_proposal(
        {
            "title": "Blocked improvement path 1",
            "summary": "A repeatedly blocked proposal.",
            "target_surface": "system",
            "proposal_kind": "workflow_tuning",
            "change_scope": ["docs/next-gen/"],
            "expected_benefit": {"confidence": 0.51},
            "evaluation_summary": {"tests_run": []},
            "rollback_plan": {"action": "restore_previous_state"},
            "proposal_state": "blocked",
            "created_by": "tester",
        }
    )
    second = evolution_service.create_improvement_proposal(
        {
            "title": "Blocked improvement path 2",
            "summary": "A rolled-back proposal without recovery.",
            "target_surface": "system",
            "proposal_kind": "workflow_tuning",
            "change_scope": ["docs/next-gen/"],
            "expected_benefit": {"confidence": 0.48},
            "evaluation_summary": {"tests_run": []},
            "rollback_plan": {"action": "restore_previous_state"},
            "proposal_state": "rolled_back",
            "created_by": "tester",
        }
    )
    with database.session_scope() as session:
        for proposal_id in (first.id, second.id):
            proposal = session.get(EvolutionImprovementProposalModel, proposal_id)
            assert proposal is not None
            proposal.created_at = fixed_now - timedelta(hours=2)
        session.commit()

    review = EvolutionCapabilityService(
        state_store=state_store,
        evolution_service=evolution_service,
    ).build_review(now=fixed_now)

    assert review.stall_state == "critical"
    assert review.should_queue_replan is True
    assert review.stall_summary is not None
    assert "blocking or rolling back" in review.stall_summary
    assert review.capability_gaps[0].gap_key == "evolution-stall"
    assert review.capability_gaps[0].severity == "critical"


def _insert_completed_codex_runs(
    *,
    database: Database,
    repo_root: Path,
    now: datetime,
    count: int,
    supervisor_loop_key: str,
) -> None:
    with database.session_scope() as session:
        for index in range(count):
            session.add(
                CodexRunModel(
                    id=f"{supervisor_loop_key}-completed-{index}",
                    workflow_run_id=f"wf-{supervisor_loop_key}-{index}",
                    supervisor_loop_key=supervisor_loop_key,
                    worker_class="analysis_worker",
                    execution_mode="local_exec",
                    strategy_mode="ralph_style",
                    objective="Bounded reflection cycle.",
                    context_summary="Capability review test fixture.",
                    repo_path=str(repo_root),
                    workspace_path=str(repo_root),
                    write_scope=["docs/next-gen/"],
                    allowed_tools=["shell"],
                    search_enabled=False,
                    risk_tier="R2",
                    max_duration_sec=300,
                    max_token_budget=40000,
                    max_iterations=2,
                    review_required=True,
                    eval_required=True,
                    request_payload={},
                    result_payload={"structured_output": {"outcome": "completed"}},
                    queued_at=now - timedelta(hours=6 - index),
                    started_at=now - timedelta(hours=5 - index),
                    completed_at=now - timedelta(hours=4 - index),
                    created_by="tester",
                    origin_type="test",
                    origin_id=supervisor_loop_key,
                    status="completed",
                )
            )
