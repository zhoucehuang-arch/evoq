from quant_evo_nextgen.config import Settings
from quant_evo_nextgen.services.discord_access import DiscordAccessPolicy


def test_discord_access_allows_trusted_user_in_control_channel() -> None:
    settings = Settings(
        discord_control_channel="control",
        discord_approvals_channel="approvals",
        discord_allowed_user_ids="1001,1002",
    )

    policy = DiscordAccessPolicy.from_settings(settings)
    decision = policy.authorize(
        action="control",
        user_id=1001,
        channel_id=None,
        channel_name="control",
    )

    assert decision.allowed is True


def test_discord_access_rejects_untrusted_user() -> None:
    settings = Settings(
        discord_control_channel="control",
        discord_approvals_channel="approvals",
        discord_allowed_user_ids="1001,1002",
    )

    policy = DiscordAccessPolicy.from_settings(settings)
    decision = policy.authorize(
        action="control",
        user_id=2001,
        channel_id=None,
        channel_name="control",
    )

    assert decision.allowed is False
    assert "allowlist" in (decision.reason or "").lower()


def test_discord_access_rejects_approval_action_in_wrong_channel() -> None:
    settings = Settings(
        discord_control_channel="control",
        discord_approvals_channel="approvals",
        discord_allowed_user_ids="1001",
    )

    policy = DiscordAccessPolicy.from_settings(settings)
    decision = policy.authorize(
        action="approval",
        user_id=1001,
        channel_id=None,
        channel_name="control",
    )

    assert decision.allowed is False
    assert "approvals channel boundary" in (decision.reason or "").lower()
