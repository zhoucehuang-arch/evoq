import { fetchOverview } from "@/lib/dashboard";

type OverviewPageProps = {
  searchParams?: Promise<{
    demo?: string;
  }>;
};

type MetricTone = "good" | "warn" | "bad" | "neutral";

type MetricCard = {
  label: string;
  value: string;
  tone: MetricTone;
  note: string;
};

type SignalItem = {
  label: string;
  value: number;
  note: string;
  tone: MetricTone;
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

function toneSuffix(tone: MetricTone): string {
  switch (tone) {
    case "good":
      return "good";
    case "warn":
      return "warn";
    case "bad":
      return "bad";
    default:
      return "neutral";
  }
}

function compactNumber(value: number): string {
  if (value >= 1000) {
    const short = value >= 10000 ? value / 1000 : value / 1000;
    return `${short.toFixed(value >= 10000 ? 0 : 1)}k`;
  }
  return `${value}`;
}

function percentLabel(value: number): string {
  return `${value.toFixed(1)}%`;
}

function clampPercent(value: number, max: number): number {
  if (max <= 0) {
    return 8;
  }
  return Math.max(8, Math.min(100, (value / max) * 100));
}

function snapshotDate(value: string): string {
  return new Date(value).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function SignalColumn({
  title,
  description,
  items,
}: {
  title: string;
  description: string;
  items: SignalItem[];
}) {
  const max = Math.max(...items.map((item) => item.value), 1);

  return (
    <div className="signal-column">
      <div className="signal-heading-row">
        <div>
          <h3 className="signal-heading">{title}</h3>
          <p className="signal-description">{description}</p>
        </div>
      </div>
      <div className="signal-stack">
        {items.map((item) => (
          <div key={item.label} className="signal-lane">
            <div className="signal-top">
              <span className="signal-title">{item.label}</span>
              <strong className={toneClass(item.tone)}>{compactNumber(item.value)}</strong>
            </div>
            <div className="signal-track" aria-hidden="true">
              <div
                className={`signal-fill signal-fill-${toneSuffix(item.tone)}`}
                style={{ width: `${clampPercent(item.value, max)}%` }}
              />
            </div>
            <div className="signal-foot">{item.note}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default async function OverviewPage({ searchParams }: OverviewPageProps) {
  const params = searchParams ? await searchParams : undefined;
  const overview = await fetchOverview({ demo: params?.demo === "1" });
  const activeSleeves = overview.system.active_sleeves.length
    ? overview.system.active_sleeves.join(" / ")
    : "unconfigured";
  const activeSleeveCount = overview.system.active_sleeves.length;

  const topMetrics: MetricCard[] = [
    {
      label: "Production sleeves",
      value: `${overview.strategy.production}`,
      tone: overview.strategy.active_production ? "good" : "warn",
      note: overview.strategy.active_production ? "governed sleeves are live-ready" : "no active production sleeve",
    },
    {
      label: "Ready insights",
      value: `${overview.learning.ready_insight_count}`,
      tone: overview.learning.ready_insight_count > 0 ? "good" : "warn",
      note: `${overview.learning.insight_count} total insight candidates`,
    },
    {
      label: "Codex queue",
      value: `${overview.system.codex_queue_depth}`,
      tone: overview.system.codex_queue_depth > 3 ? "warn" : "good",
      note: "governed execution waiting for worker time",
    },
    {
      label: "Incident pressure",
      value: `${overview.system.open_incidents}`,
      tone: overview.system.open_incidents > 0 ? "warn" : "good",
      note: `${overview.system.pending_approvals} approvals and ${overview.system.active_overrides} overrides`,
    },
    {
      label: "Feature coverage",
      value: percentLabel(overview.learning.feature_coverage_pct),
      tone: overview.learning.feature_coverage_pct >= 30 ? "good" : "neutral",
      note: `${overview.learning.occupied_feature_cells} occupied cells in the learning map`,
    },
  ];

  const strategySignals: SignalItem[] = [
    {
      label: "Candidates",
      value: overview.strategy.candidates,
      note: "fresh hypotheses and ranking ideas in research flow",
      tone: "neutral",
    },
    {
      label: "Staging",
      value: overview.strategy.staging,
      note: "strategies currently under governed paper validation",
      tone: "good",
    },
    {
      label: "Production",
      value: overview.strategy.production,
      note: overview.strategy.active_production ? "at least one sleeve is activation-ready" : "promotion path still gated",
      tone: overview.strategy.active_production ? "good" : "warn",
    },
  ];

  const learningSignals: SignalItem[] = [
    {
      label: "Documents",
      value: overview.learning.document_count,
      note: "durable research objects retained in runtime memory",
      tone: "good",
    },
    {
      label: "Insights",
      value: overview.learning.insight_count,
      note: "candidate lessons extracted from recent research",
      tone: "neutral",
    },
    {
      label: "Principles",
      value: overview.learning.principles,
      note: "repo-backed operating memory promoted into durable doctrine",
      tone: "good",
    },
  ];

  const governanceSignals: SignalItem[] = [
    {
      label: "Approvals",
      value: overview.system.pending_approvals,
      note: "governed decisions waiting for owner or policy confirmation",
      tone: overview.system.pending_approvals > 0 ? "warn" : "good",
    },
    {
      label: "Overrides",
      value: overview.system.active_overrides,
      note: "manual guardrails currently changing normal automation behavior",
      tone: overview.system.active_overrides > 0 ? "warn" : "good",
    },
    {
      label: "Incidents",
      value: overview.system.open_incidents,
      note: "open runtime or provider events still affecting the authority core",
      tone: overview.system.open_incidents > 0 ? "bad" : "good",
    },
  ];

  const operatorFocus = [
    overview.system.pending_approvals > 0
      ? `Resolve ${overview.system.pending_approvals} pending approval${overview.system.pending_approvals > 1 ? "s" : ""}.`
      : "No approvals are waiting right now.",
    overview.system.open_incidents > 0
      ? `Review ${overview.system.open_incidents} open incident${overview.system.open_incidents > 1 ? "s" : ""} before any live posture change.`
      : "No active incident is currently forcing a degraded posture.",
    overview.system.codex_queue_depth > 0
      ? `Codex queue depth is ${overview.system.codex_queue_depth}; prioritize high-signal research and execution work.`
      : "Codex worker queue is clear.",
    `Deployment is pinned to ${overview.system.deployment_market_mode.toUpperCase()} mode with ${activeSleeveCount || "no"} active sleeve${activeSleeveCount === 1 ? "" : "s"}.`,
  ];

  const ownerPrompts = [
    "What's the overall system status right now?",
    "List pending approvals and tell me what actually blocks activation.",
    "Pause auto-trading but keep learning and evaluation running.",
    "What has the system learned recently that is ready for promotion?",
    "Why was this strategy not promoted to production?",
    "Show the current runtime configuration and recent changes.",
  ];

  const deployFlow = [
    "Push the repository to GitHub.",
    "Clone the stack to /opt/evoq on a single Ubuntu VPS.",
    "Run ./ops/bin/quickstart-single-vps.sh or use onboard-single-vps first if you want a reviewable draft.",
    "Confirm the market mode, then fill Discord, relay, and dashboard secrets.",
    "Pass doctor, smoke, and broker-sync checks in paper mode before touching any real capital.",
    "Only add a second Worker VPS when you truly need stronger isolation or higher Codex throughput.",
  ];

  const activationChecks = [
    "./ops/bin/core-smoke.sh returns no fail",
    "./ops/bin/system-doctor.sh returns no fail",
    "Dashboard and Discord agree on runtime health",
    "Broker sync and reconciliation look healthy in paper mode",
    "No unresolved incident is hiding behind a stale or broken freshness state",
  ];

  const supportedSurface = [
    "US mode supports governed US equities, US options, mixed sleeves, and short-equity paths with borrow and margin gates.",
    "CN mode supports A-share research, ranking, calendar-aware supervision, and paper-first operation.",
    "Discord remains the write surface while the dashboard acts as the decision and observation terminal.",
  ];

  const honestBoundaries = [
    "CN live broker execution is still not a shipped capability.",
    "Portfolio sleeve attribution remains conservative in some cross-strategy cases.",
    "Universal maintenance-margin, borrow-fee, and locate modeling is not yet closed across every product path.",
  ];

  return (
    <>
      <section className="metric-strip" aria-label="Overview metrics">
        {topMetrics.map((metric) => (
          <article key={metric.label} className={`metric-card metric-card-${toneSuffix(metric.tone)}`}>
            <div className="metric-kicker">{metric.label}</div>
            <div className={`metric-value ${toneClass(metric.tone)}`}>{metric.value}</div>
            <div className="metric-note">{metric.note}</div>
          </article>
        ))}
      </section>

      <section className="overview-grid">
        <article className="panel hero-panel stage-panel">
          <div className="panel-heading">
            <div>
              <div className="section-kicker">Mission Control</div>
              <h2 className="headline">{overview.headline}</h2>
              <p className="panel-copy">
                EvoQ is designed to feel like an authority terminal: not just a status page, but a place to judge whether
                the runtime is healthy enough to learn, evolve, and trade.
              </p>
            </div>
            <div className="panel-badge-row">
              <span className="panel-badge">Freshness {overview.freshness.state}</span>
              <span className="panel-badge">Runtime {overview.system.mode}</span>
              <span className="panel-badge">Risk {overview.system.risk_state}</span>
            </div>
          </div>

          <div className="signal-board">
            <SignalColumn
              title="Strategy lanes"
              description="How research is converting into governed sleeves."
              items={strategySignals}
            />
            <SignalColumn
              title="Learning promotion"
              description="How raw research is turning into durable system memory."
              items={learningSignals}
            />
            <SignalColumn
              title="Governance pressure"
              description="Where review load or operational friction is building."
              items={governanceSignals}
            />
          </div>

          <div className="bullet-cloud">
            {overview.highlights.map((highlight) => (
              <div key={highlight} className="bullet-chip">
                {highlight}
              </div>
            ))}
          </div>
        </article>

        <aside className="panel command-panel">
          <div className="section-kicker">Flight Deck</div>
          <h3>Authority snapshot</h3>
          <div className="snapshot-grid">
            <article className="snapshot-cell">
              <div className="snapshot-label">Generated</div>
              <div className="snapshot-value snapshot-value-small">{snapshotDate(overview.generated_at)}</div>
            </article>
            <article className="snapshot-cell">
              <div className="snapshot-label">Market mode</div>
              <div className="snapshot-value">{overview.system.deployment_market_mode.toUpperCase()}</div>
            </article>
            <article className="snapshot-cell">
              <div className="snapshot-label">Active sleeves</div>
              <div className="snapshot-value">{activeSleeveCount}</div>
            </article>
            <article className="snapshot-cell">
              <div className="snapshot-label">Active goals</div>
              <div className="snapshot-value">{overview.system.active_goals}</div>
            </article>
            <article className="snapshot-cell">
              <div className="snapshot-label">Queue</div>
              <div className="snapshot-value">{overview.system.codex_queue_depth}</div>
            </article>
            <article className="snapshot-cell">
              <div className="snapshot-label">Overrides</div>
              <div className={`snapshot-value ${overview.system.active_overrides > 0 ? "tone-warn" : ""}`}>
                {overview.system.active_overrides}
              </div>
            </article>
          </div>

          <h4 className="subsection-title">What deserves attention now</h4>
          <div className="stack tight-stack">
            {operatorFocus.map((item) => (
              <article key={item} className="stack-card compact-stack-card">
                <p className="callout">{item}</p>
              </article>
            ))}
          </div>
        </aside>
      </section>

      <section className="analysis-grid">
        <article className="panel">
          <div className="section-kicker">Strategy</div>
          <h3>Strategy spectrum</h3>
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
          <div className="split">
            <span className="split-label">Sleeve mix</span>
            <strong>{activeSleeves}</strong>
          </div>
          <p className="callout">
            The strategy surface should look compact and directional: you should immediately see if research is turning into
            governed production instead of getting trapped in endless analysis.
          </p>
        </article>

        <article className="panel">
          <div className="section-kicker">Learning</div>
          <h3>Promotion funnel</h3>
          <div className="split">
            <span className="split-label">Documents</span>
            <strong>{overview.learning.document_count}</strong>
          </div>
          <div className="split">
            <span className="split-label">Insights</span>
            <strong>{overview.learning.insight_count}</strong>
          </div>
          <div className="split">
            <span className="split-label">Principles</span>
            <strong>{overview.learning.principles}</strong>
          </div>
          <div className="split">
            <span className="split-label">Feature coverage</span>
            <strong>{percentLabel(overview.learning.feature_coverage_pct)}</strong>
          </div>
          <p className="callout">
            Runtime learning stays separate from promoted long-term memory so the operator can tell whether the system has
            only collected research or actually absorbed reusable doctrine.
          </p>
        </article>

        <article className="panel">
          <div className="section-kicker">Governance</div>
          <h3>Risk envelope</h3>
          <div className="split">
            <span className="split-label">Risk state</span>
            <strong>{overview.system.risk_state}</strong>
          </div>
          <div className="split">
            <span className="split-label">Pending approvals</span>
            <strong className={overview.system.pending_approvals > 0 ? "tone-warn" : ""}>
              {overview.system.pending_approvals}
            </strong>
          </div>
          <div className="split">
            <span className="split-label">Open incidents</span>
            <strong className={overview.system.open_incidents > 0 ? "tone-bad" : ""}>{overview.system.open_incidents}</strong>
          </div>
          <div className="split">
            <span className="split-label">Active overrides</span>
            <strong className={overview.system.active_overrides > 0 ? "tone-warn" : ""}>{overview.system.active_overrides}</strong>
          </div>
          <p className="callout">
            This is the panel you read before any live posture change. If approvals, incidents, or overrides are elevated,
            the runtime should feel deliberately constrained rather than superficially confident.
          </p>
        </article>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <div className="section-kicker">Operate</div>
          <h3>Discord command rail</h3>
          <div className="command-list">
            {ownerPrompts.map((prompt) => (
              <code key={prompt} className="command-chip">
                {prompt}
              </code>
            ))}
          </div>

          <h4 className="subsection-title">Runtime counters</h4>
          <div className="runtime-mini-grid">
            {overview.summary_cards.map((card) => (
              <article key={card.label} className="stat-card compact-stat-card">
                <div className="stat-label">{card.label}</div>
                <div className={`stat-value compact-stat-value ${toneClass(card.tone)}`}>{card.value}</div>
                {card.hint ? <div className="tile-meta">{card.hint}</div> : null}
              </article>
            ))}
          </div>
        </article>

        <article className="panel">
          <div className="section-kicker">Deploy</div>
          <h3>Deployment surface</h3>
          <div className="fact-grid">
            <article className="fact-card">
              <div className="fact-label">Market mode</div>
              <div className="fact-value">{overview.system.deployment_market_mode.toUpperCase()}</div>
              <div className="fact-meta">one deployment chooses one market</div>
            </article>
            <article className="fact-card">
              <div className="fact-label">Calendar</div>
              <div className="fact-value">{overview.system.market_calendar ?? "n/a"}</div>
              <div className="fact-meta">{overview.system.market_timezone ?? "timezone not set"}</div>
            </article>
            <article className="fact-card">
              <div className="fact-label">Sleeves</div>
              <div className="fact-value">{activeSleeves}</div>
              <div className="fact-meta">active governed exposure lanes</div>
            </article>
            <article className="fact-card">
              <div className="fact-label">Repo root</div>
              <div className="fact-value fact-value-mono">{overview.system.repo_root}</div>
              <div className="fact-meta">authority runtime mount</div>
            </article>
          </div>

          <h4 className="subsection-title">GitHub to VPS flow</h4>
          <ol className="ordered-list">
            {deployFlow.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
        </article>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <div className="section-kicker">Scope</div>
          <h3>Current product surface</h3>
          <div className="stack tight-stack">
            {supportedSurface.map((item) => (
              <article key={item} className="stack-card compact-stack-card">
                <p className="callout">{item}</p>
              </article>
            ))}
          </div>

          <h4 className="subsection-title">Honest boundaries</h4>
          <div className="stack tight-stack">
            {honestBoundaries.map((item) => (
              <article key={item} className="stack-card compact-stack-card">
                <p className="callout">{item}</p>
              </article>
            ))}
          </div>
        </article>

        <article className="panel">
          <div className="section-kicker">Gate</div>
          <h3>Activation checklist</h3>
          <div className="stack tight-stack">
            {activationChecks.map((check) => (
              <article key={check} className="stack-card compact-stack-card">
                <p className="callout">{check}</p>
              </article>
            ))}
          </div>

          <h4 className="subsection-title">Update path</h4>
          <div className="stack tight-stack">
            <article className="stack-card compact-stack-card">
              <strong>Single VPS</strong>
              <p className="callout">
                <code>./ops/bin/update-from-github.sh core</code>
              </p>
            </article>
            <article className="stack-card compact-stack-card">
              <strong>Scale-out worker</strong>
              <p className="callout">
                <code>./ops/bin/update-from-github.sh worker</code>
              </p>
            </article>
            <article className="stack-card compact-stack-card">
              <p className="callout">
                The update helper keeps the VPS path short: fast-forward pull, role bring-up, then smoke checks before the
                node is trusted again.
              </p>
            </article>
          </div>
        </article>
      </section>
    </>
  );
}
