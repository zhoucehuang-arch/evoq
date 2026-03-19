# WORKFLOW CATALOG

## 1. Purpose

本文件定义下一代自治投资系统应长期运行的工作流清单。工作流是系统真正的运行骨架，agent、Discord、Codex 和记忆系统都应围绕这些工作流协作，而不是各自漂浮。

## 2. Workflow Design Rules

每个工作流都必须显式定义：

- 触发条件
- 输入对象
- 参与角色
- 允许调用的工具
- 预算与超时
- 输出工件
- 成功判据
- 失败判据
- 是否需要审批
- 是否允许自动重试
- 退出条件

## 3. Workflow Families

下一代系统建议至少包含以下 8 个工作流族：

1. `Governance Workflows`
2. `Learning Workflows`
3. `Council Workflows`
4. `Strategy Workflows`
5. `Execution Workflows`
6. `Evolution Workflows`
7. `Memory Workflows`
8. `Incident Workflows`

## 4. Governance Workflows

### 4.1 `WF-GOV-001 Goal Admission`

用途：
把新目标纳入系统正式追踪。

触发：

- 用户通过 Discord 下发新目标
- 系统 planner 提交季度或周度新目标
- incident 触发衍生治理目标

主要步骤：

1. 创建 `goal.proposed`
2. 收集目标来源、时间范围、预算、评估口径
3. 召开小型 council 确认目标是否纳入
4. 生成 `goal.admitted` 或 `goal.rejected`
5. 为 admitted goal 初始化计划骨架

输出：

- `goal`
- `decision_card`
- `plan`

### 4.2 `WF-GOV-002 Daily Governance Heartbeat`

用途：
维持系统健康、自治级别、预算和主要队列状态。

触发：

- 每 5 分钟 heartbeat
- 关键工作流状态变化

检查内容：

- 工作流 backlog
- agent 占用
- Codex 队列积压
- token 消耗
- 学习队列积压
- 风险状态
- broker 连通性
- Discord 连通性

输出：

- `heartbeat`
- 异常告警
- 必要时触发 `incident`

### 4.3 `WF-GOV-003 Weekly Objective Review`

用途：
审视当前目标是否应继续、修正或终止。

输出：

- `goal_revision`
- `decision_card`
- 预算调整建议

## 5. Learning Workflows

### 5.1 `WF-LRN-001 Source Ingest`

用途：
持续摄入外部信息。

来源示例：

- 新闻
- 监管公告
- 财报资料
- 开源仓库
- 官方文档
- 学术论文
- 系统依赖更新
- 你自己的运行日志和 incident

步骤：

1. 抓取原始资料
2. 规范化元数据
3. 去重
4. 分配 topic
5. 评估可信度
6. 生成 `document`

### 5.2 `WF-LRN-002 Evidence Extraction`

用途：
把原始资料转成可引用事实。

参与者：

- `scout`
- `skeptic`
- 必要时 `judge`

输出：

- `evidence_item`
- 可信度评分
- 争议标签

### 5.3 `WF-LRN-003 Topic Synthesis`

用途：
围绕一个主题把多份证据综合成可行动洞察。

输出：

- `insight`
- 相关 `evidence_item` 引用
- 需要进一步验证的问题列表

### 5.4 `WF-LRN-004 Principle Promotion`

用途：
把跨多次事件反复成立的洞察升级为原则。

晋级条件示例：

- 至少 2 个独立来源支持
- 至少 1 次内部数据或实验验证
- 通过 skeptic 挑战

输出：

- `principle`
- 生效范围
- 失效条件

## 6. Council Workflows

### 6.1 `WF-COU-001 Fast Deliberation`

适用：
中低风险、需快速形成判断的问题。

成员建议：

- `planner`
- `skeptic`
- `judge`

预算建议：

- 1 到 2 轮
- 严格 token 上限
- 必须产出 `decision_card`

### 6.2 `WF-COU-002 Strategic Council`

适用：
高不确定性或高影响议题，例如：

- 重大策略方向调整
- 新市场学习方向
- 系统结构性升级

成员建议：

- `planner`
- `scout`
- `builder`
- `guardian`
- `judge`

输出：

- 结构化决策卡
- 任务拆解
- 预算占用

### 6.3 `WF-COU-003 Incident Council`

适用：
事故、异常、连续失败、风险事件。

目标：

- 快速止血
- 定义根因调查任务
- 生成恢复和防复发动作

## 7. Strategy Workflows

### 7.1 `WF-STR-001 Hypothesis Generation`

来源：

- 学习工作流
- 市场异常
- 旧策略退化
- 人工目标

输出：

- `hypothesis`
- 目标市场
- 预期机制
- 风险假设
- 评估计划

### 7.2 `WF-STR-002 Spec Construction`

用途：
把假设变成结构化策略规范。

输出：

- `strategy_spec`
- 信号条件
- 风控边界
- 数据需求
- 失效判据

### 7.3 `WF-STR-003 Backtest Validation`

参与者：

- `builder`
- `skeptic`
- `guardian`
- `Codex worker`

步骤：

1. 生成或更新策略实现
2. 执行回测
3. 输出关键指标
4. 审查数据质量与过拟合风险
5. 决定失败、修订或通过

### 7.4 `WF-STR-004 Paper Promotion`

前提：

- backtest 通过
- 风险校验通过
- 没有严重数据污染

输出：

