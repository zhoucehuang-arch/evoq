# Owner Operation Quickstart

## 1. Primary surfaces

- Discord: ask, approve, pause, inspect, and request governed config or deploy-draft changes in natural language.
- Dashboard: inspect trading state, learning state, evolution state, incidents, and runtime health.
- SSH: use only for deploy, upgrade, restore, or break-glass repair.

## 2. First things to do after deploy

1. Open the dashboard and confirm it loads.
2. Run `./ops/bin/core-smoke.sh` on the Core VPS and confirm it reports no `fail`.
3. Run `./ops/bin/worker-smoke.sh` on the Worker VPS and confirm it reports no `fail`.
4. In Discord, verify that `/status`, `/config`, `/approvals`, `/deploy-status`, and `/deploy-bootstrap` respond only for the allowed owner accounts and channels.
5. If Alpaca is enabled, wait for the first broker sync cycle and confirm the trading dashboard updates.

## 3. Safe prompts in Discord

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

## 4. When to intervene manually

- `doctor` or `core-smoke.sh` returns `fail`
- broker sync or reconciliation turns red
- unexpected pause overrides appear
- Discord bot stops responding
- dashboard stops updating
- the Worker can no longer see `codex`

## 5. Safe owner habits

- Keep the broker in `paper` mode until the first full deploy, smoke checks, and broker sync are all clean.
- Keep `QE_DISCORD_ALLOWED_USER_IDS` narrow.
- Prefer governed config changes over manual env edits once the system is running.
- Prefer deploy-draft changes through Discord over copying secrets into random shell history.
- Treat every live-promotion step as a deliberate approval event, not a casual chat instruction.

## 6. Honest current limits

- Deploy-draft changes made through Discord usually require a service restart before the runtime reads the new values.
- Conflicting option conversion events still go to `review_required` instead of auto-applying unconditionally.
- Truly unattended live operation still depends on the VPS-side smoke checks, broker sync, paper/live promotion, and capital activation steps being completed cleanly.
