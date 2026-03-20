import { fetchSystem } from "@/lib/dashboard";

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

export default async function SystemPage() {
  const system = await fetchSystem();
  const isDegraded = system.freshness.state === "broken" || system.freshness.state === "stale";
  const operatorShortcuts = [
    {
      title: "Fast health check",
      surface: "SSH",
      detail: "Run ./ops/bin/core-smoke.sh and ./ops/bin/worker-smoke.sh before trusting live state after any change.",
    },
    {
      title: "Pause trading, keep learning",
      surface: "Discord",
      detail: "Use the Discord control surface to halt automated trading without turning off research and learning loops.",
    },
    {
      title: "Review config drift",
      surface: "Dashboard + Discord",
      detail: "Inspect runtime config and recent revisions here, then request governed changes or rollbacks through Discord.",
    },
    {
      title: "Upgrade from GitHub",
      surface: "SSH",
      detail: "Use ./ops/bin/update-from-github.sh core and worker so updates stay repeatable and smoke-checked.",
    },
  ];
  const degradedChecklist = [
    "Check whether freshness is stale because the API is down, the Worker is blocked, or provider connectivity is degraded.",
    "Pause the affected domain if trading safety could be impacted.",
    "Compare recent workflows, Codex runs, and incidents before assuming the problem is only visual.",
    "If smoke checks fail, move to SSH and the relevant recovery runbook instead of making blind config edits.",
  ];

  return (
    <>
      <section className="hero">
        <article className="panel hero-panel">
          <div className="chip-row">
            <span className="chip">
              Freshness <strong>{system.freshness.state}</strong>
            </span>
          </div>
          <h2 className="headline">Authority Core</h2>
          <ul className="list">
            {system.highlights.map((highlight) => (
              <li key={highlight}>{highlight}</li>
            ))}
          </ul>
          {system.freshness.note ? <p className="callout">Freshness note: {system.freshness.note}</p> : null}
        </article>
      </section>

      <section className="card-grid">
        {system.summary_cards.map((card) => (
          <article key={card.label} className="stat-card">
            <div className="stat-label">{card.label}</div>
            <div className={`stat-value ${toneClass(card.tone)}`}>{card.value}</div>
          </article>
        ))}
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <div className="section-kicker">Operate</div>
          <h3>Operator Shortcuts</h3>
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
          <div className="section-kicker">{isDegraded ? "Recover" : "Prepare"}</div>
          <h3>{isDegraded ? "System is degraded: do this first" : "If freshness turns stale or broken"}</h3>
          <div className="stack">
            {degradedChecklist.map((step) => (
              <article key={step} className="stack-card">
                <p className="callout">{step}</p>
              </article>
            ))}
          </div>
        </article>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <h3>Provider Profiles</h3>
          {system.providers.length === 0 ? (
            <div className="stack">
              <article className="stack-card">
                <strong>No provider profiles yet</strong>
                <p className="callout">This usually means the dashboard is still waiting for authority-core data.</p>
              </article>
            </div>
          ) : (
            <div className="table-shell">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Provider</th>
                    <th>Primary</th>
                    <th>Status</th>
                    <th>Base URL</th>
                  </tr>
                </thead>
                <tbody>
                  {system.providers.map((provider) => (
                    <tr key={provider.provider_key}>
                      <td>{provider.display_name}</td>
                      <td>{provider.is_primary ? "yes" : "no"}</td>
                      <td>{provider.health_status}</td>
                      <td>{provider.base_url ?? "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </article>

        <article className="panel">
          <h3>Supervisor Loops</h3>
          {system.supervisor_loops.length === 0 ? (
            <div className="stack">
              <article className="stack-card">
                <strong>No supervisor loops visible yet</strong>
                <p className="callout">Check freshness, backend connectivity, and recent system incidents before trusting this as healthy.</p>
              </article>
            </div>
          ) : (
            <div className="table-shell">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Loop</th>
                    <th>Domain</th>
                    <th>Status</th>
                    <th>Cadence</th>
                  </tr>
                </thead>
                <tbody>
                  {system.supervisor_loops.map((loop) => (
                    <tr key={loop.loop_key}>
                      <td>{loop.display_name}</td>
                      <td>{loop.domain}</td>
                      <td>{loop.last_status}</td>
                      <td>{loop.cadence_seconds}s</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </article>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <h3>Recent Workflows</h3>
          <div className="stack">
            {system.recent_workflows.length === 0 ? (
              <article className="stack-card">
                <strong>No recent workflows</strong>
                <p className="callout">Workflow evidence will appear here when the authority core is ingesting runtime state normally.</p>
              </article>
            ) : (
              system.recent_workflows.map((workflow) => (
                <article key={workflow.id} className="stack-card">
                  <strong>{workflow.workflow_name}</strong>
                  <span>{workflow.status}</span>
                  <p className="callout">{workflow.latest_event_summary ?? "No latest event summary."}</p>
                </article>
              ))
            )}
          </div>
        </article>

        <article className="panel">
          <h3>Recent Codex Runs</h3>
          <div className="stack">
            {system.recent_codex_runs.length === 0 ? (
              <article className="stack-card">
                <strong>No recent Codex runs</strong>
                <p className="callout">If you expected worker activity, verify the Worker role, provider access, and queue health.</p>
              </article>
            ) : (
              system.recent_codex_runs.map((run) => (
                <article key={run.id} className="stack-card">
                  <strong>{run.worker_class}</strong>
                  <span>
                    {run.status} | {run.current_attempt}/{run.max_iterations}
                  </span>
                  <p className="callout">{run.objective}</p>
                </article>
              ))
            )}
          </div>
        </article>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <h3>Runtime Config</h3>
          <div className="stack">
            {system.runtime_config.length === 0 ? (
              <article className="stack-card">
                <strong>No runtime config snapshot</strong>
                <p className="callout">Runtime config should appear here after the dashboard can read authority-core state.</p>
              </article>
            ) : (
              system.runtime_config.map((entry) => (
                <article key={`${entry.target_type}:${entry.target_key}`} className="stack-card">
                  <strong>{entry.display_name}</strong>
                  <span>
                    {entry.target_type} | {entry.category} | {entry.risk_level}
                  </span>
                  <p className="callout">{JSON.stringify(entry.value_json)}</p>
                </article>
              ))
            )}
          </div>
        </article>

        <article className="panel">
          <h3>Config Proposals</h3>
          <div className="stack">
            {system.pending_config_proposals.length === 0 ? (
              <article className="stack-card">
                <strong>No pending proposals</strong>
                <p className="callout">Runtime config changes are currently settled.</p>
              </article>
            ) : (
              system.pending_config_proposals.map((proposal) => (
                <article key={proposal.id} className="stack-card">
                  <strong>{proposal.display_name}</strong>
                  <span>
                    {proposal.status} | {proposal.risk_level} | {proposal.requested_by}
                  </span>
                  <p className="callout">{proposal.change_summary}</p>
                </article>
              ))
            )}
          </div>
        </article>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <h3>Recent Config Revisions</h3>
          <div className="stack">
            {system.recent_config_revisions.length === 0 ? (
              <article className="stack-card">
                <strong>No config revisions yet</strong>
                <p className="callout">Applied runtime config versions will appear here.</p>
              </article>
            ) : (
              system.recent_config_revisions.map((revision) => (
                <article key={revision.id} className="stack-card">
                  <strong>{revision.display_name}</strong>
                  <span>{revision.applied_by}</span>
                  <p className="callout">{revision.change_summary}</p>
                </article>
              ))
            )}
          </div>
        </article>

        <article className="panel">
          <h3>Owner Preferences</h3>
          <div className="stack">
            {system.owner_preferences.length === 0 ? (
              <article className="stack-card">
                <strong>No owner preferences yet</strong>
                <p className="callout">Owner-level preferences will show up here once they have been captured and written through the governed path.</p>
              </article>
            ) : (
              system.owner_preferences.map((preference) => (
                <article key={preference.preference_key} className="stack-card">
                  <strong>{preference.display_name}</strong>
                  <span>{preference.updated_by}</span>
                  <p className="callout">{JSON.stringify(preference.value_json)}</p>
                </article>
              ))
            )}
          </div>
        </article>
      </section>
    </>
  );
}
