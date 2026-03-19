# CODEX WORKER PROTOCOL

## 1. Purpose

本文件定义如何把 `Codex` 作为下一代系统的核心执行能力纳入自治架构。

核心结论如下：

- `Codex` 适合作为默认执行 worker
- `Codex` 不应成为唯一治理中心
- `Codex` 的运行必须被 workflow、policy、budget、review 和 artifact 管理

## 2. Why Codex Is First-Class

系统下一代重构选择 `Codex` 作为核心执行器，原因包括：

- 对 repo 和代码任务天然适配
- 可用于分析、实现、重构、修复、补测试、写文档
- 可通过 CLI 非交互执行
- 可输出结构化结果
- 可与 review、apply、cloud、MCP 等能力衔接

系统中大多数高价值“复杂任务”都应默认尝试委派给 Codex worker，而不是让通用 agent 用长文本自行模拟执行。

## 3. Worker Position in the Architecture

```text
Council / Planner / Governor
  -> Task specification
  -> Policy + budget + write scope

Codex Fabric
  -> worker queue
  -> workspace isolation
  -> run execution
  -> artifact capture
  -> review / eval handoff

Kernel
  -> state persistence
  -> retries
  -> approvals
  -> metrics
```

## 4. Supported Execution Modes

### 4.1 `local_exec`

默认模式。通过本地 CLI 执行：

```bash
codex exec --json --output-schema <schema.json> -C <workspace> "<prompt>"
```

适合：

- 本地 VPS 持续运行
- 仓库内任务
- 受控写入工作区

### 4.2 `local_review`

用于补丁或改动评审：

```bash
codex review --uncommitted
```

### 4.3 `local_apply`

用于将已生成的 patch 应用到目标工作区：

```bash
codex apply
```

### 4.4 `cloud_exec`

作为未来可选模式，用于异步云执行或高峰期弹性。

说明：

- 该模式可选，不作为系统首要依赖
- 所有云执行仍然必须回写本地状态与工件

## 5. Worker Classes

建议按任务类别定义 worker class，而不是所有任务共用一套 prompt。

### 5.1 `analysis_worker`

适用：

- repo 调研
- 依赖对比
- root cause analysis
- 架构梳理

### 5.2 `implementation_worker`

适用：

- 写代码
- 改代码
- 补测试
- 搭脚本
- 改配置

### 5.3 `review_worker`

适用：

- diff 评审
- 风险识别
- 测试缺口审查
- 回归风险提示

### 5.4 `strategy_worker`

适用：

- 策略实现
- 回测脚本生成
- 指标统计
- 研究工件生成

### 5.5 `ops_worker`

适用：

- 部署脚本
- 运维修复
- incident 自动修复候选
- 监控脚本更新

## 6. Worker Request Object

每次 Codex 运行都必须使用结构化请求对象。

### 6.1 Required fields

- `codex_run_id`
- `goal_id`
- `task_id`
- `worker_class`
- `objective`
- `context_summary`
- `repo_path`
- `workspace_path`
- `write_scope`
- `allowed_tools`
- `search_enabled`
- `risk_tier`
- `max_duration_sec`
- `max_token_budget`
- `output_schema_path`
- `acceptance_criteria`

### 6.2 Optional fields

- `base_branch`
- `comparison_ref`
- `related_artifacts`
- `memory_refs`
- `citation_requirements`
- `review_required`
- `eval_required`

## 7. Workspace Isolation Model

为避免多任务互相污染，Codex worker 必须运行在隔离工作区中。

### 7.1 Recommended modes

- `git worktree`
  推荐给仓库内补丁任务。
- `ephemeral copy`
  推荐给高风险实验或临时分析任务。
- `read_only mirror`
  推荐给纯分析和 review 任务。

### 7.2 Isolation rules

- 每个 run 只能写自己的工作区
- 不允许直接改主工作树
- 只有通过审查与评估的工件才有资格回流

## 8. Output Contract

Codex 不是只返回自然语言总结，必须产出结构化结果。

### 8.1 Required output fields

- `summary`
- `outcome`
- `files_changed`
- `tests_run`
- `test_results`
- `artifacts_produced`
- `followup_tasks`
- `risks_found`
- `citations`
- `confidence`

