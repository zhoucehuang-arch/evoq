from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from quant_evo_nextgen.config import get_settings
from quant_evo_nextgen.contracts.intents import IntentClassification, IntentType
from quant_evo_nextgen.db.session import Database
from quant_evo_nextgen.logging_utils import configure_logging
from quant_evo_nextgen.services.control_plane import ControlPlaneService
from quant_evo_nextgen.services.dashboard import DashboardService
from quant_evo_nextgen.services.discord_access import DiscordAccessPolicy
from quant_evo_nextgen.services.owner_onboarding import OwnerOnboardingService
from quant_evo_nextgen.services.repo_state import RepoStateService
from quant_evo_nextgen.services.router import NaturalLanguageRouter
from quant_evo_nextgen.services.state_store import StateStore


settings = get_settings()
configure_logging()
logger = logging.getLogger("quant_evo_nextgen.discord")

database = Database(settings.postgres_url, echo=settings.db_echo)
if settings.db_bootstrap_on_start:
    database.create_schema()
state_store = StateStore(database.session_factory)
state_store.bootstrap_reference_data(settings)
dashboard_service = DashboardService(RepoStateService(settings.resolved_repo_root), state_store)
onboarding_service = OwnerOnboardingService(settings.resolved_repo_root)
control_plane_service = ControlPlaneService(state_store, onboarding_service=onboarding_service)
router = NaturalLanguageRouter()
access_policy = DiscordAccessPolicy.from_settings(settings)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready() -> None:
    logger.info("discord shell connected as %s", bot.user)
    if settings.discord_guild_id:
        guild = discord.Object(id=settings.discord_guild_id)
        await bot.tree.sync(guild=guild)
    else:
        await bot.tree.sync()


async def _deny_interaction(interaction: discord.Interaction, reason: str) -> None:
    if interaction.response.is_done():
        await interaction.followup.send(reason, ephemeral=True)
        return
    await interaction.response.send_message(reason, ephemeral=True)


def _authorize_interaction(interaction: discord.Interaction, *, action: str) -> tuple[bool, str | None]:
    decision = access_policy.authorize(
        action=action,
        user_id=interaction.user.id if interaction.user else None,
        channel_id=getattr(interaction.channel, "id", None),
        channel_name=getattr(interaction.channel, "name", None),
    )
    if not decision.allowed:
        logger.warning(
            "discord interaction rejected: action=%s user_id=%s channel_id=%s reason=%s",
            action,
            interaction.user.id if interaction.user else None,
            getattr(interaction.channel, "id", None),
            decision.reason,
        )
    return (decision.allowed, decision.reason)


def _authorize_message(message: discord.Message, *, action: str) -> tuple[bool, str | None]:
    decision = access_policy.authorize(
        action=action,
        user_id=message.author.id,
        channel_id=getattr(message.channel, "id", None),
        channel_name=getattr(message.channel, "name", None),
    )
    if not decision.allowed:
        logger.warning(
            "discord message rejected: action=%s user_id=%s channel_id=%s reason=%s",
            action,
            message.author.id,
            getattr(message.channel, "id", None),
            decision.reason,
        )
    return (decision.allowed, decision.reason)


@bot.tree.command(name="status", description="Show the current system status.")
async def status_command(interaction: discord.Interaction) -> None:
    allowed, reason = _authorize_interaction(interaction, action="control")
    if not allowed:
        await _deny_interaction(interaction, reason or "This Discord interaction is not authorized.")
        return

    overview = dashboard_service.build_overview()
    await interaction.response.send_message(router.render_response(router.classify("status"), overview))


@bot.tree.command(name="approvals", description="List pending approvals.")
async def approvals_command(interaction: discord.Interaction) -> None:
    allowed, reason = _authorize_interaction(interaction, action="approval")
    if not allowed:
        await _deny_interaction(interaction, reason or "This Discord interaction is not authorized.")
        return

    result = control_plane_service.handle_control_intent(
        intent=router.classify("approvals"),
        actor=str(interaction.user),
        source_channel=getattr(interaction.channel, "name", "discord"),
        raw_message="slash approvals",
    )
    await interaction.response.send_message(result.response_text)


