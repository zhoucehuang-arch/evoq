import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import select

from quant_evo_nextgen.config import Settings
from quant_evo_nextgen.services.broker import BrokerAccountState, BrokerSyncRequest, BrokerSyncResult
from quant_evo_nextgen.db.models import CodexRunModel, EvolutionImprovementProposalModel, SupervisorLoopModel
from quant_evo_nextgen.db.session import Database
from quant_evo_nextgen.services.codex_fabric import CodexFabricService
from quant_evo_nextgen.services.dashboard import DashboardService
from quant_evo_nextgen.services.evolution import EvolutionService
from quant_evo_nextgen.services.execution import ExecutionService
from quant_evo_nextgen.services.repo_state import RepoStateService
from quant_evo_nextgen.services.state_store import StateStore
from quant_evo_nextgen.services.supervisor import SupervisorService


def test_supervisor_runs_due_loops_and_records_heartbeat(tmp_path: Path) -> None:
    _seed_repo_state(tmp_path)
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'supervisor.db'}")
    database.create_schema()

    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'supervisor.db'}",
        db_bootstrap_on_start=True,
    )
    state_store = StateStore(database.session_factory)
    state_store.bootstrap_reference_data(settings)
    dashboard_service = DashboardService(RepoStateService(tmp_path), state_store)
    supervisor = SupervisorService(
        state_store=state_store,
        dashboard_service=dashboard_service,
        settings=settings,
    )

    results = supervisor.run_due_loops(max_loops=2)
    runtime = state_store.get_runtime_snapshot()
    loops = state_store.list_supervisor_loops(enabled_only=True)

    assert results
    assert any(result.loop_key == "governance-heartbeat" for result in results)
    assert runtime.last_heartbeat_at is not None
    assert any(loop.loop_key == "governance-heartbeat" and loop.last_status == "completed" for loop in loops)


def test_supervisor_queues_codex_run_for_research_intake_loop(tmp_path: Path) -> None:
    _seed_repo_state(tmp_path)
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'supervisor-codex.db'}")
    database.create_schema()

    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'supervisor-codex.db'}",
        db_bootstrap_on_start=True,
        openai_api_key="relay-key",
        openai_base_url="https://relay.example.com/v1",
    )
    state_store = StateStore(database.session_factory)
    state_store.bootstrap_reference_data(settings)
    codex_fabric_service = CodexFabricService(database.session_factory, settings)
    dashboard_service = DashboardService(RepoStateService(tmp_path), state_store, codex_fabric_service)
    supervisor = SupervisorService(
        state_store=state_store,
        dashboard_service=dashboard_service,
        settings=settings,
        codex_fabric_service=codex_fabric_service,
    )
    _activate_single_loop(database, "research-intake")

    results = supervisor.run_due_loops(max_loops=1)
    codex_runs = codex_fabric_service.list_runs(limit=5)

    assert results
    assert results[0].loop_key == "research-intake"
    assert results[0].payload["status"] == "queued"
    assert len(codex_runs) == 1
    assert codex_runs[0].supervisor_loop_key == "research-intake"
    assert codex_runs[0].workflow_run_id == results[0].workflow_run_id


def test_supervisor_research_intake_includes_cn_market_context(tmp_path: Path) -> None:
    _seed_repo_state(tmp_path)
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'supervisor-cn-research.db'}")
    database.create_schema()

    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'supervisor-cn-research.db'}",
        db_bootstrap_on_start=True,
        deployment_market_mode="cn",
        market_calendar="XSHG",
        market_timezone="Asia/Shanghai",
        openai_api_key="relay-key",
        openai_base_url="https://relay.example.com/v1",
    )
    state_store = StateStore(database.session_factory)
    state_store.bootstrap_reference_data(settings)
    codex_fabric_service = CodexFabricService(database.session_factory, settings)
    dashboard_service = DashboardService(RepoStateService(tmp_path), state_store, codex_fabric_service)
    supervisor = SupervisorService(
        state_store=state_store,
        dashboard_service=dashboard_service,
        settings=settings,
        codex_fabric_service=codex_fabric_service,
    )
    _activate_single_loop(database, "research-intake")

    supervisor.run_due_loops(max_loops=1)

    with database.session_scope() as session:
        run = session.scalar(select(CodexRunModel).where(CodexRunModel.supervisor_loop_key == "research-intake"))
        assert run is not None
        assert "deployment_market_mode=cn" in run.context_summary
        assert "active_sleeves=cn_equities" in run.context_summary
        assert "AKShare" in str(run.request_payload.get("prompt_appendix"))
        assert "Do not propose US options" in str(run.request_payload.get("prompt_appendix"))


