import { pauseDomainAction, resumeDomainAction } from "@/app/actions";
import type { DomainControlState } from "@/lib/types";

type TradingDomainControlsProps = {
  controlNote: string | null;
  domainStates: DomainControlState[];
};

export function TradingDomainControls({ controlNote, domainStates }: TradingDomainControlsProps) {
  return (
    <article className="panel">
      <div className="section-kicker">Controls</div>
      <h3>Domain controls</h3>
      {controlNote ? <div className="form-status form-status-warn">{controlNote}</div> : null}
      <div className="tile-grid">
        {domainStates.map((state) => (
          <article key={state.domain} className="tile">
            <div className="tile-label">{state.domain}</div>
            <div className={`tile-value ${state.is_paused ? "tone-warn" : "tone-good"}`}>
              {state.is_paused ? "Paused" : "Running"}
            </div>
            <div className="tile-meta">pending approvals {state.pending_approval_count}</div>
            <div className="tile-meta">active overrides {state.override_count}</div>
            {state.latest_reason ? <p className="callout">{state.latest_reason}</p> : null}
            <div className="action-row">
              <form action={pauseDomainAction}>
                <input type="hidden" name="domain" value={state.domain} />
                <button className="secondary-action secondary-action-danger" type="submit">
                  Pause
                </button>
              </form>
              <form action={resumeDomainAction}>
                <input type="hidden" name="domain" value={state.domain} />
                <button className="secondary-action" type="submit">
                  Resume
                </button>
              </form>
            </div>
          </article>
        ))}
        {domainStates.length === 0 ? <div className="tile-meta">No governed domain state yet.</div> : null}
      </div>
    </article>
  );
}