### 8.2 Allowed outcomes

- `completed`
- `blocked`
- `failed`
- `needs_review`
- `needs_eval`
- `rejected`

## 9. Artifact Policy

每次 run 的关键产物都必须存档：

- diff
- patch bundle
- test logs
- benchmark or backtest outputs
- generated reports
- source citations
- review notes

## 10. Review and Evaluation Gates

不同风险等级对应不同门槛：

### 10.1 Low-risk tasks

示例：

- 读文档
- 补注释
- 小型分析脚本

要求：

- 结构化输出
- 基本日志留存

### 10.2 Medium-risk tasks

示例：

- 一般代码改动
- 数据抓取逻辑改动
- 策略研究脚本改动

要求：

- `review_worker` 或 `codex review`
- 至少一类验证

### 10.3 High-risk tasks

示例：

- 风控逻辑
- 下单路径
- 自治级别相关代码
- 生产策略逻辑

要求：

- review
- eval
- 必要时 shadow / canary
- 审批

## 11. Prompting Discipline

Codex worker 的输入应尽量结构化，而不是长段主观叙述。

### 11.1 Prompt template sections

- 任务目标
- 当前上下文摘要
- 允许修改范围
- 禁止触碰范围
- 成功标准
- 风险提醒
- 输出 schema

### 11.2 Prompt anti-patterns

- 把完整长历史聊天直接塞给 worker
- 不给成功标准
- 不限制写入范围
- 不限制时间和预算
- 一次请求要求做多个高风险不相关任务

## 12. Interaction with Councils

Codex 与 council 的关系应是：

- council 负责提出问题、评估备选路径、形成任务规范
- Codex 负责执行具体工作并返回工件
- council 或 reviewer 再决定是否采纳结果

禁止把 Codex 既当提案者、又当审批者、又当部署者而没有隔离。

## 13. Failure Handling

### 13.1 Retryable failures

- 临时网络问题
- 工具不可用
- 工作区冲突
- 测试环境瞬时异常

### 13.2 Non-retryable failures

- 任务定义不清
- write scope 不合法
- 预算不足
- 权限越界
- 输出 schema 不可满足

### 13.3 Failure outputs

失败时也必须输出：

- 失败原因
- 已完成部分
- 阻塞点
- 建议下一步

## 14. Security and Tool Policy

每个 Codex run 都必须明确：

- 是否允许联网
- 是否允许 shell 写入
- 是否允许读 secrets
- 是否允许访问 broker 凭据
- 是否允许访问生产配置

默认原则：

- 默认不授予 secrets
- 默认不授予生产 broker 权限
- 默认不允许直接部署

## 15. Suggested DB Tables

- `evo_codex_run`
- `evo_codex_run_event`
- `evo_codex_artifact`
- `evo_codex_review`
- `evo_codex_eval_link`
- `evo_codex_merge_decision`

## 16. Reference CLI Templates

### 16.1 Analysis task

```bash
codex exec --json -C <workspace> --output-schema schemas/analysis.json "
Analyze the repository and answer only according to the schema.
Respect write scope: read-only.
"
```

### 16.2 Implementation task

```bash
codex exec --json -C <workspace> --output-schema schemas/implementation.json "
Implement the requested changes.
Only modify files under <allowed_paths>.
Run relevant tests if available.
"
```

### 16.3 Review task

```bash
codex review --uncommitted
```

## 17. Versioning and Portability

为了避免将来被单一入口绑死，系统应把 Codex 封装在内部协议后面。

也就是说：

- 上层 workflow 调用的是 `codex worker protocol`
- 底层可以是 `codex exec`
- 将来必要时可切到 SDK 或 cloud mode
- 上层不应依赖某个 CLI 输出细节

## 18. Success Metrics

应持续衡量 Codex fabric 的价值：

- 每类任务完成率
- 平均 token 成本
- 平均耗时
- review 通过率
- eval 通过率
- 回归事故率
- 节省的人工操作量

## 19. Hard Rules

- Codex worker 不直接拥有最终生产发布权
- Codex worker 不直接拥有 broker 资金控制权
- 所有高风险输出必须经过治理门槛
- 每次 run 必须具备可审计输入和输出
