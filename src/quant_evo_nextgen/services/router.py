from __future__ import annotations

import re

from quant_evo_nextgen.contracts.dashboard import DashboardOverview
from quant_evo_nextgen.contracts.intents import IntentClassification, IntentType
from quant_evo_nextgen.services.deploy_fields import find_deploy_field, normalize_deploy_field_alias


APPROVAL_ID_RE = re.compile(r"\b([a-zA-Z0-9-]{8,})\b")
ROLLBACK_RE = re.compile(
    "(?:rollback(?:\\s+to)?)\\s*(?:config)?\\s*(?:(?:revision)\\s+)?(?P<revision>[a-zA-Z0-9-]{8,})$",
    re.IGNORECASE,
)
DEPLOY_BOOTSTRAP_RE = re.compile(
    "(?:bootstrap|setup|initialize)\\s*(?P<role>core|worker|research)?\\s*(?:deployment|deploy|onboarding)?$",
    re.IGNORECASE,
)
DEPLOY_STATUS_RE = re.compile(
    "(?:(?:show|list|check)\\s*)?(?P<role>core|worker|research)?\\s*(?:deployment status|deploy status|preflight)$",
    re.IGNORECASE,
)
DEPLOY_SET_RE = re.compile(
    "(?:set|update)\\s*(?:(?P<role>core|worker|research)\\s+)?(?P<field>[^=]{1,80}?)\\s*(?:(?:to)\\s+|=\\s*)(?P<value>.+)$",
    re.IGNORECASE,
)
LOOP_ENABLE_RE = re.compile(
    "(?:enable)\\s+(?:loop\\s*)?(?P<loop>[a-z0-9_-]+)(?:\\s*loop)?$",
    re.IGNORECASE,
)
LOOP_DISABLE_RE = re.compile(
    "(?:disable)\\s+(?:loop\\s*)?(?P<loop>[a-z0-9_-]+)(?:\\s*loop)?$",
    re.IGNORECASE,
)
LOOP_CADENCE_RE = re.compile(
    "(?:set|change|update)?\\s*(?P<loop>[a-z0-9_-]+)\\s*(?:loop\\s*)?(?:interval|cadence|frequency)"
    "\\s*(?:(?:to)\\s+|=\\s*)(?P<value>.+)$",
    re.IGNORECASE,
)
SETTING_RE = re.compile(
    "(?:set|change|update|modify)\\s*(?P<target>[^=]{1,80}?)\\s*(?:(?:to)\\s+|=\\s*)(?P<value>.+)$",
    re.IGNORECASE,
)

KNOWN_LOOP_KEYS = {
    "governance-heartbeat",
    "source-revalidation",
    "research-intake",
    "research-distillation",
    "learning-synthesis",
    "market-session-guard",
    "broker-state-sync",
    "strategy-evaluation",
    "council-reflection",
    "owner-absence-safe-mode",
    "evolution-governance-sync",
}