def test_supervisor_dedupes_active_codex_runs_for_same_loop(tmp_path: Path) -> None:
    _seed_repo_state(tmp_path)
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'supervisor-codex-dedupe.db'}")
    database.create_schema()

    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'supervisor-codex-dedupe.db'}",
        db_bootstrap_on_start=True,
        openai_api_key="relay-key",
        openai_base_url="https://relay.example.com/v1",
    )
    state_store = StateStore(database.session_factory)
    state_store.bootstrap_reference_data(settings)
    codex_fabric_service = CodexFabricService(database.session_factory, settings)
    dashboard_service = DashboardService(RepoStateService(tmp_path), state_store, codex_fabric_service)
    supervisor = SupervisorService(
        state_store=state_store,
        dashboard_service=dashboard_service,
        settings=settings,
        codex_fabric_service=codex_fabric_service,
    )
    _activate_single_loop(database, "research-intake")

    first_results = supervisor.run_due_loops(max_loops=1)
    _activate_single_loop(database, "research-intake")
    second_results = supervisor.run_due_loops(max_loops=1)
    active_runs = codex_fabric_service.list_runs(
        statuses=["queued", "booting", "running", "reviewing"],
        supervisor_loop_key="research-intake",
        limit=5,
    )

    assert first_results[0].payload["status"] == "queued"
    assert second_results[0].payload["status"] == "skipped"
    assert second_results[0].payload["existing_codex_run_id"] == first_results[0].payload["codex_run_id"]
    assert len(active_runs) == 1


def test_supervisor_market_session_guard_records_execution_state(tmp_path: Path) -> None:
    _seed_repo_state(tmp_path)
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'supervisor-session-guard.db'}")
    database.create_schema()

    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'supervisor-session-guard.db'}",
        db_bootstrap_on_start=True,
        market_calendar="CRYPTO_24X7",
        market_timezone="UTC",
    )
    state_store = StateStore(database.session_factory)
    state_store.bootstrap_reference_data(settings)
    execution_service = ExecutionService(database.session_factory, settings)
    dashboard_service = DashboardService(RepoStateService(tmp_path), state_store, execution_service=execution_service)
    supervisor = SupervisorService(
        state_store=state_store,
        dashboard_service=dashboard_service,
        settings=settings,
        execution_service=execution_service,
    )
    _activate_single_loop(database, "market-session-guard")

    results = supervisor.run_due_loops(max_loops=1)
    market_states = execution_service.list_market_session_states(limit=5)

    assert results
    assert results[0].loop_key == "market-session-guard"
    assert results[0].payload["status"] == "completed"
    assert market_states[0].market_calendar == "CRYPTO_24X7"
    assert market_states[0].trading_allowed is True


def test_supervisor_strategy_evaluation_includes_market_scope(tmp_path: Path) -> None:
    _seed_repo_state(tmp_path)
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'supervisor-cn-strategy.db'}")
    database.create_schema()

    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'supervisor-cn-strategy.db'}",
        db_bootstrap_on_start=True,
        deployment_market_mode="cn",
        market_calendar="XSHG",
        market_timezone="Asia/Shanghai",
        openai_api_key="relay-key",
        openai_base_url="https://relay.example.com/v1",
    )
    state_store = StateStore(database.session_factory)
    state_store.bootstrap_reference_data(settings)
    codex_fabric_service = CodexFabricService(database.session_factory, settings)
    dashboard_service = DashboardService(RepoStateService(tmp_path), state_store, codex_fabric_service)
    supervisor = SupervisorService(
        state_store=state_store,
        dashboard_service=dashboard_service,
        settings=settings,
        codex_fabric_service=codex_fabric_service,
    )
    _activate_single_loop(database, "strategy-evaluation")

    results = supervisor.run_due_loops(max_loops=1)

    assert results
    assert results[0].payload["status"] == "queued"

    with database.session_scope() as session:
        run = session.scalar(select(CodexRunModel).where(CodexRunModel.supervisor_loop_key == "strategy-evaluation"))
        assert run is not None
        assert "deployment_market_mode=cn" in run.context_summary
        assert "active_sleeves=cn_equities" in run.context_summary
        assert "outside that deployment scope" in str(run.request_payload.get("prompt_appendix"))


