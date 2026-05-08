# EvoQ 七维复查与产品化整改总计划

日期：2026-05-08  
复查基线：`35d6c7ec7625e4493eeb111d98fe94c124264feb`

## 1. 总结判断

EvoQ 的核心方向仍然是对的：Dashboard-first、paper-first、quant-first、LLM-governed 这条主线比普通 “AI trading bot” 更成熟。它的问题不是缺少架构野心，而是产品化闭环没有跟上架构复杂度。

当前最准确的定位是：

> 一个方向正确、治理意识强、已有真实工程骨架的高级原型；但它还不能被当成成熟开源产品或可长期无人值守生产系统。

整改优先级不应该继续堆新能力，而应该先把“能跑、能懂、能测、能排障、能维护”补齐。

## 1.1 本轮实施状态

本轮已按该计划完成第一轮产品化整改：

- P0：结构化日志、request id、关键 gate 事件日志、Alpaca 只读请求 retry/backoff、Codex transient failure 分类与退避重试、后端/前端安全审计。
- P1：移除 PowerShell 作者机器路径，新增 Linux/macOS Bash 启动/测试/smoke，新增 sample OHLCV 数据和 5 分钟教程，更新 README 因子能力。
- P2：新增 ruff、mypy 基础配置、pre-commit、Makefile、CI lint/audit/OpenAPI/Alembic 检查，补 `factor_engine`、`statistical_validation`、`execution_readiness`、`dashboard`、`skill_catalog`、`deploy_fields` 独立测试和共享 fixture。
- P3：新增 Docker CPU/memory/log rotation 默认值，生产 compose 核心服务只读挂载，备份保留和 runtime data retention 脚本。
- 文档：收敛新用户路径，明确 optional chat gateway 叙事，补 OpenAPI export、备份/保留策略和 VPS 资源控制说明。

验证结果：`ruff` 通过，完整后端测试 `158 passed`，Dashboard build 通过，`npm audit --omit=dev` 0 漏洞，`pip-audit` 无已知漏洞，Bash local start + smoke 已通过。Docker CLI 在当前环境不可用，已做 compose YAML 解析验证。

## 2. 复查结论校准

Hermes 七维报告的大方向成立，但有几处需要校准：

- 配置项不是 76 个，本次按 `Settings` 字段复核为 66 个；问题仍然成立，因为所有配置都集中在一个类里。
- `factor_engine.py`、`statistical_validation.py`、`execution_readiness.py` 不是完全无覆盖。它们分别被 `test_market_data_service.py`、`test_strategy_lab.py`、`test_execution_service.py` 间接覆盖；真正的问题是缺少独立单元测试、边界测试和共享 fixture。
- 源码里的 TODO/FIXME 不多；本轮已删除 `.github/workflows/daily-report.yml` 和 `validate-strategy.yml` 这两个 placeholder CI 工作流，避免把未落地流程伪装成可用自动化。
- `main.py` 确实缺少业务 logging，但 runner 层已有普通 logging。问题不是“全系统零日志”，而是缺结构化业务事件、request id、gate decision log 和外部调用失败记录。
- 生产 compose 已有 postgres/core-api healthcheck；问题在资源限制、日志轮转、备份保留和 immutable image 部署不足。

这些校准不会降低问题严重性，只是让整改目标更准确。

## 3. 已核实的问题清单

### 3.1 上手体验

成立的问题：

- 本地路径偏 Windows/PowerShell，README 把 PowerShell 作为主路径。
- `ops/tools/start_local.ps1` 和 `ops/tools/run_tests.ps1` 都包含作者本机 Python 路径。
- `ops/tools/` 没有 Linux/macOS 等价 `.sh` 脚本。
- `docker-compose.yml` 的 dashboard 放在 `local-dashboard` profile 下，默认 `docker compose up` 看不到 dashboard。
- 没有内置 OHLCV sample data；README 要求用户自己粘贴 historical bars。
- README 信息密度高，新用户无法 5 分钟获得正反馈。

