# CORE GOAL COVERAGE REVIEW

## 1. Purpose

本文件专门检查下一代系统设计中最核心的两个目标是否已经被真正覆盖：

- `自动进化`
- `自动交易`

这里不是检查“有没有提到”，而是检查是否已经形成完整闭环。

## 2. Summary Verdict

当前 `docs/next-gen/` 中，这两个核心目标都已经有了清晰骨架，但还需要进一步细化若干关键实现约束，才能避免再次出现“概念完整、运行失真”的情况。

结论如下：

- `自动进化`：方向正确，闭环基本成立，但还需补强评估、晋级梯度和能力量化。
- `自动交易`：主链路正确，风险约束也已明确，但还需补强订单幂等、对账、市场时段和生产门槛细则。

## 3. Auto-Evolution Coverage Check

### 3.1 What is already covered

当前设计中，自动进化已覆盖以下关键环节：

- 持续学习与外部资料摄入
- 证据提取、洞察形成、原则晋升
- 能力缺口挖掘
- 改进目标提出
- Codex build cycle
- review / eval / shadow / canary
- 风险治理与 rollback

对应文档：

- [WORKFLOW-CATALOG.md](WORKFLOW-CATALOG.md)
- [STATE-MODEL.md](STATE-MODEL.md)
- [CODEX-WORKER-PROTOCOL.md](CODEX-WORKER-PROTOCOL.md)
- [RISK-GOVERNANCE.md](RISK-GOVERNANCE.md)

### 3.2 Why this is a real loop now

自动进化闭环已经不是“agent 自己讨论一下”，而是：

```text
learning
  -> evidence
  -> capability_gap
  -> improvement_goal
  -> codex_run
  -> review/eval
  -> shadow/canary
  -> promote or rollback
  -> memory update
```

这已经形成了一个真正的可治理回路。

### 3.3 Remaining gaps to close

以下 6 个点仍建议补成明确规范：

1. `Capability scorecard`
   需要定义系统能力维度和分数变化规则。
2. `Evolution priority formula`
   需要定义什么类型的能力缺口优先修。
3. `Self-upgrade ladder`
   需要把自我升级分成低、中、高影响三级。
4. `Benchmark eval sets`
   需要建立系统升级前后的固定评测集。
5. `Source trust decay`
   需要定义外部知识过期和降权机制。
6. `Anti-stall replanning`
   当自动进化持续无产出时，需要自动重规划。

## 4. Auto-Trading Coverage Check

### 4.1 What is already covered

当前设计中，自动交易已覆盖：

- 策略从 hypothesis 到 production 的生命周期
- paper 与 limited live 分层
- deterministic risk engine
- signal to order workflow
- session boot
- reconciliation
- halt / freeze / safe mode

对应文档：

- [STATE-MODEL.md](STATE-MODEL.md)
- [WORKFLOW-CATALOG.md](WORKFLOW-CATALOG.md)
- [RISK-GOVERNANCE.md](RISK-GOVERNANCE.md)

### 4.2 Why this is closer to a production loop

自动交易闭环已被定义为：

```text
hypothesis
  -> strategy_spec
  -> backtest
  -> paper
  -> limited_live
  -> production
  -> degradation detection
  -> withdrawal / replacement
```

并且在资金边界处明确要求“确定性执行 + 风控兜底”。

### 4.3 Remaining gaps to close

以下 7 个点仍建议补成明确规范：

1. `Order idempotency policy`
   需要明确重复下单防护键。
2. `Broker reconciliation cadence`
   需要明确盘中、收盘、重启后的对账节奏。
3. `Market calendar rules`
   需要明确节假日、盘前盘后、异常停牌行为。
4. `Position sizing policy`
   需要明确策略级和组合级 sizing 公式。
5. `Promotion thresholds`
   需要明确 paper 到 live 的具体量化门槛。
6. `Execution degradation logic`
   需要明确在 broker 异常、数据异常时如何自动降级。
7. `Strategy correlation budget`
   需要明确多策略同向暴露预算。

## 5. Coverage Matrix

| Core Goal | Closed Loop Present | Governance Present | Risk Gate Present | Remaining Detail Work |
|---|---|---|---|---|
| 自动进化 | Yes | Yes | Yes | Medium |
| 自动交易 | Yes | Yes | Yes | Medium |

## 6. Important Judgment

这意味着当前设计不是“没做好”，而是“主骨架已经做好，但还有几项必须写死的执行细则没有补完”。

换句话说：

- 方向没偏
- 核心闭环已经成立
- 现在最该做的是把关键细则补全，而不是重新推翻路线

## 7. Recommended Next Clarifications

为了让这两个核心目标真正进入“可实施”状态，下一步最值得补的细化件是：

1. `database schema`
2. `service decomposition`
3. `order execution contract`
4. `promotion threshold policy`
5. `capability scorecard`
6. `dashboard data schema`

## 8. Acceptance Test for the Rebuild

下一代系统最终要以这两个问题来验收：

### 8.1 Auto-evolution acceptance

系统是否能在没有人工持续指挥的情况下：

- 发现能力短板
- 联网学习相关内容
- 提出改进计划
- 调用 Codex 实施
- 通过评估晋级或回滚
- 更新长期记忆与操作规则

### 8.2 Auto-trading acceptance

系统是否能在没有人工持续盯盘的情况下：

- 自动推进策略研究链
- 自动执行 paper / limited live
- 自动监控风险和状态
- 自动对账和恢复
- 自动撤退和冻结异常路径

只有这两条都成立，系统才算达到你要的核心目标。
