import { fetchOverview } from "@/lib/dashboard";

function toneClass(tone: string): string {
  switch (tone) {
    case "good":
      return "tone-good";
    case "warn":
      return "tone-warn";
    case "bad":
      return "tone-bad";
    default:
      return "";
  }
}

export default async function OverviewPage() {
  const overview = await fetchOverview();
  const activeSleeves = overview.system.active_sleeves.length
    ? overview.system.active_sleeves.join(" / ")
    : "unconfigured";
  const ownerPrompts = [
    "现在系统整体状态怎么样？",
    "当前部署是美股还是 A 股？激活了哪些交易 sleeves？",
    "列出待审批事项。",
    "查看当前运行时配置。",
    "暂停自动交易，保留学习。",
    "最近系统学到了什么？",
    "为什么这个策略没有进入生产？",
  ];
  const deployFlow = [
    "推送仓库到 GitHub。",
    "在单台 Ubuntu VPS 上 git clone 到 /opt/quant-evo-nextgen。",
    "执行 ./ops/bin/quickstart-single-vps.sh；如果想先检查草稿，就改用 ./ops/bin/onboard-single-vps.sh --no-start。",
    "在首次引导里先确认市场模式是 us 还是 cn，再填写 Discord、中转和 dashboard 密钥。",
    "先用 paper 模式跑通 doctor、smoke 与首轮 broker sync，再考虑切换真实 broker。",
    "需要隔离时，再把 Worker 扩展到第二台 VPS，而不是从一开始就拆双机。",
  ];
  const activationChecks = [
    "./ops/bin/core-smoke.sh 无 fail",
    "./ops/bin/system-doctor.sh 无 fail",
    "Dashboard 能正常打开",
    "Discord 只响应允许的账号和频道",
    "首次 broker sync 与风控状态正常",
  ];
  const supportedSurface = [
    "US 部署当前支持受治理的美股正股、期权，以及期权多腿结构。",
    "CN 部署当前支持 A 股研究、选股、市场时段治理与 paper-first 运行。",
    "两种市场模式都保留 Discord 控制面与 Dashboard 观测面。",
  ];
  const honestBoundaries = [
    "CN live broker 仍然是后续适配器闭环，不应被当成已交付能力。",
    "组合 sleeve attribution 与部分跨策略净额限制仍偏保守。",
    "通用 maintenance margin、borrow fee 与 locate 建模还没有覆盖全部产品路径。",
  ];

  return (
    <>
      <section className="hero">
        <article className="panel hero-panel">
          <div className="chip-row">
            <span className="chip">
              Freshness <strong>{overview.freshness.state}</strong>
            </span>
            <span className="chip">
              Runtime <strong>{overview.system.mode}</strong>
            </span>
            <span className="chip">
              Market <strong>{overview.system.deployment_market_mode.toUpperCase()}</strong>
            </span>
            <span className="chip">
              Risk <strong>{overview.system.risk_state}</strong>
            </span>
          </div>
          <h2 className="headline">{overview.headline}</h2>
          <ul className="list">
            {overview.highlights.map((highlight) => (
              <li key={highlight}>{highlight}</li>
            ))}
          </ul>
        </article>

        <aside className="panel">
          <h3>Governance Snapshot</h3>
          <div className="meta-grid">
            <div className="stat-card">
              <div className="stat-label">Generated</div>
              <div className="stat-value small-value">{new Date(overview.generated_at).toLocaleString("zh-CN")}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Active goals</div>
              <div className="stat-value">{overview.system.active_goals}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Pending approvals</div>
              <div className="stat-value tone-warn">{overview.system.pending_approvals}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Active sleeves</div>
              <div className="stat-value small-value">{activeSleeves}</div>
            </div>
          </div>
        </aside>
      </section>

      <section className="card-grid">
        {overview.summary_cards.map((card) => (
          <article key={card.label} className="stat-card">
            <div className="stat-label">{card.label}</div>
            <div className={`stat-value ${toneClass(card.tone)}`}>{card.value}</div>
            {card.hint ? <div className="callout">{card.hint}</div> : null}
          </article>
        ))}
      </section>

      <section className="detail-grid">
        <article className="panel">
          <h3>Strategy Surface</h3>
          <div className="split">
            <span className="split-label">Candidates</span>
            <strong>{overview.strategy.candidates}</strong>
          </div>
          <div className="split">
            <span className="split-label">Staging</span>
            <strong>{overview.strategy.staging}</strong>
          </div>
          <div className="split">
            <span className="split-label">Production</span>
            <strong>{overview.strategy.production}</strong>
          </div>
        </article>

        <article className="panel">
          <h3>Learning Surface</h3>
          <div className="split">
            <span className="split-label">Promoted principles</span>
            <strong>{overview.learning.principles}</strong>
          </div>
          <div className="split">
            <span className="split-label">Causal records</span>
            <strong>{overview.learning.causal_cases}</strong>
          </div>
          <div className="split">
            <span className="split-label">Learning docs</span>
            <strong>{overview.learning.document_count}</strong>
          </div>
          <div className="split">
            <span className="split-label">Ready insights</span>
            <strong>{overview.learning.ready_insight_count}</strong>
          </div>
          <div className="split">
            <span className="split-label">Feature coverage</span>
            <strong>{overview.learning.feature_coverage_pct.toFixed(4)}%</strong>
          </div>
          <p className="callout">
            Repo-backed principle memory is shown separately from runtime learning-mesh documents and insight candidates.
          </p>
        </article>

        <article className="panel">
          <h3>System Governance</h3>
          <div className="split">
            <span className="split-label">Open incidents</span>
            <strong>{overview.system.open_incidents}</strong>
          </div>
          <div className="split">
            <span className="split-label">Active overrides</span>
            <strong>{overview.system.active_overrides}</strong>
          </div>
          <div className="split">
            <span className="split-label">Codex queue</span>
            <strong>{overview.system.codex_queue_depth}</strong>
          </div>
        </article>

        <article className="panel">
          <h3>Market Deployment</h3>
          <div className="split">
            <span className="split-label">Market mode</span>
            <strong>{overview.system.deployment_market_mode}</strong>
          </div>
          <div className="split">
            <span className="split-label">Calendar</span>
            <strong>{overview.system.market_calendar ?? "unknown"}</strong>
          </div>
          <div className="split">
            <span className="split-label">Timezone</span>
            <strong>{overview.system.market_timezone ?? "unknown"}</strong>
          </div>
          <div className="split">
            <span className="split-label">Active sleeves</span>
            <strong>{activeSleeves}</strong>
          </div>
        </article>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <div className="section-kicker">Supported Today</div>
          <h3>Current Product Surface</h3>
          <div className="stack">
            {supportedSurface.map((item) => (
              <article key={item} className="stack-card">
                <p className="callout">{item}</p>
              </article>
            ))}
          </div>
        </article>

        <article className="panel">
          <div className="section-kicker">Boundaries</div>
          <h3>Honest Limits</h3>
          <div className="stack">
            {honestBoundaries.map((item) => (
              <article key={item} className="stack-card">
                <p className="callout">{item}</p>
              </article>
            ))}
          </div>
        </article>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <div className="section-kicker">Deploy Path</div>
          <h3>GitHub -&gt; VPS</h3>
          <div className="stack">
            {deployFlow.map((step) => (
              <article key={step} className="stack-card">
                <p className="callout">{step}</p>
              </article>
            ))}
          </div>
        </article>

        <article className="panel">
          <div className="section-kicker">First Boot</div>
          <h3>Activation Checklist</h3>
          <div className="stack">
            {activationChecks.map((check) => (
              <article key={check} className="stack-card">
                <p className="callout">{check}</p>
              </article>
            ))}
          </div>
        </article>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <div className="section-kicker">Owner UX</div>
          <h3>Discord Natural-Language Control</h3>
          <div className="command-list">
            {ownerPrompts.map((prompt) => (
              <code key={prompt} className="command-chip">
                {prompt}
              </code>
            ))}
          </div>
        </article>

        <article className="panel">
          <div className="section-kicker">Upgrade Path</div>
          <h3>GitHub Update Shortcut</h3>
          <div className="stack">
            <article className="stack-card">
              <strong>Single VPS</strong>
              <p className="callout">
                <code>./ops/bin/update-from-github.sh core</code>
              </p>
            </article>
            <article className="stack-card">
              <strong>Scale-out Later</strong>
              <p className="callout">
                <code>./ops/bin/update-from-github.sh worker</code>
              </p>
            </article>
            <article className="stack-card">
              <p className="callout">
                The update helper performs a fast-forward pull, reruns the role bring-up script, and finishes with smoke
                checks so the VPS update path stays short and repeatable.
              </p>
            </article>
          </div>
        </article>
      </section>
    </>
  );
}
