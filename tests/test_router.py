from quant_evo_nextgen.contracts.intents import IntentType
from quant_evo_nextgen.services.router import NaturalLanguageRouter


def test_router_understands_english_owner_commands() -> None:
    router = NaturalLanguageRouter()

    status_intent = router.classify("status")
    pause_trading_intent = router.classify("pause auto-trading")
    approvals_intent = router.classify("pending approvals")

    assert status_intent.intent_type is IntentType.STATUS
    assert pause_trading_intent.intent_type is IntentType.PAUSE_TRADING
    assert approvals_intent.intent_type is IntentType.LIST_APPROVALS


def test_router_parses_runtime_config_changes_and_rollbacks() -> None:
    router = NaturalLanguageRouter()

    config_intent = router.classify("set heartbeat interval to 120 seconds")
    rollback_intent = router.classify("rollback config revision-12345678")

    assert config_intent.intent_type is IntentType.PROPOSE_CONFIG_CHANGE
    assert config_intent.config_target_key == "heartbeat_runtime"
    assert config_intent.config_patch == {"interval_seconds": 120}
    assert rollback_intent.intent_type is IntentType.ROLLBACK_RUNTIME_CONFIG
    assert rollback_intent.reference_id == "revision-12345678"


def test_router_parses_deploy_bootstrap_and_secret_setting() -> None:
    router = NaturalLanguageRouter()

    bootstrap_intent = router.classify("setup worker deployment")
    secret_intent = router.classify("set core relay key to sk-live-secret-1234")

    assert bootstrap_intent.intent_type is IntentType.DEPLOY_BOOTSTRAP
    assert bootstrap_intent.deploy_role == "worker"
    assert secret_intent.intent_type is IntentType.DEPLOY_SET
    assert secret_intent.deploy_role == "core"
    assert secret_intent.contains_sensitive_value is True
    assert "sk-live-secret-1234" not in (secret_intent.sanitized_message_summary or "")


def test_router_parses_single_vps_and_playwright_fields() -> None:
    router = NaturalLanguageRouter()

    topology_intent = router.classify("set core deployment topology to single_vps_compact")
    playwright_intent = router.classify("set core playwright enabled to true")

    assert topology_intent.intent_type is IntentType.DEPLOY_SET
    assert topology_intent.contains_sensitive_value is False
    assert topology_intent.deploy_field_alias == "deployment topology"
    assert playwright_intent.intent_type is IntentType.DEPLOY_SET
    assert playwright_intent.deploy_field_alias == "playwright enabled"