额外发现：

- 默认 `docker compose up` 会启动 backend、supervisor、codex fabric runner，但不会启动最该让新用户看到的 dashboard；默认体验的服务选择和产品叙事不一致。
- `workspace/` 已提交 99 个历史 artifact，容易让新用户误解哪些是 sample、哪些是 runtime state、哪些是作者历史实验。

### 3.2 代码质量与架构

成立的问题：

- 大文件集中度过高：
  - `execution.py`：4426 行
  - `state_store.py`：2130 行
  - `dashboard.py`：1472 行
  - `contracts/state.py`：1430 行
  - `api/main.py`：814 行
- 核心服务 public/private 方法很多，但缺少 docstring。复核结果：
  - `execution.py`：107 个函数，0 docstring
  - `state_store.py`：62 个函数，0 docstring
  - `dashboard.py`：54 个函数，0 docstring
  - `api/main.py`：113 个函数，0 docstring
  - `strategy_lab.py`：37 个函数，0 docstring
  - `learning.py`：28 个函数，0 docstring
- 没有 ruff、black、mypy、isort、pre-commit、Makefile/justfile。
- 依赖约束采用 `<next_minor` 风格，安全升级和兼容升级会更频繁撞到范围限制。
- `Settings` 聚合了数据库、broker、Discord、OpenAI、Codex、dashboard、部署拓扑等配置，边界过粗。

额外发现：

- `ruff check src tests alembic` 报 9 个问题，其中 `execution.py` 存在 `remaining_quantity`、`event_price`、`multiplier` 未定义引用。该代码位于 `return` 后不可达，但说明大文件里已经混入死代码。
- `api/main.py` 把应用创建、依赖装配、中间件、所有路由都放在一个文件，后续 route ownership 会很难拆分。
- `contracts/state.py` 过大，Pydantic schema 没按 domain 拆分，影响 API 合约可读性。

### 3.3 测试与可靠性

成立的问题：

- 测试总量不低：23 个测试文件，约 8592 行，且大量使用真实 SQLite。
- 没有 `tests/conftest.py`。
- 没有固定 sample fixture 文件，测试数据多在测试代码内构造。
- 缺独立测试文件：
  - `test_factor_engine.py`
  - `test_statistical_validation.py`
  - `test_execution_readiness.py`
  - `test_dashboard_service.py`
  - `test_skill_catalog.py`
  - `test_deploy_fields.py`

额外发现：

- 全量 `pytest -q` 本地约 6 分钟，适合作为完整回归，不适合作为唯一 PR 快速反馈。
- CI 没跑 ruff、type check、npm audit、pip-audit、Alembic 空库升级。
- 当前测试覆盖了不少 happy path 和关键 service 行为，但静态检查发现的不可达死代码没有被测试/CI 拦住。

### 3.4 文档质量

成立的问题：

- 文档数量多，`docs/next-gen` 下约 40 个文档，信息架构过载。
- README 因子表过期：README 写 4 个因子，代码实际支持 10 个内置因子 + `custom_linear_combo`。
- Discord/Telegram/light gateway 叙事不统一。
- Beginner Guide、User Manual、README 有明显重叠。
- API 文档主要依赖 FastAPI Swagger，没有导出的稳定 OpenAPI artifact。

额外发现：

- 文档索引已有 “Read By Goal”，但 canonical/current/historical 的边界仍不够硬，很多历史 Discord-first 文档仍会干扰用户判断。
- 文档中“当前本地验证结果”曾写 `135 passed`，本轮整改后完整测试为 `158 passed`。
- `EVOQ-HERMES-REVIEW-IMPLEMENTATION-PLAN.md` 只覆盖上一轮 5 个能力问题，不覆盖这次 7 维产品化问题，容易让读者误以为 Hermes 问题已经全部关闭。

### 3.5 生产就绪度

成立的问题：

