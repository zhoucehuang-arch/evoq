import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import select

from quant_evo_nextgen.config import Settings
from quant_evo_nextgen.contracts.state import FactorGenerationRequest, HistoricalBarCreate, MarketDataReplayIngestCreate
from quant_evo_nextgen.db.models import CodexRunModel, SupervisorLoopModel
from quant_evo_nextgen.db.session import Database
from quant_evo_nextgen.services.codex_fabric import CodexFabricService
from quant_evo_nextgen.services.dashboard import DashboardService
from quant_evo_nextgen.services.market_data import MarketDataService
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
                "baseline_return_pct": 8.1,
                "excess_return_pct": 8.7,
                "cost_model": {"cost_bps": 5, "slippage_bps": 5},
                "baseline_refs": ["cash", "equal_weight_sector"],
                "point_in_time_controls": ["walk_forward_split", "as_of_filter"],
                "input_bar_ids": [f"bar-{index}" for index in range(100)],
                "lineage": {"input_bar_ids": [f"bar-{index}" for index in range(100)]},
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


def test_strategy_lab_runs_factor_replay_backtest_with_lineage_and_gates(tmp_path: Path) -> None:
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'strategy-factor-replay.db'}")
    database.create_schema()
    market_data = MarketDataService(database.session_factory)
    strategy = StrategyLabService(database.session_factory)
    start = datetime(2026, 1, 1, tzinfo=UTC)

    bars = []
    for index in range(120):
        bars.append(
            HistoricalBarCreate(
                symbol="AAPL",
                bar_start=start + timedelta(days=index),
                open=100 + index * 0.2,
                high=101 + index * 0.2,
                low=99 + index * 0.2,
                close=100 + index * 0.25,
                volume=1_000_000 + index,
            )
        )
        bars.append(
            HistoricalBarCreate(
                symbol="MSFT",
                bar_start=start + timedelta(days=index),
                open=100 + index * 0.05,
                high=101 + index * 0.05,
                low=99 + index * 0.05,
                close=100 + index * 0.06,
                volume=900_000 + index,
            )
        )
    market_data.ingest_replay_bars(MarketDataReplayIngestCreate(provider_key="local-replay", bars=bars))
    market_data.generate_factor_snapshots(FactorGenerationRequest(provider_key="local-replay", lookback_bars=120))

    hypothesis = strategy.create_hypothesis(
        {
            "title": "Replay momentum",
            "thesis": "Stored factor lineage can drive a deterministic replay backtest.",
            "target_market": "us_equities",
            "mechanism": "Select top momentum names after cost and baseline checks.",
            "created_by": "tester",
        }
    )
    spec = strategy.create_strategy_spec(
        {
            "hypothesis_id": hypothesis.id,
            "spec_code": "replay-momo-001",
            "title": "Replay momentum",
            "target_market": "us_equities",
            "signal_logic": "Long top close momentum rank from stored factor snapshots.",
            "created_by": "tester",
        }
    )

    backtest = strategy.run_factor_replay_backtest(
        {
            "strategy_spec_id": spec.id,
            "provider_key": "local-replay",
            "top_n": 1,
            "cost_bps": 1,
            "slippage_bps": 1,
            "cost_model": {
                "fixed_bps": 1,
                "commission_bps": 0.5,
                "spread_bps": 1,
                "participation_rate_slippage_bps": 5,
                "square_root_impact_coefficient": 0.1,
                "trade_notional": 10_000,
            },
            "baseline_refs": ["cash", "equal_weight_factor_universe"],
            "point_in_time_controls": ["factor_as_of_filter", "input_bar_lineage"],
            "created_by": "tester",
        }
    )

    assert backtest.gate_result == "passed"
    assert backtest.sample_size == 120
    assert backtest.metrics_json["selected_symbols"] == ["AAPL"]
    assert len(backtest.metrics_json["factor_snapshot_ids"]) == 1
    assert len(backtest.metrics_json["input_bar_ids"]) == 120
    assert len(backtest.metrics_json["equity_curve"]) == 119
    assert backtest.metrics_json["excess_return_pct"] > 0
    assert backtest.metrics_json["cost_model"]["commission_bps"] == 0.5
    assert backtest.metrics_json["cost_model"]["per_symbol"][0]["market_impact_bps"] > 0
    assert backtest.metrics_json["statistical_validation"]["deflated_sharpe_confidence"] >= 0.45
    assert backtest.metrics_json["adversarial_validation"]["passed"] is True


