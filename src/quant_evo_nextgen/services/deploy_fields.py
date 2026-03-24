from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DeployFieldSpec:
    key: str
    label: str
    aliases: tuple[str, ...]
    env_key: str | None = None
    roles: tuple[str, ...] = ("core", "worker")
    secret: bool = False
    kind: str = "env"


def normalize_deploy_field_alias(alias: str) -> str:
    return (
        alias.strip()
        .lower()
        .replace(" ", "")
        .replace("_", "")
        .replace("-", "")
    )


_FIELD_SPECS: tuple[DeployFieldSpec, ...] = (
    DeployFieldSpec(
        key="relay_base_url",
        label="Relay Base URL",
        aliases=(
            "relay base url",
            "relaybaseurl",
            "relay url",
            "relay endpoint",
            "openai base url",
            "openai relay url",
        ),
        env_key="QE_OPENAI_BASE_URL",
    ),
    DeployFieldSpec(
        key="relay_api_key",
        label="Relay API Key",
        aliases=(
            "relay key",
            "relaykey",
            "relay api key",
            "openai api key",
            "api key",
        ),
        env_key="QE_OPENAI_API_KEY",
        secret=True,
    ),
    DeployFieldSpec(
        key="deployment_topology",
        label="Deployment Topology",
        aliases=(
            "deployment topology",
            "deploymenttopology",
            "topology",
        ),
        env_key="QE_DEPLOYMENT_TOPOLOGY",
        kind="topology",
    ),
    DeployFieldSpec(
        key="deployment_market_mode",
        label="Deployment Market Mode",
        aliases=(
            "deployment market mode",
            "deploymentmarketmode",
            "market mode",
            "marketmode",
            "target market",
        ),
        env_key="QE_DEPLOYMENT_MARKET_MODE",
        kind="market_mode",
    ),
    DeployFieldSpec(
        key="broker_mode",
        label="Broker Mode",
        aliases=(
            "broker mode",
            "brokermode",
            "broker profile",
        ),
        roles=("core",),
        kind="broker_mode",
    ),
    DeployFieldSpec(
        key="postgres_password",
        label="Postgres Password",
        aliases=(
            "postgres password",
            "postgrespassword",
            "postgres pwd",
        ),
        env_key="QE_POSTGRES_PASSWORD",
        roles=("core",),
        secret=True,
    ),
    DeployFieldSpec(
        key="postgres_url",
        label="Worker Postgres URL",
        aliases=(
            "worker postgres url",
            "postgresurl",
            "database url",
            "database connection",
        ),
        env_key="QE_POSTGRES_URL",
        roles=("worker",),
        secret=True,
    ),
    DeployFieldSpec(
        key="discord_token",
        label="Discord Bot Token",
        aliases=(
            "discord bot token",
            "discordtoken",
            "bot token",
        ),
        env_key="QE_DISCORD_TOKEN",
        roles=("core",),
        secret=True,
    ),
    DeployFieldSpec(
        key="discord_guild_id",
        label="Discord Guild ID",
        aliases=(
            "discord guild id",
            "guildid",
            "server id",
        ),
        env_key="QE_DISCORD_GUILD_ID",
        roles=("core",),
    ),
    DeployFieldSpec(
        key="discord_control_channel_id",
        label="Discord Control Channel ID",
        aliases=(
            "discord control channel id",
            "controlchannelid",
            "control channel id",
        ),
        env_key="QE_DISCORD_CONTROL_CHANNEL_ID",
        roles=("core",),
    ),
    DeployFieldSpec(
        key="discord_approvals_channel_id",
        label="Discord Approvals Channel ID",
        aliases=(
            "discord approvals channel id",
            "approvalschannelid",
            "approvals channel id",
        ),
        env_key="QE_DISCORD_APPROVALS_CHANNEL_ID",
        roles=("core",),
    ),
    DeployFieldSpec(
        key="discord_alerts_channel_id",
        label="Discord Alerts Channel ID",
        aliases=(
            "discord alerts channel id",
            "alertschannelid",
            "alerts channel id",
        ),
        env_key="QE_DISCORD_ALERTS_CHANNEL_ID",
        roles=("core",),
    ),
    DeployFieldSpec(
        key="discord_allowed_user_ids",
        label="Discord Allowed User IDs",
        aliases=(
            "discord allowed user ids",
            "alloweduserids",
            "allowed user ids",
            "allowed control user ids",
        ),
        env_key="QE_DISCORD_ALLOWED_USER_IDS",
        roles=("core",),
    ),
    DeployFieldSpec(
        key="dashboard_username",
        label="Dashboard Username",
        aliases=(
            "dashboard username",
            "dashboardusername",
            "dashboard user",
        ),
        env_key="QE_DASHBOARD_ACCESS_USERNAME",
        roles=("core",),
    ),
    DeployFieldSpec(
        key="dashboard_password",
        label="Dashboard Password",
        aliases=(
            "dashboard password",
            "dashboardpassword",
            "dashboard pwd",
        ),
        env_key="QE_DASHBOARD_ACCESS_PASSWORD",
        roles=("core",),
        secret=True,
    ),
    DeployFieldSpec(
        key="dashboard_api_token",
        label="Dashboard API Token",
        aliases=(
            "dashboard api token",
            "dashboardapitoken",
            "dashboard token",
        ),
        env_key="QE_DASHBOARD_API_TOKEN",
        roles=("core",),
        secret=True,
    ),
    DeployFieldSpec(
        key="edge_public_host",
        label="Dashboard Public Host",
        aliases=(
            "edge public host",
            "edgepublichost",
            "dashboard domain",
            "public host",
        ),
        env_key="QE_EDGE_PUBLIC_HOST",
        roles=("core",),
    ),
    DeployFieldSpec(
        key="edge_acme_email",
        label="ACME Email",
        aliases=(
            "acme email",
            "acmeemail",
            "tls email",
            "certificate email",
        ),
        env_key="QE_EDGE_ACME_EMAIL",
        roles=("core",),
    ),
    DeployFieldSpec(
        key="searxng_base_url",
        label="SearXNG Base URL",
        aliases=(
            "searxng",
            "searxng base url",
            "searxngbaseurl",
            "searxng url",
        ),
        env_key="QE_SEARXNG_BASE_URL",
    ),
    DeployFieldSpec(
        key="rsshub_base_url",
        label="RSSHub Base URL",
        aliases=(
            "rsshub",
            "rsshub base url",
            "rsshubbaseurl",
            "rsshub url",
        ),
        env_key="QE_RSSHUB_BASE_URL",
    ),
    DeployFieldSpec(
        key="playwright_browser_enabled",
        label="Playwright Enabled",
        aliases=(
            "playwright enabled",
            "playwrightenabled",
            "playwright browser enabled",
            "browser fallback enabled",
        ),
        env_key="QE_PLAYWRIGHT_BROWSER_ENABLED",
        kind="bool",
    ),
    DeployFieldSpec(
        key="playwright_browser_endpoint",
        label="Playwright Browser Endpoint",
        aliases=(
            "playwright endpoint",
            "playwrightendpoint",
            "playwright browser endpoint",
            "browser endpoint",
        ),
        env_key="QE_PLAYWRIGHT_BROWSER_ENDPOINT",
    ),
    DeployFieldSpec(
        key="skill_library_root",
        label="Skill Library Root",
        aliases=(
            "skill library root",
            "skilllibraryroot",
            "skills root",
            "skill root",
        ),
        env_key="QE_SKILL_LIBRARY_ROOT",
    ),
    DeployFieldSpec(
        key="codex_command",
        label="Codex Command",
        aliases=(
            "codex command",
            "codexcommand",
        ),
        env_key="QE_CODEX_COMMAND",
    ),
    DeployFieldSpec(
        key="codex_default_model",
        label="Codex Default Model",
        aliases=(
            "codex default model",
            "codexdefaultmodel",
            "codexmodel",
            "codex model",
        ),
        env_key="QE_CODEX_DEFAULT_MODEL",
    ),
    DeployFieldSpec(
        key="codex_workspace_mode",
        label="Codex Workspace Mode",
        aliases=(
            "codex workspace mode",
            "codexworkspacemode",
            "workspace mode",
        ),
        env_key="QE_CODEX_WORKSPACE_MODE",
    ),
    DeployFieldSpec(
        key="alpaca_paper_api_key",
        label="Alpaca Paper Key",
        aliases=("alpacapaperkey",),
        env_key="QE_ALPACA_PAPER_API_KEY",
        roles=("core",),
        secret=True,
    ),
    DeployFieldSpec(
        key="alpaca_paper_api_secret",
        label="Alpaca Paper Secret",
        aliases=("alpacapapersecret",),
        env_key="QE_ALPACA_PAPER_API_SECRET",
        roles=("core",),
        secret=True,
    ),
    DeployFieldSpec(
        key="alpaca_live_api_key",
        label="Alpaca Live Key",
        aliases=("alpacalivekey",),
        env_key="QE_ALPACA_LIVE_API_KEY",
        roles=("core",),
        secret=True,
    ),
    DeployFieldSpec(
        key="alpaca_live_api_secret",
        label="Alpaca Live Secret",
        aliases=("alpacalivesecret",),
        env_key="QE_ALPACA_LIVE_API_SECRET",
        roles=("core",),
        secret=True,
    ),
)

_FIELD_BY_ALIAS = {
    normalize_deploy_field_alias(alias): spec
    for spec in _FIELD_SPECS
    for alias in spec.aliases
}


def list_deploy_fields() -> tuple[DeployFieldSpec, ...]:
    return _FIELD_SPECS


def find_deploy_field(alias: str) -> DeployFieldSpec | None:
    return _FIELD_BY_ALIAS.get(normalize_deploy_field_alias(alias))


def resolve_deploy_field(alias: str, *, role: str) -> DeployFieldSpec:
    spec = find_deploy_field(alias)
    if spec is None:
        raise ValueError(f"IM deployment config does not support field `{alias}` yet.")
    if role not in spec.roles:
        raise ValueError(f"Field `{alias}` is not valid for role `{role}`.")
    return spec


def known_deploy_field_aliases() -> set[str]:
    return set(_FIELD_BY_ALIAS)


def sensitive_deploy_field_aliases() -> set[str]:
    return {
        normalize_deploy_field_alias(alias)
        for spec in _FIELD_SPECS
        if spec.secret
        for alias in spec.aliases
    }
