import json
from pathlib import Path

from quant_evo_nextgen.config import Settings
from quant_evo_nextgen.db.session import Database
from quant_evo_nextgen.services.state_store import StateStore


def test_state_store_bootstrap_and_runtime_counts(tmp_path: Path) -> None:
    database_path = tmp_path / "state.db"
    database = Database(f"sqlite+pysqlite:///{database_path}")
    database.create_schema()

    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{database_path}",
        openai_base_url="https://relay.example.com/v1",
    )
    store = StateStore(database.session_factory)
    store.bootstrap_reference_data(settings)

    goal = store.create_goal(
        payload={
            "title": "Expand learning coverage",
            "description": "Track more market regimes.",
            "mission_domain": "learning",
            "status": "active",
            "created_by": "tester",
        }
    )
    incident = store.create_incident(
        payload={
            "title": "Relay degraded",
            "summary": "Provider returned inconsistent results.",
            "severity": "SEV-2",
            "status": "open",
        }
    )
    approval = store.create_approval_request(
        payload={
            "approval_type": "pause_trading",
            "subject_type": "domain",
            "subject_id": "trading",
            "requested_by": "tester",
            "risk_level": "R4",
        }
    )
    override = store.create_operator_override(
        payload={
            "scope": "trading",
            "action": "freeze",
            "reason": "Manual safety check",
            "activated_by": "tester",
        }
    )

    run = store.start_workflow_run(
        workflow_code="WF-GOV-002",
        owner_role="workflow-runner",
        summary="Persist heartbeat.",
    )
    store.record_heartbeat(
        node_role="core",
        deployment_topology="two_vps_asymmetrical",
        mode="paper_only",
        risk_state="observe",
        summary_payload={"production_strategies": 0},
    )
    store.append_workflow_event(
        run.id,
        event_type="workflow.heartbeat_recorded",
        summary="Heartbeat stored.",
    )
    store.complete_workflow_run(run.id, result_payload={"ok": True})

    runtime = store.get_runtime_snapshot()
    loops = store.list_supervisor_loops()
    providers = store.list_provider_profiles()
    preferences = store.list_owner_preferences()

    assert goal.status == "active"
    assert incident.status == "open"
    assert approval.decision_status == "pending"
    assert override.is_active is True
    assert runtime.active_goals == 1
    assert runtime.open_incidents == 1
    assert runtime.pending_approvals == 1
    assert runtime.active_overrides == 1
    assert runtime.last_heartbeat_at is not None
    assert any(loop.loop_key == "governance-heartbeat" for loop in loops)
    assert any(loop.loop_key == "broker-state-sync" for loop in loops)
    assert providers[0].provider_key == "primary-relay"
    assert any(preference.preference_key == "interaction_language" for preference in preferences)

    database.dispose()


def test_state_store_tracks_runtime_config_proposals_and_revisions(tmp_path: Path) -> None:
    database_path = tmp_path / "runtime-config.db"
    database = Database(f"sqlite+pysqlite:///{database_path}")
    database.create_schema()

    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{database_path}",
        openai_base_url="https://relay.example.com/v1",
    )
    store = StateStore(database.session_factory)
    store.bootstrap_reference_data(settings)

    proposal = store.create_runtime_config_proposal(
        {
            "target_type": "system_policy",
            "target_key": "heartbeat_runtime",
            "requested_by": "tester",
            "proposed_value_json": {"interval_seconds": 180},
            "change_summary": "Increase heartbeat interval for maintenance.",
        }
    )
    revision = store.apply_runtime_config_proposal(proposal.id, applied_by="tester")

    runtime_config = store.list_runtime_config_entries()
    revisions = store.list_runtime_config_revisions()
    heartbeat_entry = next(entry for entry in runtime_config if entry.target_key == "heartbeat_runtime")

    assert proposal.requires_approval is False
    assert heartbeat_entry.value_json["interval_seconds"] == 180
    assert revision.target_key == "heartbeat_runtime"
    assert revisions[0].id == revision.id

    database.dispose()