- API/服务层缺结构化业务日志。
- 外部调用缺统一 retry/backoff/rate-limit：
  - Alpaca HTTP adapter 有 timeout，但无 retry/backoff。
  - Codex runner/fabric 有队列和 attempt 状态，但没有统一 transient failure 分类。
  - acquisition probe 有 timeout，但无统一 resilience policy。
- Docker 无 CPU/memory limit。
- backup 脚本有创建，无自动 retention/rotation。
- 数据保留策略缺失。

额外发现：

- `alembic upgrade head` 从空 SQLite 可通过，但迁移日志每行重复输出，说明 logging handler/propagation 配置有问题。
- 生产 compose 将 `../../..:/workspace` 源码挂入容器，不是 immutable image 部署；适合开发/早期 VPS，但不适合更严格生产。
- `npm audit --omit=dev` 报 Next.js 高危 DoS 和 PostCSS 中危 XSS；`npm outdated` 显示 Next 16.1.7 落后于 16.2.6。
- `pip-audit` 对当前虚拟环境报 dev 依赖 `pytest 8.4.2` 的 CVE，修复版本为 9.0.3。

### 3.6 开发者体验

成立的问题：

- CONTRIBUTING 质量尚可，但验证命令偏 PowerShell。
- 没有统一任务入口。
- 本地验证命令分散在 `ops/tools`、`ops/bin`、README、CONTRIBUTING、GitHub PR template。
- 无 lint/type/style gate，新贡献者没有明确质量边界。

额外发现：

- CI 与本地命令不一致：CI 用 Linux + Python 3.11 + Node 20；Docker dashboard 用 Node 22；README 只说 Node 20+；本地复测 Node 22 可用。版本矩阵需要写清。
- `uv` 在本地很好用，但项目文档未给出 `uv` 路径，导致 Linux 环境没有 pip 时新用户会卡住。

### 3.7 边界情况与健壮性

成立的问题：

- 空 DB 启动和 bootstrap 做得不错。
- API key 缺失可以 degrade，不会直接全系统崩。
- 任务状态 DB-backed，比纯内存 agent 强。
- 但 retry、清理、资源限制、长期运行治理不足。

额外发现：

- Dashboard Basic Auth 在未配置用户名/密码时直接放行，依赖绑定私网和 doctor 提醒；公开部署必须有更硬的 preflight gate。
- `dashboard_api_token` 为空时 `/api/v1/*` 不要求 token，这对本地开发友好，但公开 API 绑定时必须 fail-fast。
- 对 order POST 类外部调用不能简单 retry，必须先定义幂等策略：client order id、查询确认、重放保护、状态机补偿。

## 4. 共性根因

这些问题不是独立散点，它们有共同根因：

1. **架构先行，产品闭环滞后**  
   系统边界和治理模型很强，但 clone、sample data、tutorial、first smoke 这些产品入口没有同等优先级。

2. **能力交付缺少 Definition of Done**  
   新能力落地时没有强制同时完成测试、文档、observability、sample path、CI gate。

3. **当前态和历史态没有硬隔离**  
   Discord-first 历史、Telegram/light gateway 叙事、dashboard-first 现实实现混在一起。

4. **领域边界在设计里清楚，在代码里不够清楚**  
   产品说量化、执行、治理、学习分层，但代码上 `execution.py`、`state_store.py`、`api/main.py` 承担了太多职责。

5. **运维能力停留在脚本和文档，没有变成可验证制度**  
   有 backup、healthcheck、doctor，但缺 CI/preflight/retention/resource limits/structured events 这些自动约束。

## 5. 整体整改原则

后续修改应遵守这些原则：

- 先产品化，再扩功能。
- 每个新能力必须同时交付测试、文档、日志、示例或 smoke 覆盖。
- Dashboard 是当前主界面；light gateway 是辅助入口；实际 Discord 实现必须诚实命名。
- 交易相关 retry 必须幂等，不允许盲重试下单。
- 大文件拆分优先按领域边界拆，不做纯机械搬运。
- 文档只保留少数 canonical current docs，其余标为 historical/review。
- CI 负责阻止质量倒退，不依赖人工习惯。

