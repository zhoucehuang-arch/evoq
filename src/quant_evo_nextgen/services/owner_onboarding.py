from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from quant_evo_nextgen.services.deploy_config import (
    DeployConfigService,
    SUPPORTED_DEPLOYMENT_MARKET_MODES,
    SUPPORTED_DEPLOYMENT_TOPOLOGIES,
    normalize_deploy_role,
)
from quant_evo_nextgen.services.deploy_fields import (
    DeployFieldSpec,
    resolve_deploy_field,
)


SUPPORTED_BROKER_MODES = {
    "paper": "paper_sim",
    "paper_sim": "paper_sim",
    "alpaca_paper": "alpaca_paper",
    "alpaca_live": "alpaca_live",
}
SUPPORTED_BOOLEAN_TRUE = {"1", "true", "yes", "on", "enable", "enabled"}
SUPPORTED_BOOLEAN_FALSE = {"0", "false", "no", "off", "disable", "disabled"}
SUPPORTED_TOPOLOGY_ALIASES = {
    "singlevps": "single_vps_compact",
    "singlevpscompact": "single_vps_compact",
    "singlevpsfirst": "single_vps_compact",
    "single_vps_compact": "single_vps_compact",
    "twovps": "two_vps_asymmetrical",
    "twovpsasymmetrical": "two_vps_asymmetrical",
    "two_vps_asymmetrical": "two_vps_asymmetrical",
}
SUPPORTED_MARKET_MODE_ALIASES = {
    "us": "us",
    "usa": "us",
    "usequities": "us",
    "usoptions": "us",
    "cn": "cn",
    "china": "cn",
    "ashares": "cn",
    "ashare": "cn",
    "a-share": "cn",
}


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
        lines = [
            f"Prepared the deployment draft for `{normalized}`.",
            f"Config file: `{env_path}`",
            f"Preflight status: {report['status']}",
        ]
        top_message = self._top_preflight_message(report)
        if top_message:
            lines.append(top_message)
        lines.append(
            "Note: this updates the deployment draft; related services usually need a restart before they read the new values."
        )
        return OwnerOnboardingResult(
            role=normalized,
            env_path=str(env_path),
            action="bootstrap",
            changed_keys=[],
            masked_value=None,
            sensitive=False,
            preflight_status=report["status"],
            summary_text="\n".join(lines),
        )

    def status(self, role: str) -> OwnerOnboardingResult:
        normalized = normalize_deploy_role(role)
        env_path = self.deploy_config.ensure_env_file(
            role=normalized,
            output_path=self._env_path_for_role(normalized),
        )
        report = self.deploy_config.run_preflight(role=normalized, env_path=env_path)
        lines = [
            f"`{normalized}` deployment status: {report['status']}",
            f"Config file: `{env_path}`",
        ]
        top_message = self._top_preflight_message(report)
        if top_message:
            lines.append(top_message)
        return OwnerOnboardingResult(
            role=normalized,
            env_path=str(env_path),
            action="status",
            changed_keys=[],
            masked_value=None,
            sensitive=False,
            preflight_status=report["status"],
            summary_text="\n".join(lines),
        )

    def set_field(
        self,
        *,
        role: str,
        field_alias: str,
        value: str,
    ) -> OwnerOnboardingResult:
        normalized = normalize_deploy_role(role)
        field = resolve_deploy_field(field_alias, role=normalized)
        env_path = self._env_path_for_role(normalized)
        masked_value: str

        if field.kind == "broker_mode":
            broker_mode = self._normalize_broker_mode(value)
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
        elif field.kind == "market_mode":
            market_mode = self._normalize_market_mode(value)
            updated = self.deploy_config.update_env_file(
                role=normalized,
                output_path=env_path,
                market_mode=market_mode,
            )
            changed_keys = [
                "QE_DEPLOYMENT_MARKET_MODE",
                "QE_MARKET_TIMEZONE",
                "QE_MARKET_CALENDAR",
            ]
            masked_value = market_mode
        else:
            if field.env_key is None:
                raise ValueError(f"Field `{field_alias}` has no env mapping yet.")
            normalized_value = self._normalize_value(field, value)
            updated = self.deploy_config.update_env_file(
                role=normalized,
                output_path=env_path,
                updates={field.env_key: normalized_value},
            )
            changed_keys = [field.env_key]
            masked_value = self._mask_value(normalized_value, secret=field.secret)

        report = self.deploy_config.run_preflight(role=normalized, env_path=updated)
        lines = [
            f"Updated `{normalized}` {field.label}: {masked_value}",
            f"Config file: `{updated}`",
            f"Preflight status: {report['status']}",
        ]
        top_message = self._top_preflight_message(report)
        if top_message:
            lines.append(top_message)
        lines.append(
            "Note: this updates the deployment draft; related services usually need a restart before they read the new values."
        )
        return OwnerOnboardingResult(
            role=normalized,
            env_path=str(updated),
            action="set_field",
            changed_keys=changed_keys,
            masked_value=masked_value,
            sensitive=field.secret,
            preflight_status=report["status"],
            summary_text="\n".join(lines),
        )

    def resolve_field(self, field_alias: str, *, role: str) -> DeployFieldSpec:
        return resolve_deploy_field(field_alias, role=normalize_deploy_role(role))

    def redact_secret_message(self, role: str, field_alias: str) -> str:
        normalized = normalize_deploy_role(role)
        field = self.resolve_field(field_alias, role=normalized)
        return f"Set {normalized} {field.label} (redacted)"

    def _env_path_for_role(self, role: str) -> Path | None:
        if self.env_root is None:
            return None
        return self.env_root / f"{role}.env"

    def _normalize_value(self, field: DeployFieldSpec, value: str) -> str:
        stripped = value.strip()
        if field.kind == "bool":
            return self._normalize_bool_value(stripped)
        if field.kind == "topology":
            return self._normalize_topology(stripped)
        if field.kind == "market_mode":
            return self._normalize_market_mode(stripped)
        return stripped

    def _normalize_broker_mode(self, value: str) -> str:
        normalized = value.strip().lower()
        try:
            return SUPPORTED_BROKER_MODES[normalized]
        except KeyError as exc:
            supported = ", ".join(sorted(set(SUPPORTED_BROKER_MODES.values())))
            raise ValueError(f"Broker mode must be one of: {supported}.") from exc

    def _normalize_bool_value(self, value: str) -> str:
        normalized = value.strip().lower()
        if normalized in SUPPORTED_BOOLEAN_TRUE:
            return "true"
        if normalized in SUPPORTED_BOOLEAN_FALSE:
            return "false"
        raise ValueError("Boolean field values must be true/false, yes/no, on/off, or enable/disable.")

    def _normalize_topology(self, value: str) -> str:
        normalized = value.strip().lower().replace(" ", "").replace("-", "").replace("_", "")
        mapped = SUPPORTED_TOPOLOGY_ALIASES.get(normalized)
        if mapped is None and value.strip() in SUPPORTED_DEPLOYMENT_TOPOLOGIES:
            mapped = value.strip()
        if mapped is None:
            supported = ", ".join(sorted(SUPPORTED_DEPLOYMENT_TOPOLOGIES))
            raise ValueError(f"Deployment topology must be one of: {supported}.")
        return mapped

    def _normalize_market_mode(self, value: str) -> str:
        normalized = value.strip().lower().replace(" ", "").replace("-", "").replace("_", "")
        mapped = SUPPORTED_MARKET_MODE_ALIASES.get(normalized)
        if mapped is None and value.strip().lower() in SUPPORTED_DEPLOYMENT_MARKET_MODES:
            mapped = value.strip().lower()
        if mapped is None:
            supported = ", ".join(sorted(SUPPORTED_DEPLOYMENT_MARKET_MODES))
            raise ValueError(f"Deployment market mode must be one of: {supported}.")
        return mapped

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
        failures = [
            check
            for check in checks
            if isinstance(check, dict) and check.get("status") in {"fail", "warn"}
        ]
        if not failures:
            return "All key preflight checks passed."
        top = failures[0]
        label = str(top.get("label") or top.get("key") or "Preflight Check")
        message = str(top.get("message") or "").strip()
        return f"Top preflight item to address: {label} | {message}"
