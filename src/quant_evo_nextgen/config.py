from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="QE_",
        extra="ignore",
    )

    env: str = "development"
    repo_root: Path = Path(".")
    node_role: str = "core"
    deployment_topology: str = "single_node_bootstrap"
    operator_language: str = "zh-CN"
    operator_timezone: str = "Asia/Hong_Kong"
    market_timezone: str = "America/New_York"
    market_calendar: str = "XNYS"
    default_broker_provider_key: str = "paper-sim"
    default_broker_account_ref: str = "paper-main"
    default_broker_environment: str = "paper"
    default_broker_adapter: str = "paper_sim"
    default_allocation_policy_key: str = "paper-default"
    alpaca_api_key: str | None = None
    alpaca_api_secret: str | None = None
    alpaca_paper_api_key: str | None = None
    alpaca_paper_api_secret: str | None = None
    alpaca_live_api_key: str | None = None
    alpaca_live_api_secret: str | None = None
    alpaca_paper_base_url: str = "https://paper-api.alpaca.markets"
    alpaca_live_base_url: str = "https://api.alpaca.markets"
    alpaca_timeout_seconds: int = 30
    alpaca_sync_lookback_days: int = 14

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_bind_host: str = "127.0.0.1"
    api_host_port: int = 8000
    cors_allow_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    postgres_url: str = "postgresql+psycopg://quant_evo:quant_evo@postgres:5432/quant_evo"
    db_bootstrap_on_start: bool = True
    db_echo: bool = False

    discord_token: str | None = None
    discord_guild_id: int | None = None
    discord_control_channel: str = "control"
    discord_control_channel_id: int | None = None
    discord_approvals_channel: str = "approvals"
    discord_approvals_channel_id: int | None = None
    discord_alerts_channel: str = "alerts"
    discord_alerts_channel_id: int | None = None
    discord_allowed_user_ids: str = ""

    openai_api_key: str | None = None
    openai_base_url: str | None = None
    primary_model: str = "gpt-5"
    fast_model: str = "gpt-5-mini"
    codex_command: str = "codex"
    codex_default_model: str = "gpt-5.3-codex"
    codex_timeout_seconds: int = 1800
    codex_workspace_mode: str = "isolated_copy"
    web_fetch_base_url: str | None = None
    searxng_base_url: str | None = None
    rsshub_base_url: str | None = None
    browser_fallback_enabled: bool = False
    browser_fallback_endpoint: str | None = None
    playwright_browser_enabled: bool | None = None
    playwright_browser_endpoint: str | None = None
    skill_library_root: str = "skills"

    heartbeat_interval_seconds: int = 60
    dashboard_title: str = "Quant Evo Terminal"
    dashboard_bind_host: str = "127.0.0.1"
    dashboard_host_port: int = 3000
    dashboard_api_token: str | None = None
    dashboard_access_username: str | None = None
    dashboard_access_password: str | None = None
    edge_public_host: str | None = None
    edge_acme_email: str | None = None

    @computed_field
    @property
    def resolved_repo_root(self) -> Path:
        return self.repo_root.resolve()

    @property
    def cors_allow_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
