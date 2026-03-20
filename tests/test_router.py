from quant_evo_nextgen.contracts.intents import IntentType
from quant_evo_nextgen.services.router import NaturalLanguageRouter


def test_router_understands_chinese_owner_commands() -> None:
    router = NaturalLanguageRouter()

    status_intent = router.classify("\u72b6\u6001")
    pause_trading_intent = router.classify("\u6682\u505c\u81ea\u52a8\u4ea4\u6613")
    approvals_intent = router.classify("\u5f85\u5ba1\u6279")

    assert status_intent.intent_type is IntentType.STATUS
    assert pause_trading_intent.intent_type is IntentType.PAUSE_TRADING
    assert approvals_intent.intent_type is IntentType.LIST_APPROVALS


def test_router_parses_chinese_runtime_config_changes_and_rollbacks() -> None:
    router = NaturalLanguageRouter()

    config_intent = router.classify("\u628a\u5fc3\u8df3\u95f4\u9694\u6539\u6210 120 \u79d2")
    rollback_intent = router.classify("\u56de\u6eda\u914d\u7f6e revision-12345678")

    assert config_intent.intent_type is IntentType.PROPOSE_CONFIG_CHANGE
    assert config_intent.config_target_key == "heartbeat_runtime"
    assert config_intent.config_patch == {"interval_seconds": 120}
    assert rollback_intent.intent_type is IntentType.ROLLBACK_RUNTIME_CONFIG
    assert rollback_intent.reference_id == "revision-12345678"


def test_router_parses_deploy_bootstrap_and_secret_setting() -> None:
    router = NaturalLanguageRouter()

    bootstrap_intent = router.classify("\u521d\u59cb\u5316 worker \u90e8\u7f72")
    secret_intent = router.classify("\u8bbe\u7f6e core \u4e2d\u8f6ckey \u4e3a sk-live-secret-1234")

    assert bootstrap_intent.intent_type is IntentType.DEPLOY_BOOTSTRAP
    assert bootstrap_intent.deploy_role == "worker"
    assert secret_intent.intent_type is IntentType.DEPLOY_SET
    assert secret_intent.deploy_role == "core"
    assert secret_intent.contains_sensitive_value is True
    assert "sk-live-secret-1234" not in (secret_intent.sanitized_message_summary or "")


def test_router_parses_single_vps_and_playwright_fields() -> None:
    router = NaturalLanguageRouter()

    topology_intent = router.classify("\u8bbe\u7f6e core \u90e8\u7f72\u6a21\u5f0f \u4e3a single_vps_compact")
    playwright_intent = router.classify("\u8bbe\u7f6e core playwright\u542f\u7528 \u4e3a true")

    assert topology_intent.intent_type is IntentType.DEPLOY_SET
    assert topology_intent.contains_sensitive_value is False
    assert topology_intent.deploy_field_alias == "\u90e8\u7f72\u6a21\u5f0f"
    assert playwright_intent.intent_type is IntentType.DEPLOY_SET
    assert playwright_intent.deploy_field_alias == "playwright\u542f\u7528"