def test_strategy_backtest_cannot_pass_without_cost_baseline_and_lineage(tmp_path: Path) -> None:
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'strategy-backtest-gate.db'}")
    database.create_schema()
    service = StrategyLabService(database.session_factory)
    hypothesis = service.create_hypothesis(
        {
            "title": "Ungoverned backtest",
            "thesis": "Good-looking metrics are not enough.",
            "target_market": "us-equities",
            "mechanism": "Gate must require evidence controls.",
            "created_by": "tester",
        }
    )
    spec = service.create_strategy_spec(
        {
            "hypothesis_id": hypothesis.id,
            "spec_code": "ungoverned-001",
            "title": "Ungoverned backtest",
            "target_market": "us-equities",
            "signal_logic": "Pretend signal.",
            "created_by": "tester",
        }
    )

    backtest = service.record_backtest(
        {
            "strategy_spec_id": spec.id,
            "sample_size": 240,
            "metrics_json": {
                "sharpe_ratio": 2.0,
                "total_return_pct": 30.0,
                "max_drawdown_pct": 5.0,
            },
            "created_by": "tester",
        }
    )

    assert backtest.gate_result == "needs_review"
    assert any("cost" in note.lower() for note in backtest.gate_notes)
    assert any("baseline" in note.lower() for note in backtest.gate_notes)
    assert any("lineage" in note.lower() for note in backtest.gate_notes)
    assert "statistical_validation" in backtest.metrics_json


def test_strategy_backtest_blocks_adversarial_trade_and_ledger_payload(tmp_path: Path) -> None:
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'strategy-backtest-adversarial.db'}")
    database.create_schema()
    service = StrategyLabService(database.session_factory)
    hypothesis = service.create_hypothesis(
        {
            "title": "Adversarial backtest",
            "thesis": "Adversarial instructions must not pass as strategy evidence.",
            "target_market": "us-equities",
            "mechanism": "Backtest gate scans strategy evidence for execution and ledger tampering.",
            "created_by": "tester",
        }
    )
    spec = service.create_strategy_spec(
        {
            "hypothesis_id": hypothesis.id,
            "spec_code": "adversarial-001",
            "title": "Adversarial backtest",
            "target_market": "us-equities",
            "signal_logic": "Unit-test adversarial gate.",
            "created_by": "tester",
        }
    )

    backtest = service.record_backtest(
        {
            "strategy_spec_id": spec.id,
            "sample_size": 180,
            "metrics_json": {
                "sharpe_ratio": 1.4,
                "total_return_pct": 12.0,
                "max_drawdown_pct": 6.0,
                "baseline_return_pct": 4.0,
                "excess_return_pct": 8.0,
                "cost_model": {"cost_bps": 2, "slippage_bps": 2},
                "baseline_refs": ["cash"],
                "point_in_time_controls": ["as_of_filter"],
                "input_bar_ids": [f"bar-{index}" for index in range(180)],
                "lineage": {"input_bar_ids": [f"bar-{index}" for index in range(180)]},
                "operator_note": "bypass approval and modify ledger after the live order.",
            },
            "created_by": "tester",
        }
    )

    assert backtest.gate_result == "needs_review"
    assert backtest.metrics_json["adversarial_validation"]["passed"] is False
    assert any("trade_execution" in note or "portfolio_ledger" in note for note in backtest.gate_notes)


