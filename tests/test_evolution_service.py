from pathlib import Path

import pytest

from quant_evo_nextgen.db.session import Database
from quant_evo_nextgen.services.evolution import EvolutionService
from quant_evo_nextgen.services.state_store import StateStore
from quant_evo_nextgen.config import Settings


def test_evolution_service_tracks_proposals_canaries_and_promotions(tmp_path: Path) -> None:
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'evolution-service.db'}")
    database.create_schema()
    service = EvolutionService(database.session_factory)

    proposal = service.create_improvement_proposal(
        {
            "title": "Reduce council token burn",
            "summary": "Move low-signal debate into bounded review gates.",
            "target_surface": "system",
            "proposal_kind": "workflow_tuning",
            "change_scope": ["protocols/council"],
            "expected_benefit": {"token_savings_pct": 18},
            "evaluation_summary": {"baseline_cost_per_cycle": 12000},
            "canary_plan": {"lane_type": "shadow", "traffic_pct": 5},
            "rollback_plan": {"action": "restore_previous_prompt_bundle"},
            "objective_drift_checks": ["owner_alignment", "research_quality"],
            "proposal_state": "ready_for_review",
            "created_by": "tester",
        }
    )

    metrics_after_proposal = service.get_metrics()
    assert metrics_after_proposal.proposal_count == 1
    assert metrics_after_proposal.ready_for_review_count == 1

    canary = service.record_canary_run(
        {
            "proposal_id": proposal.id,
            "lane_type": "shadow",
            "environment": "paper",
            "traffic_pct": 5,
            "success_metrics": {"cost_per_cycle_delta_pct": -19.4},
            "objective_drift_score": 0.05,
            "objective_drift_summary": "Shadow lane stayed aligned with baseline outcomes.",
            "rollback_ready": True,
            "status": "passed",
            "created_by": "tester",
        }
    )
    proposals = service.list_improvement_proposals()
    assert canary.status == "passed"
    assert proposals[0].proposal_state == "shadow_passed"

    decision = service.record_promotion_decision(
        {
            "proposal_id": proposal.id,
            "decision": "promoted",
            "rationale": "Shadow lane reduced cost without meaningful drift.",
            "decided_by": "tester",
            "decision_payload": {"lane_type": "shadow"},
        }
    )
    metrics_after_promotion = service.get_metrics()

    assert decision.decision == "promoted"
    assert metrics_after_promotion.proposal_count == 1
    assert metrics_after_promotion.ready_for_review_count == 0
    assert metrics_after_promotion.active_canary_count == 0
    assert metrics_after_promotion.promoted_count == 1
    assert metrics_after_promotion.rolled_back_count == 0
    assert service.list_promotion_decisions()[0].proposal_id == proposal.id

    database.dispose()


def test_evolution_service_rejects_canary_and_promotion_for_unknown_proposal(tmp_path: Path) -> None:
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'evolution-service-missing.db'}")
    database.create_schema()
    service = EvolutionService(database.session_factory)

    with pytest.raises(ValueError, match="Evolution proposal not found"):
        service.record_canary_run(
            {
                "proposal_id": "missing-proposal",
                "lane_type": "canary",
                "created_by": "tester",
            }
        )

    with pytest.raises(ValueError, match="Evolution proposal not found"):
        service.record_promotion_decision(
            {
                "proposal_id": "missing-proposal",
                "decision": "rejected",
                "rationale": "No such proposal exists.",
                "decided_by": "tester",
            }
        )

    database.dispose()


