# EvoQ Dashboard-First 复审报告

## 1. 结论先行

我现在的判断是：

**EvoQ 下一阶段不该继续以 IM/Discord 为中心，而应该转成 dashboard-first。**

更准确地说，不是“不要 IM”，而是：

- dashboard 是主工作台
- IM 是轻量 gateway
- agent 的组织方式改成 workflow capability，而不是人类岗位分工

这不是风格选择，而是产品结构选择。  
如果主目标是让 EvoQ 成为一个真正可操作的金融研究与量化系统，那么 dashboard 必须从“展示层”升级成“操作层”。

---

## 2. 我看了哪些证据

### 仓库侧

- `src/quant_evo_nextgen/runner/discord_shell.py`
- `src/quant_evo_nextgen/services/discord_access.py`
- `src/quant_evo_nextgen/services/control_plane.py`
- `src/quant_evo_nextgen/config.py`
- `src/quant_evo_nextgen/api/main.py`
- `src/quant_evo_nextgen/services/dashboard.py`
- `src/quant_evo_nextgen/contracts/dashboard.py`
- `apps/dashboard-web/app/*`
- `apps/dashboard-web/lib/dashboard.ts`
- `docs/next-gen/DASHBOARD-WEBSITE-SPEC.md`
- `docs/next-gen/DISCORD-NL-INTERACTION-MODEL.md`
- `docs/next-gen/ROLE-PERSONA-MODEL.md`
- `docs/next-gen/WORKFLOW-CATALOG.md`

### 外部参考

- Hermes 正式报告 `final_report_v1.0_formal.pdf`
- OpenClaw 官方仓库与文档

---

## 3. 以前的 EvoQ 到底有没有 IM

有，而且不是临时补丁。

仓库里已经存在明确的 Discord 控制面：

- bot shell
- 白名单与频道控制
- 控制命令路由
- 审批与暂停/恢复
- runtime config 变更流

也就是说，旧 EvoQ 不是纯 dashboard 产品，而是一个 **Discord + dashboard 的双面系统**。

但现在的问题不是“有没有 IM”，而是“IM 是否还应该是主工作面”。  
我的答案是：**不应该。**

---

## 4. 现在的 dashboard 到底是什么

### 代码事实

我检查后看到：

- `apps/dashboard-web` 目前基本是只读页面
- 页面主要通过 `fetch*()` 拉取汇总数据
- 前端没有真正的表单、按钮回调、提交动作
- 我没看到 dashboard 页面里有 `button`、`form`、`onClick`、`onSubmit` 这一类主操作入口

所以现在的 dashboard 本质上是：

**高密度观察层，不是操作层。**

### 后端事实

后端其实已经有不少可写能力：

- 研究 brief
- hypothesis
- strategy spec
- backtest
- paper run
- promotion / withdrawal
- approval / override
- runtime config proposal
- order intent / reconciliation / incident

所以问题不在后端没有动作，而在于：

**这些动作没有被 dashboard 组织成清晰的工作流界面。**

---

## 5. Hermes 报告给我的方向

Hermes 报告的核心结论其实很明确：

- LLM 不应该直接充当交易引擎
- LLM 更适合做研究、解释、挑战、诊断、自动化
- 量化框架负责数据、成本、回测、组合、风险、执行边界
- 真正重要的是证据链、时间戳、成本、前向验证、风控和审计

这和 EvoQ 当前要做的事情并不冲突，反而强化了一个判断：

**dashboard 应该围绕“研究 -> 证据 -> 审核 -> 运行 -> 风险 -> 追踪”来组织，而不是围绕聊天命令来组织。**

---

## 6. OpenClaw 给我的启发

OpenClaw 更像是一个 **gateway + browser control UI** 的系统，而不是“IM 先行”的系统。

它的启发不是“照抄它的产品形态”，而是：

- IM 可以是入口
- 但真正的主控面可以在浏览器里
- chat 只是轻量通道，不是中心工作区

这点很重要。  
对 EvoQ 来说，正式产品路径应该固定为 Telegram gateway；旧 Discord 只作为历史实现参考，不再作为后续产品入口。