def test_supervisor_broker_state_sync_records_external_snapshot(tmp_path: Path) -> None:
    _seed_repo_state(tmp_path)
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'supervisor-broker-sync.db'}")
    database.create_schema()

    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'supervisor-broker-sync.db'}",
        db_bootstrap_on_start=True,
        default_broker_adapter="alpaca",
        default_broker_provider_key="alpaca-paper",
        default_broker_account_ref="paper-main",
        default_broker_environment="paper",
    )
    state_store = StateStore(database.session_factory)
    state_store.bootstrap_reference_data(settings)
    execution_service = ExecutionService(
        database.session_factory,
        settings,
        adapters={"alpaca": ScriptedSyncBrokerAdapter()},
    )
    dashboard_service = DashboardService(RepoStateService(tmp_path), state_store, execution_service=execution_service)
    supervisor = SupervisorService(
        state_store=state_store,
        dashboard_service=dashboard_service,
        settings=settings,
        execution_service=execution_service,
    )
    _activate_single_loop(database, "broker-state-sync")

    results = supervisor.run_due_loops(max_loops=1)
    sync_runs = execution_service.list_broker_sync_runs(limit=5, provider_key="alpaca-paper")

    assert results
    assert results[0].loop_key == "broker-state-sync"
    assert results[0].payload["status"] == "completed"
    assert sync_runs[0].provider_key == "alpaca-paper"
    assert sync_runs[0].status == "synchronized"


def test_supervisor_syncs_completed_codex_runs_into_evolution_proposals(tmp_path: Path) -> None:
    _seed_repo_state(tmp_path)
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'supervisor-evolution-sync.db'}")
    database.create_schema()

    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'supervisor-evolution-sync.db'}",
        db_bootstrap_on_start=True,
    )
    state_store = StateStore(database.session_factory)
    state_store.bootstrap_reference_data(settings)
    evolution_service = EvolutionService(database.session_factory)
    dashboard_service = DashboardService(RepoStateService(tmp_path), state_store, evolution_service=evolution_service)
    supervisor = SupervisorService(
        state_store=state_store,
        dashboard_service=dashboard_service,
        settings=settings,
        evolution_service=evolution_service,
    )

    with database.session_scope() as session:
        session.add(
            CodexRunModel(
                id="completed-strategy-run",
                workflow_run_id="wf-strategy-1",
                supervisor_loop_key="strategy-evaluation",
                worker_class="strategy_worker",
                execution_mode="local_exec",
                strategy_mode="ralph_style",
                objective="Evaluate the next governed strategy improvement.",
                context_summary="Strategy evaluation context.",
                repo_path=str(tmp_path),
                workspace_path=str(tmp_path),
                write_scope=["strategies/"],
                allowed_tools=["shell"],
                search_enabled=False,
                risk_tier="R3",
                max_duration_sec=300,
                max_token_budget=50000,
                max_iterations=2,
                review_required=True,
                eval_required=True,
                request_payload={},
                result_payload={
                    "structured_output": {
                        "summary": "Promote the better paper candidate into a bounded shadow lane.",
                        "outcome": "completed",
                        "files_changed": ["strategies/candidates/mean_reversion.py"],
                        "tests_run": ["py -m pytest tests/test_strategy_lab.py"],
                        "test_results": ["passed"],
                        "artifacts_produced": ["strategy_eval.md"],
                        "followup_tasks": ["Schedule a shadow canary."],
                        "risks_found": ["Needs explicit owner review before production."],
                        "citations": [],
                        "confidence": 0.81,
                    }
                },
                queued_at=datetime.now(tz=UTC),
                completed_at=datetime.now(tz=UTC),
                created_by="supervisor",
                origin_type="supervisor-loop",
                origin_id="strategy-evaluation",
                status="completed",
            )
        )

    _activate_single_loop(database, "evolution-governance-sync")
    results = supervisor.run_due_loops(max_loops=1)
    proposals = evolution_service.list_improvement_proposals(limit=5)
    canary_runs = evolution_service.list_canary_runs(limit=5)

    assert results
    assert results[0].loop_key == "evolution-governance-sync"
    assert results[0].payload["created_count"] == 1
    assert len(results[0].payload["auto_canary_ids"]) == 1
    assert proposals[0].codex_run_id == "completed-strategy-run"
    assert proposals[0].proposal_state == "shadow_passed"
    assert proposals[0].proposal_kind == "strategy_improvement"
    assert canary_runs[0].status == "passed"


