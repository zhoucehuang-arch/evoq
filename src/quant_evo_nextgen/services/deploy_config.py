from __future__ import annotations

from dataclasses import asdict, dataclass
from getpass import getpass
from ipaddress import ip_address, ip_network
from pathlib import Path
import secrets
from typing import Any, Callable, Mapping

from sqlalchemy.engine import make_url

from quant_evo_nextgen.config import Settings


PRIVATE_NETWORKS = (
    ip_network("10.0.0.0/8"),
    ip_network("172.16.0.0/12"),
    ip_network("192.168.0.0/16"),
    ip_network("100.64.0.0/10"),
)
PLACEHOLDER_VALUES = {
    "",
    "change-me-now",
    "CORE_VPS_IP",
    "postgresql+psycopg://quant_evo:change-me-now@CORE_VPS_IP:5432/quant_evo",
}
SUPPORTED_DEPLOYMENT_TOPOLOGIES = {
    "single_vps_compact",
    "two_vps_asymmetrical",
}
SUPPORTED_DEPLOYMENT_MARKET_MODES = {
    "us",
    "cn",
}


@dataclass(slots=True)
class DeployConfigCheck:
    key: str
    label: str
    status: str
    message: str
    details: dict[str, Any]


@dataclass(slots=True)
class PromptField:
    key: str
    prompt: str
    secret: bool = False
    optional: bool = False


def normalize_deploy_role(role: str) -> str:
    normalized = role.strip().lower()
    if normalized == "research":
        return "worker"
    if normalized not in {"core", "worker"}:
        raise ValueError(f"Unsupported deploy role: {role}")
    return normalized


