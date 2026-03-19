from __future__ import annotations

import re

from quant_evo_nextgen.contracts.dashboard import DashboardOverview
from quant_evo_nextgen.contracts.intents import IntentClassification, IntentType


APPROVAL_ID_RE = re.compile(r"\b([a-zA-Z0-9-]{8,})\b")
ROLLBACK_RE = re.compile(
    r"(?:回滚(?:到)?|rollback(?:\s+to)?)\s*(?:配置|config)?\s*(?:(?:版本|revision)\s+)?(?P<revision>[a-zA-Z0-9-]{8,})$"
)
DEPLOY_BOOTSTRAP_RE = re.compile(
    r"(?:开始|初始化|bootstrap|setup)\s*(?P<role>core|worker|research)?\s*(?:部署|deploy|引导|onboarding)?$"
)
DEPLOY_STATUS_RE = re.compile(
    r"(?:(?:查看|显示|列出|show)\s*)?(?P<role>core|worker|research)?\s*(?:部署状态|部署预检|deploy status|preflight)$"
)
DEPLOY_SET_RE = re.compile(
    r"(?:设置|set|update)\s*(?:(?P<role>core|worker|research)\s+)?(?P<field>[^=]{1,80}?)\s*(?:为|成|to|=)\s*(?P<value>.+)$"
)
LOOP_ENABLE_RE = re.compile(r"(?:启用|打开|enable)\s+(?:loop\s*)?(?P<loop>[a-z0-9_-]+)(?:\s*loop)?$")
LOOP_DISABLE_RE = re.compile(r"(?:禁用|停用|关闭|disable)\s+(?:loop\s*)?(?P<loop>[a-z0-9_-]+)(?:\s*loop)?$")
LOOP_CADENCE_RE = re.compile(
    r"(?:把|将|set|change|update)?\s*(?P<loop>[a-z0-9_-]+)\s*(?:loop\s*)?(?:间隔|cadence|频率)"
    r"\s*(?:改成|设置为|设为|to|=)\s*(?P<value>.+)$"
)
SETTING_RE = re.compile(
    r"(?:把|将|set|change|update|modify)\s*(?P<target>[^=]{1,80}?)\s*(?:改成|设置为|设为|to|=)\s*(?P<value>.+)$"
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
KNOWN_DEPLOY_FIELD_ALIASES = {
    "中转地址",
    "relaybaseurl",
    "openaibaseurl",
    "中转key",
    "relaykey",
    "openaiapikey",
    "postgres密码",
    "postgrespassword",
    "discordtoken",
    "机器人token",
    "guildid",
    "服务器id",
    "控制频道id",
    "controlchannelid",
    "审批频道id",
    "approvalschannelid",
    "告警频道id",
    "alertschannelid",
    "允许用户id",
    "alloweduserids",
    "brokermode",
    "券商模式",
    "alpacapaperkey",
    "alpacapapersecret",
    "alpacalivekey",
    "alpacalivesecret",
    "dashboard用户名",
    "dashboardusername",
    "dashboard密码",
    "dashboardpassword",
    "dashboardapitoken",
    "dashboardtoken",
    "dashboard域名",
    "edgepublichost",
    "acmeemail",
    "postgresurl",
    "数据库url",
}
SENSITIVE_DEPLOY_FIELDS = {
    "中转key",
    "relaykey",
    "openaiapikey",
    "postgres密码",
    "postgrespassword",
    "discordtoken",
    "机器人token",
    "alpacapaperkey",
    "alpacapapersecret",
    "alpacalivekey",
    "alpacalivesecret",
    "dashboard密码",
    "dashboardpassword",
    "dashboardapitoken",
    "dashboardtoken",
    "postgresurl",
    "数据库url",
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

        if _contains_any(normalized, ("待审批", "待处理审批", "approvals", "pending approvals")):
            return IntentClassification(
                intent_type=IntentType.LIST_APPROVALS,
                proposed_action="List pending approvals in the control plane.",
                execution_supported=True,
            )

        if _contains_any(normalized, ("批准", "通过", "approve")):
            return IntentClassification(
                intent_type=IntentType.APPROVE_REQUEST,
                reference_id=reference_id,
                proposed_action="Approve a pending control request.",
                execution_supported=True,
            )

        if _contains_any(normalized, ("拒绝", "驳回", "reject")):
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

        if _contains_any(normalized, ("状态", "现状", "概况", "总览", "status", "system status")):
            return IntentClassification(
                intent_type=IntentType.STATUS,
                proposed_action="Summarize the current system status.",
                execution_supported=True,
            )

        if _contains_any(normalized, ("风险", "风控", "risk")):
            return IntentClassification(
                intent_type=IntentType.RISK_STATUS,
                target_domain="trading",
                proposed_action="Summarize current trading risk and control posture.",
                execution_supported=True,
            )

        if _contains_any(normalized, ("学到", "学习", "研究进展", "learning")):
            return IntentClassification(
                intent_type=IntentType.LEARNING_SUMMARY,
                target_domain="learning",
                proposed_action="Summarize recent learning and memory progress.",
                execution_supported=True,
            )

        if _contains_any(normalized, ("暂停", "停掉", "停止", "pause")) and _contains_any(
            normalized,
            ("进化", "自进化", "evolution"),
        ):
            return IntentClassification(
                intent_type=IntentType.PAUSE_EVOLUTION,
                target_domain="evolution",
                risk_tier="R2",
                requires_confirmation=True,
                proposed_action="Pause the auto-evolution domain.",
            )

        if _contains_any(normalized, ("暂停", "停掉", "停止", "pause")) and _contains_any(
            normalized,
            ("交易", "自动交易", "live", "trading"),
        ):
            return IntentClassification(
                intent_type=IntentType.PAUSE_TRADING,
                target_domain="trading",
                risk_tier="R4",
                requires_confirmation=True,
                proposed_action="Pause auto-trading or live execution.",
            )

        if _contains_any(normalized, ("恢复", "继续", "resume")):
            return IntentClassification(
                intent_type=IntentType.RESUME_DOMAIN,
                target_domain=_resume_target_domain(normalized),
                risk_tier="R3",
                requires_confirmation=True,
                proposed_action="Resume a previously paused domain.",
            )

        if _contains_any(normalized, ("为什么", "原因", "解释", "explain")) and _contains_any(
            normalized,
            ("策略", "strategy"),
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
                f"当前模式：{mode_label}；风险状态：{risk_label}；"
                f"生产策略数量：{overview.strategy.production}。"
            )

        if intent.intent_type is IntentType.RISK_STATUS:
            return (
                f"当前风险状态为 {risk_label}。\n"
                f"生产策略数量：{overview.strategy.production}；"
                f"未关闭事件：{overview.system.open_incidents}；"
                f"活跃目标：{overview.system.active_goals}。"
            )

        if intent.intent_type is IntentType.LEARNING_SUMMARY:
            return (
                f"当前长期原则记忆 {overview.learning.principles} 条，"
                f"因果案例 {overview.learning.causal_cases} 条，"
                f"特征图已占用 {overview.learning.occupied_feature_cells} 个格子。"
            )

        if intent.intent_type is IntentType.EXPLAIN_STRATEGY:
            return (
                "策略解释链路已经预留，但要回答到某个具体策略，"
                "还需要接入回测、评审和 promotion 记录。"
            )

        if intent.intent_type is IntentType.LIST_RUNTIME_CONFIG:
            return "我会读取当前运行时配置、待处理配置提案和最近配置版本。"

        if intent.intent_type is IntentType.PROPOSE_CONFIG_CHANGE:
            return "我识别到这是一次运行时配置调整请求，会先走提案与治理路径。"

        if intent.intent_type is IntentType.ROLLBACK_RUNTIME_CONFIG:
            return "我识别到这是一次运行时配置回滚请求，会先生成受治理的回滚提案。"

        if intent.intent_type is IntentType.DEPLOY_BOOTSTRAP:
            role = intent.deploy_role or "core"
            return f"我会先为 `{role}` 生成部署配置草稿，并返回当前预检状态。"

        if intent.intent_type is IntentType.DEPLOY_STATUS:
            role = intent.deploy_role or "core"
            return f"我会读取 `{role}` 的部署草稿并返回预检结果。"

        if intent.intent_type is IntentType.DEPLOY_SET:
            role = intent.deploy_role or "core"
            field_label = intent.deploy_field_alias or "部署字段"
            return f"我会更新 `{role}` 的 `{field_label}`，并重新跑一次部署预检。"

        if intent.requires_confirmation:
            return (
                "我识别到这是一个需要治理确认的控制意图。"
                "系统会先创建审批对象，再由审批流决定是否真正切换状态。"
            )

        return "我理解到你在查询系统，但当前语义还不够具体。你可以直接发送“状态”，或使用 `/status`。"


def _contains_any(message: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in message for keyword in keywords)


def _extract_reference_id(message: str) -> str | None:
    match = APPROVAL_ID_RE.search(message)
    return match.group(1) if match else None


def _resume_target_domain(message: str) -> str:
    if "进化" in message or "evolution" in message:
        return "evolution"
    if "交易" in message or "trading" in message:
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
    return _contains_any(message, ("配置", "设定", "settings", "runtime config", "config")) and _contains_any(
        message,
        ("查看", "显示", "列出", "show", "list", "当前", "现在", "版本", "revision"),
    )


def _parse_runtime_config_rollback(message: str, reference_id: str | None) -> IntentClassification | None:
    match = ROLLBACK_RE.match(message)
    revision_id = match.group("revision") if match else None
    if revision_id is None and _contains_any(message, ("回滚配置", "rollback config", "回滚 revision", "rollback revision")):
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
        "心跳": ("system_policy", "heartbeat_runtime", "interval_seconds"),
        "心跳间隔": ("system_policy", "heartbeat_runtime", "interval_seconds"),
        "heartbeat": ("system_policy", "heartbeat_runtime", "interval_seconds"),
        "语言": ("owner_preference", "interaction_language", "operator_language"),
        "owner语言": ("owner_preference", "interaction_language", "operator_language"),
        "interaction language": ("owner_preference", "interaction_language", "operator_language"),
        "控制频道": ("owner_preference", "discord_channels", "control_channel"),
        "control channel": ("owner_preference", "discord_channels", "control_channel"),
        "审批频道": ("owner_preference", "discord_channels", "approvals_channel"),
        "approvals channel": ("owner_preference", "discord_channels", "approvals_channel"),
        "告警频道": ("owner_preference", "discord_channels", "alerts_channel"),
        "alerts channel": ("owner_preference", "discord_channels", "alerts_channel"),
        "codex模型": ("system_policy", "codex_runtime", "default_model"),
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
    if any(unit in candidate for unit in ("小时", "hour", "hours", "hr", "hrs")):
        return quantity * 3600
    if any(unit in candidate for unit in ("分钟", "分", "minute", "minutes", "min", "mins")):
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
    if match is None and _contains_any(message, ("部署状态", "部署预检", "deploy status", "preflight")):
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
    normalized_field = _normalize_deploy_field_alias(field)
    if normalized_field not in KNOWN_DEPLOY_FIELD_ALIASES:
        return None
    sensitive = normalized_field in SENSITIVE_DEPLOY_FIELDS
    return IntentClassification(
        intent_type=IntentType.DEPLOY_SET,
        deploy_role=role,
        deploy_field_alias=field,
        deploy_value=value,
        contains_sensitive_value=sensitive,
        sanitized_message_summary=(
            f"设置 {role} 的 {field}（已脱敏）" if sensitive else f"设置 {role} 的 {field} 为 {value}"
        ),
        proposed_action="Update the deployment draft field for the requested node role.",
        execution_supported=True,
    )


def _normalize_deploy_field_alias(field: str) -> str:
    return field.strip().lower().replace(" ", "").replace("_", "").replace("-", "")