---

## 7. 我现在反对的架构

### 7.1 反对“人类式分工”作为主架构

不建议继续把 agent 组织成像人类团队那样的固定岗位：

- researcher
- analyst
- trader
- operator
- manager
- reviewer

问题不是这些名字不能用，而是它们很容易把系统带回“像团队一样聊天”的方向。

### 7.2 更好的方式

把 agent 组织成 **workflow capability**：

- research intake
- evidence synthesis
- factor discovery
- strategy hypothesis
- backtest audit
- paper monitoring
- risk halt / recovery
- config / deployment
- incident response

这样分工不变，但组织逻辑变了。  
不是“谁像谁”，而是“这个能力在什么 workflow 里、读什么状态、产出什么 artifact、经过什么 gate”。

---

## 8. 我建议的交互架构

### 8.1 主架构

- dashboard = 主工作台
- IM = 轻量 gateway
- agent = workflow 执行器
- LLM = 研究和判断增强层
- 量化引擎 = deterministic 事实与执行层

### 8.2 IM 只保留什么

IM 适合保留这些动作：

- 事件提醒
- 快速状态查询
- 轻量确认
- 暂停 / 恢复
- 紧急止损
- 关键审批提醒

IM 不适合承担：

- 长表格浏览
- 回测对比
- 因子筛选
- 证据链检查
- 长链路研究
- 多对象比较

### 8.3 dashboard 需要承担什么

dashboard 需要承担：

- 研究工作台
- 证据工作台
- 量化分析工作台
- 风险控制台
- 运行监控台
- 审批与追踪台

也就是说，它不该只是“看见系统”，而要能“操作系统”。

---

## 9. 当前 dashboard 逻辑的主要问题

我觉得现在最关键的问题不是页面数量不够，而是**页面逻辑还偏展示导向**。

典型表现是：

- 首页更像状态摘要
- trading / learning / evolution / system / incidents 更像分区看板
- 但缺少明确的“下一步动作”
- 缺少对象级 drill-down
- 缺少比较视图
- 缺少可执行操作的界面语义

金融专业工具不只是展示信息，它要支持：

- 筛选
- 对比
- 追溯
- 审核
- 版本控制
- 风险确认
- 证据归档

这也是 dashboard 现在最需要补的东西。

---

## 10. 我建议的新 dashboard 结构

### 10.1 首页

首页应该回答四个问题：

- 现在系统状态怎样
- 哪些事情卡住了
- 哪些事情可以推进
- 下一步该点哪里

首页不是信息堆叠页，而是 **today workbench**。

### 10.2 Research

研究页应该从“读资料”变成“研究生产线”：

- 输入想法
- 生成 research brief
- 看证据包
- 看 challenge notes
- 看 audit gate
- 看从 brief 到 hypothesis 的流转

### 10.3 Factor / Signals

这页不是简单展示因子，而是：

- 因子候选
- 排名变化
- universe
- 参数
- 稳定性
- 相关性
- 失效案例

### 10.4 Backtests

这页应该是证据中心：

- PIT / replay
- 成本模型
- 滑点假设
- baseline 对比
- leakage check
- 版本对比
- promotion gate

### 10.5 Paper

paper 页要变成运行监控页：

- 持仓
- 订单
- 账户
- 对账
- session
- 风险
- 停止条件

### 10.6 Risk / Incidents

这页要让人一眼看懂：

- 哪个风险在升高
- 哪个域被冻结
- 哪个审批没过
- 哪个事件需要处理
- 哪个动作会改变状态

### 10.7 System

系统页负责：

- loop health
- deploy posture
- config proposals
- doctor summary
- recovery path

---

## 11. IM 还要不要

我的结论是：**要，但要降级。**

不要把 IM 砍掉，因为它在以下场景仍然有价值：

- 移动端快速处理
- 紧急事件
- 低摩擦提醒
- 简单确认

但也不要再把 IM 当主界面，因为它天然不适合：

- 高密度研究
- 复杂比较
- 证据审查
- 工作台式操作

### 最终建议

**不要纯 dashboard。**

**也不要 IM-first。**

