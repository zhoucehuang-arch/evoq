# ROLE PERSONA MODEL

## 1. Purpose

本文件定义下一代系统中 agent 的构成方式。目标是替代当前以 `IDENTITY / SOUL / TOOLS / USER / AGENTS` 拆分的大型 prompt 形态，改为一种可组合、可治理、可复用、可实验的结构化模型。

## 2. Design Objective

下一代系统仍然保留：

- 多 agent 分工
- 不同性格和思维风格
- 多角色辩论
- 角色间互相制衡

但必须避免：

- 角色定义与人格定义混在一起
- 工具权限埋在 prompt 里
- 角色数量膨胀后 prompt 维护失控
- 单次任务临时拉很多 agent 闲聊
- 不同 agent 之间职责重叠、重复烧 token

## 3. Composition Model

一个运行中的 agent 实例不再是“一个写死的大 prompt 文件”，而是以下对象的组合：

```text
agent_instance =
  role
  + persona
  + policy
  + skillset
  + workflow_context
  + memory_scope
```

### 3.1 `role`

定义 agent 应承担的职责和成功标准。

### 3.2 `persona`

定义 agent 的思维偏好、表达风格、怀疑倾向、行动倾向。

### 3.3 `policy`

定义权限、预算、审批、工具边界、风险边界。

### 3.4 `skillset`

定义可调用的工具模板、工具调用策略和任务模板。

### 3.5 `workflow_context`

定义当前属于哪个工作流、当前阶段、当前目标、当前输入输出。

### 3.6 `memory_scope`

定义本次任务可以读取的记忆范围，而不是无限记忆。

## 4. Role Catalog

建议角色以“职责”而不是“人格”命名。

### 4.1 Core governance roles

- `planner`
  负责目标拆解、行动规划、优先级和资源分配。
- `judge`
  负责收敛分歧、形成结论、发布决策卡。
- `governor`
  负责预算、审批、自治级别、政策执行。

### 4.2 Core learning roles

- `scout`
  负责外部信息搜集、资料梳理、候选方向发现。
- `synthesizer`
  负责把多来源材料压缩成证据、洞察和原则候选。
- `archivist`
  负责长期记忆、引用链、知识清理和过期管理。

### 4.3 Core research roles

- `researcher`
  负责主题深挖、市场结构理解、策略方向提炼。
- `skeptic`
  负责挑战假设、识别漏洞、提出反例和证伪路径。
- `forensic`
  负责事故、失败、退化的因果拆解。

### 4.4 Core building roles

- `builder`
  负责把想法落成代码、脚本、配置、补丁和工件。
- `reviewer`
  负责审查补丁、测试、行为回归、风险外溢。
- `operator`
  负责工作流推进、部署控制和系统操作协调。

### 4.5 Trading and safety roles

- `strategist`
  负责策略规范与实验设计。
- `guardian`
  负责风控、熔断、退化检测、撤退建议。
- `executor`
  负责确定性执行域中的信号到订单编排。

## 5. Persona Catalog

人格只表达偏置，不表达职责。

### 5.1 Recommended personas

- `contrarian`
  优先寻找反例、错因和共识盲区。
- `conservative`
  优先保护资本、预算和系统稳定性。
- `creative`
  优先探索新路径、新假设和非线性组合。
- `forensic`
  优先还原链路、拆解因果、追责到具体机制。
- `execution_first`
  优先把问题转成可执行动作和最短闭环。
- `systems_thinker`
  优先看系统结构、耦合、反馈回路和副作用。
- `market_native`
  优先从市场机制与交易微观结构理解问题。
- `cost_sensitive`
  优先压缩 token、步骤和任务重叠。

## 6. Policy Objects

`policy` 不应藏在 prompt 里，必须结构化。

### 6.1 Required policy fields

- `max_rounds`
- `max_duration_sec`
- `max_token_budget`
- `tool_allowlist`
- `tool_denylist`
- `write_scope`
- `approval_mode`
- `memory_scope`
- `risk_tier`
- `allowed_workflows`

### 6.2 Example policy levels

- `P0-observer`
  只读、只分析、不可修改。
- `P1-analyst`
  可检索、可综合、不可写仓库。
- `P2-builder`
  可在限定工作区写代码与文档。
- `P3-operator`
  可推动工作流和部署候选，但不可绕过审批。
- `P4-guardian`
  可触发 halt、冻结高风险流程。

## 7. Skillset Objects

