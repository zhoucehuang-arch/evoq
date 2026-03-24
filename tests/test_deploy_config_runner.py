from pathlib import Path

from quant_evo_nextgen.runner.deploy_config import run


def test_deploy_config_runner_bootstrap_and_set_field(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]

    bootstrap_exit = run(
        [
            "--repo-root",
            str(repo_root),
            "--env-root",
            str(tmp_path),
            "bootstrap",
            "core",
        ]
    )
    set_exit = run(
        [
            "--repo-root",
            str(repo_root),
            "--env-root",
            str(tmp_path),
            "set-field",
            "core",
            "\u90e8\u7f72\u6a21\u5f0f",
            "single_vps_compact",
        ]
    )

    env_content = (tmp_path / "core.env").read_text(encoding="utf-8")

    assert bootstrap_exit in {0, 1}
    assert set_exit in {0, 1}
    assert "QE_DEPLOYMENT_TOPOLOGY=single_vps_compact" in env_content


def test_deploy_config_runner_onboard_single_vps(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    env_path = tmp_path / "core-single-vps.env"

    exit_code = run(
        [
            "--repo-root",
            str(repo_root),
            "onboard-single-vps",
            "--output",
            str(env_path),
            "--no-prompt",
            "--set",
            "QE_POSTGRES_PASSWORD=super-secret-password",
            "--set",
            "QE_OPENAI_API_KEY=relay-key",
            "--set",
            "QE_OPENAI_BASE_URL=https://relay.example.com/v1",
            "--set",
            "QE_DISCORD_TOKEN=discord-token",
            "--set",
            "QE_DISCORD_GUILD_ID=123456789",
            "--set",
            "QE_DISCORD_CONTROL_CHANNEL_ID=111",
            "--set",
            "QE_DISCORD_APPROVALS_CHANNEL_ID=222",
            "--set",
            "QE_DISCORD_ALERTS_CHANNEL_ID=333",
            "--set",
            "QE_DISCORD_ALLOWED_USER_IDS=444,555",
        ]
    )

    env_content = env_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert "QE_DEPLOYMENT_TOPOLOGY=single_vps_compact" in env_content
    assert "QE_DEFAULT_BROKER_ADAPTER=paper_sim" in env_content
    assert "QE_DASHBOARD_ACCESS_USERNAME=owner" in env_content
    assert "QE_DASHBOARD_ACCESS_PASSWORD=" in env_content
    assert "QE_DASHBOARD_API_TOKEN=" in env_content


def test_deploy_config_runner_onboard_single_vps_cn_market_mode(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    env_path = tmp_path / "core-single-vps-cn.env"

    exit_code = run(
        [
            "--repo-root",
            str(repo_root),
            "onboard-single-vps",
            "--output",
            str(env_path),
            "--no-prompt",
            "--market-mode",
            "cn",
            "--set",
            "QE_POSTGRES_PASSWORD=super-secret-password",
            "--set",
            "QE_OPENAI_API_KEY=relay-key",
            "--set",
            "QE_OPENAI_BASE_URL=https://relay.example.com/v1",
            "--set",
            "QE_DISCORD_TOKEN=discord-token",
            "--set",
            "QE_DISCORD_GUILD_ID=123456789",
            "--set",
            "QE_DISCORD_CONTROL_CHANNEL_ID=111",
            "--set",
            "QE_DISCORD_APPROVALS_CHANNEL_ID=222",
            "--set",
            "QE_DISCORD_ALERTS_CHANNEL_ID=333",
            "--set",
            "QE_DISCORD_ALLOWED_USER_IDS=444,555",
        ]
    )

    env_content = env_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert "QE_DEPLOYMENT_MARKET_MODE=cn" in env_content
    assert "QE_MARKET_TIMEZONE=Asia/Shanghai" in env_content
    assert "QE_MARKET_CALENDAR=XSHG" in env_content
