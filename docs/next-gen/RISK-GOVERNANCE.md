# RISK GOVERNANCE

## 1. Purpose

本文件定义下一代自治投资系统的风险治理框架。风险治理的目标不是限制系统发展，而是在持续学习、持续自进化、多 agent 协作和自动交易的前提下，防止系统因为局部优化而整体失控。

## 2. Risk Philosophy

本系统采用四条基础风险哲学：

1. `Capital is hard to earn back`
   资本损失恢复慢，必须优先保护下行。
2. `Autonomy amplifies both edge and mistakes`
   自治能力放大优势，也放大错误。
3. `Complex systems fail through coupling`
   真正危险的不是单点错误，而是多模块耦合后的级联失效。
4. `Every powerful capability needs a counterforce`
   每一类强能力都必须有对应制衡机制。

## 3. Risk Domains

系统必须同时治理以下风险域：

### 3.1 Market risk

- 方向性风险
- 波动率风险
- 跳空风险
- 流动性风险
- 集中度风险
- 相关性风险

### 3.2 Strategy risk

- 过拟合
- 数据泄漏
- 容量错判
- regime 失效
- 假设漂移
- 退出逻辑失效

### 3.3 Execution risk

- 重复下单
- 漏单
- 延迟
- broker 状态不同步
- 订单状态恢复失败

### 3.4 System risk

- 工作流卡死
- 状态源不一致
- 调度失效
- 心跳失效
- 工件链断裂

### 3.5 Model risk

- 幻觉
- 无证据强判断
- 长上下文污染
- 多 agent 集体偏差
- 对低可信来源过度依赖

### 3.6 Self-modification risk

- 自改补丁引入回归
- 风控代码被削弱
- 学习管道污染长期原则
- 角色/人格配置出现越权倾向

### 3.7 Governance risk

- 审批绕过
- 预算失控
- 自治级别被隐式提升
- 决策来源不可追溯

## 4. Risk Tiers

建议采用四级风险分类：

### 4.1 `R1 - Low`

特点：

- 不涉及资本动作
- 不涉及生产配置
- 失败成本可接受

示例：

- 离线分析
- 资料蒸馏
- 文档修改

### 4.2 `R2 - Moderate`

特点：

- 影响研究结果或中间流程
- 不直接触碰生产资金

示例：

- 回测脚本改动
- 学习抓取器改动
- 普通系统脚本改动

### 4.3 `R3 - High`

特点：

- 影响生产候选策略
- 影响风控判断
- 影响持久工作流可靠性

示例：

- 生产候选策略实现
- 关键状态机变更
- 审批逻辑变更

### 4.4 `R4 - Critical`

特点：

- 直接影响资金安全或系统宪法边界

示例：

- 下单路径
- 风险阈值
- kill switch
- 自治级别提升
- 自动部署到 live execution

## 5. Control Classes

风险控制措施分为六类：

1. `Preventive`
   事前预防，例如权限、白名单、预算、静态约束。
2. `Detective`
   事中检测，例如监控、异常发现、对账、校验。
3. `Corrective`
   事后纠正，例如回滚、补偿、撤单、冻结工作流。
4. `Compensating`
   主控制缺失时的代偿，例如 shadow、人工复核。
5. `Adaptive`
   根据市场和系统状态动态调整限额。
6. `Forensic`
   事故后因果追溯与证据保全。

## 6. Trading Risk Controls

### 6.1 Hard limits

必须有不可由 agent 直接修改的硬限制：

- `max_daily_drawdown`
- `max_total_drawdown`
- `max_position_size`
- `max_strategy_allocation`
- `max_sector_exposure`
- `max_symbol_exposure`
- `max_correlation_cluster_exposure`
- `max_intraday_loss`

### 6.2 Strategy eligibility checks

进入 paper 或 live 前必须检查：

- 数据完整性
- 回测可信度
- 交易成本敏感性
- 流动性约束
- 风控规则完整性
- 解释链完整性

### 6.3 Runtime guards

- 市场开前检查
- 实时持仓监控
- 异常收益与异常损失检测
- 实时相关性聚集监测
- broker 对账
- session close 审核

## 7. System Safety Controls

### 7.1 Workflow controls

- 每个工作流必须有 timeout
- 每个工作流必须有 retry policy
- 每个工作流必须有 owner
- 每个工作流必须有 cancellation path

### 7.2 State consistency controls

- Git 与 DB 不一致时开 incident
- broker 与本地状态不一致时冻结 execution
- Discord 与 DB 不一致只视为展示异常，不影响事实源

### 7.3 Budget controls

- 每日 token 预算
- 每周自进化预算
- 每个 council 的最大 token 预算
- 每个 Codex run 的最大预算

## 8. Knowledge and Learning Risk Controls

持续联网学习带来的最大风险之一是知识污染。

### 8.1 Required controls

- source trust score
- source freshness score
- deduplication
- contradiction detection
- evidence lineage
- principle promotion gates

### 8.2 Unsafe patterns

- 单一来源直接晋升为原则
- 旧闻被当作新事实
- 没有主题边界的无限抓取
- 未蒸馏的长文本直接进入长期记忆

