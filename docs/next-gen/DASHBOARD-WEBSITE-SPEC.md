# DASHBOARD WEBSITE SPEC

## 1. Purpose

本文件定义下一代系统的 Dashboard 网站规格。Dashboard 不是 Discord 的替代品，而是高密度可视化、趋势查看和远程管理感知层。

本设计参考：

- 参考站点：`https://nadah-dashboard.vercel.app/`
- 当前项目已有草稿：[dashboard_spec_v1_20260318.md](../dashboard_spec_v1_20260318.md)

## 2. Product Objective

Dashboard 应满足以下目标：

- 让 owner 一眼看懂系统是否健康
- 让 owner 一眼看懂自动交易是否在安全运行
- 让 owner 一眼看懂自动进化是否在持续产出
- 支持手机和桌面
- 明确展示 freshness，绝不伪装实时
- 风格上参考 NADAH TERMINAL 的“密度高、状态先行、图优先”

## 3. Division of Labor

Dashboard 负责：

- 全局概览
- 趋势图
- 复杂表格
- 历史记录
- incident 线索
- 系统活跃度与学习产出

Dashboard 不负责：

- 复杂配置编辑
- 高频审批
- 长对话交互

这些仍然应由 Discord 承担。

## 4. UX Direction

### 4.1 Reference qualities to preserve

基于参考站点和现有 `dashboard_spec_v1`，建议保留这些优点：

- KPI first
- Chart first
- 风险显性展示
- 策略归因可见
- freshness 明确
- 移动端仍可读

### 4.2 Next-gen additions

下一代 Dashboard 必须比参考站点多展示 4 个自治层面的维度：

- 自动进化状态
- 多 agent 议会状态
- Codex worker 状态
- 学习和记忆状态

## 5. Information Architecture

建议采用 6 个一级页面：

### 5.1 `/`

`Overview`

一屏总览：

- 总权益
- 当日盈亏
- 当前自治级别
- 风险状态
- learning freshness
- Codex queue
- active incidents
- active goals

### 5.2 `/trading`

`Trading`

展示：

- 账户与权益曲线
- benchmark 对比
- 持仓
- 订单
- 策略归因
- 风险暴露
- 交易 session breakdown

### 5.3 `/evolution`

`Evolution`

展示：

- capability gaps
- improvement goals
- 近期 Codex runs
- patch acceptance rate
- eval 通过率
- 最近升级 / 回滚

### 5.4 `/learning`

`Learning`

展示：

- 新摄入文档数量
- topic watch
- evidence 生成量
- principle 晋升量
- 最近高价值洞察
- 来源健康度

### 5.5 `/system`

`System`

展示：

- workflow health
- queue backlog
- service health
- heartbeat
- token / budget usage
- storage and broker health

### 5.6 `/incidents`

`Incidents`

展示：

- active incidents
- recent incidents
- severity
- root cause summary
- mitigation status

## 6. Homepage Layout

首页建议布局如下：

### 6.1 Top ribbon

- system mode
- market state
- risk state
- freshness
- generated_at

### 6.2 Primary KPI row

- total equity
- day pnl
- total pnl
- gross exposure
- net exposure
- active strategies
- active goals
- active Codex runs

### 6.3 Primary chart row

- equity curve
- benchmark comparison
- strategy attribution

### 6.4 Secondary status row

- autonomy ladder
- learning pipeline health
- evolution pipeline health
- incidents

### 6.5 Bottom detail row

- positions table
- recent decisions
- recent alerts
- recent learning highlights

## 7. Dashboard-Specific Next-Gen Widgets

这是参考站点中没有、但下一代系统必须有的组件。

### 7.1 `Autonomy Ladder`

显示当前处于：

- A0
- A1
- A2
- A3
- A4

### 7.2 `Council Activity`

显示：

- 当前活跃议题
- 当前参与角色
- 当前轮次
- 是否已生成 decision card

### 7.3 `Codex Fabric Monitor`

显示：

- 运行中 Codex worker 数
- 队列长度
- 最近完成任务
- 最近失败任务
- 最近被拒绝 patch

### 7.4 `Learning Mesh Monitor`

显示：

- 今日新文档
- 今日证据数
- 今日洞察数
- 今日原则晋升数
- source trust 异常

### 7.5 `Evolution Funnel`

显示：

- capability gaps
- improvement goals
- Codex runs
- eval passed
- deployed
- rolled back

## 8. Visual Style Direction

Dashboard 视觉方向建议参考 NADAH TERMINAL 的“终端感 + 金融控制台感”，但要更适合中文和移动端。

### 8.1 Style keywords

- dense
- crisp
- high-signal
- restrained
- not playful
- not generic SaaS purple

### 8.2 Recommended visual system

- 深色石墨背景
- 强调色使用青绿、琥珀、风险红
- 数值卡片强调状态色
- 图表优先，不做花哨装饰
- 字体优先考虑中英文混排清晰度

## 9. Mobile Rules

移动端必须不是“缩小版桌面”。

### 9.1 Mobile priorities

- 先显示总状态和风险状态
- 图表简化但不消失
- 关键表格支持折叠
- 页面跳转尽量少

## 10. Freshness Model

Dashboard 必须显式展示 freshness。

### 10.1 Required freshness fields

- `generated_at`
- `captured_at`
- `age_seconds`
- `freshness_state`
- `degraded_reason`

### 10.2 Freshness states

- `fresh`
- `lagging`
- `stale`
- `broken`

### 10.3 Rule

任何 stale 数据不得伪装为当前状态。

## 11. Data Contract

Dashboard 应通过一个统一 API 读聚合数据。

### 11.1 Required top-level objects

- `overview`
- `trading`
- `evolution`
- `learning`
- `system`
- `incidents`
- `generated_at`
- `freshness`

### 11.2 Example additions over v1

相较 [dashboard_spec_v1_20260318.md](../dashboard_spec_v1_20260318.md)，下一代至少新增：

- `autonomy`
- `active_goals`
- `active_councils`
- `codex_fabric`
- `learning_mesh`
- `capability_gaps`
- `incident_summary`

## 12. Access and Security

Dashboard 必须满足：

- 登录后可看
- 前端无 broker secrets
- 所有修改型动作默认跳回 Discord 审批
- 对外只暴露聚合 API，不暴露内部控制面

## 13. Deployment Recommendation

为兼顾易部署和效果，建议：

- 核心系统部署在 VPS
- Dashboard 使用 `Next.js`
- 前端部署在 `Vercel`
- Dashboard 通过只读 API 读取 VPS 后端

如果必须全自托管，则：

- 同一套 Next.js 也可部署在 VPS
- 由 Caddy 或 Nginx 反代

## 14. Acceptance Criteria

如果要算达标，Dashboard 至少要满足：

1. 首页一屏能看懂系统健康、风险、自治级别和 freshness。
2. 自动交易状态和自动进化状态都能单独查看。
3. 手机上仍可快速判断“是否安全”和“是否需要介入”。
4. 出现 stale / broken 数据时，界面显著警示。
5. 页面风格延续 NADAH TERMINAL 的高密度控制台感，但更适合中文 owner 使用。
