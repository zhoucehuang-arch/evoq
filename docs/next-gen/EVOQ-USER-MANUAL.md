# EvoQ 使用手册

这份文档只讲怎么用，不讲太多架构。

## 1. 启动方式

### 本机 Windows

在仓库根目录运行：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ops\tools\start_local.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ops\tools\smoke_local.ps1
```

打开：

- Dashboard: `http://127.0.0.1:3000`
- API health: `http://127.0.0.1:8000/healthz`

本机默认使用 `.runtime/evoq-local.db` 作为 SQLite 数据库。

### 单 VPS / 本机 Linux

在 Linux 主机上运行：

```bash
./ops/bin/quickstart-single-vps.sh
./ops/bin/core-smoke.sh
./ops/bin/system-doctor.sh
```

如果你想先生成部署草稿，不马上启动：

```bash
./ops/bin/onboard-single-vps.sh --no-start
```

## 2. 页面分工

- **Workbench**：输入想法或策略设计。
- **Research**：查看 research brief，检查审计状态，推进 ready brief。
- **Strategy**：创建 spec，记录 backtest，记录 paper run，记录 promotion decision。
- **Data**：管理数据源、watchlist、symbol、quote、freshness。
- **Trading**：查看交易准备状态，暂停或恢复 domain。
- **Learning**：查看学习材料、insight、source health。
- **Evolution**：查看系统改进 proposal、canary、promotion。
- **System**：查看 provider、supervisor、config、Codex run。
- **Incidents**：查看 incident 和 pending approvals，并做 approve / reject。

## 3. 从一个想法开始

1. 打开 **Workbench**。
2. 在 `Idea or strategy thought` 输入一句话，例如：
   `研究美股财报后成交量放大是否能形成短期动量因子。`
3. 选择 market 和 kind。
4. 如果你已经有完整设计，展开 advanced fields，补充 thesis、signal、data、evaluation、invalidation。
5. 点击 `Create research brief`。
6. 打开 **Research** 查看结果。

## 4. Research 页面怎么判断

Research brief 有三种重要状态：

- `Ready`：可以推进到 hypothesis。
- `Needs evidence`：还缺证据、PIT、baseline、成本模型、攻击测试等内容。
- `Blocked`：触碰了不允许的路径，例如跳过回测、直接实盘、忽视风险。

如果状态是 `Ready`，点击 `Promote`。

## 5. Strategy 页面怎么用

### 创建 spec

1. 在 **Strategy** 的 `Create spec` 区域选择 hypothesis。
2. 输入 title。
3. 输入 signal logic。
4. 可选填写 risk rules JSON、data requirements、invalidation conditions。
5. 点击 `Create spec`。

### 记录 backtest

1. 选择 strategy spec。
2. 填 sample size。
3. 填 Sharpe、Total return、Max drawdown。
4. 填 cost model、baseline refs、PIT controls 和 input bar ids。
5. 可选填写 artifact path。
6. 点击 `Record backtest`。

系统会根据样本量、Sharpe、收益、回撤、成本、baseline、PIT controls 和 lineage 自动给 gate result。

手工 backtest 只有收益、Sharpe、回撤是不够的；缺少成本模型、baseline 对比、PIT 控制或 bars-to-signal lineage 时，gate 不会通过。

### 运行 factor replay backtest

如果已经在 **Data** 页面导入 historical bars 并生成 factor snapshots，可以在 **Strategy** 页面使用 `Factor replay` 表单直接生成一条 PIT backtest。

最小字段：

- strategy spec
- factor code，默认 `momentum_close_return`
- top N
- cost bps
- slippage bps
- baseline refs
- PIT controls

系统会从 factor snapshots 找到 input bar ids，计算选中 symbol 的等权回放收益、成本后收益、baseline return、excess return、hit ratio、turnover 和 trade count，并把 lineage 写入 backtest metrics。

### 记录 paper run

1. 选择 strategy spec。
2. 填 monitoring days。
3. 填 net PnL、profit factor、max drawdown。
4. 可选填写 capital allocated。
5. 点击 `Record paper run`。

### 记录 promotion decision

1. 选择 strategy spec。
2. 选择 target stage，默认 `production`。
3. 选择 approved / rejected / deferred。
4. 写 rationale。
5. 点击 `Record decision`。

