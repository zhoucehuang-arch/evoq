from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable

from sqlalchemy import text
from sqlalchemy.orm import Session

from quant_evo_nextgen.config import Settings
from quant_evo_nextgen.services.acquisition import AcquisitionStackService
from quant_evo_nextgen.services.execution import ExecutionService
from quant_evo_nextgen.services.state_store import StateStore


EXPECTED_HEAD_REVISION = "20260320_0014"


@dataclass(slots=True)
class DoctorCheck:
    key: str
    label: str
    status: str
    message: str
    details: dict[str, Any]


@dataclass(slots=True)
class ReadinessProfile:
    key: str
    label: str
    status: str
    message: str
    blocked_by: list[str]
    details: dict[str, Any]


class DoctorService:
    def __init__(self, session_factory: Callable[[], Session], settings: Settings) -> None:
        self.session_factory = session_factory
        self.settings = settings
        self.state_store = StateStore(session_factory)
        self.execution_service = ExecutionService(session_factory, settings)

    def run(self) -> dict[str, Any]:
        checks = [
            self._check_database_connectivity(),
            self._check_schema_revision(),
            self._check_workspace_access(),
            self._check_discord_configuration(),
            self._check_codex_provider_configuration(),
            self._check_acquisition_stack(),
            self._check_broker_configuration(),
            self._check_dashboard_security_posture(),
            self._check_node_role_boundary(),
            self._check_runtime_registry(),
        ]
        overall_status = "ok"
        if any(check.status == "fail" for check in checks):
            overall_status = "fail"
        elif any(check.status == "warn" for check in checks):
            overall_status = "warn"

        readiness_profiles = self._build_readiness_profiles(checks)

        return {
            "status": overall_status,
            "expected_head_revision": EXPECTED_HEAD_REVISION,
            "checks": [asdict(check) for check in checks],
            "profiles": [asdict(profile) for profile in readiness_profiles],
        }

    def _build_readiness_profiles(self, checks: list[DoctorCheck]) -> list[ReadinessProfile]:
        check_status = {check.key: check.status for check in checks}
        runtime_snapshot = self.state_store.get_runtime_snapshot()
        execution_readiness = self.execution_service.get_execution_readiness()
        profiles = [
            self._node_vps_deploy_profile(
                check_status=check_status,
                runtime_snapshot=runtime_snapshot,
            ),
            self._capital_activation_profile(
                check_status=check_status,
                runtime_snapshot=runtime_snapshot,
                execution_readiness=execution_readiness,
            ),
            self._owner_target_full_system_profile(
                check_status=check_status,
                runtime_snapshot=runtime_snapshot,
                execution_readiness=execution_readiness,
            ),
        ]
        return profiles

    def _node_vps_deploy_profile(
        self,
        *,
        check_status: dict[str, str],
        runtime_snapshot,
    ) -> ReadinessProfile:
        blocked_by: list[str] = []
        required_ok = {
            "database": "Runtime database must be reachable.",
            "workspace": "Runtime workspace must be writable.",
            "discord": "Discord owner surface must be configured for the owner-first operating model.",
            "codex_provider": "Codex-compatible execution must be configured for learning and governed work.",
            "node_role_boundary": "Node role and secret boundary must be consistent with the authority split.",
        }
        for key, reason in required_ok.items():
            if check_status.get(key) != "ok":
                blocked_by.append(reason)
        if check_status.get("dashboard_security") == "fail":
            blocked_by.append("Dashboard security posture is unsafe for the intended deployment path.")
        if check_status.get("schema_revision") == "fail":
            blocked_by.append("Database schema is not on the expected head revision.")
        if check_status.get("runtime_registry") == "fail":
            blocked_by.append("Durable runtime registry is not readable.")

        if blocked_by:
            return ReadinessProfile(
                key="node_vps_deploy",
                label="Node VPS Deploy",
                status="fail",
                message="This node is not ready for the intended VPS deployment path yet.",
                blocked_by=blocked_by,
                details={
                    "node_role": self.settings.node_role,
                    "deployment_topology": self.settings.deployment_topology,
                    "default_broker_adapter": self.settings.default_broker_adapter,
                    "active_overrides": runtime_snapshot.active_overrides,
                },
            )

        status = "ok"
        message = "This node is ready for the intended VPS deployment path."
        warnings: list[str] = []
        if self.settings.default_broker_adapter != "paper_sim":
            status = "warn"
            message = "This node is deployable, but it is not in the safest paper-first bootstrap posture."
            warnings.append("Default broker adapter is not `paper_sim`.")
        if runtime_snapshot.pending_approvals > 0:
            status = "warn"
            if "Pending approvals already exist in durable state." not in warnings:
                warnings.append("Pending approvals already exist in durable state.")

        return ReadinessProfile(
            key="node_vps_deploy",
            label="Node VPS Deploy",
            status=status,
            message=message,
            blocked_by=warnings,
            details={
                "node_role": self.settings.node_role,
                "deployment_topology": self.settings.deployment_topology,
                "default_broker_adapter": self.settings.default_broker_adapter,
                "default_broker_environment": self.settings.default_broker_environment,
                "pending_approvals": runtime_snapshot.pending_approvals,
                "active_overrides": runtime_snapshot.active_overrides,
            },
        )

    def _capital_activation_profile(
        self,
        *,
        check_status: dict[str, str],
        runtime_snapshot,
        execution_readiness,
    ) -> ReadinessProfile:
        blocked_by: list[str] = []
        if check_status.get("database") == "fail" or check_status.get("schema_revision") == "fail":
            blocked_by.append("Database and schema health must be green before any capital-facing activation.")
        if check_status.get("discord") != "ok":
            blocked_by.append("Discord owner control must be healthy before capital-facing activation.")
        if check_status.get("codex_provider") != "ok":
            blocked_by.append("Codex-compatible execution must be healthy before capital-facing activation.")
        if check_status.get("broker") != "ok":
            blocked_by.append("Broker credentials and broker configuration must be healthy.")
        if self.settings.default_broker_adapter == "paper_sim":
            blocked_by.append("Default broker adapter is still `paper_sim`, so this environment is paper-only by design.")
        if execution_readiness.active_production_strategies <= 0:
            blocked_by.append("No governed production strategy is currently active.")
        if not execution_readiness.trading_allowed:
            blocked_by.extend(execution_readiness.blocked_reasons or ["Execution readiness is not allowing trading."])
        if runtime_snapshot.active_overrides > 0:
            blocked_by.append("Active manual overrides are present.")
        if runtime_snapshot.open_incidents > 0:
            blocked_by.append("Open incidents are present.")
        if runtime_snapshot.pending_approvals > 0:
            blocked_by.append("Pending approvals remain unresolved.")

        if blocked_by:
            return ReadinessProfile(
                key="capital_activation",
                label="Capital Activation",
                status="fail",
                message="This runtime is not ready for capital-facing activation yet.",
                blocked_by=blocked_by,
                details={
                    "default_broker_adapter": self.settings.default_broker_adapter,
                    "default_broker_environment": self.settings.default_broker_environment,
                    "trading_allowed": execution_readiness.trading_allowed,
                    "execution_status": execution_readiness.status,
                    "active_production_strategies": execution_readiness.active_production_strategies,
                    "active_overrides": runtime_snapshot.active_overrides,
                    "open_incidents": runtime_snapshot.open_incidents,
                    "pending_approvals": runtime_snapshot.pending_approvals,
                },
            )

        return ReadinessProfile(
            key="capital_activation",
            label="Capital Activation",
            status="ok",
            message="This runtime has cleared the current capital-activation gate.",
            blocked_by=[],
            details={
                "default_broker_adapter": self.settings.default_broker_adapter,
                "default_broker_environment": self.settings.default_broker_environment,
                "trading_allowed": execution_readiness.trading_allowed,
                "execution_status": execution_readiness.status,
                "active_production_strategies": execution_readiness.active_production_strategies,
            },
        )

    def _owner_target_full_system_profile(
        self,
        *,
        check_status: dict[str, str],
        runtime_snapshot,
        execution_readiness,
    ) -> ReadinessProfile:
        blocked_by: list[str] = []
        if (self.settings.codex_workspace_mode or "").strip().lower() != "isolated_copy":
            blocked_by.append(
                "Codex workspace isolation is not set to the isolated-copy execution mode on this runtime."
            )
        if check_status.get("acquisition_stack") == "fail":
            blocked_by.append("The layered research acquisition stack is not healthy enough for unattended learning.")
        if check_status.get("dashboard_security") != "ok":
            blocked_by.append("Dashboard auth or public-surface security posture is not fully configured on this runtime.")
        if check_status.get("discord") != "ok":
            blocked_by.append("Discord owner control is not fully configured on this runtime.")
        if check_status.get("codex_provider") != "ok":
            blocked_by.append("Codex-compatible execution is not fully configured on this runtime.")
        if check_status.get("broker") == "fail":
            blocked_by.append("Broker configuration is not healthy enough for the intended trading mode.")
        if runtime_snapshot.open_incidents > 0:
            blocked_by.append("Open incidents remain active.")
        if execution_readiness.active_production_strategies <= 0:
            blocked_by.append("No governed production strategy is currently active.")

        return ReadinessProfile(
            key="owner_target_full_system",
            label="Owner Target Full System",
            status="fail",
            message="The repository is not yet closed against the owner's full target system requirements.",
            blocked_by=blocked_by,
            details={
                "default_broker_adapter": self.settings.default_broker_adapter,
                "default_broker_environment": self.settings.default_broker_environment,
                "execution_status": execution_readiness.status,
                "trading_allowed": execution_readiness.trading_allowed,
                "active_production_strategies": execution_readiness.active_production_strategies,
                "open_incidents": runtime_snapshot.open_incidents,
                "pending_approvals": runtime_snapshot.pending_approvals,
            },
        )

    def _check_database_connectivity(self) -> DoctorCheck:
        try:
            with self.session_factory() as session:
                session.execute(text("SELECT 1"))
            return DoctorCheck(
                key="database",
                label="Database Connectivity",
                status="ok",
                message="The runtime database is reachable.",
                details={"postgres_url": self.settings.postgres_url},
            )
        except Exception as exc:  # pragma: no cover - defensive surface
            return DoctorCheck(
                key="database",
                label="Database Connectivity",
                status="fail",
                message=f"The runtime database is not reachable: {exc}",
                details={"postgres_url": self.settings.postgres_url},
            )

    def _check_schema_revision(self) -> DoctorCheck:
        try:
            with self.session_factory() as session:
                revision = session.execute(text("SELECT version_num FROM alembic_version")).scalar_one_or_none()
        except Exception as exc:
            return DoctorCheck(
                key="schema_revision",
                label="Schema Revision",
                status="warn",
                message=(
                    "Could not read Alembic revision state. "
                    "This usually means the database was bootstrapped without recorded migrations."
                ),
                details={"expected": EXPECTED_HEAD_REVISION},
            )

        if revision == EXPECTED_HEAD_REVISION:
            return DoctorCheck(
                key="schema_revision",
                label="Schema Revision",
                status="ok",
                message="The runtime database is on the expected head revision.",
                details={"expected": EXPECTED_HEAD_REVISION, "actual": revision},
            )

        return DoctorCheck(
            key="schema_revision",
            label="Schema Revision",
            status="fail",
            message="The runtime database is not on the expected head revision.",
            details={"expected": EXPECTED_HEAD_REVISION, "actual": revision},
        )

    def _check_workspace_access(self) -> DoctorCheck:
        workspace_root = self.settings.resolved_repo_root / ".qe"
        try:
            workspace_root.mkdir(parents=True, exist_ok=True)
            probe_path = workspace_root / ".doctor-writecheck"
            probe_path.write_text("ok", encoding="utf-8")
            probe_path.unlink(missing_ok=True)
            return DoctorCheck(
                key="workspace",
                label="Workspace Access",
                status="ok",
                message="The runtime workspace is writable.",
                details={"workspace_root": str(workspace_root)},
            )
        except Exception as exc:  # pragma: no cover - defensive surface
            return DoctorCheck(
                key="workspace",
                label="Workspace Access",
                status="fail",
                message=f"The runtime workspace is not writable: {exc}",
                details={"workspace_root": str(workspace_root)},
            )

    def _check_discord_configuration(self) -> DoctorCheck:
        missing = []
        if not self.settings.discord_token:
            missing.append("QE_DISCORD_TOKEN")
        if not self.settings.discord_control_channel:
            missing.append("QE_DISCORD_CONTROL_CHANNEL")
        if not self.settings.discord_approvals_channel:
            missing.append("QE_DISCORD_APPROVALS_CHANNEL")

        if missing:
            return DoctorCheck(
                key="discord",
                label="Discord Control Plane",
                status="warn",
                message="Discord owner control is not fully configured yet.",
                details={"missing": missing},
            )

        if not self.settings.discord_allowed_user_ids.strip():
            return DoctorCheck(
                key="discord",
                label="Discord Control Plane",
                status="warn",
                message="Discord control is configured, but trusted operator allowlists are still empty.",
                details={
                    "missing": ["QE_DISCORD_ALLOWED_USER_IDS"],
                    "control_channel": self.settings.discord_control_channel,
                    "approvals_channel": self.settings.discord_approvals_channel,
                },
            )

        return DoctorCheck(
            key="discord",
            label="Discord Control Plane",
            status="ok",
            message="Discord owner control settings are present.",
            details={
                "guild_id": self.settings.discord_guild_id,
                "control_channel": self.settings.discord_control_channel,
                "control_channel_id": self.settings.discord_control_channel_id,
                "approvals_channel": self.settings.discord_approvals_channel,
                "approvals_channel_id": self.settings.discord_approvals_channel_id,
                "alerts_channel": self.settings.discord_alerts_channel,
                "alerts_channel_id": self.settings.discord_alerts_channel_id,
                "allowed_user_ids": self.settings.discord_allowed_user_ids,
            },
        )

    def _check_codex_provider_configuration(self) -> DoctorCheck:
        if not self.settings.openai_api_key:
            return DoctorCheck(
                key="codex_provider",
                label="Codex Provider",
                status="warn",
                message="Codex-compatible execution is not configured because QE_OPENAI_API_KEY is missing.",
                details={"base_url": self.settings.openai_base_url, "codex_command": self.settings.codex_command},
            )

        message = "Codex-compatible execution settings are present."
        if self.settings.openai_base_url:
            message = "Codex-compatible relay settings are present."

        return DoctorCheck(
            key="codex_provider",
            label="Codex Provider",
            status="ok",
            message=message,
            details={
                "base_url": self.settings.openai_base_url,
                "codex_command": self.settings.codex_command,
                "default_model": self.settings.codex_default_model,
                "workspace_mode": self.settings.codex_workspace_mode,
            },
        )

    def _check_acquisition_stack(self) -> DoctorCheck:
        summary = AcquisitionStackService(self.settings).build_summary()
        return DoctorCheck(
            key="acquisition_stack",
            label="Layered Acquisition Stack",
            status=summary.status,
            message=(
                "Layered research acquisition is available."
                if summary.status == "ok"
                else "Layered research acquisition is partially degraded."
                if summary.status == "warn"
                else "Layered research acquisition is unavailable."
            ),
            details={
                "primary_mode": summary.primary_mode,
                "layers": [asdict(layer) for layer in summary.layers],
            },
        )

    def _check_broker_configuration(self) -> DoctorCheck:
        if self.settings.default_broker_adapter != "alpaca":
            return DoctorCheck(
                key="broker",
                label="Broker Configuration",
                status="ok",
                message="Default broker adapter does not require external broker credentials.",
                details={
                    "default_broker_adapter": self.settings.default_broker_adapter,
                    "default_broker_environment": self.settings.default_broker_environment,
                },
            )

        environment = self.settings.default_broker_environment
        if environment == "paper":
            key = self.settings.alpaca_paper_api_key or self.settings.alpaca_api_key
            secret = self.settings.alpaca_paper_api_secret or self.settings.alpaca_api_secret
            base_url = self.settings.alpaca_paper_base_url
        else:
            key = self.settings.alpaca_live_api_key or self.settings.alpaca_api_key
            secret = self.settings.alpaca_live_api_secret or self.settings.alpaca_api_secret
            base_url = self.settings.alpaca_live_base_url

        if not key or not secret:
            return DoctorCheck(
                key="broker",
                label="Broker Configuration",
                status="fail",
                message="Default broker adapter is Alpaca, but the matching API key or secret is missing.",
                details={
                    "default_broker_adapter": self.settings.default_broker_adapter,
                    "default_broker_environment": environment,
                    "base_url": base_url,
                },
            )

        return DoctorCheck(
            key="broker",
            label="Broker Configuration",
            status="ok",
            message="Alpaca broker credentials are present for the configured default environment.",
            details={
                "default_broker_adapter": self.settings.default_broker_adapter,
                "default_broker_environment": environment,
                "base_url": base_url,
            },
        )

    def _check_dashboard_security_posture(self) -> DoctorCheck:
        dashboard_user = (self.settings.dashboard_access_username or "").strip()
        dashboard_password = (self.settings.dashboard_access_password or "").strip()
        dashboard_api_token = (self.settings.dashboard_api_token or "").strip()
        edge_public_host = (self.settings.edge_public_host or "").strip()
        details = {
            "api_bind_host": self.settings.api_bind_host,
            "dashboard_bind_host": self.settings.dashboard_bind_host,
            "edge_public_host": edge_public_host or None,
            "dashboard_basic_auth_enabled": bool(dashboard_user and dashboard_password),
            "dashboard_api_token_enabled": bool(dashboard_api_token),
        }

        if bool(dashboard_user) ^ bool(dashboard_password):
            return DoctorCheck(
                key="dashboard_security",
                label="Dashboard Security Posture",
                status="fail",
                message="Dashboard basic auth is partially configured. Set both QE_DASHBOARD_ACCESS_USERNAME and QE_DASHBOARD_ACCESS_PASSWORD together.",
                details=details,
            )

        public_dashboard = self._is_public_bind_host(self.settings.dashboard_bind_host)
        public_api = self._is_public_bind_host(self.settings.api_bind_host)

        missing: list[str] = []
        warnings: list[str] = []

        if (public_dashboard or edge_public_host) and not (dashboard_user and dashboard_password):
            missing.extend(["QE_DASHBOARD_ACCESS_USERNAME", "QE_DASHBOARD_ACCESS_PASSWORD"])
        elif not (dashboard_user and dashboard_password) and not public_dashboard and not edge_public_host:
            warnings.append("Dashboard bind host is private-local only, so basic auth is optional but still recommended before public exposure.")

        if (public_api or edge_public_host) and not dashboard_api_token:
            missing.append("QE_DASHBOARD_API_TOKEN")
        elif not dashboard_api_token and not public_api:
            warnings.append("Dashboard/system API routes are relying on localhost binding without an additional shared token.")

        if edge_public_host and self.settings.dashboard_bind_host not in {"127.0.0.1", "::1", "localhost"}:
            warnings.append("Keep QE_DASHBOARD_BIND_HOST on localhost when QE_EDGE_PUBLIC_HOST is set so the reverse proxy remains the only public surface.")

        if missing:
            return DoctorCheck(
                key="dashboard_security",
                label="Dashboard Security Posture",
                status="fail",
                message="Dashboard public-surface protection is incomplete for the configured exposure model.",
                details={**details, "missing": missing},
            )
        if warnings:
            return DoctorCheck(
                key="dashboard_security",
                label="Dashboard Security Posture",
                status="warn",
                message="Dashboard security posture is acceptable for localhost-only access, but public deployment hardening is incomplete.",
                details={**details, "warnings": warnings},
            )
        return DoctorCheck(
            key="dashboard_security",
            label="Dashboard Security Posture",
            status="ok",
            message="Dashboard and dashboard-facing API surfaces are protected for the configured deployment posture.",
            details=details,
        )

    def _check_node_role_boundary(self) -> DoctorCheck:
        raw_node_role = self.settings.node_role.strip().lower()
        effective_node_role = "worker" if raw_node_role == "research" else raw_node_role

        if raw_node_role not in {"core", "worker", "research"}:
            return DoctorCheck(
                key="node_role_boundary",
                label="Node Role Boundary",
                status="warn",
                message="Node role is not one of the expected production values `core` or `worker` (`research` is accepted as a deprecated alias).",
                details={
                    "node_role": self.settings.node_role,
                    "effective_node_role": effective_node_role,
                    "deployment_topology": self.settings.deployment_topology,
                },
            )

        has_broker_secret = any(
            [
                self.settings.alpaca_api_key,
                self.settings.alpaca_api_secret,
                self.settings.alpaca_paper_api_key,
                self.settings.alpaca_paper_api_secret,
                self.settings.alpaca_live_api_key,
                self.settings.alpaca_live_api_secret,
            ]
        )
        if effective_node_role == "worker":
            if self.settings.default_broker_adapter == "alpaca" or has_broker_secret:
                return DoctorCheck(
                    key="node_role_boundary",
                    label="Node Role Boundary",
                    status="fail",
                    message="Worker node is carrying Alpaca broker authority or secrets, which breaks the 2-VPS trust boundary.",
                    details={
                        "node_role": self.settings.node_role,
                        "effective_node_role": effective_node_role,
                        "deployment_topology": self.settings.deployment_topology,
                        "default_broker_adapter": self.settings.default_broker_adapter,
                    },
                )
            if self.settings.discord_token:
                return DoctorCheck(
                    key="node_role_boundary",
                    label="Node Role Boundary",
                    status="warn",
                    message="Worker node should avoid holding the Discord bot token unless you intentionally collapse roles.",
                    details={
                        "node_role": self.settings.node_role,
                        "effective_node_role": effective_node_role,
                        "deployment_topology": self.settings.deployment_topology,
                    },
                )
            if raw_node_role == "research":
                return DoctorCheck(
                    key="node_role_boundary",
                    label="Node Role Boundary",
                    status="warn",
                    message="Node role still uses deprecated `research` naming. Switch it to `worker` for the canonical production path.",
                    details={
                        "node_role": self.settings.node_role,
                        "effective_node_role": effective_node_role,
                        "deployment_topology": self.settings.deployment_topology,
                    },
                )

        return DoctorCheck(
            key="node_role_boundary",
            label="Node Role Boundary",
            status="ok",
            message="Node role and secret placement are consistent with the intended authority split.",
            details={
                "node_role": self.settings.node_role,
                "effective_node_role": effective_node_role,
                "deployment_topology": self.settings.deployment_topology,
            },
        )

    def _check_runtime_registry(self) -> DoctorCheck:
        try:
            runtime_snapshot = self.state_store.get_runtime_snapshot()
            entries = self.state_store.list_runtime_config_entries(limit=6)
        except Exception as exc:
            return DoctorCheck(
                key="runtime_registry",
                label="Runtime Registry",
                status="fail",
                message=f"Could not read runtime state or runtime config registry: {exc}",
                details={},
            )

        if not entries:
            return DoctorCheck(
                key="runtime_registry",
                label="Runtime Registry",
                status="warn",
                message="The runtime config registry is empty.",
                details={"active_goals": runtime_snapshot.active_goals},
            )

        return DoctorCheck(
            key="runtime_registry",
            label="Runtime Registry",
            status="ok",
            message="Durable runtime state and config registry are readable.",
            details={
                "config_entries_sample": [f"{entry.target_type}:{entry.target_key}" for entry in entries],
                "pending_approvals": runtime_snapshot.pending_approvals,
                "active_overrides": runtime_snapshot.active_overrides,
            },
        )

    def _is_public_bind_host(self, host: str | None) -> bool:
        normalized = (host or "").strip().lower()
        return normalized not in {"", "127.0.0.1", "::1", "localhost"}


def render_text_report(report: dict[str, Any]) -> str:
    lines = [f"Quant Evo Doctor: {report['status']}"]
    for check in report["checks"]:
        lines.append(f"- [{check['status']}] {check['label']}: {check['message']}")
    profiles = report.get("profiles", [])
    if profiles:
        lines.append("Readiness profiles:")
        for profile in profiles:
            lines.append(f"- [{profile['status']}] {profile['label']}: {profile['message']}")
            for blocker in profile.get("blocked_by", []):
                lines.append(f"  - {blocker}")
    return "\n".join(lines)
