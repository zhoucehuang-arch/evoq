import { fetchOverview } from "@/lib/dashboard";

type OverviewPageProps = {
  searchParams?: Promise<{
    demo?: string;
  }>;
};

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

export default async function OverviewPage({ searchParams }: OverviewPageProps) {
  const params = searchParams ? await searchParams : undefined;
  const overview = await fetchOverview({ demo: params?.demo === "1" });
  const activeSleeves = overview.system.active_sleeves.length
    ? overview.system.active_sleeves.join(" / ")
    : "unconfigured";
  const ownerPrompts = [
    "What's the overall system status right now?",
    "Is this deployment running in US or CN market mode, and which sleeves are active?",
    "List pending approvals.",
    "Show the current runtime configuration.",
    "Pause auto-trading but keep learning running.",
    "What has the system learned recently?",
    "Why was this strategy not promoted to production?",
  ];
  const deployFlow = [
    "Push the repository to GitHub.",
    "On a single Ubuntu VPS, clone it into /opt/quant-evo-nextgen.",
    "Run ./ops/bin/quickstart-single-vps.sh; use ./ops/bin/onboard-single-vps.sh --no-start if you want to review the draft first.",
    "During first-time onboarding, confirm whether the market mode is us or cn, then fill the Discord, relay, and dashboard secrets.",
    "Bring up the first doctor, smoke, and broker-sync cycle in paper mode before pointing at a real broker.",
    "Only add a second VPS for the Worker later if you actually need stronger isolation.",
  ];
  const activationChecks = [
    "./ops/bin/core-smoke.sh returns no fail",
    "./ops/bin/system-doctor.sh returns no fail",
    "The dashboard loads correctly",
    "Discord responds only to allowed accounts and channels",
    "The first broker sync and risk state look healthy",
  ];
  const supportedSurface = [
    "US deployments currently support governed US equities, options, and multi-leg option structures.",
    "CN deployments currently support A-share research, selection, market-session governance, and paper-first operation.",
    "Both market modes keep Discord as the control surface and the dashboard as the observation surface.",
  ];
  const honestBoundaries = [
    "CN live broker execution is still an adapter gap and should not be treated as shipped capability.",
    "Portfolio sleeve attribution and some cross-strategy netting limits remain conservative.",
    "Universal maintenance-margin, borrow-fee, and locate modeling is not yet closed across every product path.",
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
              <div className="stat-value small-value">{new Date(overview.generated_at).toLocaleString("en-US")}</div>
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
