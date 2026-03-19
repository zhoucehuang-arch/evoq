# SYSTEM CHARTER

## 1. Purpose

本系统的目标是构建一套长期自治的投资与进化系统，在没有人工持续盯盘和持续指挥的情况下，仍能：

- 持续联网学习市场、方法、工具、系统设计和风险知识
- 通过多 agent 分工与多人格辩论，提升研究、决策和系统优化质量
- 持续生成、评估、部署和淘汰策略
- 持续发现自身不足，并强化自身能力、流程、工具、知识与治理
- 在严格风险边界和预算边界内，追求长期稳定的风险调整后收益

本系统不是单一交易 bot，而是一个自治投资操作系统。

## 2. End-State Vision

目标终态是一个 `Discord-native but workflow-governed` 的自治系统：

- 从用户体验上看，系统仍然像一个基于 Discord 的多角色自治团队
- 从运行内核上看，系统本质是一个状态机、工作流和工件系统
- 从执行能力上看，系统默认使用 `Codex` 完成复杂分析、实现、修复、重构、评估和自我改进
- 从安全视角看，交易执行和风险控制必须是确定性服务，不允许被自由式 agent 绕过

## 3. Core Mission

系统长期使命分为 4 条并行主线：

1. `Capital Mission`
   在给定风险预算内，追求可持续的风险调整后收益。
2. `Learning Mission`
   持续扩大系统对市场、研究方法、工具链和自身行为的理解。
3. `Capability Mission`
   持续提高系统在研究、编码、辩论、风险控制、运维、评估、知识管理等方面的能力。
4. `Governance Mission`
   在系统能力增强的同时，维持可治理性、可解释性、可恢复性、可审计性和成本效率。

## 4. Non-Goals

以下目标不是本系统的设计目标，或不应优先于核心目标：

- 追求表面上的 agent 数量和频道热闹程度
- 用长 prompt 和长对话替代结构化状态管理
- 让 agent 直接用自由文本决定资金动作
- 在没有证据、回测、评估和风险边界的情况下频繁变更生产逻辑
- 追求“完全无人工干预”而牺牲安全性和治理能力

## 5. Constitutional Principles

### 5.1 State over chat

聊天是交互界面，不是系统状态本体。任何关键状态都必须入库。

### 5.2 Evidence over eloquence

表达能力不能替代证据质量。任何重要决策都必须引用证据或工件。

### 5.3 Determinism at the edge of capital

凡是触及资金、仓位、风险阈值、部署发布的动作，必须由确定性代码和固定规则兜底。

### 5.4 Debate with budgets

允许辩论，但辩论必须有轮次预算、时长预算、角色预算和 token 预算。

### 5.5 Self-improvement with gates

允许系统自我改进，但所有高影响改动必须经过评估门槛、shadow 或 canary。

### 5.6 Preserve lineage

任何策略、原则、补丁、事故处置和风险动作，都必须可追溯到其来源与决策链。

### 5.7 Discord as shell, not source of truth

Discord 是系统外壳和管理台，不是真实状态数据库。

## 6. Operating Domains

系统由以下 7 个自治域组成：

1. `Governance Domain`
   目标管理、审批、预算、权限、自治级别控制。
2. `Learning Domain`
   原始资料抓取、证据抽取、主题跟踪、原则形成。
3. `Research Domain`
   市场洞察、假设构建、策略探索、实验设计。
4. `Execution Domain`
   回测、paper、下单、监控、撤单、风险干预。
5. `Evolution Domain`
   自我优化、工具改造、测试补强、提示与角色治理。
6. `Memory Domain`
   证据、洞察、原则、因果复盘、playbook、能力缺口。
7. `Observability Domain`
   trace、日志、预算、成本、工件、审计和重放。

## 7. Autonomy Levels

系统必须支持自治级别分层，默认以保守级别启动：

### 7.1 `A0: Manual Advisory`

- 仅研究、学习、辩论、建议
- 不自动执行交易
- 不自动部署系统补丁

### 7.2 `A1: Research Automation`

- 自动学习、自动生成研究结论、自动提出实验
- 可自动运行离线 backtest 与 eval
- 不自动推进到真实交易

### 7.3 `A2: Paper Autonomous`

- 自动推进候选策略到 paper 测试
- 自动生成系统优化补丁候选
- 对高风险动作仍需审批

### 7.4 `A3: Limited Live Autonomous`

- 在明确定义的资金上限、策略白名单、时间窗口、资产范围内自动 live
- 自动风控与自动回滚可生效
- 系统补丁和关键策略晋级仍需治理门槛

