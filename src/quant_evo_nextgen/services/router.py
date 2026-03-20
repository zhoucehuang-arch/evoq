from __future__ import annotations

import re

from quant_evo_nextgen.contracts.dashboard import DashboardOverview
from quant_evo_nextgen.contracts.intents import IntentClassification, IntentType
from quant_evo_nextgen.services.deploy_fields import find_deploy_field, normalize_deploy_field_alias


APPROVAL_ID_RE = re.compile(r"\b([a-zA-Z0-9-]{8,})\b")
ROLLBACK_RE = re.compile(
    "(?:\u56de\u6eda|rollback(?:\\s+to)?)\\s*(?:\u914d\u7f6e|config)?\\s*(?:(?:\u7248\u672c|revision)\\s+)?(?P<revision>[a-zA-Z0-9-]{8,})$",
    re.IGNORECASE,
)
DEPLOY_BOOTSTRAP_RE = re.compile(
    "(?:\u5f00\u59cb|\u521d\u59cb\u5316|bootstrap|setup)\\s*(?P<role>core|worker|research)?\\s*(?:\u90e8\u7f72|deploy|\u5f15\u5bfc|onboarding)?$",
    re.IGNORECASE,
)
DEPLOY_STATUS_RE = re.compile(
    "(?:(?:\u67e5\u770b|\u663e\u793a|\u5217\u51fa|show)\\s*)?(?P<role>core|worker|research)?\\s*(?:\u90e8\u7f72\u72b6\u6001|\u90e8\u7f72\u9884\u68c0|deploy status|preflight)$",
    re.IGNORECASE,
)
DEPLOY_SET_RE = re.compile(
    "(?:\u8bbe\u7f6e|set|update)\\s*(?:(?P<role>core|worker|research)\\s+)?(?P<field>[^=]{1,80}?)\\s*(?:\u4e3a|to|=)\\s*(?P<value>.+)$",
    re.IGNORECASE,
)
LOOP_ENABLE_RE = re.compile(
    "(?:\u542f\u7528|\u6253\u5f00|enable)\\s+(?:loop\\s*)?(?P<loop>[a-z0-9_-]+)(?:\\s*loop)?$",
    re.IGNORECASE,
)
LOOP_DISABLE_RE = re.compile(
    "(?:\u7981\u7528|\u505c\u7528|\u5173\u95ed|disable)\\s+(?:loop\\s*)?(?P<loop>[a-z0-9_-]+)(?:\\s*loop)?$",
    re.IGNORECASE,
)
LOOP_CADENCE_RE = re.compile(
    "(?:\u628a|set|change|update)?\\s*(?P<loop>[a-z0-9_-]+)\\s*(?:loop\\s*)?(?:\u95f4\u9694|cadence|\u9891\u7387)"
    "\\s*(?:\u6539\u6210|\u8bbe\u7f6e\u4e3a|to|=)\\s*(?P<value>.+)$",
    re.IGNORECASE,
)
SETTING_RE = re.compile(
    "(?:\u628a|set|change|update|modify)\\s*(?P<target>[^=]{1,80}?)\\s*(?:\u6539\u6210|\u8bbe\u7f6e\u4e3a|to|=)\\s*(?P<value>.+)$",
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

        if _contains_any(normalized, ("\u5f85\u5ba1\u6279", "\u5f85\u5904\u7406\u5ba1\u6279", "approvals", "pending approvals")):
            return IntentClassification(
                intent_type=IntentType.LIST_APPROVALS,
                proposed_action="List pending approvals in the control plane.",
                execution_supported=True,
            )

        if _contains_any(normalized, ("\u6279\u51c6", "\u901a\u8fc7", "approve")):
            return IntentClassification(
                intent_type=IntentType.APPROVE_REQUEST,
                reference_id=reference_id,
                proposed_action="Approve a pending control request.",
                execution_supported=True,
            )

        if _contains_any(normalized, ("\u62d2\u7edd", "\u9a73\u56de", "reject")):
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

        if _contains_any(normalized, ("\u72b6\u6001", "\u73b0\u72b6", "\u6982\u51b5", "\u603b\u89c8", "status", "system status")):
            return IntentClassification(
                intent_type=IntentType.STATUS,
                proposed_action="Summarize the current system status.",
                execution_supported=True,
            )

        if _contains_any(normalized, ("\u98ce\u9669", "\u98ce\u63a7", "risk")):
            return IntentClassification(
                intent_type=IntentType.RISK_STATUS,
                target_domain="trading",
                proposed_action="Summarize current trading risk and control posture.",
                execution_supported=True,
            )

        if _contains_any(normalized, ("\u5b66\u5230", "\u5b66\u4e60", "\u7814\u7a76\u8fdb\u5c55", "learning")):
            return IntentClassification(
                intent_type=IntentType.LEARNING_SUMMARY,
                target_domain="learning",
                proposed_action="Summarize recent learning and memory progress.",
                execution_supported=True,
            )

        if _contains_any(normalized, ("\u6682\u505c", "\u505c\u6b62", "pause")) and _contains_any(
            normalized,
            ("\u8fdb\u5316", "\u81ea\u8fdb\u5316", "evolution"),
        ):
            return IntentClassification(
                intent_type=IntentType.PAUSE_EVOLUTION,
                target_domain="evolution",
                risk_tier="R2",
                requires_confirmation=True,
                proposed_action="Pause the auto-evolution domain.",
            )

        if _contains_any(normalized, ("\u6682\u505c", "\u505c\u6b62", "pause")) and _contains_any(
            normalized,
            ("\u4ea4\u6613", "\u81ea\u52a8\u4ea4\u6613", "live", "trading"),
        ):
            return IntentClassification(
                intent_type=IntentType.PAUSE_TRADING,
                target_domain="trading",
                risk_tier="R4",
                requires_confirmation=True,
                proposed_action="Pause auto-trading or live execution.",
            )

        if _contains_any(normalized, ("\u6062\u590d", "\u7ee7\u7eed", "resume")):
            return IntentClassification(
                intent_type=IntentType.RESUME_DOMAIN,
                target_domain=_resume_target_domain(normalized),
                risk_tier="R3",
                requires_confirmation=True,
                proposed_action="Resume a previously paused domain.",
            )

        if _contains_any(normalized, ("\u4e3a\u4ec0\u4e48", "\u539f\u56e0", "\u89e3\u91ca", "explain")) and _contains_any(
            normalized,
            ("\u7b56\u7565", "strategy"),
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
                f"\u5f53\u524d\u6a21\u5f0f: {mode_label}\uff1b\u98ce\u9669\u72b6\u6001: {risk_label}\uff1b"
                f"\u751f\u4ea7\u7b56\u7565\u6570\u91cf: {overview.strategy.production}\u3002"
            )

        if intent.intent_type is IntentType.RISK_STATUS:
            return (
                f"\u5f53\u524d\u98ce\u9669\u72b6\u6001\u4e3a {risk_label}\u3002\n"
                f"\u751f\u4ea7\u7b56\u7565\u6570\u91cf: {overview.strategy.production}\uff1b"
                f"\u672a\u5173\u95ed\u4e8b\u4ef6: {overview.system.open_incidents}\uff1b"
                f"\u6d3b\u8dc3\u76ee\u6807: {overview.system.active_goals}\u3002"
            )

        if intent.intent_type is IntentType.LEARNING_SUMMARY:
            return (
                f"\u5f53\u524d\u957f\u671f\u539f\u5219\u8bb0\u5fc6 {overview.learning.principles} \u6761\uff0c"
                f"\u56e0\u679c\u6848\u4f8b {overview.learning.causal_cases} \u6761\uff0c"
                f"\u7279\u5f81\u56fe\u5df2\u5360\u7528 {overview.learning.occupied_feature_cells} \u4e2a\u683c\u5b50\u3002"
            )

        if intent.intent_type is IntentType.EXPLAIN_STRATEGY:
            return (
                "\u7b56\u7565\u89e3\u91ca\u94fe\u8def\u5df2\u9884\u7559\uff0c"
                "\u4f46\u8981\u56de\u7b54\u5230\u67d0\u4e2a\u5177\u4f53\u7b56\u7565\uff0c"
                "\u8fd8\u9700\u8981\u63a5\u5165\u56de\u6d4b\u3001\u8bc4\u5ba1\u548c promotion \u8bb0\u5f55\u3002"
            )

        if intent.intent_type is IntentType.LIST_RUNTIME_CONFIG:
            return "\u6211\u4f1a\u8bfb\u53d6\u5f53\u524d\u8fd0\u884c\u65f6\u914d\u7f6e\u3001\u5f85\u5904\u7406\u914d\u7f6e\u63d0\u6848\u548c\u6700\u8fd1\u914d\u7f6e\u7248\u672c\u3002"

        if intent.intent_type is IntentType.PROPOSE_CONFIG_CHANGE:
            return "\u6211\u8bc6\u522b\u5230\u8fd9\u662f\u4e00\u6b21\u8fd0\u884c\u65f6\u914d\u7f6e\u8c03\u6574\u8bf7\u6c42\uff0c\u4f1a\u5148\u8d70\u63d0\u6848\u4e0e\u6cbb\u7406\u8def\u5f84\u3002"

        if intent.intent_type is IntentType.ROLLBACK_RUNTIME_CONFIG:
            return "\u6211\u8bc6\u522b\u5230\u8fd9\u662f\u4e00\u6b21\u8fd0\u884c\u65f6\u914d\u7f6e\u56de\u6eda\u8bf7\u6c42\uff0c\u4f1a\u5148\u751f\u6210\u53d7\u6cbb\u7406\u7684\u56de\u6eda\u63d0\u6848\u3002"

        if intent.intent_type is IntentType.DEPLOY_BOOTSTRAP:
            role = intent.deploy_role or "core"
            return f"\u6211\u4f1a\u5148\u4e3a `{role}` \u751f\u6210\u90e8\u7f72\u8349\u7a3f\uff0c\u5e76\u8fd4\u56de\u5f53\u524d\u9884\u68c0\u72b6\u6001\u3002"

        if intent.intent_type is IntentType.DEPLOY_STATUS:
            role = intent.deploy_role or "core"
            return f"\u6211\u4f1a\u8bfb\u53d6 `{role}` \u7684\u90e8\u7f72\u8349\u7a3f\uff0c\u5e76\u8fd4\u56de\u9884\u68c0\u7ed3\u679c\u3002"

        if intent.intent_type is IntentType.DEPLOY_SET:
            role = intent.deploy_role or "core"
            field_label = intent.deploy_field_alias or "\u90e8\u7f72\u5b57\u6bb5"
            return f"\u6211\u4f1a\u66f4\u65b0 `{role}` \u7684 `{field_label}`\uff0c\u5e76\u91cd\u65b0\u8dd1\u4e00\u6b21\u90e8\u7f72\u9884\u68c0\u3002"

        if intent.requires_confirmation:
            return (
                "\u6211\u8bc6\u522b\u5230\u8fd9\u662f\u4e00\u4e2a\u9700\u8981\u6cbb\u7406\u786e\u8ba4\u7684\u63a7\u5236\u610f\u56fe\u3002"
                "\u7cfb\u7edf\u4f1a\u5148\u521b\u5efa\u5ba1\u6279\u5bf9\u8c61\uff0c"
                "\u518d\u7531 owner \u5ba1\u6279\u6d41\u51b3\u5b9a\u662f\u5426\u771f\u6b63\u5207\u6362\u72b6\u6001\u3002"
            )

        return "\u8fd9\u6761\u6307\u4ee4\u8fd8\u4e0d\u591f\u5177\u4f53\u3002\u4f60\u53ef\u4ee5\u76f4\u63a5\u53d1\u9001\u201c\u72b6\u6001\u201d\uff0c\u6216\u4f7f\u7528 `/status`\u3002"


def _contains_any(message: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in message for keyword in keywords)


def _extract_reference_id(message: str) -> str | None:
    match = APPROVAL_ID_RE.search(message)
    return match.group(1) if match else None


def _resume_target_domain(message: str) -> str:
    if "\u8fdb\u5316" in message or "evolution" in message:
        return "evolution"
    if "\u4ea4\u6613" in message or "trading" in message:
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
    return _contains_any(message, ("\u914d\u7f6e", "\u8bbe\u5b9a", "settings", "runtime config", "config")) and _contains_any(
        message,
        ("\u67e5\u770b", "\u663e\u793a", "\u5217\u51fa", "show", "list", "\u5f53\u524d", "\u73b0\u5728", "\u7248\u672c", "revision"),
    )


def _parse_runtime_config_rollback(message: str, reference_id: str | None) -> IntentClassification | None:
    match = ROLLBACK_RE.match(message)
    revision_id = match.group("revision") if match else None
    if revision_id is None and _contains_any(message, ("\u56de\u6eda\u914d\u7f6e", "rollback config", "\u56de\u6eda revision", "rollback revision")):
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
        "\u5fc3\u8df3": ("system_policy", "heartbeat_runtime", "interval_seconds"),
        "\u5fc3\u8df3\u95f4\u9694": ("system_policy", "heartbeat_runtime", "interval_seconds"),
        "heartbeat": ("system_policy", "heartbeat_runtime", "interval_seconds"),
        "\u8bed\u8a00": ("owner_preference", "interaction_language", "operator_language"),
        "owner\u8bed\u8a00": ("owner_preference", "interaction_language", "operator_language"),
        "interaction language": ("owner_preference", "interaction_language", "operator_language"),
        "\u63a7\u5236\u9891\u9053": ("owner_preference", "discord_channels", "control_channel"),
        "control channel": ("owner_preference", "discord_channels", "control_channel"),
        "\u5ba1\u6279\u9891\u9053": ("owner_preference", "discord_channels", "approvals_channel"),
        "approvals channel": ("owner_preference", "discord_channels", "approvals_channel"),
        "\u544a\u8b66\u9891\u9053": ("owner_preference", "discord_channels", "alerts_channel"),
        "alerts channel": ("owner_preference", "discord_channels", "alerts_channel"),
        "codex\u6a21\u578b": ("system_policy", "codex_runtime", "default_model"),
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
    if any(unit in candidate for unit in ("\u5c0f\u65f6", "hour", "hours", "hr", "hrs")):
        return quantity * 3600
    if any(unit in candidate for unit in ("\u5206\u949f", "\u5206", "minute", "minutes", "min", "mins")):
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
    if match is None and _contains_any(message, ("\u90e8\u7f72\u72b6\u6001", "\u90e8\u7f72\u9884\u68c0", "deploy status", "preflight")):
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
            f"\u8bbe\u7f6e {role} \u7684 {spec.label}\uff08\u5df2\u8131\u654f\uff09"
            if sensitive
            else f"\u8bbe\u7f6e {role} \u7684 {spec.label} \u4e3a {value}"
        ),
        proposed_action="Update the deployment draft field for the requested node role.",
        execution_supported=True,
    )


def _normalize_deploy_field_alias(field: str) -> str:
    return normalize_deploy_field_alias(field)
