from __future__ import annotations

import pytest

from quant_evo_nextgen.services.deploy_fields import (
    find_deploy_field,
    known_deploy_field_aliases,
    normalize_deploy_field_alias,
    resolve_deploy_field,
    sensitive_deploy_field_aliases,
)


def test_deploy_field_aliases_normalize_operator_language() -> None:
    assert normalize_deploy_field_alias("Relay Base URL") == "relaybaseurl"
    assert find_deploy_field("openai relay url").env_key == "QE_OPENAI_BASE_URL"
    assert find_deploy_field("dashboard-token").key == "dashboard_api_token"


def test_resolve_deploy_field_enforces_role_scope() -> None:
    assert resolve_deploy_field("postgres password", role="core").env_key == "QE_POSTGRES_PASSWORD"

    with pytest.raises(ValueError, match="not valid for role"):
        resolve_deploy_field("postgres password", role="worker")


def test_deploy_field_indexes_include_secret_and_public_aliases() -> None:
    known = known_deploy_field_aliases()
    sensitive = sensitive_deploy_field_aliases()

    assert "relaybaseurl" in known
    assert "relayapikey" in sensitive
    assert "dashboardtoken" in sensitive