## 6. 分阶段整改计划

### P0：止血与质量闸门

目标：防止已知代码缺陷、依赖风险和生产排障盲区继续扩大。

改动：

- 修复 ruff 发现的问题，特别是 `execution.py` 的不可达死代码和未定义变量。
- 在 `pyproject.toml` 增加 ruff 配置，将 `ruff check src tests alembic` 加入 CI。
- 升级 Next/PostCSS 依赖到无高危 audit 的版本，验证 `npm run build`。
- 处理 `pytest` CVE：升级到 9.x 或记录 dev-only 风险并设置后续升级任务。
- 给 API 增加基础结构化日志：
  - request id
  - route
  - status code
  - latency
  - error kind
- 给核心 gate 增加业务事件日志：
  - backtest gate result
  - paper gate result
  - execution readiness result
  - broker sync result
  - order intent blocked reason
- 增加统一 external call policy：
  - timeout
  - transient error classification
  - retry/backoff
  - rate-limit handling
  - idempotency rules
- 对 Alpaca GET/sync 可以安全 retry；对 order submit/cancel/replace 只能在 client_order_id 查询确认后补偿，不能盲重试。

验收：

- `ruff check src tests alembic` 通过。
- `uv run pytest -q` 通过。
- `npm run build` 通过。
- `npm audit --omit=dev` 无 high/critical。
- API 请求日志能关联一次 dashboard action 到后端 route 和 service gate。

### P1：新用户第一小时体验

目标：让一个新用户在 30 分钟内看到 dashboard，并在 5 分钟教程中跑通第一条 factor replay。

改动：

- 移除 PowerShell 脚本中的作者本机 Python 路径。
- 增加跨平台入口：
  - `ops/tools/start_local.sh`
  - `ops/tools/run_tests.sh`
  - `ops/tools/smoke_local.sh`
  - 或统一 `Makefile` / `justfile`
- README 首页重写成：
  - 30 秒理解项目
  - Docker quickstart
  - local dev quickstart
  - first factor replay tutorial
  - 文档入口
- 调整 Docker 本地体验：
  - 默认或明确命令启动 dashboard
  - README 写清 `--profile local-dashboard`
  - 避免默认启动不必要 worker 阻塞 first-run 心智
- 新增 sample data：
  - `sample-data/ohlcv/us-local-replay.json`
  - 至少 2-3 个 symbol，120+ bars，覆盖 factor replay 最小样本
  - 对应 API import 或 dashboard paste 示例
- 新增 `docs/next-gen/FIRST-5-MINUTES-TUTORIAL.md`：
  - clone
  - install
  - start
  - import sample bars
  - generate factor snapshots
  - create spec
  - run factor replay backtest
  - inspect readiness blockers
- 更新 README、Beginner Guide、User Manual 的因子表为 10+1。

验收：

- Linux/macOS/Windows 三条路径都有命令。
- 从空库开始，用户能用 sample data 跑出 factor snapshot 和 backtest record。
- README 不再要求用户自行构造 OHLCV 才能获得第一次成功。
- `docker compose` 文档中的 dashboard 行为和实际 profile 一致。

### P2：测试基础设施与量化核心覆盖

目标：把“测试能跑”升级成“测试可扩展、边界清晰、能保护量化正确性”。

改动：

- 新增 `tests/conftest.py`，提供：
  - temp SQLite database fixture
  - Settings fixture
  - bootstrapped StateStore fixture
  - market bars fixture
  - production strategy fixture
  - broker snapshot/reconciliation fixture
- 新增固定 fixture 数据：
  - bars JSON/CSV
  - factor expected values
  - strategy lifecycle payloads
