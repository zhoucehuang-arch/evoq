# 当前交付状态

## 日期

2026-05-08

## 摘要

EvoQ 当前已经具备 dashboard-first 的本地 paper-mode 操作能力，并保留单 VPS 部署路径。

在上一阶段的市场数据、dashboard、执行准备和部署基础上，本轮针对 Hermes review 提到的 5 个核心缺口做了补强：

- 因子层从 4 个写死因子升级为因子注册表。
- 支持受控自定义线性组合因子。
- factor snapshot 记录公式、组件、input bars 和 decay 状态。
- factor replay backtest 引入更高保真的成本/冲击模型。
- backtest gate 增加统计显著性验证。
- learning 层增加策略实验经验反思摄取。
- research brief 和 backtest evidence 增加 LLM 交易系统攻击面扫描。

## 仓库内已经可用

- Dashboard 主流程：Workbench、Research、Strategy、Data、Trading、Learning、Evolution、System、Incidents。
- 本地 Windows 启动和 smoke 工具：`ops/tools`。
- 数据源注册、watchlist、quote snapshot、freshness、replay bars、historical bars。
- 确定性因子：
  - `momentum_close_return`
  - `reversal_close_return`
  - `realized_volatility`
  - `dollar_volume_liquidity`
  - `intraday_return`
  - `overnight_gap`
  - `range_position`
  - `volume_trend`
  - `risk_adjusted_momentum`
  - `liquidity_adjusted_momentum`
  - `custom_linear_combo`
- PIT factor replay backtest。
- 成本模型字段：
  - fixed bps
  - commission bps
  - spread bps
  - participation-rate slippage
  - square-root market impact
- backtest gate：
  - cost model
  - baseline
  - PIT controls
  - input-bar lineage
  - DSR/PBO 工程近似
  - OOS / walk-forward 字段
  - adversarial validation
- learning：
  - research document ingestion
  - insight synthesis
  - quarantine
  - strategy experience reflection ingestion
- execution readiness：
  - market session
  - broker snapshot
  - reconciliation
  - provider incidents
  - operator overrides
  - stale quote blocking
- report-only live-readiness endpoint，不会下单。
- Codex-backed execution fabric，用于工程实现、测试、文档和系统进化。
- 单 VPS 部署文档、Core/Worker 扩展文档、backup/restore/break-glass 文档。

## 已验证

本轮提交前已通过：

- `npm run build` in `apps/dashboard-web`，11 个 dashboard route 构建通过。
- `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ops\tools\run_tests.ps1 -q`，139 passed。
- fresh Alembic upgrade 到 `20260508_0018`。
- `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ops\tools\smoke_local.ps1`，health、doctor、strategy、market data、live readiness、approvals 和所有 dashboard 页面通过。

## 仍需在真实 VPS 验证

- 目标 Linux 主机上的 Core 部署。
- 如果采用两节点结构，Worker 部署。
- 真实 secrets 和 relay 配置。
- Core/Worker 私网连通性。
- 真实 broker sync。
- restore drill 和 break-glass rehearsal。
- systemd 重启行为。
- 真实 paper-mode broker 行为。

## 仍然保留的边界

- 默认不是 live trading。
- LLM 不能绕过 quant、paper、risk、approval gate。
- backtest 不能只靠 Sharpe/return/drawdown 通过。
- 统计验证当前是工程门槛，不是完整论文级统计包。
- 成本模型已经支持冲击项，但还不是完整执行优化器。
- CN live broker execution 没有作为默认路径交付。
- stale market data 会阻断 execution readiness。

## 实用结论

EvoQ 现在不是单纯的 dashboard 展示项目，也不是聊天机器人式投资助手。

它已经开始具备“LLM 提出想法 + EvoQ 确定性量化验证 + Codex 工程落地 + dashboard 操作治理”的产品形态。

接下来最重要的是继续把真实数据源、真实 paper broker、统计验证细节和 dashboard drill 做深，而不是改变系统方向。