**要 dashboard-first + IM gateway。**

IM 直接绑定 Telegram bot 就够了。  
Discord 不再作为产品计划的一部分。关键不在平台名，而在它是不是只做轻量入口，不抢主工作台。

---

## 12. 这次真正应该改的不是命令，而是系统组织方式

你刚才说得很对：重点应该转向 dashboard。  
我补一句更强一点的判断：

**下一步不是把更多命令塞进 IM，而是把可操作的工作流重新组织到 dashboard。**

也就是说：

- 原来放在 Discord 的命令，要重新分流
- 能在 dashboard 做的，就放 dashboard
- 只能轻量触发的，才留给 IM
- agent 之间不按人类岗位分，而按 workflow 能力分

---

## 13. 我建议的下一步方向

如果按优先级排序，我建议下一步做这三件事：

1. 先定 dashboard 的信息架构
2. 再定 IM 的最小 gateway 边界
3. 最后重构 agent workflow 的组织方式

换句话说，先定“人怎么用”，再定“agent 怎么跑”。

---

## 14. 已确认的边界

这几个方向现在已经可以视为确认项：

1. IM 只保留轻审批、提醒、暂停/恢复、紧急处置。
2. IM 统一绑定 Telegram bot，不再保留 Discord 作为正式产品路径。
3. dashboard 是主工作台，不是展示页。
4. agent 以 workflow capability 编排，不再按人类岗位分工。
5. LLM 负责想法、研究、判断与挑战，Codex 负责实现、测试、复用、落盘。

---

## 15. 我的当前建议

如果现在就要我给一个明确方向，我会选：

**dashboard-first，Telegram 仅作 gateway，agent 以 workflow capability 编排。**

这更符合：

- 你对 dashboard 的重视
- Hermes 报告里的 LLM/quant 分工逻辑
- OpenClaw 这类 gateway + browser control UI 的产品思路
- 一个真正可落地的金融研究与量化工具的使用方式

## 16. 终局方案

### 16.1 产品定义

EvoQ 不是聊天机器人，也不是单纯量化回测器。  
它应该是一个 **dashboard 驱动的、可审计的、可持续自进化的量化研究与执行系统**。

### 16.2 系统分层

- **量化核心**：数据、因子、回测、组合、风控、paper、对账、恢复
- **LLM 研究层**：发想、检索、证据整理、质疑、总结、诊断
- **Codex 执行层**：把研究想法变成代码、工具、skill、文档、测试和补丁
- **Dashboard 工作台**：所有主操作、比较、审核、追踪都在这里完成
- **Telegram gateway**：只负责提醒、轻审批、暂停/恢复、紧急动作

### 16.3 Agent 编排原则

不再围绕“像人类的岗位”来设计 agent，而围绕 workflow 来设计：

- research intake
- evidence synthesis
- factor discovery
- strategy spec
- backtest audit
- paper monitoring
- risk halt / recovery
- config / deployment
- incident response
- evolution implementation

每个 workflow 都必须有：

- 触发条件
- 输入对象
- 允许工具
- 预算和时限
- 输出 artifact
- 审核门
- 失败退出条件

### 16.4 自进化机制

LLM 自进化不应该直接写进交易引擎里，而应该走这条链：

1. LLM 提出想法、问题、改进建议
2. 系统把想法封装成结构化 proposal / brief / task
3. Codex 读取 task 和 skill，上手实现
4. Codex 自动补测试、补文档、补验证
5. Dashboard 展示证据、差异、状态和回滚点
6. 通过 review / canary / promotion gate 后才进入稳定状态

### 16.5 第一阶段执行顺序

1. 重做 dashboard 信息架构，先把首页变成 workbench。
2. 把研究、因子、回测、paper、风险、系统拆成操作导向页面。
3. 把 Telegram gateway 缩到最小，保留轻审批和应急动作。
4. 建立 workflow catalog 和 artifact schema。
5. 建立 Codex task / skill / tool 复用机制。
6. 再推进更强的自进化、自动研究和自动实现闭环。

### 16.6 交付标准

产品只有在满足这些条件时才算可用：

