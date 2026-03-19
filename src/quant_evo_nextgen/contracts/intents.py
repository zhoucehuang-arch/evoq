from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class IntentType(str, Enum):
    STATUS = "status"
    RISK_STATUS = "risk_status"
    LEARNING_SUMMARY = "learning_summary"
    DEPLOY_BOOTSTRAP = "deploy_bootstrap"
    DEPLOY_STATUS = "deploy_status"
    DEPLOY_SET = "deploy_set"
    LIST_RUNTIME_CONFIG = "list_runtime_config"
    PROPOSE_CONFIG_CHANGE = "propose_config_change"
    ROLLBACK_RUNTIME_CONFIG = "rollback_runtime_config"
    LIST_APPROVALS = "list_approvals"
    APPROVE_REQUEST = "approve_request"
    REJECT_REQUEST = "reject_request"
    PAUSE_EVOLUTION = "pause_evolution"
    PAUSE_TRADING = "pause_trading"
    RESUME_DOMAIN = "resume_domain"
    EXPLAIN_STRATEGY = "explain_strategy"
    UNKNOWN = "unknown"


class IntentClassification(BaseModel):
    intent_type: IntentType
    target_domain: str | None = None
    reference_id: str | None = None
    config_target_type: str | None = None
    config_target_key: str | None = None
    config_patch: dict[str, object] = Field(default_factory=dict)
    config_change_summary: str | None = None
    deploy_role: str | None = None
    deploy_field_alias: str | None = None
    deploy_value: str | None = None
    contains_sensitive_value: bool = False
    sanitized_message_summary: str | None = None
    risk_tier: str = "R1"
    requires_confirmation: bool = False
    clarification_needed: bool = False
    execution_supported: bool = False
    proposed_action: str