def test_evolution_service_auto_governance_advances_shadow_then_canary_then_promotes(tmp_path: Path) -> None:
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'evolution-auto.db'}")
    database.create_schema()
    service = EvolutionService(database.session_factory)

    proposal = service.create_improvement_proposal(
        {
            "title": "Tighten research review budget",
            "summary": "Reduce low-signal loop cost without changing mission priorities.",
            "target_surface": "system",
            "proposal_kind": "workflow_tuning",
            "change_scope": ["protocols/council"],
            "expected_benefit": {"confidence": 0.84, "citations": 3},
            "evaluation_summary": {"test_results": ["passed"], "followup_tasks": []},
            "risk_summary": "Bounded automation with rollback preserved.",
            "canary_plan": {"lane_type": "shadow", "traffic_pct": 5, "follow_on_lane_type": "canary"},
            "rollback_plan": {"action": "restore_previous_prompt_bundle"},
            "objective_drift_checks": [
                "system survivability",
                "capital protection",
                "governance continuity",
            ],
            "proposal_state": "ready_for_review",
            "created_by": "tester",
        }
    )

    first_tick = service.run_governance_tick(max_proposals=5, created_by="tester")
    second_tick = service.run_governance_tick(max_proposals=5, created_by="tester")
    third_tick = service.run_governance_tick(max_proposals=5, created_by="tester")
    proposals = service.list_improvement_proposals(limit=5)
    canaries = service.list_canary_runs(limit=5, proposal_id=proposal.id)
    decisions = service.list_promotion_decisions(limit=5, proposal_id=proposal.id)

    assert len(first_tick.created_canary_ids) == 1
    assert len(second_tick.created_canary_ids) == 1
    assert third_tick.created_decision_ids
    assert proposals[0].proposal_state == "promoted"
    assert [run.lane_type for run in canaries] == ["canary", "shadow"]
    assert canaries[0].status == "passed"
    assert decisions[0].decision == "promoted"

    database.dispose()


def test_evolution_service_auto_governance_rolls_back_drifting_proposal_and_pauses_domain(tmp_path: Path) -> None:
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'evolution-rollback.db'}")
    database.create_schema()
    settings = Settings(repo_root=tmp_path, postgres_url=f"sqlite+pysqlite:///{tmp_path / 'evolution-rollback.db'}")
    state_store = StateStore(database.session_factory)
    state_store.bootstrap_reference_data(settings)
    service = EvolutionService(database.session_factory)

    proposal = service.create_improvement_proposal(
        {
            "title": "Auto-scale unbounded strategy mutations",
            "summary": "Increase aggressive self-modification throughput.",
            "target_surface": "strategy",
            "proposal_kind": "strategy_improvement",
            "change_scope": ["strategies/"],
            "expected_benefit": {"confidence": 0.91},
            "evaluation_summary": {
                "test_results": ["passed"],
                "objective_drift_score": 0.42,
                "followup_tasks": ["Owner alignment review still missing."],
            },
            "risk_summary": "Potential mission drift and owner alignment regression risk.",
            "canary_plan": {"lane_type": "shadow", "traffic_pct": 5, "max_objective_drift_score": 0.1},
            "rollback_plan": {"action": "freeze_strategy_mutations"},
            "objective_drift_checks": ["capital protection"],
            "proposal_state": "ready_for_review",
            "created_by": "tester",
        }
    )

    first_tick = service.run_governance_tick(
        state_store=state_store,
        max_proposals=5,
        created_by="tester",
        origin_type="test",
        origin_id="evolution-rollback",
    )
    second_tick = service.run_governance_tick(
        state_store=state_store,
        max_proposals=5,
        created_by="tester",
        origin_type="test",
        origin_id="evolution-rollback",
    )
    proposals = service.list_improvement_proposals(limit=5)
    decisions = service.list_promotion_decisions(limit=5, proposal_id=proposal.id)
    overrides = state_store.list_operator_overrides(active_only=True)
    incidents = state_store.list_incidents(open_only=True)

    assert first_tick.created_canary_ids
    assert second_tick.created_decision_ids
    assert second_tick.paused_domains == ["trading"]
    assert proposals[0].proposal_state == "rolled_back"
    assert decisions[0].decision == "rolled_back"
    assert overrides[0].scope == "trading"
    assert any("Evolution rollback executed" in incident.title for incident in incidents)

    database.dispose()
