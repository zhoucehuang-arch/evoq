# EvoQ 新手说明

这是一份给第一次接触 EvoQ 的人看的简明说明。

## 0. 第一次怎么把它跑起来

如果你是从 GitHub 第一次看到这个项目，不要直接从启动命令开始。正确顺序是：

1. 安装 Git、Python 3.11+、Node.js 20+ 和 PowerShell。
2. 下载代码：
   ```powershell
   git clone https://github.com/zhoucehuang-arch/evoq.git
   cd evoq
   ```
   如果不用 Git，也可以在 GitHub 页面点 **Code** -> **Download ZIP**，解压后在项目目录打开 PowerShell。
3. 安装后端依赖：
   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -e ".[dev]"
   ```
4. 安装 Dashboard 依赖：
   ```powershell
   cd apps\dashboard-web
   npm ci
   cd ..\..
   ```
5. 启动本地系统：
   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ops\tools\start_local.ps1
   ```
6. 打开 Dashboard：`http://127.0.0.1:3000`。
7. 验证：
   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ops\tools\smoke_local.ps1
   ```

看到 `EvoQ local smoke passed.` 才说明本地入口真的跑通了。

## 1. EvoQ 是什么

EvoQ 是一个可以在本机或单 VPS 上运行的量化研究与交易准备系统。

你可以把它理解成四层：

- **量化核心**：负责数据、因子、回测、paper、风控、对账
- **LLM 研究层**：负责帮你找思路、做研究、整理证据、提出质疑
- **Codex 执行层**：负责把想法变成代码、工具、skill、测试、文档
- **Dashboard 工作台**：负责你真正的主要操作

另外还有一个很轻的 **Telegram 入口**，只做提醒、轻审批和紧急动作。

## 2. 它和普通聊天机器人有什么不同

它不是一个只会聊天的模型。

它的核心特点是：

- 所有重要动作都要经过结构化流程
- 所有研究结果都要留下证据
- 所有策略都要经过回测和 paper
- 所有高风险动作都要经过审批和记录
- 所有系统改进都要可测试、可回滚

换句话说，它不是“问一句就直接交易”，而是“想法 -> 研究 -> 证据 -> 审核 -> 运行”。

## 3. 你能用它做什么

### 3.1 提出研究想法

你可以输入一个主题，比如：

- 某个行业是否有机会
- 某种因子是否值得研究
- 某个策略逻辑是否合理

系统会帮你整理成 research brief，然后去做证据收集和结构化分析。

### 3.2 做因子和策略研究

系统会把研究想法继续推进成：

- 因子候选
- 信号候选
- 策略草案
- 需要补充的证据

### 3.3 做回测和证据审查

系统会检查：

- 是否有 point-in-time 问题
- 是否有泄漏风险
- 成本假设是否合理
- 和 baseline 比较后是否还有价值

### 3.4 跑 paper

通过回测后，策略可以进入 paper 观察。

paper 里会看：

- 持仓
- 订单
- 账户
- 对账
- 风险
- 停止条件

### 3.5 管理系统进化

你可以让系统提出改进想法，也可以让它自己提出优化建议。

这些改进不会直接生效，而是会进入：

- proposal
- Codex task
- test
- review
- canary
- rollback / promote

## 4. 你应该主要怎么操作

### 4.1 主工作台是 dashboard

你平时主要看 dashboard。

dashboard 会告诉你：

- 系统现在是否健康
- 哪些任务在进行
- 哪些项目被卡住
- 哪些东西可以继续推进
- 哪些东西需要你审批

### 4.1.1 简单输入和复杂输入都支持

入口要简单，但能力不能浅。

所以 EvoQ 的工作方式是：

- 你可以只输入一句简单想法
- 也可以输入完整策略设计
- 系统会先把它变成结构化 research brief
- 后续再进入证据、因子、回测、paper、风险流程

也就是说，简单入口不会牺牲专业内核。

### 4.2 Telegram 只做轻操作

Telegram 适合做：

- 看状态
- 收提醒
- 轻审批
- 暂停
- 恢复
- 紧急处置

复杂研究、复杂比较、详细审查，都回到 dashboard 做。

### 4.3 Codex 负责“做事”

当你想让系统改进时，LLM 会先给想法，Codex 会负责实现。

也就是说：

- 你给方向
- LLM 给研究和判断
- Codex 写代码、补测试、补文档

这里的边界是：

- 金融信息获取和金融证据链由 EvoQ 自己的数据与研究流程负责
- Codex 主要发挥工程工具优势，用来实现结构优化、工具创建、skill 复用、测试和自进化落地

## 5. 系统的基本架构

```text
你
  -> Dashboard / Telegram
  -> Workflow / Artifact
  -> LLM Research
  -> Codex Implementation
  -> Quant Core
  -> Backtest / Paper / Risk
