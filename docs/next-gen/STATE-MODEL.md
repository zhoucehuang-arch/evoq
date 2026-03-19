# STATE MODEL

## 1. Purpose

本文件定义下一代自治投资系统的状态模型。目标是用结构化实体、事件与状态转移替代当前主要依赖 Discord 消息、GitHub 文件与隐式约定的运行方式。

## 2. Canonical State Sources

### 2.1 Primary source of truth

`Postgres` 是唯一的运行态事实源。

### 2.2 Secondary stores

- `Git repository`
  存放代码、策略文件、配置、长期文档和可版本化工件。
- `Artifact store`
  存放回测结果、报告、图表、原始抓取文本、模型输出、补丁包等大对象。
- `Discord`
  存放交互痕迹、通知与审批展示，不承担权威状态职责。

### 2.3 Derived state

以下内容都属于派生状态，不得视为权威源：

- Discord 频道消息
- 线程讨论内容
- README 中的运行描述
- 临时工作区中的未登记变更
- agent 会话上下文中的临时判断

## 3. State Model Layers

系统状态分为 6 层：

1. `Governance State`
   目标、政策、预算、审批、自治级别。
2. `Workflow State`
   计划、任务、运行中的工作流、重试、暂停、恢复。
3. `Knowledge State`
   文档、证据、洞察、原则、因果结论、playbook。
4. `Strategy State`
   假设、策略版本、回测、paper、production、撤销。
5. `Execution State`
   账户、订单、持仓、风险事件、broker 同步、熔断。
6. `Evolution State`
   能力缺口、改进提案、Codex 运行、补丁、评估、升级结果。

## 4. Core Entity Catalog

### 4.1 Governance entities

- `system_policy`
- `autonomy_mode`
- `budget_ledger`
- `approval_request`
- `approval_decision`
- `goal`
- `goal_revision`

### 4.2 Workflow entities

- `plan`
- `task`
- `workflow_definition`
- `workflow_run`
- `workflow_event`
- `heartbeat`
- `incident`

### 4.3 Council entities

- `council_session`
- `council_member_assignment`
- `council_turn`
- `decision_card`
- `decision_vote`

### 4.4 Knowledge entities

- `document`
- `document_chunk`
- `evidence_item`
- `insight`
- `principle`
- `causal_case`
- `playbook`
- `topic_watch`

### 4.5 Strategy entities

- `hypothesis`
- `strategy_spec`
- `strategy_version`
- `backtest_run`
- `paper_run`
- `live_run`
- `promotion_decision`
- `withdrawal_decision`

### 4.6 Trading entities

- `broker_account_snapshot`
- `market_snapshot`
- `signal_event`
- `order_intent`
- `order_record`
- `position_record`
- `risk_limit`
- `risk_event`

### 4.7 Evolution entities

- `capability_gap`
- `improvement_goal`
- `codex_run`
- `patch_artifact`
- `eval_run`
- `deployment_candidate`
- `deployment_event`

## 5. Required Global Fields

所有关键实体都应包含以下通用字段：

- `id`
- `created_at`
- `updated_at`
- `created_by`
- `origin_type`
- `origin_id`
- `status`
- `trace_id`
- `run_id`
- `tags`
- `confidence`

这样做的目标是保证任何对象都能被追溯到：

- 由谁创建
- 为什么创建
- 属于哪条链路
- 当前处于什么状态
- 是否可被信任或复用

## 6. Event-Sourced Thinking

虽然系统不一定需要完全 event sourcing 实现，但必须具备 event-sourced 视角：

- 所有重要状态变化必须产生事件
- 事件不可在事后悄悄覆盖
- 事件必须带上下文、来源和时间
- 派生状态必须可由事件重放出来

### 6.1 Required event classes

- `workflow.started`
- `workflow.paused`
- `workflow.resumed`
- `workflow.failed`
- `workflow.completed`
- `task.assigned`
- `task.blocked`
- `task.retried`
- `council.opened`
- `council.turn_added`
- `decision.issued`
- `document.ingested`
- `evidence.promoted`
- `principle.accepted`
- `hypothesis.created`
- `strategy.promoted`
- `strategy.withdrawn`
- `risk.warning`
- `risk.halt`
- `codex.run.started`
- `codex.run.completed`
- `codex.patch.accepted`
- `incident.opened`
- `incident.closed`

## 7. Goal State Machine

`goal` 是最高层业务实体之一，其建议状态如下：

```text
proposed -> admitted -> active -> paused -> completed
                  \-> rejected
active -> abandoned
active -> superseded
```

### 7.1 Goal rules

- 任何长周期工作都必须挂到某个 goal 之下
- goal 必须绑定成功指标、失败指标、时间范围和预算范围
- goal 被 superseded 时，必须记录替代 goal

## 8. Task State Machine

```text
queued -> ready -> running -> completed
      \-> blocked
      \-> cancelled
running -> retry_wait
running -> failed
retry_wait -> ready
blocked -> ready
failed -> archived
```

### 8.1 Task rules

- 任务必须声明输入、输出、所有者、依赖和超时
- 任务必须可重试或显式声明不可重试
- 高风险任务必须绑定审批策略

## 9. Council Session State Machine

```text
draft -> open -> deliberating -> reduced -> decided
     \-> cancelled
deliberating -> timed_out
decided -> archived
```

### 9.1 Council rules

