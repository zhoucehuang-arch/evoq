from __future__ import annotations

from dataclasses import dataclass

from quant_evo_nextgen.config import Settings


def _parse_int_set(raw: str) -> set[int]:
    values: set[int] = set()
    for item in raw.split(","):
        stripped = item.strip()
        if not stripped:
            continue
        try:
            values.add(int(stripped))
        except ValueError:
            continue
    return values


def _normalize_name(value: str | None) -> str:
    return (value or "").strip().lower()


@dataclass(slots=True)
class DiscordAccessDecision:
    allowed: bool
    reason: str | None = None


@dataclass(slots=True)
class DiscordAccessPolicy:
    allowed_user_ids: set[int]
    control_channel_names: set[str]
    approvals_channel_names: set[str]
    alerts_channel_names: set[str]
    control_channel_ids: set[int]
    approvals_channel_ids: set[int]
    alerts_channel_ids: set[int]

    @classmethod
    def from_settings(cls, settings: Settings) -> "DiscordAccessPolicy":
        return cls(
            allowed_user_ids=_parse_int_set(settings.discord_allowed_user_ids),
            control_channel_names={_normalize_name(settings.discord_control_channel)},
            approvals_channel_names={_normalize_name(settings.discord_approvals_channel)},
            alerts_channel_names={_normalize_name(settings.discord_alerts_channel)},
            control_channel_ids={settings.discord_control_channel_id} if settings.discord_control_channel_id else set(),
            approvals_channel_ids={settings.discord_approvals_channel_id} if settings.discord_approvals_channel_id else set(),
            alerts_channel_ids={settings.discord_alerts_channel_id} if settings.discord_alerts_channel_id else set(),
        )

    @property
    def allowlist_configured(self) -> bool:
        return bool(self.allowed_user_ids)

    def authorize(
        self,
        *,
        action: str,
        user_id: int | None,
        channel_id: int | None,
        channel_name: str | None,
    ) -> DiscordAccessDecision:
        if self.allowed_user_ids and (user_id is None or user_id not in self.allowed_user_ids):
            return DiscordAccessDecision(
                allowed=False,
                reason="This Discord user is not in the trusted operator allowlist.",
            )

        if action == "approval":
            target_ids = self.approvals_channel_ids
            target_names = self.approvals_channel_names
            label = "approvals"
        elif action == "alert":
            target_ids = self.alerts_channel_ids
            target_names = self.alerts_channel_names
            label = "alerts"
        else:
            target_ids = self.control_channel_ids
            target_names = self.control_channel_names
            label = "control"

        if target_ids or target_names:
            matched = False
            if channel_id is not None and channel_id in target_ids:
                matched = True
            if _normalize_name(channel_name) in target_names:
                matched = True
            if not matched:
                return DiscordAccessDecision(
                    allowed=False,
                    reason=f"This request is outside the trusted Discord {label} channel boundary.",
                )

        return DiscordAccessDecision(allowed=True)