- dashboard 可以作为主入口完成研究和治理工作
- Telegram 可以完成轻审批和应急处置
- LLM 的输出不会直接穿透到交易引擎
- Codex 的实现路径可复用、可测试、可回滚
- 所有关键动作都能追溯到 artifact、版本和 gate
- 系统可以持续运转，而不是只会一次性演示

## 17. 最终解决方案与实施计划（定版）

这一节是最终执行蓝图。

### 17.1 最终产品形态

EvoQ 最终应该做成一个可以部署在本机或单 VPS 上的 dashboard-first 量化研究、自进化与 paper/live 准备系统。

它不是聊天机器人，也不是让 LLM 直接下单的系统。  
它是一个以量化核心为底座、以 LLM 研究为增强、以 Codex 实现为执行、以 dashboard 为主工作台、以 Telegram 为轻 gateway 的产品。

### 17.2 总体架构

建议采用单机优先的模块化单体架构：

```text
Local Machine / 1 VPS
  ├─ Core API
  ├─ Dashboard Web
  ├─ Postgres / local dev DB
  ├─ Scheduler / Supervisor
  ├─ Quant Engine
  ├─ LLM Research Runtime
  ├─ Codex Execution Runtime
  └─ Telegram Gateway
```

原则：

- 本机和单 VPS 走同一套 runtime 形态
- 起步不要求 Core + Worker 分离
- 后续可以扩展为 Core + Worker，但不是第一目标
- broker credential 只允许进入 Core
- 所有 capital-facing 行为必须经过 deterministic quant / risk 层

### 17.3 Dashboard 信息架构

Dashboard 不按模块展示，而按工作流组织。

#### Home / Workbench

目标：第一屏就告诉用户现在该做什么。

包含：

- 今日待办
- blocked items
- ready for review
- running workflows
- stale / failed / halted 状态
- 下一步建议

操作：

- 打开研究任务
- 审核 brief
- 审核 backtest
- 进入 paper monitor
- 暂停相关 domain

#### Research Lab

目标：把用户想法和 LLM 研究变成结构化资产。

包含：

- idea input
- research brief
- evidence packet
- source / citation
- contradiction notes
- audit status
- promote / reject

#### Factor Studio

目标：把研究想法转成可计算的因子与信号。

包含：

- factor candidate
- universe
- feature definition
- ranking snapshot
- stability
- correlation
- turnover
- missing data
- factor lineage

#### Backtest Evidence

目标：判断证据是否可靠，而不是只看收益好不好看。

包含：

- strategy spec
- dataset range
- point-in-time status
- cost model
- slippage model
- baseline comparison
- leakage check
- Sharpe / Sortino / drawdown / turnover
- gate result

#### Paper Desk

目标：让策略先经过真实时间推进的 paper 观察。

包含：

- paper run status
- positions
- orders
- account snapshot
- reconciliation
- PnL
- exposure
- stop condition

#### Risk & Incidents

目标：所有风险、暂停、异常和恢复动作都在这里闭环。

包含：

- active overrides
- risk limits
- stale data
- provider incidents
- reconciliation mismatch
- open approvals
- recovery playbook

#### Evolution Center

目标：管理系统自进化，不让它变成黑盒。

包含：

- improvement proposals
- Codex tasks
- generated tools / skills
- tests
- canary status
- rollback point
- promotion decision

#### System & Deploy

目标：本机/VPS 部署、健康检查、配置和恢复。

包含：

- local / VPS mode
- service health
- scheduler health
- Telegram health
- API / dashboard binding
- env completeness
- backup / restore
- smoke tests

### 17.4 Agent / Workflow 设计

不要把 agent 设计成固定人类岗位。应该设计成可复用 workflow。

核心 workflow：

1. Idea Intake Workflow
2. Evidence Synthesis Workflow
3. Factor Discovery Workflow
4. Backtest Audit Workflow
5. Paper Monitoring Workflow
6. Risk Recovery Workflow
7. Evolution Implementation Workflow

每个 workflow 都必须有：

- 触发条件
- 输入对象
- 允许工具
- 预算和时限
- 输出 artifact
- 审核门
- 失败退出条件

