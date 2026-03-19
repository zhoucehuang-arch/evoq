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


@bot.tree.command(name="status", description="查看当前系统状态")
async def status_command(interaction: discord.Interaction) -> None:
    allowed, reason = _authorize_interaction(interaction, action="control")
    if not allowed:
        await _deny_interaction(interaction, reason or "This Discord interaction is not authorized.")
        return

    overview = dashboard_service.build_overview()
    await interaction.response.send_message(router.render_response(router.classify("状态"), overview))


@bot.tree.command(name="approvals", description="列出待处理审批")
async def approvals_command(interaction: discord.Interaction) -> None:
    allowed, reason = _authorize_interaction(interaction, action="approval")
    if not allowed:
        await _deny_interaction(interaction, reason or "This Discord interaction is not authorized.")
        return

    result = control_plane_service.handle_control_intent(
        intent=router.classify("待审批"),
        actor=str(interaction.user),
        source_channel=getattr(interaction.channel, "name", "discord"),
        raw_message="slash approvals",
    )
    await interaction.response.send_message(result.response_text)


@bot.tree.command(name="config", description="查看运行时配置、提案和最近版本")
async def config_command(interaction: discord.Interaction) -> None:
    allowed, reason = _authorize_interaction(interaction, action="control")
    if not allowed:
        await _deny_interaction(interaction, reason or "This Discord interaction is not authorized.")
        return

    result = control_plane_service.handle_control_intent(
        intent=router.classify("查看配置"),
        actor=str(interaction.user),
        source_channel=getattr(interaction.channel, "name", "discord"),
        raw_message="slash config",
    )
    await interaction.response.send_message(result.response_text)


@bot.tree.command(name="deploy-status", description="查看 core 或 worker 的部署预检状态")
@app_commands.describe(role="节点角色，支持 core / worker")
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


@bot.tree.command(name="deploy-bootstrap", description="为 core 或 worker 生成部署配置草稿")
@app_commands.describe(role="节点角色，支持 core / worker")
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


@bot.tree.command(name="rollback-config", description="创建运行时配置回滚提案")
@app_commands.describe(revision_id="要回滚到的配置版本号")
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


@bot.tree.command(name="pause-trading", description="创建暂停自动交易的审批请求")
async def pause_trading_command(interaction: discord.Interaction) -> None:
    allowed, reason = _authorize_interaction(interaction, action="control")
    if not allowed:
        await _deny_interaction(interaction, reason or "This Discord interaction is not authorized.")
        return

    result = control_plane_service.handle_control_intent(
        intent=router.classify("暂停自动交易"),
        actor=str(interaction.user),
        source_channel=getattr(interaction.channel, "name", "discord"),
        raw_message="pause-trading slash command",
    )
    await interaction.response.send_message(result.response_text)


@bot.tree.command(name="pause-evolution", description="创建暂停自动进化的审批请求")
async def pause_evolution_command(interaction: discord.Interaction) -> None:
    allowed, reason = _authorize_interaction(interaction, action="control")
    if not allowed:
        await _deny_interaction(interaction, reason or "This Discord interaction is not authorized.")
        return

    result = control_plane_service.handle_control_intent(
        intent=router.classify("暂停自动进化"),
        actor=str(interaction.user),
        source_channel=getattr(interaction.channel, "name", "discord"),
        raw_message="pause-evolution slash command",
    )
    await interaction.response.send_message(result.response_text)


@bot.tree.command(name="resume-domain", description="创建恢复某个域状态的审批请求")
@app_commands.describe(domain="要恢复的域，例如 trading 或 evolution")
async def resume_domain_command(interaction: discord.Interaction, domain: str) -> None:
    allowed, reason = _authorize_interaction(interaction, action="control")
    if not allowed:
        await _deny_interaction(interaction, reason or "This Discord interaction is not authorized.")
        return

    result = control_plane_service.handle_control_intent(
        intent=router.classify(f"恢复 {domain}"),
        actor=str(interaction.user),
        source_channel=getattr(interaction.channel, "name", "discord"),
        raw_message=f"resume-domain {domain}",
    )
    await interaction.response.send_message(result.response_text)


@bot.tree.command(name="approve", description="批准一个待处理审批")
@app_commands.describe(approval_id="待处理审批编号", reason="可选，补充说明")
async def approve_command(interaction: discord.Interaction, approval_id: str, reason: str | None = None) -> None:
    allowed, reason_text = _authorize_interaction(interaction, action="approval")
    if not allowed:
        await _deny_interaction(interaction, reason_text or "This Discord interaction is not authorized.")
        return

    result = control_plane_service.handle_control_intent(
        intent=router.classify(f"批准 {approval_id}"),
        actor=str(interaction.user),
        source_channel=getattr(interaction.channel, "name", "discord"),
        raw_message=reason or f"approve {approval_id}",
    )
    await interaction.response.send_message(result.response_text)


@bot.tree.command(name="reject", description="拒绝一个待处理审批")
@app_commands.describe(approval_id="待处理审批编号", reason="可选，补充说明")
async def reject_command(interaction: discord.Interaction, approval_id: str, reason: str | None = None) -> None:
    allowed, reason_text = _authorize_interaction(interaction, action="approval")
    if not allowed:
        await _deny_interaction(interaction, reason_text or "This Discord interaction is not authorized.")
        return

    result = control_plane_service.handle_control_intent(
        intent=router.classify(f"拒绝 {approval_id}"),
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
