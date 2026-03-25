import { fetchSystem } from "@/lib/dashboard";
import type { DashboardFrontendStatus } from "@/lib/types";

type MetricTone = "good" | "warn" | "bad" | "neutral";

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

function statusLabel(status?: DashboardFrontendStatus): string {
  switch (status?.error_kind) {
    case "auth":
      return "Dashboard Auth Failed";
    case "unavailable":
      return "Backend Unavailable";
    case "server":
      return "Backend Error";
    case "http":
      return "Unexpected API Response";
    case "network":
      return "Network Path Broken";
    default:
      return "Degraded Dashboard";
  }
}

function dateLabel(value: string | null | undefined): string {
  if (!value) {
    return "n/a";
  }
  return new Date(value).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function previewLines(lines: string[], fallback: string): string[] {
  return lines.length > 0 ? lines : [fallback];
}

function loopTone(status: string, failureStreak: number): string {
  if (failureStreak > 0) {
    return "tone-warn";
  }
  return /warning|review|degraded|halt/i.test(status) ? "tone-warn" : "tone-good";
}

function summaryValue(summaryCards: { label: string; value: string }[], label: string): string {
  return summaryCards.find((card) => card.label === label)?.value ?? "n/a";
}

export default async function SystemPage() {
  const system = await fetchSystem();
  const frontendStatus = system.frontend_status;
  const healthyProviders = system.providers.filter((provider) => ["healthy", "ok"].includes(provider.health_status.toLowerCase())).length;
  const degradedProviders = system.providers.length - healthyProviders;
  const enabledLoops = system.supervisor_loops.filter((loop) => loop.is_enabled).length;
  const loopsWithFailures = system.supervisor_loops.filter((loop) => loop.failure_streak > 0).length;
  const loopsNeedingReview = system.supervisor_loops.filter((loop) => /warning|review|degraded|halt/i.test(loop.last_status)).length;
  const mutableConfigCount = system.runtime_config.filter((entry) => entry.is_mutable).length;
  const restartRequiredCount = system.runtime_config.filter((entry) => entry.requires_restart).length;
  const highRiskProposals = system.pending_config_proposals.filter((proposal) => proposal.risk_level.toLowerCase() === "high").length;
  const deploymentMode =
    system.runtime_config.find((entry) => entry.target_key === "deployment_market_mode")?.value_preview ??
    system.owner_preferences.find((preference) => preference.preference_key === "owner_market_focus")?.value_preview ??
    "n/a";
  const openIncidentCount = summaryValue(system.summary_cards, "Open incidents");

  const topMetrics = [
    {
      label: "Freshness",
      value: system.freshness.state,
      tone: system.freshness.state === "fresh" ? "good" : system.freshness.state === "lagging" ? "warn" : "bad",
      note: frontendStatus ? statusLabel(frontendStatus) : system.freshness.note ?? "authority aggregation is current",
    },
    {
      label: "Providers",
      value: `${healthyProviders}/${system.providers.length || 0}`,
      tone: degradedProviders > 0 ? "warn" : "good",
      note: degradedProviders > 0 ? `${degradedProviders} provider surface needs attention` : "provider fabric is healthy",
    },
    {
      label: "Supervisor loops",
      value: `${enabledLoops}/${system.supervisor_loops.length || 0}`,
      tone: loopsWithFailures > 0 || loopsNeedingReview > 0 ? "warn" : enabledLoops > 0 ? "good" : "neutral",
      note:
        loopsWithFailures > 0
          ? `${loopsWithFailures} loop failure streaks visible`
          : loopsNeedingReview > 0
            ? `${loopsNeedingReview} loop status${loopsNeedingReview === 1 ? " needs" : "es need"} review`
            : "no failure streak is visible",
    },
    {
      label: "Config queue",
      value: `${system.pending_config_proposals.length}`,
      tone: system.pending_config_proposals.length > 0 ? "warn" : "good",
      note: `${highRiskProposals} high-risk proposal${highRiskProposals === 1 ? "" : "s"} in governed review`,
    },
    {
      label: "Owner memory",
      value: `${system.owner_preferences.length}`,
      tone: system.owner_preferences.length > 0 ? "good" : "warn",
      note: `${mutableConfigCount} mutable config entries are currently visible`,
    },
  ] as const;

  const operatorFocus = [
    frontendStatus
      ? `${statusLabel(frontendStatus)}. ${frontendStatus.operator_action}`
      : "The dashboard is reading live authority-core state and is not currently in degraded frontend mode.",
    degradedProviders > 0
      ? `${degradedProviders} provider surface${degradedProviders === 1 ? " is" : "s are"} not fully healthy, so system trust should stay guarded.`
      : "Provider fabric appears healthy enough for normal observation and governed action.",
    loopsWithFailures > 0
      ? `${loopsWithFailures} supervisor loop${loopsWithFailures === 1 ? " has" : "s have"} a visible failure streak and deserves immediate review.`
      : loopsNeedingReview > 0
        ? `${loopsNeedingReview} supervisor loop${loopsNeedingReview === 1 ? " is" : "s are"} not failing but still reports a warning or review state.`
        : "No visible supervisor loop is currently showing a failure streak.",
    system.pending_config_proposals.length > 0
      ? `${system.pending_config_proposals.length} config proposal${system.pending_config_proposals.length === 1 ? " is" : "s are"} still waiting for governance.`
      : "No config proposal is currently waiting in the authority queue.",
    restartRequiredCount > 0
      ? `${restartRequiredCount} runtime setting${restartRequiredCount === 1 ? " requires" : "s require"} a restart to fully apply.`
      : "Visible runtime config changes do not currently require a restart.",
  ];

  const operatorShortcuts = [
    {
      title: "Fast health check",
      surface: "SSH",
      detail: "Run ./ops/bin/core-smoke.sh and ./ops/bin/worker-smoke.sh before trusting live state after any config or code change.",
    },
    {
      title: "Pause trading, keep learning",
      surface: "Discord",
      detail: "Use the Discord control surface to halt automated trading while leaving research, learning, and evaluation loops active.",
    },
    {
      title: "Review drift before changing posture",
      surface: "Dashboard + Discord",
      detail: "Inspect config, owner preferences, proposals, and incidents here before requesting a governed runtime change.",
    },
    {
      title: "Update from GitHub",
      surface: "SSH",
      detail: "Use ./ops/bin/update-from-github.sh core and worker so upgrades stay repeatable, auditable, and smoke-checked.",
    },
  ];

  const recoveryPlaybook = [
    "Check whether degraded freshness comes from API reachability, a blocked worker loop, or provider-side connectivity trouble.",
    "Pause the affected live domain before making speculative config changes if trading safety could be impacted.",
    "Compare workflows, Codex runs, incidents, and config proposals before assuming the problem is purely visual.",
    "If smoke checks fail, move to the relevant runbook instead of patching live state from intuition.",
  ];

  return (
    <>
      <section className="metric-strip" aria-label="System metrics">
        {topMetrics.map((metricCard) => (
          <article key={metricCard.label} className={`metric-card metric-card-${toneSuffix(metricCard.tone)}`}>
            <div className="metric-kicker">{metricCard.label}</div>
            <div className={`metric-value ${toneClass(metricCard.tone)}`}>{metricCard.value}</div>
            <div className="metric-note">{metricCard.note}</div>
          </article>
        ))}
      </section>

      <section className="overview-grid">
        <article className="panel hero-panel stage-panel">
          <div className="panel-heading">
            <div>
              <div className="section-kicker">Authority Core</div>
              <h2 className="headline">System Command Surface</h2>
              <p className="panel-copy">
                This page should answer whether the authority core is trustworthy enough to accept owner intent, run Codex
                work, and keep the learning and trading planes under control.
              </p>
            </div>
            <div className="panel-badge-row">
              <span className="panel-badge">Freshness {system.freshness.state}</span>
              <span className="panel-badge">Market mode {deploymentMode}</span>
              <span className="panel-badge">Open incidents {openIncidentCount}</span>
            </div>
          </div>

          <div className="fact-grid">
            <article className="fact-card">
              <div className="fact-label">Generated</div>
              <div className="fact-value">{dateLabel(system.generated_at)}</div>
              <div className="fact-meta">authority snapshot timestamp</div>
            </article>
            <article className="fact-card">
              <div className="fact-label">Providers</div>
              <div className={`fact-value ${degradedProviders > 0 ? "tone-warn" : "tone-good"}`}>
                {healthyProviders}/{system.providers.length || 0}
              </div>
              <div className="fact-meta">healthy / visible provider surfaces</div>
            </article>
            <article className="fact-card">
              <div className="fact-label">Loops</div>
              <div className={`fact-value ${loopsWithFailures > 0 ? "tone-warn" : ""}`}>
                {enabledLoops}/{system.supervisor_loops.length || 0}
              </div>
              <div className="fact-meta">enabled / visible supervisor loops</div>
            </article>
            <article className="fact-card">
              <div className="fact-label">Runtime config</div>
              <div className="fact-value">{system.runtime_config.length}</div>
              <div className="fact-meta">{mutableConfigCount} mutable entries currently visible</div>
            </article>
          </div>

          <div className="bullet-cloud">
            {system.highlights.map((highlight) => (
              <div key={highlight} className="bullet-chip">
                {highlight}
              </div>
            ))}
          </div>

          {frontendStatus ? (
            <div className="stack">
              <article className="stack-card">
                <strong>{statusLabel(frontendStatus)}</strong>
                <span>{frontendStatus.status_code ? `HTTP ${frontendStatus.status_code}` : "no HTTP status"}</span>
                <p className="callout">{frontendStatus.detail}</p>
                <p className="callout">{frontendStatus.operator_action}</p>
              </article>
            </div>
          ) : null}
        </article>

        <aside className="panel command-panel">
          <div className="section-kicker">Flight Deck</div>
          <h3>Authority snapshot</h3>
          <div className="snapshot-grid">
            <article className="snapshot-cell">
              <div className="snapshot-label">Recent workflows</div>
              <div className="snapshot-value">{system.recent_workflows.length}</div>
            </article>
            <article className="snapshot-cell">
              <div className="snapshot-label">Codex runs</div>
              <div className="snapshot-value">{system.recent_codex_runs.length}</div>
            </article>
            <article className="snapshot-cell">
              <div className="snapshot-label">Pending proposals</div>
              <div className={`snapshot-value ${system.pending_config_proposals.length > 0 ? "tone-warn" : ""}`}>
                {system.pending_config_proposals.length}
              </div>
            </article>
            <article className="snapshot-cell">
              <div className="snapshot-label">High-risk proposals</div>
              <div className={`snapshot-value ${highRiskProposals > 0 ? "tone-warn" : ""}`}>{highRiskProposals}</div>
            </article>
            <article className="snapshot-cell">
              <div className="snapshot-label">Revisions</div>
              <div className="snapshot-value">{system.recent_config_revisions.length}</div>
            </article>
            <article className="snapshot-cell">
              <div className="snapshot-label">Owner prefs</div>
              <div className="snapshot-value">{system.owner_preferences.length}</div>
            </article>
          </div>

          <h4 className="subsection-title">What to review now</h4>
          <div className="stack tight-stack">
            {operatorFocus.map((item) => (
              <article key={item} className="stack-card compact-stack-card">
                <p className="callout">{item}</p>
              </article>
            ))}
          </div>
        </aside>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <div className="section-kicker">Operate</div>
          <h3>Operator shortcuts</h3>
          <div className="stack">
            {operatorShortcuts.map((shortcut) => (
              <article key={shortcut.title} className="stack-card">
                <strong>{shortcut.title}</strong>
                <span>{shortcut.surface}</span>
                <p className="callout">{shortcut.detail}</p>
              </article>
            ))}
          </div>
        </article>

        <article className="panel">
          <div className="section-kicker">Recover</div>
          <h3>When the authority core degrades</h3>
          <div className="stack">
            {recoveryPlaybook.map((step) => (
              <article key={step} className="stack-card">
                <p className="callout">{step}</p>
              </article>
            ))}
          </div>
        </article>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <div className="section-kicker">Providers</div>
          <h3>Provider fabric</h3>
          <div className="tile-grid">
            {system.providers.map((provider) => (
              <article key={provider.provider_key} className="tile">
                <div className="tile-label">{provider.display_name}</div>
                <div
                  className={`tile-value ${
                    ["healthy", "ok"].includes(provider.health_status.toLowerCase()) ? "tone-good" : "tone-warn"
                  }`}
                >
                  {provider.health_status}
                </div>
                <div className="tile-meta">key {provider.provider_key}</div>
                <div className="tile-meta">style {provider.api_style}</div>
                <div className="tile-meta">primary {provider.is_primary ? "yes" : "no"}</div>
                {provider.base_url ? <div className="tile-meta">{provider.base_url}</div> : null}
              </article>
            ))}
            {system.providers.length === 0 ? <div className="tile-meta">No provider profiles are visible yet.</div> : null}
          </div>
        </article>

        <article className="panel">
          <div className="section-kicker">Cadence</div>
          <h3>Supervisor loops</h3>
          <div className="tile-grid">
            {system.supervisor_loops.map((loop) => (
              <article key={loop.loop_key} className="tile">
                <div className="tile-label">{loop.display_name}</div>
                <div className={`tile-value ${loopTone(loop.last_status, loop.failure_streak)}`}>{loop.last_status}</div>
                <div className="tile-meta">domain {loop.domain}</div>
                <div className="tile-meta">mode {loop.execution_mode}</div>
                <div className="tile-meta">enabled {loop.is_enabled ? "yes" : "no"}</div>
                <div className="tile-meta">cadence {loop.cadence_seconds}s</div>
                <div className="tile-meta">next due {dateLabel(loop.next_due_at)}</div>
                {loop.last_error ? <p className="callout">{loop.last_error}</p> : null}
              </article>
            ))}
            {system.supervisor_loops.length === 0 ? <div className="tile-meta">No supervisor loop is visible yet.</div> : null}
          </div>
        </article>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <div className="section-kicker">Workflow</div>
          <h3>Recent workflows</h3>
          <div className="stack">
            {system.recent_workflows.map((workflow) => (
              <article key={workflow.id} className="stack-card">
                <strong>{workflow.workflow_name}</strong>
                <span>
                  {workflow.workflow_family} | {workflow.status}
                </span>
                <p className="callout">{workflow.latest_event_summary ?? "No latest event summary recorded."}</p>
                <p className="callout">
                  {dateLabel(workflow.started_at)}
                  {workflow.ended_at ? ` -> ${dateLabel(workflow.ended_at)}` : " -> still running"}
                </p>
              </article>
            ))}
            {system.recent_workflows.length === 0 ? <div className="tile-meta">No recent workflow evidence is visible yet.</div> : null}
          </div>
        </article>

        <article className="panel">
          <div className="section-kicker">Codex</div>
          <h3>Recent Codex activity</h3>
          <div className="stack">
            {system.recent_codex_runs.map((run) => (
              <article key={run.id} className="stack-card">
                <strong>{run.worker_class}</strong>
                <span>
                  {run.status} | {run.current_attempt}/{run.max_iterations}
                </span>
                <p className="callout">{run.objective}</p>
                <p className="callout">
                  queued {dateLabel(run.queued_at)}
                  {run.completed_at ? ` | completed ${dateLabel(run.completed_at)}` : " | still running"}
                </p>
              </article>
            ))}
            {system.recent_codex_runs.length === 0 ? <div className="tile-meta">No recent Codex system run is visible yet.</div> : null}
          </div>
        </article>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <div className="section-kicker">Runtime</div>
          <h3>Runtime config</h3>
          <div className="stack">
            {system.runtime_config.map((entry) => (
              <article key={`${entry.target_type}:${entry.target_key}`} className="stack-card">
                <strong>{entry.display_name}</strong>
                <span>
                  {entry.category} | {entry.risk_level} | mutable {entry.is_mutable ? "yes" : "no"}
                </span>
                {previewLines(entry.preview_lines, entry.value_preview).map((line, index) => (
                  <p key={`${entry.target_type}:${entry.target_key}:${index}`} className="callout">
                    {line}
                  </p>
                ))}
                <p className="callout">
                  updated {dateLabel(entry.updated_at)}
                  {entry.updated_by ? ` | by ${entry.updated_by}` : ""}
                  {entry.requires_restart ? " | restart required" : ""}
                </p>
                {entry.contains_sensitive_fields ? <p className="callout">Sensitive fields stay masked in the dashboard preview.</p> : null}
              </article>
            ))}
            {system.runtime_config.length === 0 ? <div className="tile-meta">No runtime config snapshot is visible yet.</div> : null}
          </div>
        </article>

        <article className="panel">
          <div className="section-kicker">Governance</div>
          <h3>Config change queue</h3>
          <div className="stack">
            {system.pending_config_proposals.map((proposal) => (
              <article key={proposal.id} className="stack-card">
                <strong>{proposal.display_name}</strong>
                <span>
                  {proposal.status} | {proposal.risk_level} | requested by {proposal.requested_by}
                </span>
                <p className="callout">{proposal.change_summary}</p>
                <p className="callout">
                  created {dateLabel(proposal.created_at)}
                  {proposal.approval_request_id ? ` | approval ${proposal.approval_request_id}` : ""}
                </p>
              </article>
            ))}
            {system.pending_config_proposals.length === 0 ? <div className="tile-meta">No config proposal is waiting right now.</div> : null}
          </div>
        </article>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <div className="section-kicker">History</div>
          <h3>Recent config revisions</h3>
          <div className="stack">
            {system.recent_config_revisions.map((revision) => (
              <article key={revision.id} className="stack-card">
                <strong>{revision.display_name}</strong>
                <span>{revision.applied_by}</span>
                <p className="callout">{revision.change_summary}</p>
                <p className="callout">applied {dateLabel(revision.applied_at)}</p>
              </article>
            ))}
            {system.recent_config_revisions.length === 0 ? <div className="tile-meta">No applied runtime revision is visible yet.</div> : null}
          </div>
        </article>

        <article className="panel">
          <div className="section-kicker">Intent</div>
          <h3>Owner preferences</h3>
          <div className="stack">
            {system.owner_preferences.map((preference) => (
              <article key={preference.preference_key} className="stack-card">
                <strong>{preference.display_name}</strong>
                <span>
                  {preference.scope} | updated by {preference.updated_by}
                </span>
                {previewLines(preference.preview_lines, preference.value_preview).map((line, index) => (
                  <p key={`${preference.preference_key}:${index}`} className="callout">
                    {line}
                  </p>
                ))}
                <p className="callout">updated {dateLabel(preference.updated_at)}</p>
                {preference.contains_sensitive_fields ? <p className="callout">Sensitive fields stay masked in dashboard previews.</p> : null}
              </article>
            ))}
            {system.owner_preferences.length === 0 ? <div className="tile-meta">No owner preference has been captured yet.</div> : null}
          </div>
        </article>
      </section>
    </>
  );
}