- `paper_run`
- 监控计划
- 退出条件

### 7.5 `WF-STR-005 Live Promotion`

前提：

- paper 达到门槛
- 风控议会批准
- 资本配额可用

限制：

- 先进入 `live_limited`
- 必须设定回滚条件和 kill threshold

### 7.6 `WF-STR-006 Strategy Withdrawal`

触发：

- 回撤失控
- 统计退化
- 风险相关性飙升
- 数据假设失效
- 人工指令

输出：

- `withdrawal_decision`
- `causal_case`
- 后续复盘任务

## 8. Execution Workflows

### 8.1 `WF-EXE-001 Market Session Boot`

用途：
交易前检查。

检查项：

- broker 连通
- 市场状态
- 策略状态
- 风险开关
- 预算开关

### 8.2 `WF-EXE-002 Signal to Order`

用途：
把策略信号转成订单意图并交由确定性风控决策。

规则：

- agent 可以提出 signal reasoning
- 下单权限只属于 execution domain

### 8.3 `WF-EXE-003 Reconciliation`

用途：

- broker 状态对账
- 订单与持仓同步
- 重启后恢复

## 9. Evolution Workflows

### 9.1 `WF-EVO-001 Capability Gap Mining`

输入：

- incident
- failed task
- cost anomaly
- debate quality issue
- strategy failure
- user feedback

输出：

- `capability_gap`
- 严重级别
- 影响范围

### 9.2 `WF-EVO-002 Improvement Proposal`

用途：
把能力缺口转成可执行的系统改进提案。

输出：

- `improvement_goal`
- 候选方案
- 成本收益判断

### 9.3 `WF-EVO-003 Codex Build Cycle`

用途：
让 Codex 执行具体分析、编码、修复、补丁、测试和文档更新。

步骤：

1. 形成任务规范
2. 启动 `codex_run`
3. 收集工件和 diff
4. 执行 review / eval
5. 形成采纳或拒绝结论

### 9.4 `WF-EVO-004 Shadow / Canary Upgrade`

适用：

- 系统补丁
- prompt / role policy 变更
- 风控模型变更
- 学习管道变更

输出：

- `eval_run`
- `deployment_candidate`
- 晋级或回滚结论

## 10. Memory Workflows

### 10.1 `WF-MEM-001 Daily Distillation`

用途：
把当天高价值运行记录蒸馏入长期记忆。

来源：

- council 决策
- 风险事件
- strategy 评估
- Codex 运行
- incident 处理

输出：

- `insight`
- `causal_case`
- 候选 `principle`

### 10.2 `WF-MEM-002 Playbook Update`

用途：
维护稳定可执行的操作手册。

触发：

- 某类 incident 重复出现
- 某类任务已有稳定处理模式

## 11. Incident Workflows

### 11.1 `WF-INC-001 Safety Stop`

触发：

- broker 异常
- 风险阈值突破
- 重复下单风险
- 关键依赖不可用
- 审计链失效

动作：

1. 立即拉起 `risk.halt`
2. 冻结高风险 workflow
3. 通知 Discord
4. 开 incident

### 11.2 `WF-INC-002 Root Cause Analysis`

用途：
对事故做结构化复盘。

输出：

- `incident report`
- `causal_case`
- 修复任务
- 防复发措施

## 12. Workflow Priority Policy

默认优先级建议如下：

1. 安全类工作流
2. 交易执行与恢复类工作流
3. 事故类工作流
4. 高价值治理类工作流
5. 策略评估类工作流
6. 学习类工作流
7. 自进化类工作流

## 13. Budget Policy by Workflow Family

不同工作流必须有不同预算策略：

- `Incident`
  可突破普通预算，但要留下审计记录。
- `Execution`
  低延迟优先，token 使用最小化。
- `Council`
  严格限制轮数与参与者数。
- `Learning`
  允许批量处理，但必须做去重和蒸馏。
- `Evolution`
  必须与收益预期绑定，避免持续烧 token。

## 14. Workflow Exit Discipline

每个工作流在结束时必须选择以下结局之一：

- `completed`
- `failed`
- `cancelled`
- `superseded`
- `archived`

并产出以下至少一类工件：

- `decision_card`
- `report`
- `artifact bundle`
- `incident record`
- `memory promotion record`

## 15. Anti-Drift Rule

为了避免系统再次演化成“复杂角色很多，但没有稳定运行骨架”的状态，新增工作流必须满足：

- 说明为什么不能复用现有工作流
- 定义清晰状态机
- 定义预算
- 定义 owner
- 定义退出条件
- 定义至少一个可审计输出

## 16. Additional Mandatory Workflows from the Audit

本轮审查新增了一批强制工作流。在更深层自治被视为生产级能力前，这些工作流必须存在：

- `WF-GOV-004 Mission Priority Review`
- `WF-GOV-005 Owner Absence Safe-Mode Escalation`
- `WF-LRN-005 Source Revalidation and Trust Decay`
- `WF-LRN-006 Prompt Injection and Poison Quarantine`
- `WF-EXE-004 Market Calendar and Session Guard`
- `WF-EXE-005 Broker Outage Degradation`
- `WF-EVO-005 Objective Drift Review`
- `WF-INC-003 Provider or Relay Outage Response`
- `WF-INC-004 Credential or Bot Token Compromise Response`
- `WF-OPS-001 Disaster Recovery Drill`
