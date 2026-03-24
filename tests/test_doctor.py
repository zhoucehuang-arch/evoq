from pathlib import Path
from types import SimpleNamespace

from sqlalchemy import text

from quant_evo_nextgen.config import Settings
from quant_evo_nextgen.db.session import Database
from quant_evo_nextgen.services.doctor import DoctorService
from quant_evo_nextgen.services.state_store import StateStore


def test_doctor_reports_ok_on_bootstrapped_runtime(tmp_path: Path) -> None:
    database_path = tmp_path / "doctor.db"
    database = Database(f"sqlite+pysqlite:///{database_path}")
    database.create_schema()

    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{database_path}",
        discord_token="token",
        discord_allowed_user_ids="123456789",
        openai_api_key="relay-key",
        openai_base_url="https://relay.example.com/v1",
    )
    store = StateStore(database.session_factory)
    store.bootstrap_reference_data(settings)
    with database.session_scope() as session:
        session.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
        session.execute(text("INSERT INTO alembic_version (version_num) VALUES ('20260320_0014')"))
    report = DoctorService(database.session_factory, settings).run()
    profiles = {profile["key"]: profile for profile in report["profiles"]}

    assert report["status"] == "warn"
    assert any(check["key"] == "runtime_registry" and check["status"] == "ok" for check in report["checks"])
    assert any(check["key"] == "dashboard_security" and check["status"] == "warn" for check in report["checks"])
    assert profiles["node_vps_deploy"]["status"] == "ok"
    assert profiles["capital_activation"]["status"] == "fail"
    assert profiles["owner_target_full_system"]["status"] == "fail"

    database.dispose()


def test_doctor_warns_when_discord_and_codex_are_unconfigured(tmp_path: Path) -> None:
    database_path = tmp_path / "doctor-warn.db"
    database = Database(f"sqlite+pysqlite:///{database_path}")
    database.create_schema()

    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{database_path}",
    )
    store = StateStore(database.session_factory)
    store.bootstrap_reference_data(settings)
    report = DoctorService(database.session_factory, settings).run()

    statuses = {check["key"]: check["status"] for check in report["checks"]}
    profiles = {profile["key"]: profile for profile in report["profiles"]}
    assert report["status"] == "warn"
    assert statuses["discord"] == "warn"
    assert statuses["codex_provider"] == "warn"
    assert statuses["dashboard_security"] == "warn"
    assert statuses["broker"] == "ok"
    assert profiles["node_vps_deploy"]["status"] == "fail"
    assert profiles["capital_activation"]["status"] == "fail"

    database.dispose()


def test_doctor_fails_when_default_alpaca_broker_lacks_credentials(tmp_path: Path) -> None:
    database_path = tmp_path / "doctor-broker.db"
    database = Database(f"sqlite+pysqlite:///{database_path}")
    database.create_schema()

    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{database_path}",
        default_broker_adapter="alpaca",
        default_broker_provider_key="alpaca-paper",
        default_broker_account_ref="paper-main",
        default_broker_environment="paper",
    )
    store = StateStore(database.session_factory)
    store.bootstrap_reference_data(settings)
    report = DoctorService(database.session_factory, settings).run()

    statuses = {check["key"]: check["status"] for check in report["checks"]}
    profiles = {profile["key"]: profile for profile in report["profiles"]}
    assert report["status"] == "fail"
    assert statuses["broker"] == "fail"
    assert profiles["capital_activation"]["status"] == "fail"

    database.dispose()


def test_doctor_fails_when_cn_market_mode_uses_alpaca(tmp_path: Path) -> None:
    database_path = tmp_path / "doctor-cn-alpaca.db"
    database = Database(f"sqlite+pysqlite:///{database_path}")
    database.create_schema()

    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{database_path}",
        deployment_market_mode="cn",
        default_broker_adapter="alpaca",
        default_broker_provider_key="alpaca-paper",
        default_broker_account_ref="paper-main",
        default_broker_environment="paper",
    )
    store = StateStore(database.session_factory)
    store.bootstrap_reference_data(settings)
    report = DoctorService(database.session_factory, settings).run()

    statuses = {check["key"]: check["status"] for check in report["checks"]}
    assert report["status"] == "fail"
    assert statuses["broker"] == "fail"

    database.dispose()


def test_doctor_fails_when_worker_node_has_broker_secrets(tmp_path: Path) -> None:
    database_path = tmp_path / "doctor-worker-boundary.db"
    database = Database(f"sqlite+pysqlite:///{database_path}")
    database.create_schema()

    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{database_path}",
        node_role="worker",
        deployment_topology="two_vps_asymmetrical",
        default_broker_adapter="paper_sim",
        alpaca_paper_api_key="paper-key",
        alpaca_paper_api_secret="paper-secret",
    )
    store = StateStore(database.session_factory)
    store.bootstrap_reference_data(settings)
    report = DoctorService(database.session_factory, settings).run()

    statuses = {check["key"]: check["status"] for check in report["checks"]}
    assert report["status"] == "fail"
    assert statuses["node_role_boundary"] == "fail"

    database.dispose()