### 17.5 LLM 与 Codex 的分工

LLM 做：

- 发现研究方向
- 解释市场逻辑
- 整理证据
- 提出因子假设
- 找反例
- 诊断异常
- 总结 paper 表现
- 提出系统改进

Codex 做：

- 写代码
- 修改策略模板
- 创建工具
- 创建 skill
- 写测试
- 运行验证
- 更新文档
- 生成迁移
- 做可回滚实现

Codex 的优势应该主要用于结构优化、自进化落地、工具调用、测试验证、skill 复用和工程执行。金融信息获取、数据源接入、证据链与市场数据 freshness 仍应由 EvoQ 自己的数据和研究流程负责，不能为了省事把金融事实层外包给 Codex。

LLM 不做：

- 直接下单
- 直接改 capital-facing 配置
- 绕过 backtest / paper / risk gate
- 直接把自然语言建议变成实盘动作

### 17.6 数据与对象模型

必须固定这些对象：

- Idea
- ResearchBrief
- EvidencePacket
- Hypothesis
- FactorDefinition
- SignalSnapshot
- StrategySpec
- BacktestRun
- PaperRun
- PromotionDecision
- Incident
- Override
- EvolutionProposal
- CodexTask
- ToolArtifact
- SkillArtifact

所有 dashboard 页面都围绕这些对象展开，而不是围绕日志或聊天记录展开。

### 17.7 Telegram Gateway 设计

Telegram 只做轻入口。

保留命令：

- `/status`
- `/alerts`
- `/approvals`
- `/approve <id>`
- `/reject <id>`
- `/pause <domain>`
- `/resume <domain>`
- `/open <object_id>`

每条重要消息都应跳 dashboard 深链，不在 Telegram 里完成复杂工作。

### 17.8 单机部署方案

第一可交付版本必须支持：

- 本机启动
- 单 VPS 启动
- 同一套 `single_vps_compact` runtime
- dashboard 本地访问
- Telegram gateway 可选启用
- paper broker / paper sim 默认启用
- live trading 默认禁用

推荐第一阶段本机启动形态：

```text
API: 127.0.0.1:8000
Dashboard: 127.0.0.1:3000
DB: local Postgres or SQLite-dev
Telegram: optional
Broker: paper_sim
Codex runner: same host
```

### 17.9 实施计划

#### Phase 1：Dashboard Workbench 重做

目标：先让产品能用。

交付：

- 新首页 workbench
- Research Lab
- Backtest Evidence
- Paper Desk
- Risk & Incidents
- System & Deploy

验收：

- 用户能从 dashboard 创建研究想法
- 用户能看到 ready / blocked / running / failed
- 用户能做 approve / reject / pause / resume
- 所有动作写入 durable state

#### Phase 2：Workflow 与 Artifact 内核

目标：让 LLM / Codex / dashboard 围绕同一套对象工作。

交付：

- workflow registry
- artifact schema
- task queue
- object detail drawer
- provenance view

验收：

- 每个 workflow 都有输入、输出、gate、状态
- 每个对象都能追溯来源和版本
- dashboard 能打开任意 artifact 详情

#### Phase 3：Quant Signal Kernel

目标：传统量化骨架先立住。

交付：

- market data adapter
- historical bars
- factor registry
- signal snapshot
- ranking
- lineage

验收：

- 没有 LLM 也能跑因子和信号
- 相同输入可复现相同结果
- dashboard 能看 factor / signal / ranking

#### Phase 4：Backtest 与 Evidence Engine

目标：证据可靠，而不是收益好看。

交付：

- PIT replay
- cost model
- slippage model
- baseline comparison
- leakage check
- backtest gate

验收：

- 没有成本和 baseline 不能通过
- 有泄漏风险必须 blocked / needs_review
- dashboard 能对比不同 backtest 版本

#### Phase 5：LLM Research Advantage

目标：发挥 LLM 最大优势。

交付：

- automatic research brief
- evidence synthesis
- challenge pass
- contradiction notes
- prompt/tool trace
- ablation marker

验收：