@bot.tree.command(name="config", description="Show runtime config, proposals, and recent revisions.")
async def config_command(interaction: discord.Interaction) -> None:
    allowed, reason = _authorize_interaction(interaction, action="control")
    if not allowed:
        await _deny_interaction(interaction, reason or "This Discord interaction is not authorized.")
        return

    result = control_plane_service.handle_control_intent(
        intent=router.classify("show config"),
        actor=str(interaction.user),
        source_channel=getattr(interaction.channel, "name", "discord"),
        raw_message="slash config",
    )
    await interaction.response.send_message(result.response_text)


@bot.tree.command(name="deploy-status", description="Run deployment preflight for core or worker.")
@app_commands.describe(role="Node role: core or worker.")
async def deploy_status_command(interaction: discord.Interaction, role: str = "core") -> None:
    allowed, reason = _authorize_interaction(interaction, action="control")
    if not allowed:
        await _deny_interaction(interaction, reason or "This Discord interaction is not authorized.")
        return

    result = control_plane_service.handle_control_intent(
        intent=IntentClassification(
            intent_type=IntentType.DEPLOY_STATUS,
            deploy_role=role,
            proposed_action="Show deploy status for the requested role.",
            execution_supported=True,
        ),
        actor=str(interaction.user),
        source_channel=getattr(interaction.channel, "name", "discord"),
        raw_message=f"deploy-status {role}",
    )
    await interaction.response.send_message(result.response_text)


@bot.tree.command(name="deploy-bootstrap", description="Prepare the deployment draft for core or worker.")
@app_commands.describe(role="Node role: core or worker.")
async def deploy_bootstrap_command(interaction: discord.Interaction, role: str = "core") -> None:
    allowed, reason = _authorize_interaction(interaction, action="control")
    if not allowed:
        await _deny_interaction(interaction, reason or "This Discord interaction is not authorized.")
        return

    result = control_plane_service.handle_control_intent(
        intent=IntentClassification(
            intent_type=IntentType.DEPLOY_BOOTSTRAP,
            deploy_role=role,
            proposed_action="Bootstrap deployment draft for the requested role.",
            execution_supported=True,
        ),
        actor=str(interaction.user),
        source_channel=getattr(interaction.channel, "name", "discord"),
        raw_message=f"deploy-bootstrap {role}",
    )
    await interaction.response.send_message(result.response_text)


@bot.tree.command(name="rollback-config", description="Create a governed runtime-config rollback proposal.")
@app_commands.describe(revision_id="Revision id to roll back to.")
async def rollback_config_command(interaction: discord.Interaction, revision_id: str) -> None:
    allowed, reason = _authorize_interaction(interaction, action="control")
    if not allowed:
        await _deny_interaction(interaction, reason or "This Discord interaction is not authorized.")
        return

    result = control_plane_service.handle_control_intent(
        intent=IntentClassification(
            intent_type=IntentType.ROLLBACK_RUNTIME_CONFIG,
            reference_id=revision_id,
            proposed_action="Create a governed rollback proposal for a runtime config revision.",
            execution_supported=True,
        ),
        actor=str(interaction.user),
        source_channel=getattr(interaction.channel, "name", "discord"),
        raw_message=f"rollback-config {revision_id}",
    )
    await interaction.response.send_message(result.response_text)


@bot.tree.command(name="pause-trading", description="Create an approval request to pause auto-trading.")
async def pause_trading_command(interaction: discord.Interaction) -> None:
    allowed, reason = _authorize_interaction(interaction, action="control")
    if not allowed:
        await _deny_interaction(interaction, reason or "This Discord interaction is not authorized.")
        return

    result = control_plane_service.handle_control_intent(
        intent=router.classify("pause trading"),
        actor=str(interaction.user),
        source_channel=getattr(interaction.channel, "name", "discord"),
        raw_message="pause-trading slash command",
    )
    await interaction.response.send_message(result.response_text)


