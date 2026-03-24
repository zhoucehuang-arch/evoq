from pathlib import Path

from quant_evo_nextgen.config import Settings
from quant_evo_nextgen.contracts.intents import IntentClassification, IntentType
from quant_evo_nextgen.db.session import Database
from quant_evo_nextgen.services.control_plane import ControlPlaneService
from quant_evo_nextgen.services.owner_onboarding import OwnerOnboardingService
from quant_evo_nextgen.services.state_store import StateStore


def test_control_plane_creates_and_executes_durable_approval_request(tmp_path) -> None:
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'control.db'}")
    database.create_schema()
    settings = Settings(repo_root=tmp_path, postgres_url=f"sqlite+pysqlite:///{tmp_path / 'control.db'}")
    state_store = StateStore(database.session_factory)
    state_store.bootstrap_reference_data(settings)
    control_plane = ControlPlaneService(state_store)

    create_result = control_plane.handle_control_intent(
        intent=IntentClassification(
            intent_type=IntentType.PAUSE_TRADING,
            target_domain="trading",
            risk_tier="R4",
            requires_confirmation=True,
            proposed_action="Pause auto-trading or live execution.",
        ),
        actor="tester",
        source_channel="control",
        raw_message="pause auto-trading for now",
    )

    approvals = state_store.list_approval_requests(pending_only=True)

    assert create_result.created_record_id is not None
    assert "Created approval request" in create_result.response_text
    assert len(approvals) == 1
    assert approvals[0].approval_type == "pause_trading"

    approve_result = control_plane.handle_control_intent(
        intent=IntentClassification(
            intent_type=IntentType.APPROVE_REQUEST,
            reference_id=approvals[0].id,
            proposed_action="Approve a pending control request.",
            execution_supported=True,
        ),
        actor="tester",
        source_channel="control",
        raw_message=f"approve {approvals[0].id}",
    )

    overrides = state_store.list_operator_overrides(active_only=True)

    assert "Approved approval request" in approve_result.response_text
    assert overrides[0].scope == "trading"
    assert overrides[0].action == "pause"


def test_control_plane_applies_low_risk_runtime_config_change_without_approval(tmp_path) -> None:
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'config-control.db'}")
    database.create_schema()
    settings = Settings(repo_root=tmp_path, postgres_url=f"sqlite+pysqlite:///{tmp_path / 'config-control.db'}")
    state_store = StateStore(database.session_factory)
    state_store.bootstrap_reference_data(settings)
    control_plane = ControlPlaneService(state_store)

    result = control_plane.handle_control_intent(
        intent=IntentClassification(
            intent_type=IntentType.PROPOSE_CONFIG_CHANGE,
            config_target_type="system_policy",
            config_target_key="heartbeat_runtime",
            config_patch={"interval_seconds": 120},
            config_change_summary="Update heartbeat runtime interval.",
            proposed_action="Create runtime config proposal.",
            execution_supported=True,
        ),
        actor="tester",
        source_channel="control",
        raw_message="set heartbeat interval to 120 seconds",
    )

    entries = state_store.list_runtime_config_entries()
    revisions = state_store.list_runtime_config_revisions()

    heartbeat_entry = next(entry for entry in entries if entry.target_key == "heartbeat_runtime")
    assert "Applied runtime config proposal" in result.response_text
    assert heartbeat_entry.value_json["interval_seconds"] == 120
    assert len(revisions) == 1


def test_control_plane_routes_risky_runtime_config_change_into_approval(tmp_path) -> None:
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'config-approval.db'}")
    database.create_schema()
    settings = Settings(repo_root=tmp_path, postgres_url=f"sqlite+pysqlite:///{tmp_path / 'config-approval.db'}")
    state_store = StateStore(database.session_factory)
    state_store.bootstrap_reference_data(settings)
    control_plane = ControlPlaneService(state_store)

    result = control_plane.handle_control_intent(
        intent=IntentClassification(
            intent_type=IntentType.PROPOSE_CONFIG_CHANGE,
            config_target_type="owner_preference",
            config_target_key="discord_channels",
            config_patch={"control_channel": "owner-control"},
            config_change_summary="Update Discord control channel.",
            proposed_action="Create runtime config proposal.",
            execution_supported=True,
        ),
        actor="tester",
        source_channel="control",
        raw_message="set control channel to owner-control",
    )

    proposals = state_store.list_runtime_config_proposals()
    approvals = state_store.list_approval_requests(pending_only=True)

    assert "Created runtime config proposal" in result.response_text
    assert len(proposals) == 1
    assert proposals[0].status == "awaiting_approval"
    assert len(approvals) == 1
    assert approvals[0].approval_type == "runtime_config_change"