class NaturalLanguageRouter:
    def classify(self, message: str) -> IntentClassification:
        raw = message.strip()
        normalized = raw.lower()
        reference_id = _extract_reference_id(normalized)

        deploy_bootstrap = _parse_deploy_bootstrap(normalized)
        if deploy_bootstrap is not None:
            return deploy_bootstrap

        deploy_status = _parse_deploy_status(normalized)
        if deploy_status is not None:
            return deploy_status

        deploy_set = _parse_deploy_setting(raw)
        if deploy_set is not None:
            return deploy_set

        if _contains_any(normalized, ("approvals", "pending approvals")):
            return IntentClassification(
                intent_type=IntentType.LIST_APPROVALS,
                proposed_action="List pending approvals in the control plane.",
                execution_supported=True,
            )

        if _contains_any(normalized, ("approve",)):
            return IntentClassification(
                intent_type=IntentType.APPROVE_REQUEST,
                reference_id=reference_id,
                proposed_action="Approve a pending control request.",
                execution_supported=True,
            )

        if _contains_any(normalized, ("reject",)):
            return IntentClassification(
                intent_type=IntentType.REJECT_REQUEST,
                reference_id=reference_id,
                proposed_action="Reject a pending control request.",
                execution_supported=True,
            )

        rollback_intent = _parse_runtime_config_rollback(normalized, reference_id)
        if rollback_intent is not None:
            return rollback_intent

        config_change = _parse_runtime_config_change(normalized)
        if config_change is not None:
            return config_change

        if _is_runtime_config_query(normalized):
            return IntentClassification(
                intent_type=IntentType.LIST_RUNTIME_CONFIG,
                proposed_action="Show the effective runtime configuration and recent config history.",
                execution_supported=True,
            )

        if _contains_any(normalized, ("status", "system status", "overview")):
            return IntentClassification(
                intent_type=IntentType.STATUS,
                proposed_action="Summarize the current system status.",
                execution_supported=True,
            )

        if _contains_any(normalized, ("risk", "risk status")):
            return IntentClassification(
                intent_type=IntentType.RISK_STATUS,
                target_domain="trading",
                proposed_action="Summarize current trading risk and control posture.",
                execution_supported=True,
            )

        if _contains_any(normalized, ("learning", "learned", "research progress")):
            return IntentClassification(
                intent_type=IntentType.LEARNING_SUMMARY,
                target_domain="learning",
                proposed_action="Summarize recent learning and memory progress.",
                execution_supported=True,
            )

        if _contains_any(normalized, ("pause",)) and _contains_any(
            normalized,
            ("evolution", "auto-evolution"),
        ):
            return IntentClassification(
                intent_type=IntentType.PAUSE_EVOLUTION,
                target_domain="evolution",
                risk_tier="R2",
                requires_confirmation=True,
                proposed_action="Pause the auto-evolution domain.",
            )

        if _contains_any(normalized, ("pause",)) and _contains_any(
            normalized,
            ("trading", "auto-trading", "live"),
        ):
            return IntentClassification(
                intent_type=IntentType.PAUSE_TRADING,
                target_domain="trading",
                risk_tier="R4",
                requires_confirmation=True,
                proposed_action="Pause auto-trading or live execution.",
            )

        if _contains_any(normalized, ("resume",)):
            return IntentClassification(
                intent_type=IntentType.RESUME_DOMAIN,
                target_domain=_resume_target_domain(normalized),
                risk_tier="R3",
                requires_confirmation=True,
                proposed_action="Resume a previously paused domain.",
            )

        if _contains_any(normalized, ("why", "reason", "explain")) and _contains_any(
            normalized,
            ("strategy",),
        ):
            return IntentClassification(
                intent_type=IntentType.EXPLAIN_STRATEGY,
                target_domain="strategy",
                proposed_action="Explain why a strategy was not promoted or why it degraded.",
                execution_supported=True,
            )

        return IntentClassification(
            intent_type=IntentType.UNKNOWN,
            clarification_needed=True,
            proposed_action="Ask for concise clarification or route to a slash command fallback.",
        )

    def render_response(self, intent: IntentClassification, overview: DashboardOverview) -> str:
        mode_label = _format_mode(overview.system.mode)
        risk_label = _format_risk_state(overview.system.risk_state)

        if intent.intent_type is IntentType.STATUS:
            return (
                f"{overview.headline}\n"
                f"Current mode: {mode_label}; risk state: {risk_label}; "
                f"production strategies: {overview.strategy.production}."
            )

        if intent.intent_type is IntentType.RISK_STATUS:
            return (
                f"Current risk state is {risk_label}.\n"
                f"Production strategies: {overview.strategy.production}; "
                f"open incidents: {overview.system.open_incidents}; "
                f"active goals: {overview.system.active_goals}."
            )

        if intent.intent_type is IntentType.LEARNING_SUMMARY:
            return (
                f"Durable principle memory currently holds {overview.learning.principles} principles, "
                f"{overview.learning.causal_cases} causal cases, and "
                f"{overview.learning.occupied_feature_cells} occupied feature cells."
            )

        if intent.intent_type is IntentType.EXPLAIN_STRATEGY:
            return (
                "The strategy explanation path is wired, but answering for a specific strategy "
                "still requires linked backtest, review, and promotion records."
            )

        if intent.intent_type is IntentType.LIST_RUNTIME_CONFIG:
            return "I will read the current runtime configuration, pending config proposals, and recent revisions."

        if intent.intent_type is IntentType.PROPOSE_CONFIG_CHANGE:
            return "I recognized this as a runtime config change request and will route it through the proposal and governance path."

        if intent.intent_type is IntentType.ROLLBACK_RUNTIME_CONFIG:
            return "I recognized this as a runtime config rollback request and will create a governed rollback proposal first."

        if intent.intent_type is IntentType.DEPLOY_BOOTSTRAP:
            role = intent.deploy_role or "core"
            return f"I will prepare the deployment draft for `{role}` and return the current preflight state."

        if intent.intent_type is IntentType.DEPLOY_STATUS:
            role = intent.deploy_role or "core"
            return f"I will read the deployment draft for `{role}` and return its current preflight result."

        if intent.intent_type is IntentType.DEPLOY_SET:
            role = intent.deploy_role or "core"
            field_label = intent.deploy_field_alias or "deployment field"
            return f"I will update `{role}` field `{field_label}` and rerun deployment preflight."

        if intent.requires_confirmation:
            return (
                "I recognized this as a governed control intent. "
                "The system will create an approval object first and wait for owner approval before changing state."
            )

        return "This instruction is not specific enough. You can send `status` directly or use `/status`."