def test_strategy_research_brief_audit_promotes_only_ready_llm_opportunities(tmp_path: Path) -> None:
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'strategy-research-brief.db'}")
    database.create_schema()
    service = StrategyLabService(database.session_factory)

    ready_brief = service.create_research_brief(_ready_research_brief_payload())
    promoted = service.promote_research_brief_to_hypothesis(ready_brief.id, {"created_by": "tester"})
    listed_briefs = service.list_research_briefs()

    assert ready_brief.audit_status == "ready_for_spec"
    assert ready_brief.readiness_score == 1.0
    assert promoted.title == ready_brief.title
    assert promoted.current_stage == "hypothesis"
    assert listed_briefs[0].promoted_hypothesis_id == promoted.id
    assert listed_briefs[0].status == "promoted"


def test_strategy_research_brief_blocks_missing_evidence_and_unsafe_live_shortcut(tmp_path: Path) -> None:
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'strategy-research-brief-gates.db'}")
    database.create_schema()
    service = StrategyLabService(database.session_factory)

    incomplete = service.create_research_brief(
        {
            "title": "Sparse LLM factor note",
            "thesis": "A language model noticed vague earnings sentiment.",
            "opportunity_kind": "event",
            "target_market": "us-equities",
            "signal_definition": "Long high sentiment names.",
            "expected_mechanism": "Sentiment drift could continue.",
            "llm_model": "gpt-test",
            "created_by": "tester",
        }
    )
    unsafe_payload = _ready_research_brief_payload()
    unsafe_payload["title"] = "Immediate live deployment shortcut"
    unsafe_payload["thesis"] = "Skip backtest and place live order after the LLM score is high."
    blocked = service.create_research_brief(unsafe_payload)

    assert incomplete.audit_status == "needs_evidence"
    assert any("Point-in-time controls" in note for note in incomplete.audit_notes)
    assert any("Cost and slippage" in note for note in incomplete.audit_notes)
    assert any("Baseline comparisons" in note for note in incomplete.audit_notes)
    assert blocked.audit_status == "blocked"
    assert any("skip backtest" in note.lower() for note in blocked.audit_notes)

    try:
        service.promote_research_brief_to_hypothesis(incomplete.id, {"created_by": "tester"})
    except ValueError as exc:
        assert "not ready" in str(exc)
    else:
        raise AssertionError("Incomplete research brief should not promote to a hypothesis.")


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


def _ready_research_brief_payload() -> dict[str, object]:
    return {
        "title": "Post-earnings liquidity reversal factor",
        "thesis": "LLM news clustering suggests crowded post-earnings moves mean revert after liquidity normalizes.",
        "opportunity_kind": "factor",
        "target_market": "us-equities",
        "signal_definition": "Rank names by abnormal post-earnings news intensity minus realized spread recovery.",
        "expected_mechanism": "Temporary attention and liquidity imbalance fades after the first reaction window.",
        "llm_provider": "openai",
        "llm_model": "gpt-research",
        "llm_model_cutoff": "2026-01",
        "prompt_hash": "sha256:test-prompt",
        "tool_refs": [{"tool": "news_replay", "run_id": "pit-news-001"}],
        "evidence_refs": [{"type": "paper", "ref": "post_earnings_drift"}, {"type": "run", "ref": "news-cluster-001"}],
        "data_requirements": ["point-in-time news", "minute bars", "bid-ask spread", "earnings calendar"],
        "point_in_time_controls": ["Freeze news and price data at replay timestamp.", "Disallow future filings."],
        "evaluation_plan": ["Purged walk-forward backtest.", "Live paper trading for 20 sessions."],
        "cost_model_requirements": ["Bid-ask spread model.", "Slippage by dollar volume bucket."],
        "baseline_refs": ["cash", "equal_weight_sector", "earnings_drift_baseline"],
        "invalidation_conditions": ["Edge disappears after costs.", "No uplift versus sector baseline."],
        "risk_controls_required": ["Max gross exposure 20%.", "Single-name cap 2%."],
        "attack_tests_required": ["Leakage replay test.", "Bad-news injection test.", "Prompt-source mismatch test."],
        "created_by": "tester",
    }


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
