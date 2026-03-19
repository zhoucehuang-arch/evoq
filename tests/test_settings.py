from pathlib import Path

from quant_evo_nextgen.config import Settings


def test_settings_support_provider_and_timezone_fields() -> None:
    settings = Settings(
        repo_root=Path("."),
        node_role="worker",
        deployment_topology="two_vps_asymmetrical",
        db_bootstrap_on_start=False,
        db_echo=True,
        operator_timezone="Asia/Hong_Kong",
        market_timezone="America/New_York",
        market_calendar="XNYS",
        openai_base_url="https://relay.example.com/v1",
        primary_model="relay-main",
        fast_model="relay-fast",
    )

    assert settings.node_role == "worker"
    assert settings.deployment_topology == "two_vps_asymmetrical"
    assert settings.db_bootstrap_on_start is False
    assert settings.db_echo is True
    assert settings.market_calendar == "XNYS"
    assert settings.openai_base_url == "https://relay.example.com/v1"
    assert settings.primary_model == "relay-main"
    assert settings.fast_model == "relay-fast"