- LLM 输出不能绕过 gate
- 每个 LLM 结论都有来源和时间戳
- dashboard 能看到 LLM 贡献和反例

#### Phase 6：Codex Self-Evolution

目标：让系统可以持续改进，但不失控。

交付：

- evolution proposal
- Codex task
- tool / skill artifact
- automated tests
- review / canary / rollback

验收：

- Codex 不能无记录改系统
- 每次改动都有任务、diff、测试和文档
- dashboard 能 approve / rollback

#### Phase 7：Telegram Gateway

目标：轻入口，不抢 dashboard 主工作台。

交付：

- Telegram bot
- allowlist
- alerts
- approvals
- pause / resume
- dashboard deep links

验收：

- Telegram 能完成轻审批
- 高复杂操作必须跳回 dashboard
- 所有 Telegram 动作写入 durable state

#### Phase 8：Local / VPS Productization

目标：真正可部署。

交付：

- 本机启动命令
- 单 VPS 启动命令
- smoke test
- doctor
- backup / restore
- safe mode

验收：

- 本机能跑完整产品
- 1 VPS 能跑完整产品
- 测试和 smoke 通过
- 默认只启用 paper，不启用 live

### 17.10 最小可用版本定义

最小可用版本不是“功能全”，而是这条链能跑通：

```text
用户想法
  -> Research Brief
  -> Evidence Packet
  -> Factor / Signal Candidate
  -> Strategy Spec
  -> Backtest Evidence
  -> Paper Run
  -> Promotion / Rejection Decision
```

这条链必须主要通过 dashboard 操作。

### 17.11 立即执行顺序

现在不要先做 broker，也不要先做 live，也不要先做复杂多 agent。

立即执行顺序：

1. 重做 dashboard workbench 和页面结构
2. 补 owner action API：approve / reject / pause / resume / create idea
3. 建立 workflow + artifact 对象模型
4. 打通 research brief -> hypothesis -> strategy spec
5. 打通 factor / signal 的 deterministic kernel
6. 打通 backtest evidence
7. 打通 paper run
8. 接 Telegram gateway
9. 做本机和单 VPS 一键启动
10. 再做 Codex 自进化闭环

这条路径先把产品做成真正可用，再逐步增强智能和自动化。

## 18. 我是如何学习这些类似项目的

你刚才问得很对。前面的方案如果只给结构，不讲学习路径，就会显得像拍脑袋。  
这一节我把“我是怎么学的”讲清楚。

### 18.1 我不是先看热闹，而是先拆四件事

我看每个开源项目时，先不是问“它火不火”，而是看四个固定维度：

1. **架构与结构形式**
   - 它是单体、分层、工作流、Agent swarm，还是 benchmark harness
   - 它把什么放在核心，什么放在外层
   - 它的 state、memory、tool、UI、execution 分别在哪里

2. **组织方式**
   - 它是按人类岗位分工
   - 还是按 workflow / capability 分工
   - 它的主入口是 CLI、Web、MCP、API、还是 chat

3. **功能与特点**
   - 它主要解决研究、回测、模拟、实盘、还是评估
   - 它是否重视 memory、skill、checkpoint、audit、replay
   - 它是否把自然语言真正变成可执行流程

4. **它为什么这样设计**
   - 它是为了可复现
   - 为了低门槛
   - 为了评估公平
   - 为了更像真实交易桌
   - 为了更容易本地启动

我不是只看 README 的营销语，而是拿它的目标、入口、workflow、state 和约束来判断它到底是什么产品。

### 18.2 我对几个代表项目的理解

#### FinRL

我把 FinRL 看成 **量化底座型项目**。

它的核心是三层：

- market environments
- DRL agents
- financial applications

它的意义不是“LLM trading”，而是告诉我：

- 量化系统首先要有清晰的环境层
- 训练、验证、交易要有明确边界
- 数据和状态要可复现

所以我从 FinRL 得到的第一条逻辑是：

**先把量化事实层做稳，再谈智能。**

#### FinRL-Meta

我把 FinRL-Meta 看成 **数据与环境工程化项目**。

