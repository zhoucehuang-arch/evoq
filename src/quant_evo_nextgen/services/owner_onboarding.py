from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from quant_evo_nextgen.services.deploy_config import DeployConfigService, normalize_deploy_role


@dataclass(frozen=True, slots=True)
class OnboardingField:
    label: str
    env_key: str | None = None
    secret: bool = False
    roles: tuple[str, ...] = ("core", "worker")
    broker_mode: bool = False


@dataclass(slots=True)
class OwnerOnboardingResult:
    role: str
    env_path: str
    action: str
    changed_keys: list[str]
    masked_value: str | None
    sensitive: bool
    preflight_status: str
    summary_text: str


_FIELD_ALIASES: dict[str, OnboardingField] = {
    "中转地址": OnboardingField("中转地址", env_key="QE_OPENAI_BASE_URL"),
    "relaybaseurl": OnboardingField("中转地址", env_key="QE_OPENAI_BASE_URL"),
    "openaibaseurl": OnboardingField("中转地址", env_key="QE_OPENAI_BASE_URL"),
    "中转key": OnboardingField("中转 Key", env_key="QE_OPENAI_API_KEY", secret=True),
    "relaykey": OnboardingField("中转 Key", env_key="QE_OPENAI_API_KEY", secret=True),
    "openaiapikey": OnboardingField("中转 Key", env_key="QE_OPENAI_API_KEY", secret=True),
    "postgres密码": OnboardingField("Postgres 密码", env_key="QE_POSTGRES_PASSWORD", secret=True, roles=("core",)),
    "postgrespassword": OnboardingField("Postgres 密码", env_key="QE_POSTGRES_PASSWORD", secret=True, roles=("core",)),
    "discordtoken": OnboardingField("Discord Bot Token", env_key="QE_DISCORD_TOKEN", secret=True, roles=("core",)),
    "机器人token": OnboardingField("Discord Bot Token", env_key="QE_DISCORD_TOKEN", secret=True, roles=("core",)),
    "guildid": OnboardingField("Discord Guild ID", env_key="QE_DISCORD_GUILD_ID", roles=("core",)),
    "服务器id": OnboardingField("Discord Guild ID", env_key="QE_DISCORD_GUILD_ID", roles=("core",)),
    "控制频道id": OnboardingField("控制频道 ID", env_key="QE_DISCORD_CONTROL_CHANNEL_ID", roles=("core",)),
    "controlchannelid": OnboardingField("控制频道 ID", env_key="QE_DISCORD_CONTROL_CHANNEL_ID", roles=("core",)),
    "审批频道id": OnboardingField("审批频道 ID", env_key="QE_DISCORD_APPROVALS_CHANNEL_ID", roles=("core",)),
    "approvalschannelid": OnboardingField("审批频道 ID", env_key="QE_DISCORD_APPROVALS_CHANNEL_ID", roles=("core",)),
    "告警频道id": OnboardingField("告警频道 ID", env_key="QE_DISCORD_ALERTS_CHANNEL_ID", roles=("core",)),
    "alertschannelid": OnboardingField("告警频道 ID", env_key="QE_DISCORD_ALERTS_CHANNEL_ID", roles=("core",)),
    "允许用户id": OnboardingField("允许控制的 Discord 用户 ID", env_key="QE_DISCORD_ALLOWED_USER_IDS", roles=("core",)),
    "alloweduserids": OnboardingField("允许控制的 Discord 用户 ID", env_key="QE_DISCORD_ALLOWED_USER_IDS", roles=("core",)),
    "brokermode": OnboardingField("券商模式", roles=("core",), broker_mode=True),
    "券商模式": OnboardingField("券商模式", roles=("core",), broker_mode=True),
    "alpacapaperkey": OnboardingField("Alpaca Paper Key", env_key="QE_ALPACA_PAPER_API_KEY", secret=True, roles=("core",)),
    "alpacapapersecret": OnboardingField("Alpaca Paper Secret", env_key="QE_ALPACA_PAPER_API_SECRET", secret=True, roles=("core",)),
    "alpacalivekey": OnboardingField("Alpaca Live Key", env_key="QE_ALPACA_LIVE_API_KEY", secret=True, roles=("core",)),
    "alpacalivesecret": OnboardingField("Alpaca Live Secret", env_key="QE_ALPACA_LIVE_API_SECRET", secret=True, roles=("core",)),
    "dashboard用户名": OnboardingField("Dashboard 用户名", env_key="QE_DASHBOARD_ACCESS_USERNAME", roles=("core",)),
    "dashboardusername": OnboardingField("Dashboard 用户名", env_key="QE_DASHBOARD_ACCESS_USERNAME", roles=("core",)),
    "dashboard密码": OnboardingField("Dashboard 密码", env_key="QE_DASHBOARD_ACCESS_PASSWORD", secret=True, roles=("core",)),
    "dashboardpassword": OnboardingField("Dashboard 密码", env_key="QE_DASHBOARD_ACCESS_PASSWORD", secret=True, roles=("core",)),
    "dashboardapitoken": OnboardingField("Dashboard API Token", env_key="QE_DASHBOARD_API_TOKEN", secret=True, roles=("core",)),
    "dashboardtoken": OnboardingField("Dashboard API Token", env_key="QE_DASHBOARD_API_TOKEN", secret=True, roles=("core",)),
    "dashboard域名": OnboardingField("Dashboard 公网域名", env_key="QE_EDGE_PUBLIC_HOST", roles=("core",)),
    "edgepublichost": OnboardingField("Dashboard 公网域名", env_key="QE_EDGE_PUBLIC_HOST", roles=("core",)),
    "acmeemail": OnboardingField("ACME 邮箱", env_key="QE_EDGE_ACME_EMAIL", roles=("core",)),
    "postgresurl": OnboardingField("Worker Postgres URL", env_key="QE_POSTGRES_URL", secret=True, roles=("worker",)),
    "数据库url": OnboardingField("Worker Postgres URL", env_key="QE_POSTGRES_URL", secret=True, roles=("worker",)),
}