## 9. Multi-Agent Risk Controls

多人格协作虽然能提质，但也有特有风险：

- 共识幻觉
- 角色互相迎合
- 围绕错误前提做高质量讨论
- token 膨胀
- 责任模糊

### 9.1 Controls

- 强制 `judge` 或 `reducer`
- 限制轮数
- 限制成员数量
- 引用证据
- 记录 dissent
- 对重要议题保留 contrarian 角色

## 10. Codex and Self-Modification Risk Controls

### 10.1 Required controls for self-change

- 限定写入范围
- review gate
- eval gate
- shadow / canary gate
- rollback artifact
- deployment approval

### 10.2 Forbidden behaviors

- 直接修改生产 secrets
- 直接修改 live risk thresholds 而无审批
- 直接将未经验证的 patch 部署到生产
- 自我修改后跳过验证

## 11. Approval Matrix

建议采用如下审批矩阵：

| Action | Risk Tier | Default Approval |
|---|---|---|
| 离线研究 | R1 | 无需人工审批 |
| 普通代码补丁 | R2 | review 即可 |
| 学习管道改动 | R2/R3 | review + eval |
| 策略晋级到 paper | R2/R3 | governor 或 guardian 同意 |
| 策略晋级到 live | R3/R4 | guardian + governor + policy gate |
| 风控阈值修改 | R4 | 人工审批 |
| 自治级别提升 | R4 | 人工审批 |
| 自动部署生产补丁 | R4 | 人工审批 |

## 12. Kill Switches

必须至少具备以下 kill switch：

- `TRADING_HALT`
  停止新开仓。
- `EXECUTION_FREEZE`
  停止订单路径。
- `EVOLUTION_FREEZE`
  停止自我修改与自动部署。
- `LEARNING_FREEZE`
  停止外部信息摄入。
- `GLOBAL_SAFE_MODE`
  降级到只读、只分析模式。

### 12.1 Kill switch requirements

- 可由 guardian 或系统触发
- 可由用户手动触发
- 触发后必须广播到 Discord
- 触发后必须写入 DB
- 触发后必须有解除流程

## 13. Incident Severity Model

建议采用四级事故模型：

### 13.1 `SEV-1`

资本或系统宪法存在即时风险。

### 13.2 `SEV-2`

关键生产能力受损，但可控。

### 13.3 `SEV-3`

局部退化或异常，需要修复但未危及核心安全。

### 13.4 `SEV-4`

轻微问题、噪声或单次失败。

## 14. Mandatory Incident Flow

一旦出现高等级事故，必须自动执行：

1. 触发 halt / freeze
2. 锁定相关工作流
3. 建立 incident
4. 快速对账和状态快照
5. 召开 incident council
6. 生成 root cause analysis
7. 生成补救与防复发任务

## 15. Risk Metrics

系统必须长期追踪以下指标：

- 日回撤
- 组合最大回撤
- 策略胜率、Sharpe、turnover
- 异常订单率
- broker 对账差异率
- incident 数量与等级
- rollback 频率
- Codex patch 拒绝率
- principle 被撤销率
- 单位有效产出的 token 成本

## 16. Governance Reports

至少应自动生成：

- 每日风险摘要
- 每周策略健康报告
- 每周系统治理报告
- 每月自进化收益/事故报告

## 17. Risk Ownership

风险治理不能只归一个 agent：

- `guardian`
  风险检测与 halt 触发
- `governor`
  审批与政策边界
- `judge`
  结论收敛
- `operator`
  执行协调与恢复推进
- `user`
  宪法边界与最终例外授权

## 18. Minimum Safe Defaults

如果系统状态不明、依赖异常、对账失败或审计链断裂，应默认：

- 不下新单
- 不晋级策略
- 不部署补丁
- 不提升自治级别
- 可以继续做只读分析和事故诊断

## 19. Governance Review Cadence

风险治理本身也需要定期复盘：

- 每周复盘风险事件和近 miss
- 每月复盘风控阈值是否合理
- 每季度复盘审批矩阵与自治级别设置

## 20. Final Principle

系统可以强自治、强学习、强进化，但不能强失控。

任何能力增强，如果不能同时增强以下四项中的至少两项，就不应进入长期正式系统：

- 安全性
- 可治理性
- 可解释性
- 资本效率

## 21. Additional Risk Domains Made Explicit by the Audit

本轮审查将以下风险域明确提升为一等风险域：

### 21.1 Provider and relay risk

- 限流策略漂移
- 模型能力漂移
- 局部故障
- 工具行为不一致

### 21.2 Knowledge poisoning risk

- 来自实时网页内容的 prompt injection
- 低可信社媒传言污染
- 过期事实被当作当前真相提升

### 21.3 Identity and access risk

- Discord token 泄露或被盗用
- dashboard 访问泄露
- worker 凭证权限过大

### 21.4 Operator absence risk

- 审批过期但没有安全回退
- 事故发生时无人可接管
- 实际运行隐藏依赖人工半夜介入

### 21.5 Mission drift risk

- 自进化优化输出量而非真实系统质量
- 辩论优化表达感而非证据质量
- 学习优化新奇度而非可信度