它强调 DataOps、动态数据集、市场环境、训练-测试-交易管线。  
它真正重要的不是某个策略，而是它把金融 RL 变成了可以持续生产 benchmark 的数据与环境系统。

所以我从它得到的第二条逻辑是：

**如果想做真正能落地的金融系统，必须把数据层、环境层、freshness、replay、监控做成第一公民。**

这直接影响了我对 EvoQ 的判断：

- market data hub 不能只是接口
- dashboard 不能只看结果
- 所有状态必须能追溯到数据时间和环境版本

#### TradingAgents

我把 TradingAgents 看成 **人类交易桌抽象型项目**。

它最有价值的地方，不是“很多 agent 很热闹”，而是它把交易桌拆成了：

- fundamental
- sentiment
- technical
- risk
- trader
- portfolio manager

它其实表达的是一个真实交易团队的职责分离。

但我从中学到的，不是“照搬岗位名”，而是：

- 交易判断天然是多阶段的
- 不同阶段需要不同视角
- 风险和最终决策必须独立于研究冲动

所以我吸收的是它的 **workflow 分层思想**，而不是它的 **人类岗位叙事**。  
这就是为什么我最后把 EvoQ 的 agent 设计改成 workflow capability，而不是 human role。

#### Vibe-Trading

我把 Vibe-Trading 看成 **产品化与个人工作台型项目**。

它和很多纯研究 repo 不一样的地方在于：

- 有 CLI
- 有 Web
- 有 MCP
- 有 persistent memory
- 有 skill CRUD
- 有自然语言到策略的完整入口

它告诉我一个很重要的事实：

**真正可用的 AI 金融产品，不是只有模型，也不是只有研究，而是要有可持续交互的产品面。**

我从它那里学到三件事：

1. 交互入口要做成产品，不要只做脚本
2. memory 和 skill 要显式化
3. 本地启动、零配置、MCP 接入，会极大提高可用性

但我也看到它的一个风险：

- 如果自然语言入口太强，而结构化 gate 不够强，就会把系统带回“聊天生成一切”

所以我对 Vibe-Trading 的吸收方式是：

- 学它的产品化
- 学它的 skill / memory / MCP
- 但不学它把自然语言放在过高位置

#### AgenticTrading

我把 AgenticTrading 看成 **agent pool + memory service 型项目**。

它的结构更像：

- data agent pool
- alpha agent pool
- portfolio agent pool
- execution agent pool
- backtest agent pool
- audit agent pool
- memory agent

这个设计说明它在尝试把一个交易系统拆成多个协同工厂，而不是一个大 agent。

我从它身上学到两点：

1. **memory 不应该只是 prompt 附件，而应该是系统级服务**
2. **agent 编排要围绕任务链，而不是围绕某个万能角色**

但我也注意到，这类设计容易过度分布式，最终变成：

- 角色很多
- 责任很多
- 但主控点不清楚

所以我没有照搬它的“agent pool”外观，而是保留它的 **模块分拆思路**，然后把主控权收回到 dashboard 和 workflow registry。

#### LiveTradeBench

我把 LiveTradeBench 看成 **评估平台型项目**，不是生产产品。

它强调的是：

- real-time
- multi-market
- avoiding backtest overfitting
- REST API
- benchmark 多模型比较

它对我的最大影响是提醒我：

**不要把历史回测当成全部证据。**

如果一个系统没有实时、前向、市场演化中的评估能力，就不能说自己真的适合金融场景。

所以我从它这里得到的不是产品结构，而是 **验证哲学**：

- 评估必须区分 benchmark 和 product
- 回测只能说明一部分
- real-time / paper / live 的证据级别要单独管理

#### QuantConnect MCP

我把这类项目看成 **成熟平台的工具化接口样本**。

它最重要的地方不是“有 MCP”，而是：

- 把编译、回测、部署、监控、平仓这些动作变成结构化工具

它告诉我：

**如果一个金融系统要给 LLM 或 Codex 用，最重要的不是能不能聊天，而是动作是否被结构化成工具。**

这直接影响了 EvoQ 后面要做的事：

- dashboard 上的按钮本质上是结构化 tool
- Telegram 的命令本质上也是结构化 tool
- 不是把自由文本丢给系统，而是把动作变成有边界的操作