def test_supervisor_capability_review_opens_recovery_goal_and_queues_replan(tmp_path: Path) -> None:
    _seed_repo_state(tmp_path)
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'supervisor-capability-review.db'}")
    database.create_schema()

    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'supervisor-capability-review.db'}",
        db_bootstrap_on_start=True,
        openai_api_key="relay-key",
        openai_base_url="https://relay.example.com/v1",
    )
    state_store = StateStore(database.session_factory)
    state_store.bootstrap_reference_data(settings)
    codex_fabric_service = CodexFabricService(database.session_factory, settings)
    evolution_service = EvolutionService(database.session_factory)
    dashboard_service = DashboardService(
        RepoStateService(tmp_path),
        state_store,
        codex_fabric_service,
        evolution_service=evolution_service,
    )
    supervisor = SupervisorService(
        state_store=state_store,
        dashboard_service=dashboard_service,
        settings=settings,
        codex_fabric_service=codex_fabric_service,
        evolution_service=evolution_service,
    )
    _insert_completed_codex_runs(
        database=database,
        repo_root=tmp_path,
        supervisor_loop_key="strategy-evaluation",
        count=3,
    )
    _activate_single_loop(database, "capability-review")

    results = supervisor.run_due_loops(max_loops=1)
    goals = state_store.list_goals(statuses=("active",))
    incidents = state_store.list_incidents(open_only=True)
    queued_runs = codex_fabric_service.list_runs(supervisor_loop_key="capability-review", limit=5)

    assert results
    assert results[0].loop_key == "capability-review"
    assert results[0].payload["stall_state"] == "warning"
    assert results[0].payload["created_goal_id"] is not None
    assert results[0].payload["created_incident_id"] is None
    assert results[0].payload["queued_replan"]["status"] == "queued"
    assert any(goal.title == "Evolution anti-stall recovery" for goal in goals)
    assert not incidents
    assert queued_runs[0].status == "queued"


def test_supervisor_capability_review_creates_incident_for_critical_stall(tmp_path: Path) -> None:
    _seed_repo_state(tmp_path)
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'supervisor-capability-critical.db'}")
    database.create_schema()

    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'supervisor-capability-critical.db'}",
        db_bootstrap_on_start=True,
        openai_api_key="relay-key",
        openai_base_url="https://relay.example.com/v1",
    )
    state_store = StateStore(database.session_factory)
    state_store.bootstrap_reference_data(settings)
    codex_fabric_service = CodexFabricService(database.session_factory, settings)
    evolution_service = EvolutionService(database.session_factory)
    dashboard_service = DashboardService(
        RepoStateService(tmp_path),
        state_store,
        codex_fabric_service,
        evolution_service=evolution_service,
    )
    supervisor = SupervisorService(
        state_store=state_store,
        dashboard_service=dashboard_service,
        settings=settings,
        codex_fabric_service=codex_fabric_service,
        evolution_service=evolution_service,
    )

    first = evolution_service.create_improvement_proposal(
        {
            "title": "Blocked review path 1",
            "summary": "Repeatedly blocked proposal.",
            "target_surface": "system",
            "proposal_kind": "workflow_tuning",
            "change_scope": ["docs/next-gen/"],
            "proposal_state": "blocked",
            "created_by": "tester",
        }
    )
    second = evolution_service.create_improvement_proposal(
        {
            "title": "Blocked review path 2",
            "summary": "Repeatedly rolled back proposal.",
            "target_surface": "system",
            "proposal_kind": "workflow_tuning",
            "change_scope": ["docs/next-gen/"],
            "proposal_state": "rolled_back",
            "created_by": "tester",
        }
    )
    with database.session_scope() as session:
        for proposal_id in (first.id, second.id):
            proposal = session.get(EvolutionImprovementProposalModel, proposal_id)
            assert proposal is not None
            proposal.created_at = datetime.now(tz=UTC) - timedelta(hours=2)

    _activate_single_loop(database, "capability-review")
    results = supervisor.run_due_loops(max_loops=1)
    goals = state_store.list_goals(statuses=("active",))
    incidents = state_store.list_incidents(open_only=True)
    queued_runs = codex_fabric_service.list_runs(supervisor_loop_key="capability-review", limit=5)

    assert results
    assert results[0].payload["stall_state"] == "critical"
    assert results[0].payload["created_goal_id"] is not None
    assert results[0].payload["created_incident_id"] is not None
    assert results[0].payload["queued_replan"]["status"] == "queued"
    assert any(goal.title == "Evolution anti-stall recovery" for goal in goals)
    assert any(incident.title == "Evolution anti-stall escalation" for incident in incidents)
    assert queued_runs[0].status == "queued"


