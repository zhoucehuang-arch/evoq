from pathlib import Path

from quant_evo_nextgen.services.owner_onboarding import OwnerOnboardingService


def test_owner_onboarding_bootstrap_and_status_use_temp_env_root(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    service = OwnerOnboardingService(repo_root, env_root=tmp_path)

    bootstrap = service.bootstrap_role("worker")
    status = service.status("worker")

    assert (tmp_path / "worker.env").exists()
    assert bootstrap.role == "worker"
    assert status.preflight_status in {"fail", "warn", "ok"}
    assert "worker" in status.summary_text


def test_owner_onboarding_sets_broker_mode_and_masks_secret_values(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    service = OwnerOnboardingService(repo_root, env_root=tmp_path)

    mode_result = service.set_field(role="core", field_alias="\u5238\u5546\u6a21\u5f0f", value="alpaca_paper")
    key_result = service.set_field(role="core", field_alias="\u4e2d\u8f6ckey", value="sk-super-secret-1234")
    env_content = (tmp_path / "core.env").read_text(encoding="utf-8")

    assert "QE_DEFAULT_BROKER_ADAPTER=alpaca" in env_content
    assert "QE_DEFAULT_BROKER_ENVIRONMENT=paper" in env_content
    assert "QE_OPENAI_API_KEY=sk-super-secret-1234" in env_content
    assert mode_result.masked_value == "alpaca_paper"
    assert key_result.masked_value.startswith("sk***")
    assert "sk-super-secret-1234" not in service.redact_secret_message("core", "\u4e2d\u8f6ckey")


def test_owner_onboarding_sets_single_vps_and_playwright_toggle(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    service = OwnerOnboardingService(repo_root, env_root=tmp_path)

    topology_result = service.set_field(role="core", field_alias="\u90e8\u7f72\u6a21\u5f0f", value="\u5355vps")
    browser_result = service.set_field(role="core", field_alias="playwright\u542f\u7528", value="\u542f\u7528")
    env_content = (tmp_path / "core.env").read_text(encoding="utf-8")

    assert topology_result.masked_value == "single_vps_compact"
    assert browser_result.masked_value == "true"
    assert "QE_DEPLOYMENT_TOPOLOGY=single_vps_compact" in env_content
    assert "QE_PLAYWRIGHT_BROWSER_ENABLED=true" in env_content
