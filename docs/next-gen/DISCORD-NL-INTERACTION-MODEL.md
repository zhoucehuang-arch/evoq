# DISCORD NATURAL LANGUAGE INTERACTION MODEL

## 1. Purpose

本文件定义下一代系统与 owner 的 Discord 交互方式。设计重点是“自然语言优先”，而不是要求 owner 记很多命令、路径或技术术语。

## 2. Design Objective

系统应当让 owner 感觉自己是在和一个自治投资团队沟通，而不是在操作一堆命令行程序。

因此交互原则是：

- 自然语言优先
- Slash command 作为兜底
- 高风险动作需要确认卡
- 回答默认用中文
- 回复要先给结论，再给原因，再给下一步

## 3. Interaction Modes

### 3.1 Natural language command

owner 直接发普通消息：

- “现在系统状态如何？”
- “今天暂停自动进化。”
- “帮我解释最近一次 halt 的原因。”
- “为什么这个策略没有推进到 production？”

系统负责理解意图并路由。

### 3.2 Slash command fallback

当自然语言不清楚，或需要明确参数时，提供 `/status`、`/pause`、`/resume`、`/approve` 等命令作为兜底。

### 3.3 Approval card

对于高风险动作，系统应返回一个可点击确认卡，而不是直接执行。

### 3.4 Scheduled summaries

系统自动在固定时间发：

- 早报
- 收盘摘要
- 每日学习摘要
- 每周治理摘要

## 4. Natural Language Router

自然语言交互必须有一个专门的“路由层”，而不是把任何消息直接丢给大模型执行。

### 4.1 Router pipeline

```text
Discord message
  -> intent classification
  -> entity extraction
  -> policy check
  -> ambiguity detection
  -> action plan
  -> confirmation or execution
  -> result summary
```

### 4.2 Router outputs

路由层至少要输出：

- `intent_type`
- `target_domain`
- `risk_tier`
- `requires_confirmation`
- `clarification_needed`
- `proposed_action`

## 5. Intent Catalog

建议把 owner 意图分成以下类别：

### 5.1 Governance intents

- 查看状态
- 切自治级别
- 暂停或恢复域
- 调预算
- 发起或关闭目标

### 5.2 Learning intents

- 让系统研究某个主题
- 追问最近学到的重点
- 查询某个知识点来源

### 5.3 Strategy intents

- 查询策略状态
- 解释晋级或淘汰原因
- 请求重点分析某个方向

### 5.4 Trading intents

- 查询实时风险和持仓
- 暂停自动交易
- 切换到 paper only
- 查询某次交易决策原因

### 5.5 Evolution intents

- 查询最近系统自我改进
- 暂停自动进化
- 审批某次升级
- 查询 Codex 运行结果

### 5.6 Incident intents

- 解释告警
- 查看最近 incident
- 请求安全模式
- 请求恢复评估

## 6. Confirmation Policy

不是所有自然语言都要二次确认，但高风险动作必须确认。

### 6.1 No-confirm actions

- 查看信息
- 生成报告
- 发起只读分析
- 查询某个决策解释

### 6.2 Soft-confirm actions

- 暂停学习
- 暂停自动进化
- 调整普通预算

### 6.3 Hard-confirm actions

- 启用 live trading
- 恢复被 halt 的 execution
- 修改风控边界
- 提升自治级别
- 接受高风险 Codex 补丁

## 7. Clarification Strategy

为避免用户被系统反复追问，clarification 只在真正必要时发起。

### 7.1 Clarification is needed when

- 意图冲突
- 时间范围不明确且风险高
- 涉及多个目标对象
- 会触发生产级副作用

### 7.2 Clarification style

系统不应问宽泛问题，而应问最短澄清问题，例如：

- “你是要暂停自动进化 12 小时，还是暂停到你手动恢复？”
- “你说的‘保守模式’，是指只停 live，还是连 paper 也停？”

## 8. Response Style

系统对 owner 的回复应遵循固定风格：

1. 先说结论
2. 再说当前状态
3. 再说风险或影响
4. 再说下一步

### 8.1 Good response example

“已将系统切换为保守模式。自动进化已暂停，自动交易保留在 paper 层，当前没有 live 风险暴露。明天开盘前我会再次提醒你是否恢复正常模式。”

## 9. Channel Model

建议 Discord 交互模型如下：

- `#control`
  owner 与系统的主要对话入口
- `#approvals`
  高风险审批卡
- `#alerts`
  告警和 halt
- `#daily-brief`
  每日摘要
- `#council`
  高价值议题的压缩版讨论结果
- `#ops`
  运维和 incident

大多数 owner 自然语言交互应集中在 `#control`。

## 10. Threading Model

复杂问题应自动开 thread，而不是在主频道持续刷屏。

### 10.1 Recommended thread cases

- 一个新目标
- 一次重大 incident
- 一次重大策略辩论
- 一次高风险升级审批

## 11. Discord UI Components

自然语言优先并不意味着不用结构化 UI。

建议配合使用：

- Buttons
- Select menus
- Modals
- Slash commands
- Thread links

这样 owner 可以“说自然语言”，但关键动作仍可点按确认。

## 12. Dashboard Hand-off

当信息密度过高时，Discord 不应硬塞长表格，而应：

- 给摘要
- 给关键指标
- 给 Dashboard 深链

例如：

“组合风险正常，但今天两条策略出现相关性聚集。详细图表我已放到 Dashboard 的 Risk 页面。”

## 13. Memory of Owner Preferences

系统应记住 owner 的交互偏好，但要结构化保存：

- 默认回复中文
- 偏好自然语言而不是命令
- 偏好结论先行
- 不希望看到大量工程细节
- 仅在必要时给技术解释

## 14. Anti-Confusion Rules

为降低认知负担，系统应避免：

- 同时给太多按钮
- 在一个回复里夹杂多条不相关建议
- 用内部模块名直接对用户说话
- 让 owner 自己拼配置

## 15. Acceptance Criteria

下一代 Discord 交互如果要算达标，至少要满足：

1. owner 可用自然语言完成 80% 以上日常操作。
2. 高风险动作有明确确认卡。
3. 系统回复默认中文且结论先行。
4. 复杂问题能自动开 thread 并压缩结论。
5. 不懂代码的 owner 也能理解系统当前状态与建议动作。
