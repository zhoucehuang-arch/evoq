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
          <h3>Provider Profiles</h3>
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
        </article>

        <article className="panel">
          <h3>Supervisor Loops</h3>
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
        </article>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <h3>Recent Workflows</h3>
          <div className="stack">
            {system.recent_workflows.map((workflow) => (
              <article key={workflow.id} className="stack-card">
                <strong>{workflow.workflow_name}</strong>
                <span>{workflow.status}</span>
                <p className="callout">{workflow.latest_event_summary ?? "No latest event summary."}</p>
              </article>
            ))}
          </div>
        </article>

        <article className="panel">
          <h3>Recent Codex Runs</h3>
          <div className="stack">
            {system.recent_codex_runs.map((run) => (
              <article key={run.id} className="stack-card">
                <strong>{run.worker_class}</strong>
                <span>
                  {run.status} | {run.current_attempt}/{run.max_iterations}
                </span>
                <p className="callout">{run.objective}</p>
              </article>
            ))}
          </div>
        </article>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <h3>Runtime Config</h3>
          <div className="stack">
            {system.runtime_config.map((entry) => (
              <article key={`${entry.target_type}:${entry.target_key}`} className="stack-card">
                <strong>{entry.display_name}</strong>
                <span>
                  {entry.target_type} | {entry.category} | {entry.risk_level}
                </span>
                <p className="callout">{JSON.stringify(entry.value_json)}</p>
              </article>
            ))}
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
            {system.owner_preferences.map((preference) => (
              <article key={preference.preference_key} className="stack-card">
                <strong>{preference.display_name}</strong>
                <span>{preference.updated_by}</span>
                <p className="callout">{JSON.stringify(preference.value_json)}</p>
              </article>
            ))}
          </div>
        </article>
      </section>
    </>
  );
}