## 6. Data 页面怎么用

### 保存 provider

用于告诉系统某个数据源是否可用、覆盖什么市场、是否支持实时和历史数据。

最小字段：

- provider key
- display name
- market coverage
- health state
- freshness SLA

### 保存 watchlist

用于定义研究和交易观察的 symbol 篮子。

最小字段：

- watchlist key
- display name
- market scope

### 保存 symbol

用于把 symbol 加入 watchlist。

最小字段：

- watchlist key
- symbol
- market
- currency

### 保存 quote

用于记录一条 quote snapshot。真实数据接入完成前，也可以用它验证 freshness 流程。

最小字段：

- provider key
- symbol
- market
- last

### 导入 replay historical bars

用于把本地或手工准备的 OHLCV 历史行情导入 EvoQ。导入后系统会记录 ingestion run、保存 historical bars，并自动用每个 symbol 最新 bar 生成一条 quote snapshot，方便 freshness 页面立刻看到数据状态。

最小字段：

- provider key，默认可用 `local-replay`
- market，默认 `us_equities`
- timeframe，默认 `1d`
- bars JSON array

bars JSON 示例：

```json
[
  {"symbol":"AAPL","bar_start":"2026-05-04T00:00:00Z","open":185,"high":188,"low":184,"close":187,"volume":1200000},
  {"symbol":"AAPL","bar_start":"2026-05-05T00:00:00Z","open":187,"high":190,"low":186,"close":189,"volume":1250000},
  {"symbol":"AAPL","bar_start":"2026-05-06T00:00:00Z","open":189,"high":193,"low":188,"close":192,"volume":1320000}
]
```

### 生成 deterministic factor

用于从已保存的 historical bars 生成确定性因子快照。当前可用路径包括：

- `momentum_close_return`：lookback 内最后一个 close / 第一个 close - 1。
- `reversal_close_return`：momentum 的反向分数。
- `realized_volatility`：close-to-close return 的波动率。
- `dollar_volume_liquidity`：平均 `close * volume`。

最小字段：

- factor code，默认 `momentum_close_return`
- market
- timeframe
- lookback bars，至少 2

生成后可以在 **Factors** 区域看到 value、rank、percentile、lookback 和 input bar lineage。LLM 可以提出因子想法，但这里的因子值由 EvoQ 自己的确定性计算链路产生，不由 LLM 直接决定。

## 7. Trading 和 Incidents 怎么用

### 暂停 domain

在 **Trading** 页面找到 `Domain controls`。

- 点击 `Pause`：创建 active operator override。
- 点击 `Resume`：释放该 domain 的 active overrides。

这适合临时停止 trading 或 evolution，但不删除任何研究和历史状态。

### 数据 stale 门禁

Execution readiness 会检查最新 quote snapshot。如果系统发现已有行情数据但最新 quote 超过 48 小时，会阻断 trading readiness；超过 24 小时会提示 degraded warning。没有 quote 的空环境不会被这个门禁误伤，方便本地初始化。

### Live readiness report-only drill

API 提供 `GET /api/v1/execution/live-readiness-report`。它只返回 readiness 报告，不会创建订单，也不会触发 broker 下单。实盘前必须先看这个报告，再走显式审批和受限 live gate。

### 审批

在 **Incidents** 页面找到 `Pending approvals`。

- 点击 `Approve`：记录批准。
- 点击 `Reject`：记录拒绝。

高风险动作应该走审批，不应该由 LLM 或后台任务直接绕过。

## 8. 验证方式

每次重要修改后至少运行：

```powershell
npm run build
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ops\tools\run_tests.ps1 -q
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ops\tools\smoke_local.ps1
```

其中：

- `npm run build` 验证 dashboard 能构建。
- `run_tests.ps1` 验证后端和服务逻辑。
- `smoke_local.ps1` 验证本机运行中的 API 和 dashboard 页面。

## 9. 重要边界

- LLM 不直接交易。
- Dashboard 是主操作界面。
- Telegram 只保留提醒、轻审批和紧急入口。
- Codex 用于工程实现、工具创建、测试和系统进化落地。
- 金融数据和证据链由 EvoQ 自己的 provider、watchlist、quote、freshness、research artifact 流程负责。
- 实盘之前必须经过 backtest、paper、risk、approval 和 broker sync。
