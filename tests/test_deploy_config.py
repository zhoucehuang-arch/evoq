from pathlib import Path

from quant_evo_nextgen.services.deploy_config import DeployConfigService


def test_deploy_config_core_preflight_passes_with_complete_settings(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    service = DeployConfigService(repo_root)
    env_path = tmp_path / "core.env"

    created = service.initialize_env_file(
        role="core",
        output_path=env_path,
        overrides={
            "QE_POSTGRES_PASSWORD": "super-secret-password",
            "QE_POSTGRES_BIND_HOST": "100.64.0.10",
            "QE_OPENAI_API_KEY": "relay-key",
            "QE_OPENAI_BASE_URL": "https://relay.example.com/v1",
            "QE_DISCORD_TOKEN": "discord-token",
            "QE_DISCORD_GUILD_ID": "123456789",
            "QE_DISCORD_CONTROL_CHANNEL_ID": "111",
            "QE_DISCORD_APPROVALS_CHANNEL_ID": "222",
            "QE_DISCORD_ALERTS_CHANNEL_ID": "333",
            "QE_DISCORD_ALLOWED_USER_IDS": "444,555",
        },
        interactive=False,
    )

    report = service.run_preflight(role="core", env_path=created)
    statuses = {check["key"]: check["status"] for check in report["checks"]}
    content = created.read_text(encoding="utf-8")

    assert report["status"] == "ok"
    assert statuses["role_alignment"] == "ok"
    assert statuses["discord_owner_surface"] == "ok"
    assert statuses["broker_and_db"] == "ok"
    assert statuses["postgres_exposure"] == "ok"
    assert statuses["dashboard_surface"] == "ok"
    assert "QE_DASHBOARD_ACCESS_USERNAME=owner" in content
    assert "QE_DASHBOARD_ACCESS_PASSWORD=" in content
    assert "QE_DASHBOARD_API_TOKEN=" in content


def test_deploy_config_worker_preflight_fails_for_local_postgres_target(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    service = DeployConfigService(repo_root)
    env_path = tmp_path / "worker-localhost.env"

    created = service.initialize_env_file(
        role="worker",
        output_path=env_path,
        overrides={
            "QE_POSTGRES_URL": "postgresql+psycopg://quant_evo:secret@localhost:5432/quant_evo",
            "QE_OPENAI_API_KEY": "relay-key",
        },
        interactive=False,
    )

    report = service.run_preflight(role="worker", env_path=created)
    statuses = {check["key"]: check["status"] for check in report["checks"]}

    assert report["status"] == "fail"
    assert statuses["worker_postgres_target"] == "fail"


def test_deploy_config_worker_preflight_fails_for_core_only_secrets(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    service = DeployConfigService(repo_root)
    env_path = tmp_path / "worker-secrets.env"

    created = service.initialize_env_file(
        role="worker",
        output_path=env_path,
        overrides={
            "QE_POSTGRES_URL": "postgresql+psycopg://quant_evo:secret@100.64.0.20:5432/quant_evo",
            "QE_OPENAI_API_KEY": "relay-key",
            "QE_DISCORD_TOKEN": "discord-token",
            "QE_ALPACA_PAPER_API_KEY": "paper-key",
        },
        interactive=False,
    )

    report = service.run_preflight(role="worker", env_path=created)
    statuses = {check["key"]: check["status"] for check in report["checks"]}

    assert report["status"] == "fail"
    assert statuses["worker_secret_boundary"] == "fail"


def test_deploy_config_research_alias_initializes_canonical_worker_role(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    service = DeployConfigService(repo_root)
    env_path = tmp_path / "worker.env"

    created = service.initialize_env_file(
        role="research",
        output_path=env_path,
        overrides={
            "QE_POSTGRES_URL": "postgresql+psycopg://quant_evo:secret@100.64.0.30:5432/quant_evo",
            "QE_OPENAI_API_KEY": "relay-key",
            "QE_OPENAI_BASE_URL": "https://relay.example.com/v1",
        },
        interactive=False,
    )

    report = service.run_preflight(role="research", env_path=created)
    content = created.read_text(encoding="utf-8")

    assert "QE_NODE_ROLE=worker" in content
    assert report["status"] == "ok"


def test_deploy_config_core_public_dashboard_bootstrap_generates_security_values(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    service = DeployConfigService(repo_root)
    env_path = tmp_path / "core-public-dashboard.env"

    created = service.initialize_env_file(
        role="core",
        output_path=env_path,
        overrides={
            "QE_POSTGRES_PASSWORD": "super-secret-password",
            "QE_POSTGRES_BIND_HOST": "100.64.0.10",
            "QE_OPENAI_API_KEY": "relay-key",
            "QE_DISCORD_TOKEN": "discord-token",
            "QE_DISCORD_GUILD_ID": "123456789",
            "QE_DISCORD_CONTROL_CHANNEL_ID": "111",
            "QE_DISCORD_APPROVALS_CHANNEL_ID": "222",
            "QE_DISCORD_ALERTS_CHANNEL_ID": "333",
            "QE_DISCORD_ALLOWED_USER_IDS": "444,555",
            "QE_DASHBOARD_BIND_HOST": "0.0.0.0",
            "QE_API_BIND_HOST": "0.0.0.0",
            "QE_DASHBOARD_ACCESS_USERNAME": "",
            "QE_DASHBOARD_ACCESS_PASSWORD": "",
            "QE_DASHBOARD_API_TOKEN": "",
        },
        interactive=False,
    )

    report = service.run_preflight(role="core", env_path=created)
    statuses = {check["key"]: check["status"] for check in report["checks"]}
    content = created.read_text(encoding="utf-8")

    assert report["status"] == "ok"
    assert statuses["dashboard_surface"] == "ok"
    assert "QE_DASHBOARD_ACCESS_PASSWORD=" in content
    assert "QE_DASHBOARD_API_TOKEN=" in content
