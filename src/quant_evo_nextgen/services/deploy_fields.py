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
            "\u4e2d\u8f6c\u5730\u5740",
            "\u4e2d\u8f6curl",
            "relaybaseurl",
            "relayurl",
            "relayendpoint",
            "openaibaseurl",
            "openairelayurl",
        ),
        env_key="QE_OPENAI_BASE_URL",
    ),
    DeployFieldSpec(
        key="relay_api_key",
        label="Relay API Key",
        aliases=(
            "\u4e2d\u8f6ckey",
            "\u4e2d\u8f6capikey",
            "relaykey",
            "relayapikey",
            "openaiapikey",
            "apikey",
        ),
        env_key="QE_OPENAI_API_KEY",
        secret=True,
    ),
    DeployFieldSpec(
        key="deployment_topology",
        label="Deployment Topology",
        aliases=(
            "\u90e8\u7f72\u6a21\u5f0f",
            "\u90e8\u7f72\u62d3\u6251",
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
            "\u5e02\u573a\u6a21\u5f0f",
            "\u90e8\u7f72\u5e02\u573a",
            "deploymentmarketmode",
            "marketmode",
            "targetmarket",
        ),
        env_key="QE_DEPLOYMENT_MARKET_MODE",
        kind="market_mode",
    ),
    DeployFieldSpec(
        key="broker_mode",
        label="Broker Mode",
        aliases=(
            "\u5238\u5546\u6a21\u5f0f",
            "brokermode",
            "brokerprofile",
        ),
        roles=("core",),
        kind="broker_mode",
    ),
    DeployFieldSpec(
        key="postgres_password",
        label="Postgres Password",
        aliases=(
            "postgrespassword",
            "postgrespwd",
            "postgres\u5bc6\u7801",
        ),
        env_key="QE_POSTGRES_PASSWORD",
        roles=("core",),
        secret=True,
    ),
    DeployFieldSpec(
        key="postgres_url",
        label="Worker Postgres URL",
        aliases=(
            "postgresurl",
            "\u6570\u636e\u5e93url",
            "\u6570\u636e\u5e93\u8fde\u63a5",
        ),
        env_key="QE_POSTGRES_URL",
        roles=("worker",),
        secret=True,
    ),
    DeployFieldSpec(
        key="discord_token",
        label="Discord Bot Token",
        aliases=(
            "discordtoken",
            "bottoken",
            "\u673a\u5668\u4ebatoken",
        ),
        env_key="QE_DISCORD_TOKEN",
        roles=("core",),
        secret=True,
    ),
    DeployFieldSpec(
        key="discord_guild_id",
        label="Discord Guild ID",
        aliases=(
            "guildid",
            "\u670d\u52a1\u5668id",
        ),
        env_key="QE_DISCORD_GUILD_ID",
        roles=("core",),
    ),
    DeployFieldSpec(
        key="discord_control_channel_id",
        label="Discord Control Channel ID",
        aliases=(
            "controlchannelid",
            "\u63a7\u5236\u9891\u9053id",
        ),
        env_key="QE_DISCORD_CONTROL_CHANNEL_ID",
        roles=("core",),
    ),
    DeployFieldSpec(
        key="discord_approvals_channel_id",
        label="Discord Approvals Channel ID",
        aliases=(
            "approvalschannelid",
            "\u5ba1\u6279\u9891\u9053id",
        ),
        env_key="QE_DISCORD_APPROVALS_CHANNEL_ID",
        roles=("core",),
    ),
    DeployFieldSpec(
        key="discord_alerts_channel_id",
        label="Discord Alerts Channel ID",
        aliases=(
            "alertschannelid",
            "\u544a\u8b66\u9891\u9053id",
        ),
        env_key="QE_DISCORD_ALERTS_CHANNEL_ID",
        roles=("core",),
    ),
    DeployFieldSpec(
        key="discord_allowed_user_ids",
        label="Discord Allowed User IDs",
        aliases=(
            "alloweduserids",
            "\u5141\u8bb8\u7528\u6237id",
            "\u5141\u8bb8\u63a7\u5236\u7528\u6237id",
        ),
        env_key="QE_DISCORD_ALLOWED_USER_IDS",
        roles=("core",),
    ),
    DeployFieldSpec(
        key="dashboard_username",
        label="Dashboard Username",
        aliases=(
            "dashboardusername",
            "dashboarduser",
            "dashboard\u7528\u6237\u540d",
        ),
        env_key="QE_DASHBOARD_ACCESS_USERNAME",
        roles=("core",),
    ),
    DeployFieldSpec(
        key="dashboard_password",
        label="Dashboard Password",
        aliases=(
            "dashboardpassword",
            "dashboardpwd",
            "dashboard\u5bc6\u7801",
        ),
        env_key="QE_DASHBOARD_ACCESS_PASSWORD",
        roles=("core",),
        secret=True,
    ),
    DeployFieldSpec(
        key="dashboard_api_token",
        label="Dashboard API Token",
        aliases=(
            "dashboardapitoken",
            "dashboardtoken",
            "dashboardapi\u4ee4\u724c",
        ),
        env_key="QE_DASHBOARD_API_TOKEN",
        roles=("core",),
        secret=True,
    ),
    DeployFieldSpec(
        key="edge_public_host",
        label="Dashboard Public Host",
        aliases=(
            "edgepublichost",
            "dashboarddomain",
            "dashboard\u57df\u540d",
            "\u516c\u7f51\u57df\u540d",
        ),
        env_key="QE_EDGE_PUBLIC_HOST",
        roles=("core",),
    ),
    DeployFieldSpec(
        key="edge_acme_email",
        label="ACME Email",
        aliases=(
            "acmeemail",
            "tlsemail",
            "\u8bc1\u4e66\u90ae\u7bb1",
        ),
        env_key="QE_EDGE_ACME_EMAIL",
        roles=("core",),
    ),
    DeployFieldSpec(
        key="searxng_base_url",
        label="SearXNG Base URL",
        aliases=(
            "searxng",
            "searxngbaseurl",
            "searxngurl",
            "searxng\u5730\u5740",
        ),
        env_key="QE_SEARXNG_BASE_URL",
    ),
    DeployFieldSpec(
        key="rsshub_base_url",
        label="RSSHub Base URL",
        aliases=(
            "rsshub",
            "rsshubbaseurl",
            "rsshuburl",
            "rsshub\u5730\u5740",
        ),
        env_key="QE_RSSHUB_BASE_URL",
    ),
    DeployFieldSpec(
        key="playwright_browser_enabled",
        label="Playwright Enabled",
        aliases=(
            "playwrightenabled",
            "playwrightbrowserenabled",
            "browserfallbackenabled",
            "playwright\u542f\u7528",
            "\u6d4f\u89c8\u5668\u56de\u9000\u542f\u7528",
        ),
        env_key="QE_PLAYWRIGHT_BROWSER_ENABLED",
        kind="bool",
    ),
    DeployFieldSpec(
        key="playwright_browser_endpoint",
        label="Playwright Browser Endpoint",
        aliases=(
            "playwrightendpoint",
            "playwrightbrowserendpoint",
            "browserendpoint",
            "playwright\u5730\u5740",
        ),
        env_key="QE_PLAYWRIGHT_BROWSER_ENDPOINT",
    ),
    DeployFieldSpec(
        key="skill_library_root",
        label="Skill Library Root",
        aliases=(
            "skilllibraryroot",
            "skillsroot",
            "\u6280\u80fd\u76ee\u5f55",
            "skill\u76ee\u5f55",
        ),
        env_key="QE_SKILL_LIBRARY_ROOT",
    ),
    DeployFieldSpec(
        key="codex_command",
        label="Codex Command",
        aliases=(
            "codexcommand",
            "codex\u547d\u4ee4",
        ),
        env_key="QE_CODEX_COMMAND",
    ),
    DeployFieldSpec(
        key="codex_default_model",
        label="Codex Default Model",
        aliases=(
            "codexdefaultmodel",
            "codexmodel",
            "codex\u6a21\u578b",
        ),
        env_key="QE_CODEX_DEFAULT_MODEL",
    ),
    DeployFieldSpec(
        key="codex_workspace_mode",
        label="Codex Workspace Mode",
        aliases=(
            "codexworkspacemode",
            "workspacemode",
            "codex\u5de5\u4f5c\u533a\u6a21\u5f0f",
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