def _contains_any(message: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in message for keyword in keywords)


def _extract_reference_id(message: str) -> str | None:
    match = APPROVAL_ID_RE.search(message)
    return match.group(1) if match else None


def _resume_target_domain(message: str) -> str:
    if "evolution" in message:
        return "evolution"
    if "trading" in message:
        return "trading"
    return "governance"


def _format_mode(mode: str) -> str:
    mapping = {
        "paper_only": "Paper Only",
        "limited_live_ready": "Limited Live Ready",
        "degraded": "Degraded",
    }
    return mapping.get(mode, mode)


def _format_risk_state(risk_state: str) -> str:
    mapping = {
        "observe": "Observe",
        "normal": "Normal",
        "halted": "Halted",
    }
    return mapping.get(risk_state, risk_state)


def _is_runtime_config_query(message: str) -> bool:
    return _contains_any(message, ("settings", "runtime config", "config")) and _contains_any(
        message,
        ("show", "list", "current", "now", "revision"),
    )


def _parse_runtime_config_rollback(message: str, reference_id: str | None) -> IntentClassification | None:
    match = ROLLBACK_RE.match(message)
    revision_id = match.group("revision") if match else None
    if revision_id is None and _contains_any(message, ("rollback config", "rollback revision")):
        revision_id = reference_id
    if revision_id is None:
        return None
    return IntentClassification(
        intent_type=IntentType.ROLLBACK_RUNTIME_CONFIG,
        reference_id=revision_id,
        proposed_action="Create a governed rollback proposal for a runtime config revision.",
        execution_supported=True,
    )


def _parse_runtime_config_change(message: str) -> IntentClassification | None:
    loop_enable = LOOP_ENABLE_RE.match(message)
    if loop_enable:
        loop_key = loop_enable.group("loop")
        if _looks_like_loop_key(loop_key):
            return IntentClassification(
                intent_type=IntentType.PROPOSE_CONFIG_CHANGE,
                config_target_type="supervisor_loop",
                config_target_key=loop_key,
                config_patch={"is_enabled": True},
                config_change_summary=f"Enable supervisor loop `{loop_key}`.",
                proposed_action="Create a config proposal to enable the supervisor loop.",
                execution_supported=True,
            )

    loop_disable = LOOP_DISABLE_RE.match(message)
    if loop_disable:
        loop_key = loop_disable.group("loop")
        if _looks_like_loop_key(loop_key):
            return IntentClassification(
                intent_type=IntentType.PROPOSE_CONFIG_CHANGE,
                config_target_type="supervisor_loop",
                config_target_key=loop_key,
                config_patch={"is_enabled": False},
                config_change_summary=f"Disable supervisor loop `{loop_key}`.",
                proposed_action="Create a config proposal to disable the supervisor loop.",
                execution_supported=True,
            )

    loop_cadence = LOOP_CADENCE_RE.match(message)
    if loop_cadence:
        loop_key = loop_cadence.group("loop")
        if _looks_like_loop_key(loop_key):
            cadence_seconds = _parse_duration_seconds(loop_cadence.group("value"))
            if cadence_seconds is not None:
                return IntentClassification(
                    intent_type=IntentType.PROPOSE_CONFIG_CHANGE,
                    config_target_type="supervisor_loop",
                    config_target_key=loop_key,
                    config_patch={"cadence_seconds": cadence_seconds},
                    config_change_summary=f"Change `{loop_key}` cadence to {cadence_seconds} seconds.",
                    proposed_action="Create a config proposal to change the supervisor loop cadence.",
                    execution_supported=True,
                )

    setting_match = SETTING_RE.match(message)
    if setting_match:
        parsed = _parse_named_setting(
            setting_match.group("target").strip(),
            setting_match.group("value").strip(),
        )
        if parsed is not None:
            return parsed

    return None


