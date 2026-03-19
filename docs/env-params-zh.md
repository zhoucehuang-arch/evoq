# Quant-Evo 配置参数说明（中文）

适用仓库：`zhoucehuang-arch/quant-evo-do-test`

## 1) Discord 相关

- `DISCORD_GUILD_ID`
  - 含义：Discord 服务器（Guild）ID。
  - 用途：绑定路由时限定在哪个服务器内收发消息。

- `DISCORD_BOT_TOKEN_EXPLORER`
- `DISCORD_BOT_TOKEN_CRITIC`
- `DISCORD_BOT_TOKEN_EVOLVER`
- `DISCORD_BOT_TOKEN_B`
  - 含义：4 个 Bot 各自的 token。
  - 用途：4 个实例分别登录 Discord。
  - 建议：生产中必须 4 个独立 bot token，避免身份串台与自消息过滤问题。

- `CH_A_ARENA` / `CH_A_RESEARCH` / `CH_A_REPORT` / `CH_A_VERDICT`
  - 含义：System A 的频道 ID。
  - 用途：Explorer/Critic/Evolver 的讨论、裁决与汇报路由。

- `CH_B_OPS` / `CH_B_DESK` / `CH_B_RISK` / `CH_B_REPORT`
  - 含义：System B 的频道 ID。
  - 用途：Operator/Trader/Guardian 的运维、执行、风控与汇报路由。

- `CH_BRIDGE` / `CH_ADMIN`
  - 含义：跨系统桥接与全局管理频道 ID。
  - 用途：A/B 状态同步与全局管理指令。

## 2) 模型与推理相关

- `OPENAI_KEY_A1` / `OPENAI_KEY_A2` / `OPENAI_KEY_A3`
  - 含义：System A 三个 Agent 的模型 API Key。
  - 用途：Explorer/Critic/Evolver 各自调用 LLM。

- `OPENAI_KEY_B1` / `OPENAI_KEY_B2` / `OPENAI_KEY_B3`
  - 含义：System B 三个 Agent 的模型 API Key。
  - 用途：Operator/Trader/Guardian 各自调用 LLM。

- `KIMI_KEY_SHARED`
  - 含义：可选的低成本回退模型 Key。
  - 用途：低风险任务降级（例如汇总、归档）。

## 3) GitHub 相关

- `GITHUB_REPO`
  - 含义：目标仓库，格式 `owner/repo`。
  - 当前值：`zhoucehuang-arch/quant-evo-do-test`

- `GITHUB_TOKEN_A`
  - 含义：System A 的 GitHub PAT。
  - 最小建议权限：私有仓库 Contents 读写（至少能读写策略、evo、memory）。

- `GITHUB_TOKEN_B`
  - 含义：System B 的 GitHub PAT。
  - 最小建议权限：私有仓库 Contents 读写（至少能读写 trading 与策略状态）。

## 4) Alpaca 相关（仅 System B）

- `ALPACA_API_KEY`
- `ALPACA_SECRET_KEY`
- `ALPACA_BASE_URL`
  - 含义：Alpaca 交易接口凭据与地址。
  - 用途：Trader 下单、Guardian 风控监控。
  - 建议：先固定使用 paper 地址：`https://paper-api.alpaca.markets`。

## 5) 心跳参数（在 openclaw.json，不在 .env）

- Explorer: `600000`（10 分钟，毫秒）
- Critic: `600000`（10 分钟，毫秒）
- Evolver: `7200000`（2 小时，毫秒）
- Instance-B: `300000`（5 分钟，毫秒）

## 6) 本次已完成的 Discord 侧配置

- 已在目标 Guild 创建并确认频道：
  - `a-arena`, `a-verdict`, `a-research`, `a-report`
  - `b-ops`, `b-desk`, `b-risk`, `b-report`
  - `bridge`, `admin`
- 频道 ID 映射文件：`config/discord-channel-map.json`

## 7) 分机器/分用户部署建议

每台机器只保留对应实例目录：

- Explorer 机：`~/.openclaw-explorer/`
- Critic 机：`~/.openclaw-critic/`
- Evolver 机：`~/.openclaw-evolver/`
- B 系统机：`~/.openclaw-b/`

每台机器的 `.env` 只填该实例必需参数，避免无关密钥扩散。
