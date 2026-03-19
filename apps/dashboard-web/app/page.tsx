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
  const ownerPrompts = [
    "现在系统整体状态怎么样？",
    "列出待审批事项。",
    "查看当前运行时配置。",
    "暂停自动交易，保留学习。",
    "最近系统学到了什么？",
    "为什么这个策略没有进入生产？",
  ];
  const deployFlow = [
    "推送仓库到 GitHub。",
    "在 Core 与 Worker VPS 上 git clone 到 /opt/quant-evo-nextgen。",
    "两台机器都执行 sudo ./ops/bin/install-host-deps.sh。",
    "Core 执行 ./ops/bin/bootstrap-node.sh core，Worker 执行 ./ops/bin/bootstrap-node.sh worker。",
    "先用 paper 模式启动，再运行 smoke 检查。",
  ];
  const activationChecks = [
    "./ops/bin/core-smoke.sh 无 fail",
    "./ops/bin/worker-smoke.sh 无 fail",
    "Dashboard 能正常打开",
    "Discord 只响应允许的账号和频道",
    "首次 broker sync 与风控状态正常",
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
              Mode <strong>{overview.system.mode}</strong>
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
            <span className="split-label">Principles</span>
            <strong>{overview.learning.principles}</strong>
          </div>
          <div className="split">
            <span className="split-label">Causal records</span>
            <strong>{overview.learning.causal_cases}</strong>
          </div>
          <div className="split">
            <span className="split-label">Feature coverage</span>
            <strong>{overview.learning.feature_coverage_pct.toFixed(4)}%</strong>
          </div>
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
              <strong>Core VPS</strong>
              <p className="callout">
                <code>./ops/bin/update-from-github.sh core</code>
              </p>
            </article>
            <article className="stack-card">
              <strong>Worker VPS</strong>
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