```

这里最重要的是：

- dashboard 是主要界面
- Telegram 是轻入口
- 量化核心是事实层
- LLM 是研究层
- Codex 是实现层

## 6. 常见任务怎么走

### 任务 A：我有一个投资想法

流程：

1. 在 dashboard 提交想法
2. 系统生成 research brief
3. 系统收集证据和反例
4. 你在 dashboard 审核
5. 通过后再进入 hypothesis / strategy

### 任务 B：我想研究一个因子

流程：

1. 提出因子想法
2. 系统生成 factor candidate
3. 系统检查数据、稳定性、相关性
4. 进入 backtest
5. 看证据后决定是否保留

### 任务 C：我想看一个策略能不能继续做

流程：

1. 打开 Backtest Evidence
2. 看成本、baseline、泄漏、回撤
3. 如果证据不足，直接 reject
4. 如果证据够，再进 paper

### 任务 D：我想让系统自己优化

流程：

1. LLM 提出改进建议
2. 系统转成 proposal
3. Codex 实现
4. 自动补测试
5. dashboard 审核
6. 通过后才上线

## 7. 你需要记住的一个原则

**LLM 负责想法，Codex 负责实现，dashboard 负责主操作，Telegram 负责轻入口，量化核心负责事实和边界。**

这是 EvoQ 的核心设计。

## 8. 当前 dashboard 可以完成的主流程

当前 dashboard 已经从展示页推进成可操作工作台。

你现在可以按下面的顺序使用：

1. 在 **Workbench** 页面输入一个简单想法，或者展开高级字段输入完整策略设计。
2. 系统创建一个结构化的 **research brief**。
3. 在 **Research** 页面查看这个 brief 的审计状态。
4. 如果状态是 `Ready`，可以从 dashboard 直接把它推进成 strategy hypothesis。
5. 在 **Strategy** 页面把 hypothesis 变成 deterministic strategy spec。
6. 在 **Strategy** 页面记录 backtest 结果。
7. 在 **Strategy** 页面记录 paper run 结果。
8. 在 **Strategy** 页面记录 promotion decision。
9. 在 **Data** 页面管理 provider、watchlist、symbol、quote、historical bars、factor snapshots 和 freshness。
10. 如需离线验证数据链路，在 **Data** 页面导入 `local-replay` historical bars。
11. 如需第一条确定性量化信号，在 **Data** 页面生成 `momentum_close_return` factor snapshots。
12. 在 **Strategy** 页面使用 `Factor replay` 从 factor snapshots 自动生成 PIT backtest。
13. 在 **Trading** 页面确认 execution readiness；如果已有 quote 但数据超过 48 小时，系统会阻断 readiness。
14. 在 **Trading** 页面暂停或恢复 trading / evolution 等 domain。
15. 在 **Incidents** 页面处理 pending approvals。

如果 research brief 是 `Needs evidence`，说明还缺少数据、PIT 控制、baseline、成本模型或攻击测试等材料。

如果 research brief 是 `Blocked`，说明它触碰了跳过回测、直接实盘、忽视风险等禁区，需要重写。

这套流程的意义是：你不需要一开始就懂完整量化流程，只需要先把想法放进去；但系统内部仍然会按专业量化研究的方式检查证据、风控和可验证性。
