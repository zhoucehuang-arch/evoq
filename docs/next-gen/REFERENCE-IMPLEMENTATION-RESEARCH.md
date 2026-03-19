# Reference Implementation Research

## 1. Purpose

这份文档记录本项目在实现路径上参考了哪些外部系统，以及从中吸收什么、不吸收什么。

目标不是追热点，而是避免重复犯错。

## 2. Sources Reviewed

1. Ralph Loop Agent
   https://github.com/vercel-labs/ralph-loop-agent
2. Dynamous Remote Coding Agent
   https://github.com/coleam00/remote-agentic-coding-system
3. OpenClaw
   https://github.com/openclaw/openclaw
4. OpenClaw ACP Bridge
   https://github.com/openclaw/openclaw/blob/main/docs.acp.md
5. OpenAI Codex docs
   https://developers.openai.com/codex/agent-approvals-security/
   https://developers.openai.com/codex/config-reference/

## 3. Ralph Loop Agent

核心启发：

- 它把 agent 的一次工具调用循环外面再包了一层 outer loop
- outer loop 会在 `verifyCompletion` 不通过时继续重试
- 它原生支持 iteration、token、cost 三类 stop conditions

对本项目的价值：

- 很适合拿来抽象“持续研究”“持续修复”“持续反思”这种长任务
- 能解决 one-shot agent 经常半成品退出的问题

不直接照搬的原因：

- Ralph 更偏向单 agent 的持续完成框架
- 它没有替你解决多 agent 治理、资金风险、owner 缺席、审批、交易边界

本项目的吸收方式：

- 采用 `Ralph-style bounded outer loop`
- 每个 loop 都必须绑定：
  - verify function
  - token budget
  - cost budget
  - failure budget
  - human override / safe mode
  - workflow record

结论：

- `Ralph Loop` 适合作为 `Continuous Loop Supervisor` 的思想来源
- 不适合作为整套自治投资系统的唯一运行内核

## 4. Dynamous Remote Coding Agent

核心启发：

- 使用数据库持久化 conversation / session
- 支持 Telegram / GitHub 等远程 IM 控制
- 显式支持 session resume
- 把 `plan -> execute` 视为需要新 session 的特殊边界，以减少上下文污染和 token 膨胀
- 提供 `/reset` 这类 owner 可理解的逃生阀

对本项目的价值：

- 证明了 “IM adapter + session persistence + Codex/Claude client abstraction” 是一条可跑通的路线
- 很适合作为 Discord control plane 和 Codex session persistence 的参考

局限：

- 重点是远程 coding assistant，不是自治投资系统
- 数据模型过轻，不足以承载 trading、learning、risk、evolution 的长期运行

本项目的吸收方式：

- 参考它的 session persistence、platform adapter、escape hatch、AI client abstraction
- 不采用它的轻量三表模型作为最终 runtime truth

## 5. OpenClaw

核心启发：

- `Gateway` 作为统一 control plane 的设计是成立的
- 多渠道接入、会话路由、daemon 常驻运行、agent/session 隔离都很成熟
- ACP bridge 说明“IDE / agent client / gateway session 映射”是可用的

对本项目的价值：

- 继续保留“Discord 作为外壳，运行真相不在聊天里”的方向
- 可以借鉴 gateway、session mapping、daemon install、channel routing、agent-scoped session key 等实现思路

关键警告：

- OpenClaw 的安全模型本质是 `personal assistant / trusted operator`
- 它不是为“资金治理 + 自进化 + 多 agent 投资系统”直接设计的
- 如果直接拿来拼装，很容易重回“prompt-heavy shell + runtime truth 分散”的老问题

本项目的吸收方式：

- 借鉴外壳与控制面思路
- 不复用其“聊天驱动即真实运行”的倾向
- 不把 OpenClaw 的 trusted-operator 安全模型直接套到交易系统

## 6. Codex Official Guidance

官方约束带来的设计结论：

- `Codex CLI / IDE` 默认并不是天然的长期 daemon 编排器
- sandbox、approval、network access、web search 都是需要显式治理的
- `requirements.toml` 可以强约束 approval policy、sandbox mode、web search、MCP allowlist

对本项目的价值：

- 说明 Codex 很适合作为执行层，但不该单独承担长期自治治理
- 说明 research workers 必须有独立的外层 supervisor 和 policy envelope
- 说明 relay/provider abstraction 需要从一开始就进入配置和状态模型

本项目的吸收方式：

- `Codex-centered, not Codex-only`
- 外面必须包 durable workflow + supervisor + review/eval gates
- web search 与 internet access 必须被预算和安全策略约束

## 7. Final Synthesis

参考实现调研后的最终结论是：

1. 整套系统不应重新回到 “OpenClaw prompt swarm”。
2. 也不应把 `Codex CLI` 当作唯一常驻调度器。
3. 最优方向是：
   - `authoritative core + runtime DB + Discord shell + dashboard + Codex fabric + bounded loop supervisor`
4. Ralph Loop 的思想适合成为持续运行层的内核之一，但必须放进治理、预算、审批和风险边界里。
5. OpenClaw 适合作为 gateway/session/channel 外壳参考，不适合作为资金系统的真实状态与治理基座。