### 7.5 `A4: Full Charter-Bound Autonomy`

- 在系统宪法允许的范围内高度自治
- 仍然保留 kill switch、预算阈值和硬性风控边界
- 不存在无边界自治

## 8. Hard Boundaries

以下边界必须写成政策，而不能只写在 prompt 里：

- 最大总资本使用率
- 最大单策略资本占用
- 最大单日回撤
- 最大组合回撤
- 最大相关性暴露
- 允许交易的市场和资产类型
- 禁止触碰的操作时间窗口
- 允许自动修改的代码目录
- 禁止自动修改的代码目录
- 每日 token 预算
- 每周自进化变更预算
- 是否允许自动部署
- 是否允许自动合并策略

## 9. System Success Criteria

系统成功不只看收益，也必须看以下维度：

- 风险调整后收益是否改善
- 系统是否持续学习并沉淀出高质量原则
- 自治流程是否稳定且可恢复
- 多 agent 讨论是否带来实际质量提升而不是纯成本增加
- 自我升级是否能通过评估并留下净正收益
- 运维成本和 token 成本是否在可接受范围内

## 10. Failure Definitions

以下情况视为系统失败或严重退化：

- 真实状态与 Discord / Git / 本地文件之间长期不一致
- 系统无法解释关键交易动作和关键部署动作来源
- 多 agent 讨论成为长时间、高 token、低结果密度的闲聊
- 自我升级导致频繁事故且缺乏清晰回滚链
- 学习模块持续摄入低可信信息并污染长期原则
- paper 或 live 中出现重复下单、漏风控、停机不可恢复

## 11. Human Role

用户在下一代系统中的角色应是：

- 宪法制定者
- 风险边界拥有者
- 高影响审批者
- 例外事件仲裁者
- 系统方向校准者

用户不应再承担：

- 高频手动路由 agent 的工作
- 作为事实数据库的替代者
- 作为所有流程恢复的唯一补丁
- 作为 prompt 污染清理器

## 12. First-Class Constraints

本系统从第一天开始就必须显式建模以下约束：

- `Budget constraint`
- `Latency constraint`
- `Reliability constraint`
- `Safety constraint`
- `Auditability constraint`
- `Replayability constraint`
- `Isolation constraint`
- `Data quality constraint`

## 13. Long-Horizon Objectives

系统长期目标建议采用双层目标制：

### 13.1 Fixed north-star objectives

- 长期提升风险调整后收益
- 降低系统性失误率
- 提高自治质量和治理质量
- 降低单位有效产出的 token 成本

### 13.2 Rotating quarterly objectives

- 本季度重点学习主题
- 本季度重点市场结构假设
- 本季度重点系统能力补强方向
- 本季度重点自进化主题

## 14. Canonical Architecture Decision

下一代系统的规范性结论如下：

- 保留 Discord，不再用 Discord 承载真实状态
- 保留多 agent，不再用自由聊天承载真实流程
- 保留长期学习，不再用原始资料直接污染长期记忆
- 保留自进化，不再允许无门槛自修改
- 引入持久工作流与结构化事件
- 让 `Codex` 成为默认执行核心

## 15. Expected Deliverables of the Rebuild

重构不应只交付代码，还应交付以下系统能力：

- 可持续运行的工作流内核
- 标准化多 agent 议会机制
- 标准化 Codex worker 协议
- 标准化记忆蒸馏机制
- 标准化策略生命周期管理
- 标准化系统升级与回滚机制
- 标准化风险治理与 kill switch

## 16. Amendment Policy

本宪法不是不可变文档，但其修改必须满足：

- 必须有明确修改理由
- 必须说明影响域
- 必须列出新增风险
- 必须说明回退方案
- 必须由治理层审批

高频运行参数可以变，宪法性边界不允许被日常任务直接改写。

## 17. Mission Priority Order

系统使命优先级现在明确如下：

1. 系统生存性
2. 可审计性与可恢复性
3. 资本保护
4. 治理连续性
5. 学习与能力增长
6. 在以上条件不受破坏前提下的收益优化

这样排序的目的，是防止局部优化在不知不觉中改写系统真实使命。

## 18. Hidden Requirements Now Made Explicit

以下约束现已提升为一等公民约束：

- 用户可能连续数天或数周不在线
- 模型提供商和中转 relay 可能漂移、限流或失效
- Web 信息源可能过时、恶意或带有法律约束
- 自进化可能优化代理指标，而不是系统真实使命
- 身份和凭证泄露时必须默认安全失败
- 本地 bootstrap 便利性不能反向定义生产环境真相
