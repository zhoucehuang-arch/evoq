# EvoQ

[English README](README.md)

EvoQ 是一个 **Dashboard 优先** 的量化研究与 paper-trading 运行时：LLM 负责研究、解释、挑战和诊断；确定性量化链路负责数据、因子、回测、风险和执行门禁。

> 这不是金融建议，也不是“让 LLM 直接下单”的项目。第一次使用请保持 paper 模式，先验证数据、因子、回测、paper、风控和审批。

## 一句话理解

EvoQ 想解决的是：如何让“金融 + 量化 + 大模型”的系统长期运行，同时仍然可审计、可暂停、可回滚、可解释。

它的核心分工是：

- **Dashboard 是主操作界面**：Data、Research、Strategy、Trading、Learning、Evolution、System、Incidents 都在 dashboard 上看和操作。
- **量化核心是确定性的**：market data、historical bars、factor snapshots、PIT replay backtest、成本、baseline、lineage 都由系统计算和记录。
- **LLM 是研究和治理助手**：它可以提出想法、总结证据、挑战假设、诊断失败，但不能绕过回测、paper、风险和审批。
- **交易路径 paper-first**：没有干净的 market session、broker snapshot、reconciliation、freshness、promotion 和 approval，不应该进入 capital-facing 执行。

## 当前能做什么

| 模块 | 当前能力 |
|---|---|
| 本地运行 | Windows PowerShell 和 Linux/macOS Bash 都可一键启动 API + Dashboard，并可 smoke 验证 |
| Dashboard | Workbench、Research、Strategy、Data、Trading、Learning、Evolution、System、Incidents |
| 市场数据 | provider、watchlist、quote、freshness、local replay bars、historical bars API |
| 因子 | 10 个内置因子 + `custom_linear_combo`：momentum、reversal、volatility、liquidity、intraday、overnight、range、volume trend、risk-adjusted momentum、liquidity-adjusted momentum |
| 回测 | 从 factor snapshots 运行 PIT replay backtest，包含成本、滑点、baseline、lineage、equity curve |
| 策略生命周期 | research brief -> hypothesis -> spec -> backtest -> paper run -> promotion / withdrawal |
| 执行门禁 | market session、broker snapshot、reconciliation、provider incident、override、stale quote blocking |
| 部署文档 | 单 VPS 优先，后续 Core/Worker 扩展，backup/restore，break-glass runbook |

## 和同类开源项目的关系

EvoQ 借鉴了几类优秀项目的组织方式：

- 类似 Qlib，把量化研究看成从数据到信号、回测、上线的 pipeline。
- 类似 OpenBB，重视研究入口和可用的操作界面，而不只是脚本。
- 类似 FinGPT 方向，把 LLM 放在金融研究和理解层，但不让 LLM 直接控制交易事实。

EvoQ 的不同点是：它更关注 owner 可以长期运行的 **dashboard-first、paper-first、quant-first、LLM-governed** 产品形态。

## 从 GitHub 到本地 Dashboard

这是第一次使用 EvoQ 时最推荐的路径：先在本地跑起来，使用本地 SQLite 和 paper/simulated 环境，不需要券商密钥，也不会进入实盘交易。最快的数据到回测路径见：[First 5 Minutes](docs/next-gen/FIRST-5-MINUTES-TUTORIAL.md)。

### 1. 先安装基础工具

请先安装：

- Git：<https://git-scm.com/downloads>
- Python 3.11 或更新版本：<https://www.python.org/downloads/>
- Node.js 20 或更新版本：<https://nodejs.org/>
- Shell：Windows PowerShell、PowerShell 7+，或 Linux/macOS Bash

打开一个新的终端，确认命令可用：

```bash
git --version
python --version
node --version
npm --version
```

### 2. 下载代码

方式 A：用 Git 克隆：

```powershell
git clone https://github.com/zhoucehuang-arch/evoq.git
cd evoq
```

方式 B：从 GitHub 下载 ZIP：

1. 在 GitHub 页面点击 **Code** -> **Download ZIP**。
2. 解压 ZIP。
3. 在解压后的项目文件夹里打开 PowerShell。

后面的命令都假设你已经在仓库根目录，也就是能看到 `README.md`、`src`、`apps`、`ops` 的那个目录。

### 3. 安装依赖

安装 Python 后端依赖：

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

安装 Dashboard 前端依赖：

```powershell
cd apps\dashboard-web
npm ci
cd ..\..
```

### 4. 启动本地运行时

Linux/macOS：

```bash
./ops/tools/start_local.sh
```

Windows：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ops\tools\start_local.ps1
```

打开：

- Dashboard：`http://127.0.0.1:3000`
- API health：`http://127.0.0.1:8000/healthz`

默认使用本地 SQLite 数据库：`.runtime/evoq-local.db`。

### 5. 验证是否真的可用

Linux/macOS：

```bash
./ops/tools/smoke_local.sh
```