def test_control_plane_can_roll_back_low_risk_runtime_config_revision(tmp_path) -> None:
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'config-rollback.db'}")
    database.create_schema()
    settings = Settings(repo_root=tmp_path, postgres_url=f"sqlite+pysqlite:///{tmp_path / 'config-rollback.db'}")
    state_store = StateStore(database.session_factory)
    state_store.bootstrap_reference_data(settings)
    control_plane = ControlPlaneService(state_store)

    forward_result = control_plane.handle_control_intent(
        intent=IntentClassification(
            intent_type=IntentType.PROPOSE_CONFIG_CHANGE,
            config_target_type="system_policy",
            config_target_key="heartbeat_runtime",
            config_patch={"interval_seconds": 120},
            config_change_summary="Update heartbeat runtime interval.",
            proposed_action="Create runtime config proposal.",
            execution_supported=True,
        ),
        actor="tester",
        source_channel="control",
        raw_message="set heartbeat interval to 120 seconds",
    )
    latest_revision = state_store.list_runtime_config_revisions()[0]

    rollback_result = control_plane.handle_control_intent(
        intent=IntentClassification(
            intent_type=IntentType.ROLLBACK_RUNTIME_CONFIG,
            reference_id=latest_revision.id,
            proposed_action="Create a governed rollback proposal for a runtime config revision.",
            execution_supported=True,
        ),
        actor="tester",
        source_channel="control",
        raw_message=f"rollback config {latest_revision.id}",
    )

    entries = state_store.list_runtime_config_entries()
    heartbeat_entry = next(entry for entry in entries if entry.target_key == "heartbeat_runtime")

    assert "Applied runtime config proposal" in forward_result.response_text
    assert "Applied config rollback proposal" in rollback_result.response_text
    assert heartbeat_entry.value_json["interval_seconds"] == 60


def test_control_plane_updates_deploy_secret_without_persisting_raw_secret(tmp_path: Path) -> None:
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'deploy-control.db'}")
    database.create_schema()
    settings = Settings(repo_root=tmp_path, postgres_url=f"sqlite+pysqlite:///{tmp_path / 'deploy-control.db'}")
    state_store = StateStore(database.session_factory)
    state_store.bootstrap_reference_data(settings)
    repo_root = Path(__file__).resolve().parents[1]
    onboarding_service = OwnerOnboardingService(repo_root, env_root=tmp_path)
    control_plane = ControlPlaneService(state_store, onboarding_service=onboarding_service)

    result = control_plane.handle_control_intent(
        intent=IntentClassification(
            intent_type=IntentType.DEPLOY_SET,
            deploy_role="core",
            deploy_field_alias="relay key",
            deploy_value="sk-live-secret-1234",
            contains_sensitive_value=True,
            sanitized_message_summary="Set core Relay API Key (redacted)",
            proposed_action="Update deployment draft field.",
            execution_supported=True,
        ),
        actor="tester",
        source_channel="control",
        raw_message="set core relay key to sk-live-secret-1234",
    )

    owner_presence = state_store.get_owner_preference("last_owner_interaction")
    env_content = (tmp_path / "core.env").read_text(encoding="utf-8")
    workflow_runs = state_store.list_workflow_runs(limit=5)

    assert "sk-live-secret-1234" not in owner_presence.value_json["message_summary"]
    assert "sk-live-secret-1234" in env_content
    assert "Updated `core` Relay API Key" in result.response_text
    assert "***" in result.response_text
    assert workflow_runs[0].workflow_code == "WF-OPS-001"