- 新增独立测试：
  - `test_factor_engine.py`
  - `test_statistical_validation.py`
  - `test_execution_readiness.py`
  - `test_dashboard_service.py`
  - `test_skill_catalog.py`
  - `test_deploy_fields.py`
- 将测试分层：
  - fast unit
  - service integration
  - API integration
  - smoke
- CI 增加：
  - fast gate
  - full backend tests
  - Alembic empty DB upgrade
  - dashboard build

验收：

- factor formulas 有确定数值断言。
- custom factor AST sandbox 覆盖禁止调用、属性访问、未授权名称、除零等场景。
- statistical validation 覆盖 sample too small、DSR proxy、PBO proxy、OOS、walk-forward。
- readiness 覆盖 ready/degraded/blocked、stale quote、open incident、missing broker snapshot、live capability 缺失。
- 新增业务能力必须同时新增测试或明确豁免。

### P3：代码结构重构

目标：让代码结构反映产品的治理边界，降低修改风险。

改动：

- 拆 `api/main.py`：
  - `api/routes/dashboard.py`
  - `api/routes/market_data.py`
  - `api/routes/strategy.py`
  - `api/routes/execution.py`
  - `api/routes/governance.py`
  - `api/routes/evolution.py`
  - `api/dependencies.py`
- 拆 `execution.py`：
  - `execution/service.py`
  - `execution/orders.py`
  - `execution/reconciliation.py`
  - `execution/instruments.py`
  - `execution/options.py`
  - `execution/capital.py`
  - `execution/mappers.py`
  - `execution/readiness.py`
- 拆 `state_store.py`：
  - governance store
  - runtime config store
  - workflow store
  - bootstrap seed registry
  - summary mappers
- 拆 `contracts/state.py`：
  - governance contracts
  - market data contracts
  - strategy contracts
  - execution contracts
  - runtime config contracts
- 拆 `Settings`：
  - DatabaseSettings
  - BrokerSettings
  - DashboardSettings
  - CodexSettings
  - GatewaySettings
  - DeploymentSettings
- 给核心 public methods 增加 docstring：
  - 作用
  - 输入语义
  - 持久化副作用
  - 异常
  - gate/approval 边界

验收：

- 单个服务文件目标小于 800 行；超过需要设计说明。
- API route 文件按 domain ownership 拆分。
- execution 相关 tests 不需要理解 4000 行单文件即可定位失败。
- 新贡献者能从 docstring 理解关键 service method 的状态变更。

### P4：文档信息架构收敛

目标：把“文档很多”变成“读者路径清楚”。

改动：

- 文档分层：
  - `current/`：当前真实产品契约
  - `tutorials/`：从零跑通
  - `runbooks/`：生产和故障操作
  - `architecture/`：设计与状态模型
  - `reviews/`：历史评审和研究
  - `historical/`：Discord-first 等旧设计
- README 只链接 3 条主路径：
  - 新用户试用
  - 开发者贡献
  - 部署者上线
- 明确 gateway 决策：
  - 如果当前实现仍是 Discord，就文档写 Discord shell。
  - 如果产品要转 Telegram，就开明确 migration plan，不把未实现的 Telegram 写成当前能力。
- 导出 `openapi.yaml` 并加入 CI 校验。
- 合并 Beginner Guide 和 User Manual 重复段落，减少叙事漂移。

验收：

- 新用户最多读 3 个文档就能完成 first run。
- 所有 current docs 中 Discord/Telegram 术语一致。
- README 因子、测试数量、启动命令和代码同步。
- 历史文档不会出现在默认阅读路径中。

### P5：生产可观测性与长期运行

目标：让系统能长期运行、可排查、可恢复，而不只是能启动。

改动：

- 结构化 JSON logs 支持：
  - service
  - event_type
  - trace_id
  - subject_type
  - subject_id
  - decision
  - blocked_reason
  - latency_ms
- 增加 metrics/diagnostics：
  - queue depth
  - supervisor loop lag
  - external call failure rate
  - gate pass/fail count
  - broker sync age
  - backup age
