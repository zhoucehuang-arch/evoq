# EvoQ 针对 Hermes Review 的补强计划与执行记录

日期：2026-05-08

## 1. 设计原则

本轮修改保持 EvoQ 的核心定位不变：

- Dashboard 是主交互入口。
- Telegram 只保留轻审批、提醒和紧急控制。
- LLM 不直接充当交易引擎。
- LLM 负责提出研究方向、解释证据、挑战假设。
- EvoQ 自己负责数据、因子、回测、paper、风控、账本和审批边界。
- Codex 负责工程实现、工具创建、测试、文档和系统进化落地。

Hermes review 提到的 5 个问题是正确方向，但不能用“多接几个 agent”解决。EvoQ 应该把这些能力沉到底层服务里，让 dashboard 调用的是可审计、可复用、可测试的金融工程能力。

## 2. 对五个问题的判断

### 2.1 内置因子太少

原状态只有 4 个确定性因子，适合证明 paper trading 流程，但不适合长期 alpha 发掘。

本轮方案：

- 把因子计算从 `MarketDataService` 抽成独立 `factor_engine`。
- 保留原有 4 个因子。
- 新增 intraday、gap、range、volume trend、risk-adjusted momentum、liquidity-adjusted momentum。
- 新增 `custom_linear_combo`，允许用户或 LLM 提出线性组合公式。
- 公式只允许白名单组件和基本四则运算，避免 LLM 注入任意代码。
- 因子 snapshot 写入 components、formula、input bars 和 decay 状态。

### 2.2 成本模型不够真实

原状态主要是 cost bps + slippage bps。它能做门槛检查，但不能描述真实交易摩擦。

本轮方案：

- 新增 `CostModelConfig.apply_trade(...)`。
- 支持 fixed bps。
- 支持 commission bps。
- 支持 spread bps。
- 支持 participation-rate slippage。
- 支持 square-root market impact。
- factor replay backtest 会生成 per-symbol 成本分解，并写入 metrics。

这不是完整 Almgren-Chriss 执行优化器，但已经把成本模型从“单一扣点”升级为可扩展的市场冲击接口。

### 2.3 缺少 LLM 记忆/反思层

EvoQ 已有 documents、evidence、insights、source health 和 quarantine，但缺少把策略实验结果变成长周期经验的机制。

本轮方案：

- 新增 `ingest_strategy_experience_reflections()`。
- backtest 和 paper run 的结果会沉淀为 durable learning document。
- gate notes、统计失败、成本问题、paper 表现会变成 evidence。
- 后续由已有 learning synthesis 生成 insight。
- supervisor 的 research-distillation loop 会自动尝试摄取策略经验反思。

这让系统记住“哪些策略为什么失败、为什么通过、下次要验证什么”，而不是只记住外部研究材料。

### 2.4 缺少统计检验框架

只看 Sharpe、return、drawdown 容易产生回测幻觉，尤其是多次试验和样本不足时。

本轮方案：

- 新增 `statistical_validation`。
- 自动生成 `statistical_validation` metrics。
- 检查 sample size。
- 计算 deflated Sharpe confidence 的工程近似。
- 计算 PBO proxy。
- 检查 OOS return。
- 检查 walk-forward pass rate。
- backtest gate 只有在治理证据、统计门槛和安全检查都通过时才会通过。

注意：当前 DSR/PBO 是工程近似门槛，不是论文级完整统计包。它的价值是先把“多重检验风险”和“OOS 风险”纳入产品路径，后续可以替换为更严格的数学实现。

### 2.5 缺少安全压力测试

EvoQ 已有 doctor 和一些研究 brief blocker，但缺少专门面向 LLM 交易系统攻击面的规则。

本轮方案：

- 新增 `adversarial` 检查模块。
- 覆盖 market intelligence、strategy formulation、portfolio ledger、trade execution、tool hijacking 五类风险。
- research brief 和 backtest metrics 都会被扫描。
- 出现绕过审批、直接实盘、篡改账本、伪造来源、泄露密钥等文本时，不能通过 gate。

## 3. Dashboard 交互变化

### Data 页面

- factor code 下拉菜单新增更多因子。
- 支持 `custom_linear_combo`。
- 新增 custom expression 输入框。
- 因子结果继续显示 value、rank、percentile、lookback 和 input lineage。

### Strategy 页面

- 手工 backtest 和 factor replay 都增加更细的成本字段：
  - commission bps
  - impact coefficient
  - participation slippage bps
  - trade notional
- 回测结果会自动带上 statistical validation 和 adversarial validation。

## 4. 已执行的代码落点

- `src/quant_evo_nextgen/services/factor_engine.py`
- `src/quant_evo_nextgen/services/cost_models.py`
- `src/quant_evo_nextgen/services/statistical_validation.py`
- `src/quant_evo_nextgen/services/adversarial.py`
- `src/quant_evo_nextgen/services/market_data.py`
- `src/quant_evo_nextgen/services/strategy_lab.py`
- `src/quant_evo_nextgen/services/learning.py`
- `src/quant_evo_nextgen/services/supervisor.py`
- `src/quant_evo_nextgen/contracts/state.py`
- `apps/dashboard-web/app/actions.ts`
- `apps/dashboard-web/app/data/page.tsx`
- `apps/dashboard-web/app/strategy/page.tsx`
- `tests/test_market_data_service.py`
- `tests/test_strategy_lab.py`
- `tests/test_learning.py`

## 5. 后续计划

下一阶段不应该推翻本轮结构，而是在这 5 个内核上继续深化：

1. 把 custom factor 从线性表达式扩展为受控 factor recipe。
2. 引入更正式的 purged walk-forward 和 embargo split。
3. 把 DSR/PBO 从工程近似升级为完整统计模块。
4. 为成本模型增加资产类别差异，例如股票、ETF、期权、crypto。
5. 在 dashboard 增加 factor catalog、validation detail 和 reflection timeline。
6. 把安全压力测试变成可从 dashboard 触发的 drill。
7. 将 strategy experience reflection 和 evolution proposal 更紧密连接，让失败经验自动生成可审查的改进任务。

## 6. 当前结论

Hermes review 的五个不足已经被转化为 EvoQ 自己的产品能力，而不是临时补丁。

这轮修改后，EvoQ 的方向更清晰：入口仍然简单，但内核开始具备专业量化系统应有的因子、成本、统计、反思和安全边界。