class OwnerOnboardingService:
    def __init__(self, repo_root: Path, *, env_root: Path | None = None) -> None:
        self.repo_root = repo_root.resolve()
        self.deploy_config = DeployConfigService(self.repo_root)
        self.env_root = env_root.resolve() if env_root is not None else None

    def bootstrap_role(self, role: str) -> OwnerOnboardingResult:
        normalized = normalize_deploy_role(role)
        env_path = self.deploy_config.ensure_env_file(
            role=normalized,
            output_path=self._env_path_for_role(normalized),
        )
        report = self.deploy_config.run_preflight(role=normalized, env_path=env_path)
        summary = (
            f"已为 `{normalized}` 生成或确认部署配置草稿：`{env_path}`。\n"
            f"当前预检状态：{report['status']}。{self._top_preflight_message(report)}\n"
            "说明：这是部署草稿更新，相关服务通常需要重启后才会读取新值。"
        )
        return OwnerOnboardingResult(
            role=normalized,
            env_path=str(env_path),
            action="bootstrap",
            changed_keys=[],
            masked_value=None,
            sensitive=False,
            preflight_status=report["status"],
            summary_text=summary,
        )

    def status(self, role: str) -> OwnerOnboardingResult:
        normalized = normalize_deploy_role(role)
        env_path = self.deploy_config.ensure_env_file(
            role=normalized,
            output_path=self._env_path_for_role(normalized),
        )
        report = self.deploy_config.run_preflight(role=normalized, env_path=env_path)
        summary = (
            f"`{normalized}` 当前部署预检状态：{report['status']}。\n"
            f"配置文件：`{env_path}`。{self._top_preflight_message(report)}"
        )
        return OwnerOnboardingResult(
            role=normalized,
            env_path=str(env_path),
            action="status",
            changed_keys=[],
            masked_value=None,
            sensitive=False,
            preflight_status=report["status"],
            summary_text=summary,
        )

    def set_field(
        self,
        *,
        role: str,
        field_alias: str,
        value: str,
    ) -> OwnerOnboardingResult:
        normalized = normalize_deploy_role(role)
        field = self.resolve_field(field_alias, role=normalized)
        env_path = self._env_path_for_role(normalized)
        changed_keys: list[str]
        if field.broker_mode:
            broker_mode = value.strip().lower()
            if broker_mode not in {"paper_sim", "alpaca_paper", "alpaca_live"}:
                raise ValueError("券商模式只支持 `paper_sim`、`alpaca_paper` 或 `alpaca_live`。")
            updated = self.deploy_config.update_env_file(
                role=normalized,
                output_path=env_path,
                broker_mode=broker_mode,
            )
            changed_keys = [
                "QE_DEFAULT_BROKER_PROVIDER_KEY",
                "QE_DEFAULT_BROKER_ACCOUNT_REF",
                "QE_DEFAULT_BROKER_ENVIRONMENT",
                "QE_DEFAULT_BROKER_ADAPTER",
            ]
            masked_value = broker_mode
        else:
            if field.env_key is None:
                raise ValueError(f"字段 `{field_alias}` 还没有映射到部署配置。")
            updated = self.deploy_config.update_env_file(
                role=normalized,
                output_path=env_path,
                updates={field.env_key: value.strip()},
            )
            changed_keys = [field.env_key]
            masked_value = self._mask_value(value.strip(), secret=field.secret)

        report = self.deploy_config.run_preflight(role=normalized, env_path=updated)
        summary = (
            f"已更新 `{normalized}` 的 {field.label}：{masked_value}。\n"
            f"配置文件：`{updated}`。当前预检状态：{report['status']}。{self._top_preflight_message(report)}\n"
            "说明：这是部署草稿更新，相关服务通常需要重启后才会读取新值。"
        )
        return OwnerOnboardingResult(
            role=normalized,
            env_path=str(updated),
            action="set_field",
            changed_keys=changed_keys,
            masked_value=masked_value,
            sensitive=field.secret,
            preflight_status=report["status"],
            summary_text=summary,
        )

    def resolve_field(self, field_alias: str, *, role: str) -> OnboardingField:
        normalized = self._normalize_alias(field_alias)
        field = _FIELD_ALIASES.get(normalized)
        if field is None:
            raise ValueError(f"还不支持通过 IM 设置字段 `{field_alias}`。")
        if role not in field.roles:
            raise ValueError(f"字段 `{field_alias}` 不适用于 `{role}`。")
        return field

    def redact_secret_message(self, role: str, field_alias: str) -> str:
        normalized = normalize_deploy_role(role)
        field = self.resolve_field(field_alias, role=normalized)
        return f"设置 {normalized} 的 {field.label}（已脱敏）"

    def _env_path_for_role(self, role: str) -> Path | None:
        if self.env_root is None:
            return None
        return self.env_root / f"{role}.env"

    def _normalize_alias(self, field_alias: str) -> str:
        return (
            field_alias.strip()
            .lower()
            .replace(" ", "")
            .replace("_", "")
            .replace("-", "")
        )

    def _mask_value(self, value: str, *, secret: bool) -> str:
        if not secret:
            return value
        if len(value) <= 8:
            return "*" * len(value)
        return f"{value[:2]}***{value[-2:]}"

    def _top_preflight_message(self, report: dict[str, object]) -> str:
        checks = report.get("checks", [])
        if not isinstance(checks, list):
            return ""
        failures = [check for check in checks if isinstance(check, dict) and check.get("status") in {"fail", "warn"}]
        if not failures:
            return "所有关键预检项都已通过。"
        top = failures[0]
        label = str(top.get("label") or top.get("key") or "预检项")
        message = str(top.get("message") or "").strip()
        return f"当前最重要的待处理项：{label}，{message}"
