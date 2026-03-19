from quant_evo_nextgen.contracts.intents import IntentType
from quant_evo_nextgen.services.router import NaturalLanguageRouter


def test_router_understands_chinese_owner_commands() -> None:
    router = NaturalLanguageRouter()

    status_intent = router.classify("状态")
    pause_trading_intent = router.classify("暂停自动交易")
    approvals_intent = router.classify("待审批")

    assert status_intent.intent_type is IntentType.STATUS
    assert pause_trading_intent.intent_type is IntentType.PAUSE_TRADING
    assert approvals_intent.intent_type is IntentType.LIST_APPROVALS


def test_router_parses_chinese_runtime_config_changes_and_rollbacks() -> None:
    router = NaturalLanguageRouter()

    config_intent = router.classify("把心跳间隔改成 120 秒")
    rollback_intent = router.classify("回滚配置 revision-12345678")

    assert config_intent.intent_type is IntentType.PROPOSE_CONFIG_CHANGE
    assert config_intent.config_target_key == "heartbeat_runtime"
    assert config_intent.config_patch == {"interval_seconds": 120}
    assert rollback_intent.intent_type is IntentType.ROLLBACK_RUNTIME_CONFIG
    assert rollback_intent.reference_id == "revision-12345678"


def test_router_parses_deploy_bootstrap_and_secret_setting() -> None:
    router = NaturalLanguageRouter()

    bootstrap_intent = router.classify("初始化 worker 部署")
    secret_intent = router.classify("设置 core 中转key 为 sk-live-secret-1234")

    assert bootstrap_intent.intent_type is IntentType.DEPLOY_BOOTSTRAP
    assert bootstrap_intent.deploy_role == "worker"
    assert secret_intent.intent_type is IntentType.DEPLOY_SET
    assert secret_intent.deploy_role == "core"
    assert secret_intent.contains_sensitive_value is True
    assert "sk-live-secret-1234" not in (secret_intent.sanitized_message_summary or "")