- Docker 增加：
  - memory limit
  - CPU limit
  - log rotation
  - restart backoff strategy where possible
- 生产部署从源码挂载逐步转向 immutable image + named runtime volumes。
- backup 增加：
  - retention days
  - max backups
  - restore rehearsal command
  - backup age doctor check
- 数据保留策略：
  - old Codex artifacts
  - raw logs
  - stale market snapshots
  - old runtime backups
  - archived research docs

验收：

- 一次 failed backtest 能从日志定位 gate notes、input spec、run id。
- 一次 broker sync failure 能看到 provider、status code、retry count、final decision。
- 单 VPS 不会因 Codex runner 无限占用资源拖垮 core API。
- 备份会自动保留合理窗口并能演练恢复。

### P6：量化严谨性继续升级

目标：把当前工程近似逐步升级成更可信的研究验证框架。

改动：

- 将 DSR/PBO proxy 标注为 engineering proxy，并规划更严格实现。
- 引入 purged/embargo walk-forward split。
- 增加 factor recipe schema，替代仅线性表达式的 custom factor。
- 增加 data lineage 校验：
  - provider
  - as_of
  - adjusted/unadjusted
  - PIT availability
  - corporate action assumptions
- Backtest gate 把 sample size、cost model、baseline、lineage、PIT controls、OOS/walk-forward 明确分层展示。

验收：

- 策略无法只凭单次 in-sample 高 Sharpe 进入 paper candidate。
- Dashboard 能解释 backtest 为什么通过、为什么 needs_review、为什么 failed。
- 因子定义、数据来源、成本模型、baseline 都可追踪。

## 7. 任务映射表

| Hermes 问题 | 处理阶段 | 主要落点 |
|---|---:|---|
| PowerShell only / 硬编码路径 | P1 | `ops/tools/*.sh`, PowerShell resolver, README |
| Docker 默认不启 dashboard | P1 | `docker-compose.yml`, README quickstart |
| 无 sample data | P1/P2 | `sample-data`, tutorial, fixtures |
| README 过载/过期 | P1/P4 | README, Beginner/User Manual |
| 大文件 | P3 | execution/state_store/dashboard/api/contracts 拆分 |
| 零 docstring | P3 | core service public methods |
| 无 ruff/mypy/pre-commit | P0/P3 | `pyproject.toml`, CI, pre-commit |
| factor/statistical/readiness 测试缺口 | P2 | 独立单元测试和 fixture |
| 无 conftest | P2 | shared fixtures |
| 44 个文档迷宫 | P4 | docs IA 重组 |
| Discord/Telegram 混乱 | P1/P4 | gateway decision + docs/code 命名 |
| API logging 不足 | P0/P5 | request logs + business events |
| LLM/provider retry 不足 | P0/P5 | external call policy |
| Docker 无资源限制 | P5 | compose resource/log policies |
| backup 无轮转 | P5 | retention + restore rehearsal |
| 数据清理缺失 | P5 | retention jobs and doctor checks |
| Settings 过大 | P3 | settings submodels |
| API docs 不稳定 | P4 | OpenAPI export |

## 8. 建议执行顺序

建议按下面顺序执行，不要并行大改所有方向：

1. P0：静态检查、依赖安全、日志、retry 策略。
2. P1：新用户第一小时体验。
3. P2：测试基础设施。
4. P3：拆大文件。
5. P4：文档重组。
6. P5：生产长期运行。
7. P6：量化严谨性深化。

理由：

- 如果不先上质量闸门，重构会继续引入隐性死代码。
- 如果不先修 first-run，新用户和贡献者不会走到发现系统优点那一步。
- 如果不先建 fixture，大文件拆分会缺少安全网。
- 如果不先统一 gateway 叙事，文档重组会继续产生新漂移。

## 9. 最终验收标准

整改完成后，项目应该满足：