#### FinanceQA / 其他金融分析 benchmark

这类项目虽然不是交易系统，但我也看了，因为它们回答了一个关键问题：

**LLM 在金融里强在哪里，弱在哪里。**

我从中得到的结论是：

- LLM 可以很强地做解释、总结、抽取、比较、推理
- 但在数值精度、专业约束、会计/估值/规则一致性上，错误成本很高

所以我对 EvoQ 的定位就更清楚了：

- LLM 适合做金融研究和策略生成的上游
- 量化内核必须负责精确、可复现、可约束的下游

### 18.3 我是怎么把这些项目归类的

我最后把这些项目分成五类：

1. **量化底座型**
   - FinRL
   - FinRL-Meta

2. **人类交易桌抽象型**
   - TradingAgents
   - AgenticTrading

3. **产品化工作台型**
   - Vibe-Trading

4. **评估基准型**
   - LiveTradeBench
   - FinanceQA

5. **工具化平台接口型**
   - QuantConnect MCP

这五类分别回答不同问题：

- 底座型回答“怎么把量化跑起来”
- 交易桌型回答“怎么组织协作”
- 产品化型回答“怎么让人真的用起来”
- 评估型回答“怎么判断真假能力”
- 接口型回答“怎么把成熟系统接到 agent 上”

### 18.4 我形成了怎样的个人逻辑

我最后形成的逻辑不是“哪个项目最好”，而是下面这套判断链：

#### 第一层：先看它解决什么问题

- 是研究
- 是回测
- 是实时评估
- 是生产执行
- 是用户工作台

#### 第二层：再看它把什么放在核心

- 数据
- 环境
- 工作流
- 记忆
- 交互
- 风控
- 工具

#### 第三层：再看它的主入口是什么

- CLI
- Web
- MCP
- API
- Chat

#### 第四层：再看它的状态是怎么流转的

- input -> artifact -> gate -> output
- 还是一堆消息和日志

#### 第五层：再看它能不能落地

- 本机能不能启动
- 一台机器能不能跑
- 有没有测试
- 有没有回滚
- 有没有持续运转能力

### 18.5 这套逻辑如何导出 EvoQ 的最终方案

正是因为我这样看这些项目，所以我最后没有选：

- pure chat-first
- pure agent-role-first
- pure benchmark-first
- pure trading-engine-first

而是选了：

**dashboard-first + Telegram gateway + quant-core + LLM research + Codex execution + workflow capability orchestration**

为什么？

- 因为 FinRL / FinRL-Meta 告诉我：底座必须先稳
- 因为 TradingAgents / AgenticTrading 告诉我：协作要按 workflow，不要靠人设
- 因为 Vibe-Trading 告诉我：真正可用的产品需要工作台、memory、skill、MCP 和本地启动能力
- 因为 LiveTradeBench 告诉我：要把验证和生产分开
- 因为 QuantConnect MCP 告诉我：工具化接口比自由文本更可靠
- 因为 FinanceQA 告诉我：LLM 强在金融理解与分析，但不能替代严谨的数值与规则层

### 18.6 一句话总结我的学习结论

我从这些项目学到的不是“照搬一个最像的样子”，而是：

**金融 + LLM + 量化系统要同时满足三件事：**

1. 量化内核要严谨
2. 交互入口要产品化
3. LLM 自进化要被 workflow、artifact 和 gate 约束住

这就是我最终给 EvoQ 的设计逻辑。

### 18.7 参考仓库

- FinRL: https://github.com/AI4Finance-Foundation/FinRL
- FinRL-Meta: https://github.com/AI4Finance-Foundation/FinRL-Meta
- FinRL-Trading / FinRL-X: https://github.com/AI4Finance-Foundation/FinRL-Trading
- TradingAgents: https://github.com/TauricResearch/TradingAgents
- AgenticTrading: https://github.com/Open-Finance-Lab/AgenticTrading
- live-trade-bench: https://github.com/ulab-uiuc/live-trade-bench
- Vibe-Trading: https://github.com/HKUDS/Vibe-Trading