def _parse_named_setting(target: str, value: str) -> IntentClassification | None:
    alias_map = {
        "heartbeat": ("system_policy", "heartbeat_runtime", "interval_seconds"),
        "heartbeat interval": ("system_policy", "heartbeat_runtime", "interval_seconds"),
        "interaction language": ("owner_preference", "interaction_language", "operator_language"),
        "owner language": ("owner_preference", "interaction_language", "operator_language"),
        "control channel": ("owner_preference", "discord_channels", "control_channel"),
        "approvals channel": ("owner_preference", "discord_channels", "approvals_channel"),
        "alerts channel": ("owner_preference", "discord_channels", "alerts_channel"),
        "codex model": ("system_policy", "codex_runtime", "default_model"),
    }

    target_normalized = target.strip().lower()
    resolved = alias_map.get(target_normalized)
    if resolved is None:
        return None

    target_type, target_key, field_name = resolved
    if field_name == "interval_seconds":
        parsed_value = _parse_duration_seconds(value)
        if parsed_value is None:
            return None
    else:
        parsed_value = value

    return IntentClassification(
        intent_type=IntentType.PROPOSE_CONFIG_CHANGE,
        config_target_type=target_type,
        config_target_key=target_key,
        config_patch={field_name: parsed_value},
        config_change_summary=f"Update `{target_key}` field `{field_name}`.",
        proposed_action="Create a durable runtime config proposal.",
        execution_supported=True,
    )


def _looks_like_loop_key(loop_key: str) -> bool:
    return loop_key in KNOWN_LOOP_KEYS or "-" in loop_key


def _parse_duration_seconds(value: str) -> int | None:
    candidate = value.strip().lower()
    match = re.search(r"(\d+)", candidate)
    if match is None:
        return None
    quantity = int(match.group(1))
    if any(unit in candidate for unit in ("hour", "hours", "hr", "hrs")):
        return quantity * 3600
    if any(unit in candidate for unit in ("minute", "minutes", "min", "mins")):
        return quantity * 60
    return quantity


def _parse_deploy_bootstrap(message: str) -> IntentClassification | None:
    match = DEPLOY_BOOTSTRAP_RE.match(message)
    if match is None:
        return None
    role = (match.group("role") or "core").lower()
    return IntentClassification(
        intent_type=IntentType.DEPLOY_BOOTSTRAP,
        deploy_role=role,
        proposed_action="Bootstrap or confirm the deployment draft for the requested node role.",
        execution_supported=True,
    )


def _parse_deploy_status(message: str) -> IntentClassification | None:
    match = DEPLOY_STATUS_RE.match(message)
    if match is None and _contains_any(message, ("deployment status", "deploy status", "preflight")):
        role = "worker" if "worker" in message or "research" in message else "core"
    elif match is not None:
        role = (match.group("role") or "core").lower()
    else:
        return None
    return IntentClassification(
        intent_type=IntentType.DEPLOY_STATUS,
        deploy_role=role,
        proposed_action="Show the deployment preflight state for the requested node role.",
        execution_supported=True,
    )


def _parse_deploy_setting(message: str) -> IntentClassification | None:
    match = DEPLOY_SET_RE.match(message)
    if match is None:
        return None
    role = (match.group("role") or "core").lower()
    field = match.group("field").strip()
    value = match.group("value").strip()
    spec = find_deploy_field(field)
    if spec is None:
        return None
    sensitive = spec.secret
    return IntentClassification(
        intent_type=IntentType.DEPLOY_SET,
        deploy_role=role,
        deploy_field_alias=field,
        deploy_value=value,
        contains_sensitive_value=sensitive,
        sanitized_message_summary=(
            f"Set {role} {spec.label} (redacted)"
            if sensitive
            else f"Set {role} {spec.label} to {value}"
        ),
        proposed_action="Update the deployment draft field for the requested node role.",
        execution_supported=True,
    )


def _normalize_deploy_field_alias(field: str) -> str:
    return normalize_deploy_field_alias(field)
