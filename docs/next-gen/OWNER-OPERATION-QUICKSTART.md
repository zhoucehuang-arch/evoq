# Owner Operation Quickstart

This guide is for the person operating the system day to day.

## Main Surfaces

- Discord: control, approvals, questions, pauses, and governed config changes
- Dashboard: health, trading state, learning state, evolution state, and incident visibility
- SSH: deployment, upgrade, restore, and break-glass recovery

## First-Day Checklist

1. Open the dashboard and confirm it loads.
2. Run `./ops/bin/core-smoke.sh` on the Core VPS and confirm it reports no `fail`.
3. Run `./ops/bin/worker-smoke.sh` on the Worker VPS and confirm it reports no `fail`.
4. In Discord, verify that only the allowed owner accounts and channels can control the bot.
5. If a real broker is configured, wait for the first broker sync and confirm the trading view updates correctly.

## Good Discord Prompts

- `现在系统整体状态怎么样？`
- `列出待审批事项。`
- `查看当前运行时配置。`
- `把 heartbeat 改成 120 秒。`
- `禁用 research-intake loop。`
- `回滚配置 rev-12345678。`
- `暂停自动交易，保留学习。`
- `暂停自动进化。`
- `恢复 trading。`
- `最近系统学到了什么？`
- `为什么这个策略没有进入生产？`
- `初始化 core 部署。`
- `查看 worker 部署状态。`
- `设置 core 中转地址为 https://relay.example.com/v1`
- `设置 core 中转key 为 <secret>`
- `设置 worker 数据库url 为 <private-postgres-url>`

## When To Intervene

Intervene manually if:

- `doctor` or `core-smoke.sh` returns `fail`
- broker sync or reconciliation turns red
- unexpected pause overrides appear
- Discord bot stops responding
- dashboard stops updating
- the Worker can no longer see `codex`

## Safe Operating Habits

- Keep the broker in `paper` mode until the first full deploy and smoke cycle are clean.
- Keep `QE_DISCORD_ALLOWED_USER_IDS` narrow.
- Prefer governed config changes over manual env edits after the system is running.
- Prefer Discord deploy-draft updates over copying secrets into shell history.
- Treat every live-promotion step as an explicit approval event.

## What Still Requires SSH

- first deployment
- GitHub-based upgrades
- backup and restore
- systemd setup
- break-glass repair

## Important Limits

- Deploy-draft changes made through Discord usually still require a service restart before the runtime reads the new values.
- Conflicting option conversion events still go to `review_required` instead of applying automatically.
- Truly unattended live operation still depends on clean smoke checks, broker sync, paper/live promotion discipline, and actual production activation on the target VPS.

## Next Reading

- [FAQ.md](FAQ.md)
- [GITHUB-TO-VPS-DEPLOYMENT.md](GITHUB-TO-VPS-DEPLOYMENT.md)
- [VPS-DEPLOYMENT-RUNBOOK.md](VPS-DEPLOYMENT-RUNBOOK.md)