- 新用户按 README 在 30 分钟内看到 dashboard。
- 新用户按 5 分钟教程能用 sample data 跑出 factor snapshot 和 factor replay backtest。
- Linux/macOS/Windows 都有本地启动和测试路径。
- CI 至少包含 pytest、ruff、dashboard build、Alembic upgrade、npm audit high/critical gate。
- README 能力表和代码同步。
- current docs 不再混用 Discord/Telegram 当前态。
- 核心服务有结构化业务日志。
- 外部调用有 timeout/retry/backoff/idempotency policy。
- 大文件按领域拆分，核心 public methods 有 docstring。
- backup 有 retention，Docker 有资源限制和日志轮转。
- 数据保留策略能防止长期运行无限增长。

## 10. 本轮项目整洁审查补充

本轮在不改变功能边界的前提下，优先做低风险减法。

已清理：

- 删除本地验证产生的缓存和运行产物：`.mypy_cache/`、`.pytest_cache/`、`.ruff_cache/`、`.runtime/`、`__pycache__/`。
- 删除未被当前 README/文档引用、且内容哈希完全相同的重复 dashboard 截图，只保留 `docs/assets/dashboard-hero-evoq.png`。
- 删除 `workspace/` 中未被引用的完全重复样例产物，只保留被 cycle/report 明确指向的 canonical 文件。
- 删除两个只输出 `TODO`、引用旧 legacy 脚本且带自动 push 行为的遗留 GitHub Actions：`daily-report.yml` 和 `validate-strategy.yml`。当前保留的 CI 入口是 `.github/workflows/ci.yml`。
- 将当前 Dashboard 和 active docs 里的 Telegram-specific 当前态表述收敛为 `optional light gateway` / `chat gateway`。
- 在 `.gitignore` 中补充 ruff 和 coverage 产物，避免后续本地验证污染工作树。

有意保留：

- `src/quant_evo_nextgen/runner/discord_shell.py`、`services/discord_access.py`、`QE_DISCORD_*` 配置和 compose 里的 `discord-shell` 服务名仍然保留。它们是当前可运行的兼容实现，直接删除会破坏可选 chat control 功能。文档应把它描述为 light-gateway compatibility layer，而不是新的产品主路径。
- `legacy/original-system/` 保留为历史归档。它不在当前启动路径中，但仍有审计和设计溯源价值。
- `workspace/` 下的策略、memory、trading log 和 skill 文件保留。它们既是 repo-state/dashboard 可展示的 seed artifact，也是学习系统的样例语料；删除会让当前演示和审计上下文变薄。
- `runner/workflow.py` 保留为旧 supervisor 入口兼容别名。虽然当前文档不再推荐它，但删除 public module alias 有兼容风险。

后续可以继续做的减法：

1. 建一个正式的 gateway migration：把 Discord-specific 实现包在 `light_gateway` 抽象后，再迁移 compose service、env alias、doctor check 和 deploy prompt。迁移前不应简单删除 Discord 命名。
2. 把 `workspace/` 分成 `sample-workspace/` 和 runtime-owned workspace，确保 sample artifact 与真实运行产物有清晰边界。
3. 把历史 review/design 文档迁到 `docs/next-gen/historical/`，并用链接索引保留可发现性。移动前要统一更新所有相对链接。
4. 继续拆分 `execution.py`、`state_store.py`、`dashboard.py`，这是代码层最大的结构性减法，但必须在现有测试网下分阶段完成。

## 11. 结论

EvoQ 最需要的不是重做架构，也不是继续增加更多 agent 能力。它需要把已有正确方向产品化：

- 入口更短。
- 文档更少但更准。
- 代码边界更清楚。
- 测试更可扩展。
- 日志和 retry 更像生产系统。
- 历史设计和当前能力不再混杂。

这轮整改完成后，EvoQ 才能从“高级原型”推进到“可被外部用户试用、可被贡献者维护、可被 owner 长期运行”的阶段。