技能不是角色本身，而是任务模板与工具使用约束。

### 7.1 Skill families

- `web_research`
- `document_synthesis`
- `code_implementation`
- `code_review`
- `strategy_backtest`
- `incident_analysis`
- `risk_analysis`
- `memory_distillation`
- `broker_reconciliation`

### 7.2 Skill requirements

每个 skill 必须说明：

- 输入模式
- 输出模式
- 允许工具
- 成功标准
- 常见失败
- 适用角色

## 8. Workflow Context

同一个角色在不同工作流下表现应不同，因此必须显式提供上下文对象。

### 8.1 Required workflow context fields

- `workflow_id`
- `workflow_type`
- `goal_id`
- `task_id`
- `stage`
- `priority`
- `deadline`
- `input_artifacts`
- `expected_outputs`
- `acceptance_criteria`

## 9. Memory Scope Policy

为控制 token 和污染风险，memory scope 必须按任务裁剪。

### 9.1 Memory scopes

- `none`
  不读取历史记忆。
- `local`
  只读当前 goal 与当前 workflow 相关记忆。
- `domain`
  只读某一领域记忆，例如风控、策略、系统架构。
- `curated_long_term`
  只读已晋升的原则与 playbook。
- `incident_mode`
  强制加载最近相关事故和风险事件。

## 10. Council Assembly Rules

议会不是固定团队，而是按任务动态组装。

### 10.1 Assembly inputs

- 问题复杂度
- 风险等级
- 所需能力类型
- 预算约束
- 时间要求

### 10.2 Recommended council shapes

- `solo`
  1 个 agent，适合低风险明确任务。
- `duo`
  builder + reviewer，适合补丁和实现。
- `trio`
  planner + skeptic + judge，适合一般决策。
- `quorum-5`
  planner + scout + builder + guardian + judge，适合高影响议题。

### 10.3 Hard limits

- 默认不超过 5 个 agent
- 默认不超过 2 轮自由辩论
- 超过限制必须由 governor 批准

## 11. Anti-Redundancy Rules

为防止多人格系统退化成重复劳动，必须遵守：

- 同一轮中，多个 agent 不得重复读取相同大批量资料
- 同一任务中，builder 和 reviewer 的职责必须分离
- 同一问题若已被 `solo` 解决，不应默认升级为 council
- council 必须有 reducer 或 judge 负责收敛
- 长上下文必须先蒸馏再共享

## 12. Debate Discipline

辩论不是自由聊天，而是结构化交换：

### 12.1 Each turn should contain

- 当前立场
- 证据引用
- 对上一轮的回应
- 新增风险或新信息
- 结论建议

### 12.2 Invalid turns

以下发言不应计入有效轮次：

- 没有新增信息的复述
- 纯风格化表达
- 无证据的强判断
- 对职责边界之外内容做决定

## 13. Suggested Config Layout

建议配置层按如下方式组织：

```text
config/
  roles/
    planner.yaml
    scout.yaml
    skeptic.yaml
    builder.yaml
    guardian.yaml
  personas/
    contrarian.yaml
    conservative.yaml
    creative.yaml
    systems_thinker.yaml
  policies/
    p0-observer.yaml
    p1-analyst.yaml
    p2-builder.yaml
    p4-guardian.yaml
  skills/
    code_implementation.yaml
    backtest.yaml
    risk_analysis.yaml
  councils/
    trio-standard.yaml
    quorum-5-risk.yaml
```

## 14. Migration from Current OpenClaw Layout

当前每个角色拆成：

- `IDENTITY`
- `SOUL`
- `TOOLS`
- `USER`
- `AGENTS`

下一代建议映射为：

- `IDENTITY` -> `role` + `persona`
- `SOUL` -> `persona` + `long-term heuristics`
- `TOOLS` -> `skillset` + `policy.tool_allowlist`
- `USER` -> `policy` + `workflow_context defaults`
- `AGENTS` -> `council assembly rules`

## 15. Role Quality Metrics

角色和人格不是写完就结束，必须持续评估：

- 结论正确率
- 发现反例的能力
- token 成本
- 任务完成率
- 对其它角色的增益值
- 是否导致流程拥堵
- 是否经常越权

## 16. Decommission Rule

某个角色、人格或组合如果长期出现以下情况，应降级或删除：

- 增益不明显
- 高成本低产出
- 经常制造重复讨论
- 与其它角色高度重叠
- 高风险越权倾向