Windows：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ops\tools\smoke_local.ps1
```

看到下面结果，说明本地 API、Dashboard、Data、Strategy、Trading readiness、Approvals 和各个页面都能正常访问：

```text
EvoQ local smoke passed.
```

## 第一次应该怎么玩

建议按这个顺序理解：

1. 把 `sample-data/ohlcv/us-local-replay.json` 导入 `/api/v1/market-data/replay-bars`。
2. 在 **Data** 页面查看 `local-replay` historical bars。
3. 在 **Data** 页面生成 factor snapshots。
4. 在 **Workbench / Research** 创建 research brief。
5. 在 **Research** 查看 brief 是 `Ready`、`Needs evidence` 还是 `Blocked`。
6. 在 **Strategy** 把 ready brief 推进到 hypothesis，再创建 deterministic spec。
7. 在 **Strategy** 使用 `Factor replay` 生成 PIT backtest。
8. 在 **Strategy** 记录 paper run 和 promotion decision。
9. 在 **Trading** 查看 execution readiness。
10. 在 **Incidents** 处理 approvals，并在需要时 pause/resume。

可直接执行的 5 分钟流程见：[First 5 Minutes](docs/next-gen/FIRST-5-MINUTES-TUTORIAL.md)。更适合新手的说明见：[EVOQ-BEGINNER-README.md](docs/next-gen/EVOQ-BEGINNER-README.md)。

## 安全边界

- LLM 不直接交易。
- Backtest 缺少成本、baseline、PIT controls、input-bar lineage 时不能通过 gate。
- 已有行情数据但 quote 超过 48 小时，会阻断 execution readiness。
- live readiness endpoint 只生成报告，不下单。
- broker credentials 应该留在 Core，不放在 Worker。
- 实盘前必须先有 paper evidence、risk readiness 和 owner approval。

## 架构简图

```mermaid
flowchart LR
  Owner[Owner] --> Dashboard[Dashboard]
  Owner --> Gateway[Optional light gateway]
  Dashboard --> API[FastAPI Core]
  Gateway --> API
  API --> DB[(Runtime DB)]
  API --> Data[Market Data + Historical Bars]
  API --> Factors[Deterministic Factor Engine]
  Factors --> Backtests[PIT Replay Backtests]
  Backtests --> Strategy[Strategy Lifecycle]
  Strategy --> Risk[Risk + Readiness Gates]
  Risk --> Paper[Paper Broker / Sim]
  API --> Codex[Codex Worker Queue]
```

设计规则：**一个权威 Core，一个运行时数据库，确定性金融逻辑，LLM 只做研究/挑战/治理辅助。**

## 仓库结构

| 路径 | 作用 |
|---|---|
| `src/quant_evo_nextgen` | 后端 API、contracts、services、DB models、控制面 |
| `apps/dashboard-web` | Next.js Dashboard |
| `alembic/versions` | 数据库迁移 |
| `ops/tools` | 本地 PowerShell/Bash 启动、测试、smoke 工具 |
| `sample-data` | 首次教程使用的内置 local replay OHLCV 数据 |
| `ops/production` | Core/Worker 部署示例 |
| `docs/next-gen` | 当前产品文档、用户手册、部署 runbook、评审 |
| `workspace` | 仓库内 memory、knowledge、strategies、trading artifacts |
| `legacy/original-system` | 早期系统归档 |
| `tests` | 服务和 API 回归测试 |

## 常用验证命令

统一 task runner：

```bash
make lint test build-dashboard audit
```

Windows 明确命令：

```powershell
cd apps\dashboard-web
npm run build
cd ..\..
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ops\tools\run_tests.ps1 -q
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ops\tools\smoke_local.ps1
```

Linux/macOS 等价命令：

```bash
cd apps/dashboard-web
npm run build
cd ../..
./ops/tools/run_tests.sh -q
./ops/tools/smoke_local.sh
```

当前本地验证结果：

- Dashboard build：通过
- 后端/服务测试：`158 passed`
- Local smoke：通过

## 部署入口

首次建议：

- 一台 VPS
- `single_vps_compact`
- 本地 Postgres
- paper 模式
- Dashboard 主操作
- 可选 chat gateway 只做轻提醒和审批入口

阅读顺序：

1. [GitHub to VPS Deployment Guide](docs/next-gen/GITHUB-TO-VPS-DEPLOYMENT.md)
2. [VPS Deployment Runbook](docs/next-gen/VPS-DEPLOYMENT-RUNBOOK.md)
3. [First Paper Run Checklist](docs/next-gen/FIRST-PAPER-RUN-CHECKLIST.md)
4. [Break Glass Runbook](docs/next-gen/BREAK-GLASS-RUNBOOK.md)

## 文档地图

| 目标 | 文档 |
|---|---|
| 新手理解 | [Beginner README](docs/next-gen/EVOQ-BEGINNER-README.md) |
| 日常使用 | [User Manual](docs/next-gen/EVOQ-USER-MANUAL.md) |
| 产品定位 | [Product Overview](docs/next-gen/PRODUCT-OVERVIEW.md) |
| 当前计划和状态 | [Complete Delivery Plan](docs/next-gen/EVOQ-COMPLETE-DELIVERY-PLAN.md) |
| 全部文档 | [Docs Index](docs/next-gen/README.md) |
| 环境变量 | [Environment Parameters](docs/env-params.md) |
| 安全 | [Security Policy](SECURITY.md) |
| 贡献 | [Contributing Guide](CONTRIBUTING.md) |

## License

MIT。见 [LICENSE](LICENSE)。