def _activate_single_loop(database: Database, loop_key: str) -> None:
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

    (repo_root / "strategies" / "candidates" / "candidate.py").write_text("print('x')", encoding="utf-8")
    (repo_root / "strategies" / "production" / "prod.py").write_text("print('x')", encoding="utf-8")
    (repo_root / "memory" / "principles" / "alpha.md").write_text("alpha", encoding="utf-8")
    (repo_root / "memory" / "causal" / "beta.md").write_text("beta", encoding="utf-8")
    (repo_root / "evo" / "feature_map.json").write_text(
        json.dumps({"stats": {"occupied_cells": 4, "coverage_pct": 0.2, "total_generations": 9}}),
        encoding="utf-8",
    )


def _insert_completed_codex_runs(
    *,
    database: Database,
    repo_root: Path,
    supervisor_loop_key: str,
    count: int,
) -> None:
    current_time = datetime.now(tz=UTC)
    with database.session_scope() as session:
        for index in range(count):
            session.add(
                CodexRunModel(
                    id=f"{supervisor_loop_key}-fixture-{index}",
                    workflow_run_id=f"wf-{supervisor_loop_key}-{index}",
                    supervisor_loop_key=supervisor_loop_key,
                    worker_class="analysis_worker",
                    execution_mode="local_exec",
                    strategy_mode="ralph_style",
                    objective="Bounded reflection cycle.",
                    context_summary="Capability review fixture.",
                    repo_path=str(repo_root),
                    workspace_path=str(repo_root),
                    write_scope=["docs/next-gen/"],
                    allowed_tools=["shell"],
                    search_enabled=False,
                    risk_tier="R2",
                    max_duration_sec=300,
                    max_token_budget=45000,
                    max_iterations=2,
                    review_required=True,
                    eval_required=True,
                    request_payload={},
                    result_payload={"structured_output": {"outcome": "completed"}},
                    queued_at=current_time - timedelta(hours=6 - index),
                    started_at=current_time - timedelta(hours=5 - index),
                    completed_at=current_time - timedelta(hours=4 - index),
                    created_by="tester",
                    origin_type="test",
                    origin_id=supervisor_loop_key,
                    status="completed",
                )
            )


class ScriptedSyncBrokerAdapter:
    adapter_key = "alpaca"

    def execute_order(self, request, current_position):  # pragma: no cover - not used in this test
        raise AssertionError("execute_order should not be called in broker sync supervisor test")

    def sync_state(self, request: BrokerSyncRequest) -> BrokerSyncResult:
        return BrokerSyncResult(
            account_state=BrokerAccountState(
                provider_key=request.provider_key,
                account_ref=request.account_ref,
                environment=request.environment,
                equity=10050.0,
                cash=8050.0,
                buying_power=15000.0,
                gross_exposure=2000.0,
                net_exposure=2000.0,
                positions_count=0,
                open_orders_count=0,
                source_captured_at=datetime.now(tz=UTC),
                source_age_seconds=0,
                raw_payload={"adapter": self.adapter_key},
            ),
            orders=[],
            positions=[],
            notes=[],
            raw_payload={"adapter": self.adapter_key},
        )

    def cancel_order(self, request, current_order):  # pragma: no cover - not used in this test
        raise AssertionError("cancel_order should not be called in broker sync supervisor test")

    def replace_order(self, request, current_order):  # pragma: no cover - not used in this test
        raise AssertionError("replace_order should not be called in broker sync supervisor test")
