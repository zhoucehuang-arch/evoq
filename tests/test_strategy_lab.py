import json
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select

from quant_evo_nextgen.config import Settings
from quant_evo_nextgen.db.models import CodexRunModel, SupervisorLoopModel
from quant_evo_nextgen.db.session import Database
from quant_evo_nextgen.services.codex_fabric import CodexFabricService
from quant_evo_nextgen.services.dashboard import DashboardService
from quant_evo_nextgen.services.repo_state import RepoStateService
from quant_evo_nextgen.services.state_store import StateStore
from quant_evo_nextgen.services.strategy_lab import StrategyLabService
from quant_evo_nextgen.services.supervisor import SupervisorService


def test_strategy_lab_service_tracks_lifecycle_and_metrics(tmp_path: Path) -> None:
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'strategy-lab.db'}")
    database.create_schema()
    service = StrategyLabService(database.session_factory)

    hypothesis = service.create_hypothesis(
        {
            "title": "Funding dislocation carry",
            "thesis": "Extreme funding dislocations mean revert within a bounded holding window.",
            "target_market": "crypto-perps",
            "mechanism": "Capture carry decay after extreme positioning unwinds.",
            "evaluation_plan": ["Backtest on stressed funding windows.", "Paper trade for 10 sessions."],
            "invalidation_conditions": ["Carry persists", "Liquidity vanishes"],
            "created_by": "tester",
        }
    )
    spec = service.create_strategy_spec(
        {
            "hypothesis_id": hypothesis.id,
            "spec_code": "carry-001",
            "version_label": "v1",
            "title": "Funding dislocation carry",
            "target_market": "crypto-perps",
            "signal_logic": "Enter after funding and open-interest extremes revert.",
            "risk_rules": {"max_position_pct": 0.01},
            "data_requirements": ["funding", "open_interest"],
            "execution_constraints": {"venue": "binance"},
            "created_by": "tester",
        }
    )
    backtest = service.record_backtest(
        {
            "strategy_spec_id": spec.id,
            "dataset_range": "2024-01-01..2025-12-31",
            "sample_size": 180,
            "metrics_json": {
                "sharpe_ratio": 1.31,
                "total_return_pct": 16.8,
                "max_drawdown_pct": 10.2,
            },
            "created_by": "tester",
        }
    )
    paper_run = service.record_paper_run(
        {
            "strategy_spec_id": spec.id,
            "deployment_label": "paper-carry",
            "monitoring_days": 12,
            "metrics_json": {
                "net_pnl_pct": 3.7,
                "profit_factor": 1.16,
                "max_drawdown_pct": 4.5,
            },
            "capital_allocated": 2500,
            "created_by": "tester",
        }
    )
    promotion = service.record_promotion_decision(
        {
            "strategy_spec_id": spec.id,
            "paper_run_id": paper_run.id,
            "target_stage": "production",
            "decision": "approved",
            "rationale": "Backtest and paper evidence both cleared the gate.",
            "decided_by": "tester",
        }
    )

    metrics_after_promotion = service.get_metrics()
    spec_after_promotion = service.list_strategy_specs(limit=5)[0]

    withdrawal = service.record_withdrawal_decision(
        {
            "strategy_spec_id": spec.id,
            "reason": "Spread edge decayed below acceptable threshold.",
            "decided_by": "tester",
        }
    )
    metrics_after_withdrawal = service.get_metrics()
    withdrawn_spec = service.list_strategy_specs(limit=5)[0]

    assert backtest.gate_result == "passed"
    assert paper_run.gate_result == "ready_for_live_review"
    assert promotion.decision == "approved"
    assert metrics_after_promotion.production_count == 1
    assert spec_after_promotion.current_stage == "production"
    assert withdrawal.reason == "Spread edge decayed below acceptable threshold."
    assert metrics_after_withdrawal.production_count == 0
    assert withdrawn_spec.current_stage == "withdrawn"
    assert withdrawn_spec.status == "withdrawn"


def test_supervisor_strategy_evaluation_uses_strategy_lab_context(tmp_path: Path) -> None:
    _seed_repo_state(tmp_path)
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'strategy-supervisor.db'}")
    database.create_schema()

    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'strategy-supervisor.db'}",
        db_bootstrap_on_start=True,
        openai_api_key="relay-key",
        openai_base_url="https://relay.example.com/v1",
    )
    state_store = StateStore(database.session_factory)
    state_store.bootstrap_reference_data(settings)
    codex_fabric_service = CodexFabricService(database.session_factory, settings)
    strategy_service = StrategyLabService(database.session_factory)
    dashboard_service = DashboardService(
        RepoStateService(tmp_path),
        state_store,
        codex_fabric_service,
        None,
        strategy_service,
    )
    supervisor = SupervisorService(
        state_store=state_store,
        dashboard_service=dashboard_service,
        settings=settings,
        codex_fabric_service=codex_fabric_service,
        strategy_service=strategy_service,
    )

    hypothesis = strategy_service.create_hypothesis(
        {
            "title": "Momentum exhaustion reversal",
            "thesis": "Fast reversal after exhaustion can be captured with hard risk bounds.",
            "target_market": "us-equities",
            "mechanism": "Fade one-sided exhaustion near close with stop discipline.",
            "created_by": "tester",
        }
    )
    strategy_service.create_strategy_spec(
        {
            "hypothesis_id": hypothesis.id,
            "spec_code": "rev-001",
            "title": "Momentum exhaustion reversal",
            "target_market": "us-equities",
            "signal_logic": "Enter on exhaustion signal plus liquidity confirmation.",
            "created_by": "tester",
        }
    )
    _activate_single_loop(database, "strategy-evaluation")

    results = supervisor.run_due_loops(max_loops=1)

    with database.session_scope() as session:
        queued_run = session.scalar(
            select(CodexRunModel).where(CodexRunModel.supervisor_loop_key == "strategy-evaluation")
        )

    assert results
    assert results[0].loop_key == "strategy-evaluation"
    assert results[0].payload["status"] == "queued"
    assert queued_run is not None
    assert "Hypotheses=1" in queued_run.context_summary
    assert "specs=1" in queued_run.context_summary


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