class DeployConfigService:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root.resolve()

    def example_env_path(self, role: str) -> Path:
        normalized = normalize_deploy_role(role)
        if normalized == "core":
            return self.repo_root / "ops" / "production" / "core" / "core.env.example"
        return self.repo_root / "ops" / "production" / "worker" / "worker.env.example"

    def default_env_path(self, role: str) -> Path:
        normalized = normalize_deploy_role(role)
        if normalized == "core":
            return self.repo_root / "ops" / "production" / "core" / "core.env"
        return self.repo_root / "ops" / "production" / "worker" / "worker.env"

    def initialize_env_file(
        self,
        *,
        role: str,
        output_path: Path | None = None,
        overrides: Mapping[str, str] | None = None,
        overwrite: bool = False,
        interactive: bool = True,
        prompt: Callable[[str], str] | None = None,
        secret_prompt: Callable[[str], str] | None = None,
        prompt_profile: str = "full",
    ) -> Path:
        normalized = normalize_deploy_role(role)
        example_path = self.example_env_path(normalized)
        target_path = output_path or self.default_env_path(normalized)
        target_path = target_path if target_path.is_absolute() else (self.repo_root / target_path).resolve()

        if target_path.exists() and not overwrite and not interactive and not overrides:
            raise ValueError(f"Refusing to overwrite existing env file without overrides: {target_path}")

        template_lines = example_path.read_text(encoding="utf-8").splitlines()
        values = self._read_env_values(example_path)
        values.update(self._role_defaults(normalized))
        if target_path.exists() and not overwrite:
            values.update(self._read_env_values(target_path))
        if overrides:
            values.update({key: value for key, value in overrides.items() if key.startswith("QE_")})

        broker_mode = str((overrides or {}).get("__broker_mode__", "") or values.get("__broker_mode__", "paper_sim")).strip().lower()
        market_mode = str(
            (overrides or {}).get("__market_mode__", "")
            or values.get("__market_mode__", values.get("QE_DEPLOYMENT_MARKET_MODE", "us"))
        ).strip().lower()
        prompt_fn = prompt or input

        if interactive:
            values = self._prompt_for_role_values(
                role=normalized,
                values=values,
                prompt=prompt_fn,
                secret_prompt=secret_prompt or getpass,
                prompt_profile=prompt_profile,
            )
            if normalized == "core" and prompt_profile == "full":
                broker_mode = self._prompt_broker_mode(prompt_fn, broker_mode)

        self._apply_market_mode(values, market_mode)
        self._apply_broker_mode(values, broker_mode)
        if normalized == "core":
            self._ensure_core_security_defaults(values)
        rendered = self._render_env_file(template_lines, values)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(rendered + "\n", encoding="utf-8")
        return target_path

    def ensure_env_file(
        self,
        *,
        role: str,
        output_path: Path | None = None,
        broker_mode: str | None = None,
        market_mode: str | None = None,
    ) -> Path:
        normalized = normalize_deploy_role(role)
        target_path = output_path or self.default_env_path(normalized)
        target_path = target_path if target_path.is_absolute() else (self.repo_root / target_path).resolve()
        if target_path.exists():
            return target_path
        overrides: dict[str, str] | None = None
        if broker_mode or market_mode:
            overrides = {}
            if broker_mode:
                overrides["__broker_mode__"] = broker_mode
            if market_mode:
                overrides["__market_mode__"] = market_mode
        return self.initialize_env_file(
            role=normalized,
            output_path=target_path,
            overrides=overrides,
            interactive=False,
        )

    def update_env_file(
        self,
        *,
        role: str,
        updates: Mapping[str, str] | None = None,
        output_path: Path | None = None,
        broker_mode: str | None = None,
        market_mode: str | None = None,
    ) -> Path:
        normalized = normalize_deploy_role(role)
        target_path = self.ensure_env_file(
            role=normalized,
            output_path=output_path,
            broker_mode=broker_mode,
            market_mode=market_mode,
        )
        example_path = self.example_env_path(normalized)
        template_lines = example_path.read_text(encoding="utf-8").splitlines()
        values = self._read_env_values(example_path)
        values.update(self._role_defaults(normalized))
        values.update(self._read_env_values(target_path))
        if market_mode:
            self._apply_market_mode(values, market_mode)
        if broker_mode:
            self._apply_broker_mode(values, broker_mode)
        if updates:
            values.update({key: value for key, value in updates.items() if key.startswith("QE_")})
        if normalized == "core":
            self._ensure_core_security_defaults(values)
        rendered = self._render_env_file(template_lines, values)
        target_path.write_text(rendered + "\n", encoding="utf-8")
        return target_path

    def run_preflight(self, *, role: str, env_path: Path) -> dict[str, Any]:
        normalized = normalize_deploy_role(role)
        resolved_env = env_path if env_path.is_absolute() else (self.repo_root / env_path).resolve()
        if not resolved_env.exists():
            return {
                "status": "fail",
                "role": normalized,
                "env_path": str(resolved_env),
                "checks": [
                    asdict(
                        DeployConfigCheck(
                            key="env_file",
                            label="Env File Presence",
                            status="fail",
                            message=f"Env file does not exist: {resolved_env}",
                            details={},
                        )
                    )
                ],
            }

        raw_values = self._read_env_values(resolved_env)
        try:
            settings = Settings(_env_file=str(resolved_env), repo_root=self.repo_root)
        except Exception as exc:
            return {
                "status": "fail",
                "role": normalized,
                "env_path": str(resolved_env),
                "checks": [
                    asdict(
                        DeployConfigCheck(
                            key="env_parse",
                            label="Env Parse",
                            status="fail",
                            message=f"Env file could not be parsed by runtime settings: {exc}",
                            details={},
                        )
                    )
                ],
            }

        checks = [
            self._check_role_alignment(role=normalized, raw_values=raw_values, settings=settings),
            self._check_runtime_profile(role=normalized, raw_values=raw_values, settings=settings),
            self._check_codex_provider(raw_values=raw_values, settings=settings),
        ]
        if normalized == "core":
            checks.extend(
                [
                    self._check_core_discord(raw_values=raw_values),
                    self._check_core_broker(raw_values=raw_values, settings=settings),
                    self._check_core_postgres_exposure(raw_values=raw_values, settings=settings),
                    self._check_core_dashboard_security(raw_values=raw_values, settings=settings),
                ]
            )
        else:
            checks.extend(
                [
                    self._check_worker_postgres_target(raw_values=raw_values),
                    self._check_worker_secret_boundary(raw_values=raw_values),
                ]
            )

        overall_status = "ok"
        if any(check.status == "fail" for check in checks):
            overall_status = "fail"
        elif any(check.status == "warn" for check in checks):
            overall_status = "warn"

        return {
            "status": overall_status,
            "role": normalized,
            "env_path": str(resolved_env),
            "checks": [asdict(check) for check in checks],
        }

    def render_preflight_report(self, report: dict[str, Any]) -> str:
        lines = [f"Quant Evo Deploy Preflight ({report['role']}): {report['status']}"]
        for check in report["checks"]:
            lines.append(f"- [{check['status']}] {check['label']}: {check['message']}")
        return "\n".join(lines)

    def _prompt_for_role_values(
        self,
        *,
        role: str,
        values: dict[str, str],
        prompt: Callable[[str], str],
        secret_prompt: Callable[[str], str],
        prompt_profile: str,
    ) -> dict[str, str]:
        for field in self._prompt_fields(role, prompt_profile=prompt_profile):
            default = values.get(field.key, "").strip()
            suffix = " [Optional]" if field.optional else ""
            prompt_text = f"{field.prompt}{suffix}"
            if default:
                prompt_text = f"{prompt_text} [{default}]"
            prompt_text = f"{prompt_text}: "
            answer = secret_prompt(prompt_text) if field.secret else prompt(prompt_text)
            if answer.strip():
                values[field.key] = answer.strip()
        return values

    def _prompt_broker_mode(self, prompt: Callable[[str], str], current_mode: str) -> str:
        default = current_mode or "paper_sim"
        answer = prompt(
            "Core broker mode [paper_sim/alpaca_paper/alpaca_live]"
            f" [{default}]: "
        ).strip().lower()
        return answer or default

    def _prompt_fields(self, role: str, *, prompt_profile: str = "full") -> list[PromptField]:
        if role == "core":
            if prompt_profile == "single_vps_minimal":
                return [
                    PromptField("__market_mode__", "Deployment market mode [us/cn]", optional=True),
                    PromptField("QE_POSTGRES_PASSWORD", "Postgres password", secret=True),
                    PromptField("QE_OPENAI_API_KEY", "Relay or OpenAI API key", secret=True),
                    PromptField("QE_OPENAI_BASE_URL", "Relay base URL", optional=True),
                    PromptField("QE_DISCORD_TOKEN", "Discord bot token", secret=True),
                    PromptField("QE_DISCORD_GUILD_ID", "Discord guild ID"),
                    PromptField("QE_DISCORD_CONTROL_CHANNEL_ID", "Discord control channel ID"),
                    PromptField("QE_DISCORD_APPROVALS_CHANNEL_ID", "Discord approvals channel ID"),
                    PromptField("QE_DISCORD_ALERTS_CHANNEL_ID", "Discord alerts channel ID"),
                    PromptField("QE_DISCORD_ALLOWED_USER_IDS", "Allowed Discord user IDs, comma-separated"),
                ]
            return [
                PromptField("__market_mode__", "Deployment market mode [us/cn]", optional=True),
                PromptField("QE_POSTGRES_PASSWORD", "Postgres password", secret=True),
                PromptField("QE_OPENAI_API_KEY", "Relay or OpenAI API key", secret=True),
                PromptField("QE_OPENAI_BASE_URL", "Relay base URL", optional=True),
                PromptField("QE_DISCORD_TOKEN", "Discord bot token", secret=True),
                PromptField("QE_DISCORD_GUILD_ID", "Discord guild ID"),
                PromptField("QE_DISCORD_CONTROL_CHANNEL_ID", "Discord control channel ID"),
                PromptField("QE_DISCORD_APPROVALS_CHANNEL_ID", "Discord approvals channel ID"),
                PromptField("QE_DISCORD_ALERTS_CHANNEL_ID", "Discord alerts channel ID"),
                PromptField("QE_DISCORD_ALLOWED_USER_IDS", "Allowed Discord user IDs, comma-separated"),
                PromptField("QE_DASHBOARD_ACCESS_USERNAME", "Dashboard login username", optional=True),
                PromptField("QE_DASHBOARD_ACCESS_PASSWORD", "Dashboard login password", secret=True, optional=True),
                PromptField("QE_DASHBOARD_API_TOKEN", "Dashboard API shared token", secret=True, optional=True),
                PromptField("QE_EDGE_PUBLIC_HOST", "Dashboard public domain", optional=True),
                PromptField("QE_EDGE_ACME_EMAIL", "ACME email for Caddy HTTPS", optional=True),
                PromptField("QE_SEARXNG_BASE_URL", "SearXNG or local search/scrape base URL", optional=True),
                PromptField("QE_RSSHUB_BASE_URL", "RSSHub base URL", optional=True),
                PromptField("QE_PLAYWRIGHT_BROWSER_ENDPOINT", "Playwright browser endpoint", optional=True),
                PromptField("QE_ALPACA_PAPER_API_KEY", "Alpaca paper API key", secret=True, optional=True),
                PromptField("QE_ALPACA_PAPER_API_SECRET", "Alpaca paper API secret", secret=True, optional=True),
                PromptField("QE_ALPACA_LIVE_API_KEY", "Alpaca live API key", secret=True, optional=True),
                PromptField("QE_ALPACA_LIVE_API_SECRET", "Alpaca live API secret", secret=True, optional=True),
            ]
        return [
            PromptField("__market_mode__", "Deployment market mode [us/cn]", optional=True),
            PromptField(
                "QE_POSTGRES_URL",
                "Core Postgres URL"
                " (example: postgresql+psycopg://quant_evo:<password>@100.x.x.x:5432/quant_evo)",
            ),
            PromptField("QE_OPENAI_API_KEY", "Relay or OpenAI API key", secret=True),
            PromptField("QE_OPENAI_BASE_URL", "Relay base URL", optional=True),
            PromptField("QE_SEARXNG_BASE_URL", "SearXNG or local search/scrape base URL", optional=True),
            PromptField("QE_RSSHUB_BASE_URL", "RSSHub base URL", optional=True),
            PromptField("QE_PLAYWRIGHT_BROWSER_ENDPOINT", "Playwright browser endpoint", optional=True),
        ]

    def _role_defaults(self, role: str) -> dict[str, str]:
        if role == "core":
            return {
                "QE_ENV": "production",
                "QE_NODE_ROLE": "core",
                "QE_DEPLOYMENT_TOPOLOGY": "two_vps_asymmetrical",
                "QE_DEPLOYMENT_MARKET_MODE": "us",
                "QE_DEFAULT_BROKER_PROVIDER_KEY": "paper-sim",
                "QE_DEFAULT_BROKER_ACCOUNT_REF": "paper-main",
                "QE_DEFAULT_BROKER_ENVIRONMENT": "paper",
                "QE_DEFAULT_BROKER_ADAPTER": "paper_sim",
                "QE_MARKET_TIMEZONE": "America/New_York",
                "QE_MARKET_CALENDAR": "XNYS",
                "QE_POSTGRES_BIND_HOST": "127.0.0.1",
                "QE_API_BIND_HOST": "127.0.0.1",
                "QE_DASHBOARD_BIND_HOST": "127.0.0.1",
                "QE_DASHBOARD_ACCESS_USERNAME": "owner",
                "QE_EDGE_PUBLIC_HOST": "",
                "QE_EDGE_ACME_EMAIL": "",
                "QE_SEARXNG_BASE_URL": "",
                "QE_RSSHUB_BASE_URL": "",
                "QE_PLAYWRIGHT_BROWSER_ENABLED": "false",
                "QE_PLAYWRIGHT_BROWSER_ENDPOINT": "",
                "QE_SKILL_LIBRARY_ROOT": "skills",
            }
        return {
            "QE_ENV": "production",
            "QE_NODE_ROLE": "worker",
            "QE_DEPLOYMENT_TOPOLOGY": "two_vps_asymmetrical",
            "QE_DEPLOYMENT_MARKET_MODE": "us",
            "QE_MARKET_TIMEZONE": "America/New_York",
            "QE_MARKET_CALENDAR": "XNYS",
            "QE_SEARXNG_BASE_URL": "",
            "QE_RSSHUB_BASE_URL": "",
            "QE_PLAYWRIGHT_BROWSER_ENABLED": "false",
            "QE_PLAYWRIGHT_BROWSER_ENDPOINT": "",
            "QE_SKILL_LIBRARY_ROOT": "skills",
        }

    def _apply_market_mode(self, values: dict[str, str], market_mode: str) -> None:
        normalized = market_mode.strip().lower() or "us"
        if normalized == "us":
            values["QE_DEPLOYMENT_MARKET_MODE"] = "us"
            values["QE_MARKET_TIMEZONE"] = "America/New_York"
            values["QE_MARKET_CALENDAR"] = "XNYS"
        elif normalized == "cn":
            values["QE_DEPLOYMENT_MARKET_MODE"] = "cn"
            values["QE_MARKET_TIMEZONE"] = "Asia/Shanghai"
            values["QE_MARKET_CALENDAR"] = "XSHG"
        else:
            raise ValueError(f"Unsupported market mode: {market_mode}")
        values["__market_mode__"] = normalized

    def _apply_broker_mode(self, values: dict[str, str], broker_mode: str) -> None:
        normalized = broker_mode.strip().lower() or "paper_sim"
        if normalized == "paper_sim":
            values["QE_DEFAULT_BROKER_PROVIDER_KEY"] = "paper-sim"
            values["QE_DEFAULT_BROKER_ACCOUNT_REF"] = "paper-main"
            values["QE_DEFAULT_BROKER_ENVIRONMENT"] = "paper"
            values["QE_DEFAULT_BROKER_ADAPTER"] = "paper_sim"
        elif normalized == "alpaca_paper":
            values["QE_DEFAULT_BROKER_PROVIDER_KEY"] = "alpaca-paper"
            values["QE_DEFAULT_BROKER_ACCOUNT_REF"] = "paper-main"
            values["QE_DEFAULT_BROKER_ENVIRONMENT"] = "paper"
            values["QE_DEFAULT_BROKER_ADAPTER"] = "alpaca"
        elif normalized == "alpaca_live":
            values["QE_DEFAULT_BROKER_PROVIDER_KEY"] = "alpaca-live"
            values["QE_DEFAULT_BROKER_ACCOUNT_REF"] = "live-main"
            values["QE_DEFAULT_BROKER_ENVIRONMENT"] = "live"
            values["QE_DEFAULT_BROKER_ADAPTER"] = "alpaca"
        else:
            raise ValueError(f"Unsupported broker mode: {broker_mode}")
        values["__broker_mode__"] = normalized

    def _check_role_alignment(
        self,
        *,
        role: str,
        raw_values: dict[str, str],
        settings: Settings,
    ) -> DeployConfigCheck:
        raw_node_role = raw_values.get("QE_NODE_ROLE", "").strip().lower()
        effective_role = "worker" if raw_node_role == "research" else settings.node_role
        if effective_role != role:
            return DeployConfigCheck(
                key="role_alignment",
                label="Role Alignment",
                status="fail",
                message=f"Env file role `{raw_node_role or settings.node_role}` does not match expected role `{role}`.",
                details={"env_node_role": raw_node_role or settings.node_role, "expected_role": role},
            )
        if raw_node_role == "research":
            return DeployConfigCheck(
                key="role_alignment",
                label="Role Alignment",
                status="warn",
                message="Env file still uses deprecated `research` role naming. Switch it to `worker` for the canonical path.",
                details={"env_node_role": raw_node_role, "expected_role": role},
            )
        return DeployConfigCheck(
            key="role_alignment",
            label="Role Alignment",
            status="ok",
            message="Env file role matches the canonical deployment role.",
            details={"env_node_role": raw_node_role or settings.node_role, "expected_role": role},
        )

    def _check_runtime_profile(
        self,
        *,
        role: str,
        raw_values: dict[str, str],
        settings: Settings,
    ) -> DeployConfigCheck:
        issues: list[str] = []
        if settings.env != "production":
            issues.append("QE_ENV should be production for VPS deployment.")
        topology = (settings.deployment_topology or "").strip().lower()
        if topology not in SUPPORTED_DEPLOYMENT_TOPOLOGIES:
            issues.append(
                "QE_DEPLOYMENT_TOPOLOGY should be either `single_vps_compact` or `two_vps_asymmetrical`."
            )
        market_mode = (settings.deployment_market_mode or "").strip().lower()
        if market_mode not in SUPPORTED_DEPLOYMENT_MARKET_MODES:
            issues.append("QE_DEPLOYMENT_MARKET_MODE should be either `us` or `cn`.")
        if role == "worker" and topology != "two_vps_asymmetrical":
            return DeployConfigCheck(
                key="runtime_profile",
                label="Runtime Profile",
                status="fail",
                message="Worker env files are only valid for the two-VPS topology. Single-VPS deployments should bootstrap only the Core env.",
                details={"deployment_topology": settings.deployment_topology, "role": role},
            )
        if settings.heartbeat_interval_seconds <= 0:
            return DeployConfigCheck(
                key="runtime_profile",
                label="Runtime Profile",
                status="fail",
                message="Heartbeat interval must be positive.",
                details={"heartbeat_interval_seconds": settings.heartbeat_interval_seconds},
            )
        if issues:
            return DeployConfigCheck(
                key="runtime_profile",
                label="Runtime Profile",
                status="warn",
                message="Runtime profile is parseable but not aligned with the recommended VPS defaults.",
                details={"issues": issues},
            )
        return DeployConfigCheck(
            key="runtime_profile",
            label="Runtime Profile",
            status="ok",
            message=(
                "Runtime profile matches the recommended single-VPS defaults."
                if topology == "single_vps_compact"
                else "Runtime profile matches the recommended two-VPS defaults."
            ),
            details={
                "env": settings.env,
                "deployment_topology": settings.deployment_topology,
                "deployment_market_mode": settings.deployment_market_mode,
                "heartbeat_interval_seconds": settings.heartbeat_interval_seconds,
            },
        )

    def _check_codex_provider(self, *, raw_values: dict[str, str], settings: Settings) -> DeployConfigCheck:
        if self._is_missing_or_placeholder(raw_values.get("QE_OPENAI_API_KEY")):
            return DeployConfigCheck(
                key="codex_provider",
                label="Codex Provider",
                status="fail",
                message="QE_OPENAI_API_KEY is still missing or set to a placeholder.",
                details={"base_url": settings.openai_base_url},
            )
        if settings.openai_base_url and not settings.openai_base_url.startswith(("http://", "https://")):
            return DeployConfigCheck(
                key="codex_provider",
                label="Codex Provider",
                status="fail",
                message="QE_OPENAI_BASE_URL must start with http:// or https:// when a relay is used.",
                details={"base_url": settings.openai_base_url},
            )
        if not settings.codex_command.strip():
            return DeployConfigCheck(
                key="codex_provider",
                label="Codex Provider",
                status="fail",
                message="QE_CODEX_COMMAND must not be empty.",
                details={},
            )
        workspace_mode = (settings.codex_workspace_mode or "").strip().lower()
        if workspace_mode not in {"direct", "isolated_copy"}:
            return DeployConfigCheck(
                key="codex_provider",
                label="Codex Provider",
                status="fail",
                message="QE_CODEX_WORKSPACE_MODE must be either `direct` or `isolated_copy`.",
                details={"workspace_mode": settings.codex_workspace_mode},
            )
        message = "Codex provider settings are present."
        if settings.openai_base_url:
            message = "Codex relay settings are present."
        return DeployConfigCheck(
            key="codex_provider",
            label="Codex Provider",
            status="ok",
            message=message,
            details={
                "base_url": settings.openai_base_url,
                "codex_command": settings.codex_command,
                "default_model": settings.codex_default_model,
                "workspace_mode": settings.codex_workspace_mode,
            },
        )

    def _check_core_discord(self, *, raw_values: dict[str, str]) -> DeployConfigCheck:
        required_keys = [
            "QE_DISCORD_TOKEN",
            "QE_DISCORD_GUILD_ID",
            "QE_DISCORD_CONTROL_CHANNEL_ID",
            "QE_DISCORD_APPROVALS_CHANNEL_ID",
            "QE_DISCORD_ALERTS_CHANNEL_ID",
            "QE_DISCORD_ALLOWED_USER_IDS",
        ]
        missing = [key for key in required_keys if self._is_missing_or_placeholder(raw_values.get(key))]
        if missing:
            return DeployConfigCheck(
                key="discord_owner_surface",
                label="Discord Owner Surface",
                status="fail",
                message="Core Discord owner-control settings are still incomplete.",
                details={"missing": missing},
            )
        return DeployConfigCheck(
            key="discord_owner_surface",
            label="Discord Owner Surface",
            status="ok",
            message="Core Discord owner-control settings are present.",
            details={
                "guild_id": raw_values.get("QE_DISCORD_GUILD_ID"),
                "control_channel_id": raw_values.get("QE_DISCORD_CONTROL_CHANNEL_ID"),
                "approvals_channel_id": raw_values.get("QE_DISCORD_APPROVALS_CHANNEL_ID"),
                "alerts_channel_id": raw_values.get("QE_DISCORD_ALERTS_CHANNEL_ID"),
            },
        )

    def _check_core_broker(self, *, raw_values: dict[str, str], settings: Settings) -> DeployConfigCheck:
        if self._is_missing_or_placeholder(raw_values.get("QE_POSTGRES_PASSWORD")):
            return DeployConfigCheck(
                key="broker_and_db",
                label="Broker And Database Guard",
                status="fail",
                message="QE_POSTGRES_PASSWORD is still missing or set to a placeholder.",
                details={},
            )
        if settings.deployment_market_mode == "cn" and settings.default_broker_adapter == "alpaca":
            return DeployConfigCheck(
                key="broker_and_db",
                label="Broker And Database Guard",
                status="fail",
                message=(
                    "CN deployment mode cannot use Alpaca. Keep `paper_sim` for China-market deployments "
                    "until a bounded CN broker adapter is configured."
                ),
                details={
                    "deployment_market_mode": settings.deployment_market_mode,
                    "default_broker_adapter": settings.default_broker_adapter,
                },
            )
        if settings.default_broker_adapter != "alpaca":
            return DeployConfigCheck(
                key="broker_and_db",
                label="Broker And Database Guard",
                status="ok",
                message="Core is configured for paper-first bring-up and does not require external broker credentials yet.",
                details={
                    "deployment_market_mode": settings.deployment_market_mode,
                    "default_broker_adapter": settings.default_broker_adapter,
                },
            )

        if settings.default_broker_environment == "paper":
            key_name = "QE_ALPACA_PAPER_API_KEY"
            secret_name = "QE_ALPACA_PAPER_API_SECRET"
            base_url = settings.alpaca_paper_base_url
        else:
            key_name = "QE_ALPACA_LIVE_API_KEY"
            secret_name = "QE_ALPACA_LIVE_API_SECRET"
            base_url = settings.alpaca_live_base_url

        missing = [
            key
            for key in (key_name, secret_name)
            if self._is_missing_or_placeholder(raw_values.get(key))
        ]
        if missing:
            return DeployConfigCheck(
                key="broker_and_db",
                label="Broker And Database Guard",
                status="fail",
                message="Core is configured for Alpaca, but the matching credentials are still incomplete.",
                details={"missing": missing, "base_url": base_url},
            )
        return DeployConfigCheck(
            key="broker_and_db",
            label="Broker And Database Guard",
            status="ok",
            message="Core broker settings are consistent with the selected Alpaca mode.",
            details={
                "base_url": base_url,
                "deployment_market_mode": settings.deployment_market_mode,
                "default_broker_environment": settings.default_broker_environment,
            },
        )

    def _check_core_postgres_exposure(
        self,
        *,
        raw_values: dict[str, str],
        settings: Settings,
    ) -> DeployConfigCheck:
        bind_host = raw_values.get("QE_POSTGRES_BIND_HOST", "127.0.0.1").strip()
        if bind_host == "127.0.0.1":
            if (settings.deployment_topology or "").strip().lower() == "single_vps_compact":
                return DeployConfigCheck(
                    key="postgres_exposure",
                    label="Postgres Exposure",
                    status="ok",
                    message="Core Postgres is bound to 127.0.0.1, which is correct for the single-VPS profile.",
                    details={"postgres_bind_host": bind_host},
                )
            return DeployConfigCheck(
                key="postgres_exposure",
                label="Postgres Exposure",
                status="warn",
                message="Core Postgres is still bound to 127.0.0.1. This is safe for first boot, but the Worker VPS will not connect until you switch it to a private-network IP.",
                details={"postgres_bind_host": bind_host},
            )
        if bind_host == "0.0.0.0":
            return DeployConfigCheck(
                key="postgres_exposure",
                label="Postgres Exposure",
                status="warn",
                message="Core Postgres is bound to 0.0.0.0. Prefer a private-network IP or Tailscale IP over a wide bind.",
                details={"postgres_bind_host": bind_host},
            )
        return DeployConfigCheck(
            key="postgres_exposure",
            label="Postgres Exposure",
            status="ok",
            message="Core Postgres bind host is compatible with a private Worker connection.",
            details={"postgres_bind_host": bind_host},
        )

    def _check_core_dashboard_security(
        self,
        *,
        raw_values: dict[str, str],
        settings: Settings,
    ) -> DeployConfigCheck:
        dashboard_user = raw_values.get("QE_DASHBOARD_ACCESS_USERNAME", "").strip()
        dashboard_password = raw_values.get("QE_DASHBOARD_ACCESS_PASSWORD", "").strip()
        dashboard_api_token = raw_values.get("QE_DASHBOARD_API_TOKEN", "").strip()
        edge_public_host = raw_values.get("QE_EDGE_PUBLIC_HOST", "").strip()
        details = {
            "api_bind_host": raw_values.get("QE_API_BIND_HOST", settings.api_bind_host),
            "dashboard_bind_host": raw_values.get("QE_DASHBOARD_BIND_HOST", settings.dashboard_bind_host),
            "edge_public_host": edge_public_host or None,
        }

        if bool(dashboard_user) ^ bool(dashboard_password):
            return DeployConfigCheck(
                key="dashboard_surface",
                label="Dashboard Surface Security",
                status="fail",
                message="Set QE_DASHBOARD_ACCESS_USERNAME and QE_DASHBOARD_ACCESS_PASSWORD together.",
                details=details,
            )

        missing: list[str] = []
        warnings: list[str] = []
        public_dashboard = self._is_public_bind_host(details["dashboard_bind_host"])
        public_api = self._is_public_bind_host(details["api_bind_host"])

        if (public_dashboard or edge_public_host) and (self._is_missing_or_placeholder(dashboard_user) or self._is_missing_or_placeholder(dashboard_password)):
            missing.extend(["QE_DASHBOARD_ACCESS_USERNAME", "QE_DASHBOARD_ACCESS_PASSWORD"])
        if (public_api or edge_public_host) and self._is_missing_or_placeholder(dashboard_api_token):
            missing.append("QE_DASHBOARD_API_TOKEN")
        if edge_public_host and self._is_missing_or_placeholder(raw_values.get("QE_EDGE_ACME_EMAIL")):
            warnings.append("QE_EDGE_ACME_EMAIL is still empty. Fill it before public HTTPS exposure.")
        if edge_public_host and details["dashboard_bind_host"] not in {"127.0.0.1", "::1", "localhost"}:
            warnings.append("Keep QE_DASHBOARD_BIND_HOST on localhost when the edge proxy is enabled.")

        if missing:
            return DeployConfigCheck(
                key="dashboard_surface",
                label="Dashboard Surface Security",
                status="fail",
                message="Dashboard public-surface security is incomplete for the current exposure settings.",
                details={**details, "missing": missing},
            )
        if warnings:
            return DeployConfigCheck(
                key="dashboard_surface",
                label="Dashboard Surface Security",
                status="warn",
                message="Dashboard security is close, but the public edge settings still need one or more fixes.",
                details={**details, "warnings": warnings},
            )
        return DeployConfigCheck(
            key="dashboard_surface",
            label="Dashboard Surface Security",
            status="ok",
            message="Dashboard login protection and dashboard-facing API protection are configured.",
            details=details,
        )

    def _check_worker_postgres_target(self, *, raw_values: dict[str, str]) -> DeployConfigCheck:
        raw_url = raw_values.get("QE_POSTGRES_URL", "").strip()
        if self._is_missing_or_placeholder(raw_url):
            return DeployConfigCheck(
                key="worker_postgres_target",
                label="Worker Postgres Target",
                status="fail",
                message="Worker QE_POSTGRES_URL is still missing or set to the template placeholder.",
                details={},
            )
        try:
            parsed = make_url(raw_url)
        except Exception as exc:
            return DeployConfigCheck(
                key="worker_postgres_target",
                label="Worker Postgres Target",
                status="fail",
                message=f"Worker QE_POSTGRES_URL is not a valid SQLAlchemy database URL: {exc}",
                details={},
            )

        host = (parsed.host or "").strip().lower()
        if host in {"", "postgres", "localhost", "127.0.0.1"}:
            return DeployConfigCheck(
                key="worker_postgres_target",
                label="Worker Postgres Target",
                status="fail",
                message="Worker QE_POSTGRES_URL still points to a local or container-only Postgres host. Use the Core node private IP or Tailscale IP instead.",
                details={"host": host},
            )
        if self._is_public_host(host):
            return DeployConfigCheck(
                key="worker_postgres_target",
                label="Worker Postgres Target",
                status="warn",
                message="Worker Postgres host does not look private. Prefer a private-network path between Core and Worker.",
                details={"host": host},
            )
        return DeployConfigCheck(
            key="worker_postgres_target",
            label="Worker Postgres Target",
            status="ok",
            message="Worker Postgres target looks compatible with a private Core connection.",
            details={"host": host},
        )

    def _check_worker_secret_boundary(self, *, raw_values: dict[str, str]) -> DeployConfigCheck:
        forbidden = [
            key
            for key in (
                "QE_DISCORD_TOKEN",
                "QE_ALPACA_API_KEY",
                "QE_ALPACA_API_SECRET",
                "QE_ALPACA_PAPER_API_KEY",
                "QE_ALPACA_PAPER_API_SECRET",
                "QE_ALPACA_LIVE_API_KEY",
                "QE_ALPACA_LIVE_API_SECRET",
            )
            if not self._is_missing_or_placeholder(raw_values.get(key))
        ]
        if forbidden:
            return DeployConfigCheck(
                key="worker_secret_boundary",
                label="Worker Secret Boundary",
                status="fail",
                message="Worker env file is carrying Core-only secrets. Remove broker and Discord authority from the Worker node.",
                details={"forbidden_keys": forbidden},
            )
        return DeployConfigCheck(
            key="worker_secret_boundary",
            label="Worker Secret Boundary",
            status="ok",
            message="Worker env file respects the Core versus Worker secret boundary.",
            details={},
        )

    def _read_env_values(self, path: Path) -> dict[str, str]:
        values: dict[str, str] = {}
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("#") or "=" not in raw_line:
                continue
            key, value = raw_line.split("=", 1)
            values[key.strip()] = value.strip()
        return values

    def _render_env_file(self, template_lines: list[str], values: Mapping[str, str]) -> str:
        rendered: list[str] = []
        seen: set[str] = set()
        for line in template_lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in line:
                rendered.append(line)
                continue
            key, _ = line.split("=", 1)
            key = key.strip()
            if key in values:
                rendered.append(f"{key}={values[key]}")
                seen.add(key)
            else:
                rendered.append(line)
        for key, value in values.items():
            if key.startswith("__") or key in seen:
                continue
            rendered.append(f"{key}={value}")
        return "\n".join(rendered)

    def _is_missing_or_placeholder(self, value: str | None) -> bool:
        if value is None:
            return True
        stripped = value.strip()
        if stripped in PLACEHOLDER_VALUES:
            return True
        lowered = stripped.lower()
        return lowered.startswith("your_") or lowered.startswith("<fill") or lowered.endswith("_placeholder")

    def _is_public_host(self, host: str) -> bool:
        try:
            ip = ip_address(host)
        except ValueError:
            return False
        return not any(ip in network for network in PRIVATE_NETWORKS)

    def _is_public_bind_host(self, host: str | None) -> bool:
        normalized = (host or "").strip().lower()
        return normalized not in {"", "127.0.0.1", "::1", "localhost"}

    def _ensure_core_security_defaults(self, values: dict[str, str]) -> None:
        if self._is_missing_or_placeholder(values.get("QE_DASHBOARD_ACCESS_USERNAME")):
            values["QE_DASHBOARD_ACCESS_USERNAME"] = "owner"
        if self._is_missing_or_placeholder(values.get("QE_DASHBOARD_ACCESS_PASSWORD")):
            values["QE_DASHBOARD_ACCESS_PASSWORD"] = secrets.token_urlsafe(18)
        if self._is_missing_or_placeholder(values.get("QE_DASHBOARD_API_TOKEN")):
            values["QE_DASHBOARD_API_TOKEN"] = secrets.token_urlsafe(24)