@bot.tree.command(name="pause-evolution", description="Create an approval request to pause auto-evolution.")
async def pause_evolution_command(interaction: discord.Interaction) -> None:
    allowed, reason = _authorize_interaction(interaction, action="control")
    if not allowed:
        await _deny_interaction(interaction, reason or "This Discord interaction is not authorized.")
        return

    result = control_plane_service.handle_control_intent(
        intent=router.classify("pause evolution"),
        actor=str(interaction.user),
        source_channel=getattr(interaction.channel, "name", "discord"),
        raw_message="pause-evolution slash command",
    )
    await interaction.response.send_message(result.response_text)


@bot.tree.command(name="resume-domain", description="Create an approval request to resume a domain.")
@app_commands.describe(domain="Domain to resume, for example trading or evolution.")
async def resume_domain_command(interaction: discord.Interaction, domain: str) -> None:
    allowed, reason = _authorize_interaction(interaction, action="control")
    if not allowed:
        await _deny_interaction(interaction, reason or "This Discord interaction is not authorized.")
        return

    result = control_plane_service.handle_control_intent(
        intent=router.classify(f"resume {domain}"),
        actor=str(interaction.user),
        source_channel=getattr(interaction.channel, "name", "discord"),
        raw_message=f"resume-domain {domain}",
    )
    await interaction.response.send_message(result.response_text)


@bot.tree.command(name="approve", description="Approve a pending approval request.")
@app_commands.describe(approval_id="Pending approval id.", reason="Optional reason.")
async def approve_command(interaction: discord.Interaction, approval_id: str, reason: str | None = None) -> None:
    allowed, reason_text = _authorize_interaction(interaction, action="approval")
    if not allowed:
        await _deny_interaction(interaction, reason_text or "This Discord interaction is not authorized.")
        return

    result = control_plane_service.handle_control_intent(
        intent=router.classify(f"approve {approval_id}"),
        actor=str(interaction.user),
        source_channel=getattr(interaction.channel, "name", "discord"),
        raw_message=reason or f"approve {approval_id}",
    )
    await interaction.response.send_message(result.response_text)


@bot.tree.command(name="reject", description="Reject a pending approval request.")
@app_commands.describe(approval_id="Pending approval id.", reason="Optional reason.")
async def reject_command(interaction: discord.Interaction, approval_id: str, reason: str | None = None) -> None:
    allowed, reason_text = _authorize_interaction(interaction, action="approval")
    if not allowed:
        await _deny_interaction(interaction, reason_text or "This Discord interaction is not authorized.")
        return

    result = control_plane_service.handle_control_intent(
        intent=router.classify(f"reject {approval_id}"),
        actor=str(interaction.user),
        source_channel=getattr(interaction.channel, "name", "discord"),
        raw_message=reason or f"reject {approval_id}",
    )
    await interaction.response.send_message(result.response_text)


@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author.bot:
        return

    overview = dashboard_service.build_overview()
    intent = router.classify(message.content)
    action = (
        "approval"
        if intent.intent_type in {IntentType.LIST_APPROVALS, IntentType.APPROVE_REQUEST, IntentType.REJECT_REQUEST}
        else "control"
    )
    allowed, reason = _authorize_message(message, action=action)
    if not allowed:
        await message.reply(reason or "This Discord message is not authorized.")
        return

    if intent.execution_supported and intent.intent_type not in {
        IntentType.STATUS,
        IntentType.RISK_STATUS,
        IntentType.LEARNING_SUMMARY,
        IntentType.EXPLAIN_STRATEGY,
    }:
        result = control_plane_service.handle_control_intent(
            intent=intent,
            actor=str(message.author),
            source_channel=getattr(message.channel, "name", "discord"),
            raw_message=message.content,
        )
        await message.reply(result.response_text)
    else:
        await message.reply(router.render_response(intent, overview))
    await bot.process_commands(message)


def run() -> None:
    if not settings.discord_token:
        raise RuntimeError("QE_DISCORD_TOKEN is required to run the Discord shell.")
    bot.run(settings.discord_token)


if __name__ == "__main__":
    run()