- council 必须有明确议题
- council 成员是运行时选择，不是固定绑死
- council 必须产出 `decision_card`
- 未产出 `decision_card` 的辩论不得视为有效决策

## 10. Strategy Lifecycle State Machine

```text
hypothesis
  -> specified
  -> backtesting
  -> backtest_failed
  -> backtest_passed
  -> paper_candidate
  -> paper_running
  -> paper_failed
  -> live_candidate
  -> live_limited
  -> production
  -> degraded
  -> withdrawn
  -> archived
```

### 10.1 Strategy rules

- 不允许跳过 backtest 直接进入 paper
- 不允许跳过 paper 直接进入 production
- production 策略必须有回退版本
- 任何 withdrawal 都必须关联原因和证据

## 11. Codex Run State Machine

```text
planned -> queued -> booting -> running -> reviewing -> completed
       \-> cancelled
running -> failed
failed -> retry_wait
reviewing -> rejected
reviewing -> accepted
accepted -> merged
accepted -> archived
```

### 11.1 Codex rules

- 每次 Codex run 必须绑定明确 objective
- 每次 Codex run 必须绑定允许修改的工作区
- 每次 Codex run 必须产生结构化结果
- 高影响补丁必须通过 review 或 eval

## 12. Memory Promotion Model

记忆不应直接从“看到一篇文章”跳到“长期原则”。

推荐晋级路径：

```text
document -> evidence_item -> insight -> principle -> playbook
                               \-> causal_case
```

### 12.1 Promotion rules

- `document`
  原始资料，不默认可信。
- `evidence_item`
  可引用事实，必须保留来源、时间、摘录、解析方法。
- `insight`
  针对特定主题的归纳判断。
- `principle`
  跨多个场景依然成立的高质量结论。
- `playbook`
  具备操作步骤与触发条件的可执行规则。

## 13. Dual Storage Rules

当对象同时在数据库与 Git 中存在时，必须遵守以下规则：

- 运行状态以数据库为准
- 可版本化工件以 Git 为准
- 如果二者不一致，系统必须开 incident

### 13.1 Examples

- `strategy_version`
  Git 存代码与配置，DB 存生命周期状态与统计结果。
- `principle`
  Git 可存导出文档，DB 存元数据、引用链与生效状态。
- `patch_artifact`
  Git 存补丁，DB 存审批与评估链路。

## 14. Approval Model

审批不是消息动作，而是一类结构化状态对象。

### 14.1 `approval_request` minimal fields

- `approval_type`
- `subject_type`
- `subject_id`
- `requested_by`
- `requested_at`
- `risk_level`
- `deadline`
- `decision_status`

### 14.2 Approval states

```text
pending -> approved
pending -> rejected
pending -> expired
approved -> executed
approved -> superseded
```

## 15. Idempotency and Replay

所有外部副作用任务必须具备幂等键，例如：

- broker 下单
- Discord 发布决策
- 工件上传
- Git patch 应用
- 日报发送

系统必须能基于事件和运行记录重放：

- 某次策略晋级过程
- 某次事故恢复过程
- 某次 Codex 自我升级过程

## 16. Consistency Contracts

为避免当前系统中“角色描述很完整，但真实运行状态空心化”的问题，下一代系统必须定义以下一致性契约：

- 任何 `production` 策略都必须同时存在于 Git 与 DB
- 任何 `active` goal 都必须至少有一个未终结 workflow
- 任何 `decision_card` 都必须能追到 evidence 或 artifact
- 任何 `risk.halt` 都必须影响 execution state
- 任何 `approved patch` 都必须能追到 eval / review 结果

## 17. Suggested Physical Schema Groups

建议数据库按以下 schema 或逻辑模块组织：

- `gov_*`
- `wf_*`
- `council_*`
- `mem_*`
- `strat_*`
- `exec_*`
- `evo_*`
- `obs_*`

## 18. Migration Mapping from Current Repo

当前仓库中的很多目录仍有参考价值，但其语义会改变：

- `memory/`
  从文件记忆集合转向 DB 驱动的导出视图
- `strategies/`
  保留为 Git 工件层
- `trading/`
  部分运行日志迁入 DB，保留导出与报表文件
- `config/instance-*`
  从 OpenClaw prompt 拆分为结构化 role/persona/policy/workflow 配置

## 19. Minimal Invariants

以下不变量必须长期成立：

- 一个运行中的 workflow 只能有一个当前状态
- 一个 order_intent 对应零个或多个 broker order，但必须有映射表
- 一个 decision_card 只能对应一个最终结论版本
- 一个 production strategy 在任意时刻只能有一个主版本
- 一个 Codex run 只能有一个最终 outcome

## 20. Additional State Entities Required by the Audit

在继续深入实现前，状态模型还应补充以下实体：

- `provider_profile`
- `provider_capability_snapshot`
- `provider_incident`
- `source_policy`
- `source_health`
- `source_revalidation_job`
- `market_calendar_state`
- `trading_window`
- `operator_override`
- `manual_takeover_session`
- `drill_run`
- `recovery_checkpoint`

## 21. Hidden Invariants

本轮审查新增以下隐含不变量：

- 过期证据在重新校验前不得晋升为原则
- 人工接管或 operator override 必须优先于自治执行
- provider 故障不得静默改变面向资本的状态
- 本地 bootstrap 环境必须被明确标记为非生产环境
- 任何影响 owner 判断的 dashboard 载荷都必须带 freshness 语义