def test_doctor_warns_when_deprecated_research_alias_is_used(tmp_path: Path) -> None:
    database_path = tmp_path / "doctor-research-alias.db"
    database = Database(f"sqlite+pysqlite:///{database_path}")
    database.create_schema()

    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{database_path}",
        node_role="research",
        deployment_topology="two_vps_asymmetrical",
        default_broker_adapter="paper_sim",
        openai_api_key="relay-key",
    )
    store = StateStore(database.session_factory)
    store.bootstrap_reference_data(settings)
    report = DoctorService(database.session_factory, settings).run()

    statuses = {check["key"]: check["status"] for check in report["checks"]}
    assert statuses["node_role_boundary"] == "warn"

    database.dispose()


def test_doctor_fails_when_public_dashboard_surface_lacks_auth(tmp_path: Path) -> None:
    database_path = tmp_path / "doctor-dashboard-security.db"
    database = Database(f"sqlite+pysqlite:///{database_path}")
    database.create_schema()

    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{database_path}",
        dashboard_bind_host="0.0.0.0",
        api_bind_host="0.0.0.0",
    )
    store = StateStore(database.session_factory)
    store.bootstrap_reference_data(settings)
    report = DoctorService(database.session_factory, settings).run()

    statuses = {check["key"]: check["status"] for check in report["checks"]}
    profiles = {profile["key"]: profile for profile in report["profiles"]}
    assert report["status"] == "fail"
    assert statuses["dashboard_security"] == "fail"
    assert profiles["node_vps_deploy"]["status"] == "fail"

    database.dispose()


def test_doctor_surfaces_acquisition_probe_details(monkeypatch, tmp_path: Path) -> None:
    database_path = tmp_path / "doctor-acquisition.db"
    database = Database(f"sqlite+pysqlite:///{database_path}")
    database.create_schema()

    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{database_path}",
        openai_api_key="relay-key",
        searxng_base_url="http://searxng:8080",
    )
    store = StateStore(database.session_factory)
    store.bootstrap_reference_data(settings)

    def _raise_probe(*args, **kwargs):
        raise OSError("probe down")

    monkeypatch.setattr("quant_evo_nextgen.services.acquisition.urlopen", _raise_probe)
    report = DoctorService(database.session_factory, settings).run()

    acquisition_check = next(check for check in report["checks"] if check["key"] == "acquisition_stack")
    search_scrape_layer = next(layer for layer in acquisition_check["details"]["layers"] if layer["key"] == "search_scrape")

    assert acquisition_check["details"]["probe_endpoints"] is True
    assert search_scrape_layer["status"] == "warn"
    assert search_scrape_layer["details"]["probed"] is True

    database.dispose()


def test_doctor_owner_target_profile_can_turn_ok_when_runtime_is_fully_live_ready(
    monkeypatch,
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "doctor-owner-target-ok.db"
    database = Database(f"sqlite+pysqlite:///{database_path}")
    database.create_schema()

    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{database_path}",
        codex_workspace_mode="isolated_copy",
        default_broker_adapter="alpaca",
        default_broker_provider_key="alpaca-live",
        default_broker_account_ref="live-main",
        default_broker_environment="live",
        alpaca_live_api_key="live-key",
        alpaca_live_api_secret="live-secret",
        openai_api_key="relay-key",
        openai_base_url="https://relay.example.com/v1",
        discord_token="discord-token",
        discord_control_channel="owner-control",
        discord_approvals_channel="owner-approvals",
        discord_allowed_user_ids="123456789",
        dashboard_access_username="owner",
        dashboard_access_password="super-secret-password",
        dashboard_api_token="dashboard-token",
    )
    store = StateStore(database.session_factory)
    store.bootstrap_reference_data(settings)
    with database.session_scope() as session:
        session.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
        session.execute(text("INSERT INTO alembic_version (version_num) VALUES ('20260320_0014')"))

    doctor = DoctorService(database.session_factory, settings)
    monkeypatch.setattr(
        doctor.execution_service,
        "get_execution_readiness",
        lambda: SimpleNamespace(
            status="ready",
            trading_allowed=True,
            active_production_strategies=1,
            blocked_reasons=[],
        ),
    )

    report = doctor.run()
    profiles = {profile["key"]: profile for profile in report["profiles"]}

    assert profiles["owner_target_full_system"]["status"] == "ok"

    database.dispose()
