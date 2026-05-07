import {
  generateFactorSnapshotsAction,
  ingestReplayBarsAction,
  recordMarketQuoteAction,
  upsertMarketDataProviderAction,
  upsertWatchlistAction,
  upsertWatchlistItemAction,
} from "@/app/actions";
import { fetchMarketDataWorkbench } from "@/lib/dashboard";

type DataPageProps = {
  searchParams?: Promise<{
    data?: string;
    code?: string;
  }>;
};

function message(status?: string, code?: string): string | null {
  switch (status) {
    case "provider_saved":
      return "Market data provider saved.";
    case "watchlist_saved":
      return "Watchlist saved.";
    case "symbol_saved":
      return "Watchlist item saved.";
    case "quote_recorded":
      return "Quote snapshot recorded.";
    case "replay_ingested":
      return "Replay historical bars ingested.";
    case "factors_generated":
      return "Factor snapshots generated.";
    case "missing_provider":
      return "Provider key and display name are required.";
    case "missing_watchlist":
      return "Watchlist key and display name are required.";
    case "missing_symbol":
      return "Watchlist item requires watchlist key and symbol.";
    case "missing_quote":
      return "Quote recording requires provider key and symbol.";
    case "missing_bars":
      return "Replay ingest requires provider key and a non-empty JSON bar array.";
    case "failed":
      return `Operation failed${code ? ` with HTTP ${code}` : ""}.`;
    case "unavailable":
      return "Backend unavailable.";
    default:
      return null;
  }
}

function timeLabel(value: string): string {
  return new Date(value).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default async function DataPage({ searchParams }: DataPageProps) {
  const params = searchParams ? await searchParams : undefined;
  const data = await fetchMarketDataWorkbench();
  const note = message(params?.data, params?.code);

  return (
    <>
      <section className="metric-strip" aria-label="Market data metrics">
        <article className="metric-card metric-card-good">
          <div className="metric-kicker">Fresh</div>
          <div className="metric-value tone-good">{data.freshness.fresh}</div>
          <div className="metric-note">symbols with recent quotes</div>
        </article>
        <article className="metric-card metric-card-warn">
          <div className="metric-kicker">Stale</div>
          <div className="metric-value tone-warn">{data.freshness.stale}</div>
          <div className="metric-note">symbols that need refresh</div>
        </article>
        <article className="metric-card metric-card-bad">
          <div className="metric-kicker">Missing</div>
          <div className="metric-value tone-bad">{data.freshness.missing}</div>
          <div className="metric-note">symbols without usable quotes</div>
        </article>
        <article className="metric-card metric-card-neutral">
          <div className="metric-kicker">Factors</div>
          <div className="metric-value">{data.factor_snapshots.length}</div>
          <div className="metric-note">deterministic signal snapshots</div>
        </article>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <div>
            <div className="section-kicker">Data Workbench</div>
            <h2 className="headline">Register provider truth, baskets, symbols, and quote freshness.</h2>
            <p className="panel-copy">
              Research and strategy should not assume data exists. This page makes provider readiness and symbol freshness
              explicit, so the owner can see what the runtime can actually trust.
            </p>
          </div>
          <div className="panel-badge-row">
            <span className="panel-badge">Provider</span>
            <span className="panel-badge">Watchlist</span>
            <span className="panel-badge">Quote</span>
            <span className="panel-badge">Replay</span>
            <span className="panel-badge">Factor</span>
            <span className="panel-badge">Freshness</span>
          </div>
        </div>

        {note ? <div className="form-status form-status-warn">{note}</div> : null}

        <div className="detail-grid two-col">
          <article className="panel compact-panel">
            <div className="section-kicker">Provider</div>
            <h3>Register provider</h3>
            <form action={upsertMarketDataProviderAction} className="stack tight-stack">
              <label className="field">
                <span>Provider key</span>
                <input name="provider_key" placeholder="alpha-vantage" required />
              </label>
              <label className="field">
                <span>Display name</span>
                <input name="display_name" placeholder="Alpha Vantage" required />
              </label>
              <label className="field">
                <span>Provider type</span>
                <select name="provider_type" defaultValue="data_vendor">
                  <option value="data_vendor">data_vendor</option>
                  <option value="broker">broker</option>
                  <option value="scraper">scraper</option>
                  <option value="internal">internal</option>
                  <option value="custom">custom</option>
                </select>
              </label>
              <label className="field">
                <span>Market coverage</span>
                <textarea name="market_coverage" rows={3} placeholder="us_equities" />
              </label>
              <label className="field">
                <span>Entitlement state</span>
                <input name="entitlement_state" placeholder="ready" />
              </label>
              <label className="field">
                <span>Health state</span>
                <input name="health_status" placeholder="healthy" />
              </label>
              <label className="field">
                <span>Latency ms</span>
                <input name="latency_ms" type="number" min="0" />
              </label>
              <label className="field">
                <span>Freshness SLA seconds</span>
                <input name="freshness_sla_seconds" type="number" min="1" defaultValue="120" />
              </label>
              <label className="field">
                <span>Notes</span>
                <textarea name="notes" rows={3} />
              </label>
              <label className="field">
                <span>Realtime</span>
                <input name="supports_realtime" type="checkbox" />
              </label>
              <label className="field">
                <span>Historical</span>
                <input name="supports_historical" type="checkbox" defaultChecked />
              </label>
              <button className="primary-action" type="submit">
                Save provider
              </button>
            </form>
          </article>

          <article className="panel compact-panel">
            <div className="section-kicker">Watchlists and quotes</div>
            <h3>Basket and symbol control</h3>
            <div className="stack tight-stack">
              <form action={upsertWatchlistAction} className="stack tight-stack">
                <label className="field">
                  <span>Watchlist key</span>
                  <input name="watchlist_key" placeholder="owner-us-core" required />
                </label>
                <label className="field">
                  <span>Display name</span>
                  <input name="display_name" placeholder="Owner US Core" required />
                </label>
                <label className="field">
                  <span>Market scope</span>
                  <input name="market_scope" placeholder="us_equities" defaultValue="us_equities" />
                </label>
                <label className="field">
                  <span>Description</span>
                  <textarea name="description" rows={3} />
                </label>
                <label className="field">
                  <span>Default</span>
                  <input name="is_default" type="checkbox" />
                </label>
                <button className="secondary-action" type="submit">
                  Save watchlist
                </button>
              </form>

              <form action={upsertWatchlistItemAction} className="stack tight-stack">
                <label className="field">
                  <span>Watchlist key</span>
                  <input name="watchlist_key" placeholder="owner-us-core" required />
                </label>
                <label className="field">
                  <span>Symbol</span>
                  <input name="symbol" placeholder="AAPL" required />
                </label>
                <label className="field">
                  <span>Instrument key</span>
                  <input name="instrument_key" />
                </label>
                <label className="field">
                  <span>Market</span>
                  <input name="market" placeholder="us_equities" defaultValue="us_equities" />
                </label>
                <label className="field">
                  <span>Venue</span>
                  <input name="venue" placeholder="NASDAQ" />
                </label>
                <label className="field">
                  <span>Currency</span>
                  <input name="currency" defaultValue="USD" />
                </label>
                <label className="field">
                  <span>Priority</span>
                  <input name="priority" type="number" min="0" defaultValue="100" />
                </label>
                <label className="field">
                  <span>Metadata JSON</span>
                  <textarea name="metadata_payload" rows={3} placeholder='{"theme": "core"}' />
                </label>
                <button className="secondary-action" type="submit">
                  Save item
                </button>
              </form>

              <form action={recordMarketQuoteAction} className="stack tight-stack">
                <label className="field">
                  <span>Provider key</span>
                  <input name="provider_key" placeholder="paper-sim" required />
                </label>
                <label className="field">
                  <span>Symbol</span>
                  <input name="symbol" placeholder="AAPL" required />
                </label>
                <label className="field">
                  <span>Market</span>
                  <input name="market" placeholder="us_equities" defaultValue="us_equities" />
                </label>
                <label className="field">
                  <span>Venue</span>
                  <input name="venue" placeholder="NASDAQ" />
                </label>
                <div className="detail-grid two-col">
                  <label className="field">
                    <span>Bid</span>
                    <input name="bid" type="number" step="0.01" />
                  </label>
                  <label className="field">
                    <span>Ask</span>
                    <input name="ask" type="number" step="0.01" />
                  </label>
                  <label className="field">
                    <span>Last</span>
                    <input name="last" type="number" step="0.01" />
                  </label>
                  <label className="field">
                    <span>Volume</span>
                    <input name="volume" type="number" step="1" />
                  </label>
                </div>
                <label className="field">
                  <span>Latency ms</span>
                  <input name="source_latency_ms" type="number" min="0" />
                </label>
                <label className="field">
                  <span>Realtime</span>
                  <input name="is_realtime" type="checkbox" />
                </label>
                <label className="field">
                  <span>Payload JSON</span>
                  <textarea name="payload" rows={3} placeholder='{"source": "dashboard"}' />
                </label>
                <button className="secondary-action" type="submit">
                  Save quote
                </button>
              </form>
            </div>
          </article>
        </div>

        <div className="detail-grid two-col">
          <article className="panel compact-panel">
            <div className="section-kicker">Local replay</div>
            <h3>Import historical bars</h3>
            <p className="panel-copy">
              Paste deterministic OHLCV bars. EvoQ stores the bars, records the ingestion run, and derives a latest
              quote snapshot for freshness checks.
            </p>
            <form action={ingestReplayBarsAction} className="stack tight-stack">
              <label className="field">
                <span>Provider key</span>
                <input name="provider_key" placeholder="local-replay" defaultValue="local-replay" required />
              </label>
              <label className="field">
                <span>Source ref</span>
                <input name="source_ref" placeholder="manual-demo-bars.json" />
              </label>
              <div className="detail-grid two-col">
                <label className="field">
                  <span>Market</span>
                  <input name="market" defaultValue="us_equities" />
                </label>
                <label className="field">
                  <span>Timeframe</span>
                  <input name="timeframe" defaultValue="1d" />
                </label>
              </div>
              <input name="adapter_key" type="hidden" value="local_replay" />
              <label className="field">
                <span>Bars JSON array</span>
                <textarea
                  name="bars_json"
                  rows={9}
                  defaultValue={`[
  {"symbol":"AAPL","bar_start":"2026-05-04T00:00:00Z","open":185,"high":188,"low":184,"close":187,"volume":1200000},
  {"symbol":"AAPL","bar_start":"2026-05-05T00:00:00Z","open":187,"high":190,"low":186,"close":189,"volume":1250000},
  {"symbol":"AAPL","bar_start":"2026-05-06T00:00:00Z","open":189,"high":193,"low":188,"close":192,"volume":1320000}
]`}
                />
              </label>
              <button className="primary-action" type="submit">
                Ingest replay bars
              </button>
            </form>
          </article>

          <article className="panel compact-panel">
            <div className="section-kicker">Factor engine</div>
            <h3>Generate deterministic factor</h3>
            <p className="panel-copy">
              LLMs can suggest ideas, but this kernel computes evidence deterministically, including custom linear
              combinations from approved components.
            </p>
            <form action={generateFactorSnapshotsAction} className="stack tight-stack">
              <label className="field">
                <span>Factor code</span>
                <select name="factor_code" defaultValue="momentum_close_return">
                  <option value="momentum_close_return">momentum_close_return</option>
                  <option value="reversal_close_return">reversal_close_return</option>
                  <option value="realized_volatility">realized_volatility</option>
                  <option value="dollar_volume_liquidity">dollar_volume_liquidity</option>
                  <option value="intraday_return">intraday_return</option>
                  <option value="overnight_gap">overnight_gap</option>
                  <option value="range_position">range_position</option>
                  <option value="volume_trend">volume_trend</option>
                  <option value="risk_adjusted_momentum">risk_adjusted_momentum</option>
                  <option value="liquidity_adjusted_momentum">liquidity_adjusted_momentum</option>
                  <option value="custom_linear_combo">custom_linear_combo</option>
                </select>
              </label>
              <label className="field">
                <span>Factor name</span>
                <input name="factor_name" defaultValue="Close-to-close momentum return" />
              </label>
              <label className="field">
                <span>Custom expression</span>
                <textarea
                  name="custom_expression"
                  rows={3}
                  placeholder="0.6 * momentum + 0.3 * volume_trend - 0.1 * volatility"
                />
              </label>
              <label className="field">
                <span>Provider key optional</span>
                <input name="provider_key" placeholder="local-replay" />
              </label>
              <label className="field">
                <span>Symbols optional</span>
                <textarea name="symbols" rows={3} placeholder="AAPL, MSFT" />
              </label>
              <div className="detail-grid two-col">
                <label className="field">
                  <span>Market</span>
                  <input name="market" defaultValue="us_equities" />
                </label>
                <label className="field">
                  <span>Timeframe</span>
                  <input name="timeframe" defaultValue="1d" />
                </label>
                <label className="field">
                  <span>Lookback bars</span>
                  <input name="lookback_bars" type="number" min="2" defaultValue="3" />
                </label>
                <label className="field">
                  <span>As of optional</span>
                  <input name="as_of" type="datetime-local" />
                </label>
              </div>
              <button className="primary-action" type="submit">
                Generate factors
              </button>
            </form>
          </article>
        </div>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <div className="section-kicker">Providers</div>
          <h3>Registered data providers</h3>
          <div className="stack tight-stack">
            {data.providers.map((provider) => (
              <article key={provider.id} className="stack-card compact-stack-card">
                <strong>{provider.display_name}</strong>
                <div className="tile-meta">{provider.provider_key} | {provider.provider_type} | {provider.health_status}</div>
                <p className="callout">Coverage: {provider.market_coverage.join(", ") || "n/a"}</p>
                <div className="tile-meta">Updated {timeLabel(provider.updated_at)}</div>
              </article>
            ))}
            {data.providers.length === 0 ? <div className="tile-meta">No provider saved yet.</div> : null}
          </div>
        </article>

        <article className="panel">
          <div className="section-kicker">Freshness</div>
          <h3>Quote freshness</h3>
          <div className="stack tight-stack">
            {data.freshness.items.map((item) => (
              <article key={`${item.symbol}-${item.market}`} className="stack-card compact-stack-card">
                <strong>{item.symbol}</strong>
                <div className="tile-meta">{item.market} | {item.status} | {item.provider_key ?? "n/a"}</div>
                <p className="callout">
                  {item.reason ?? "Freshness tracked from latest quote snapshot."}
                </p>
                <div className="tile-meta">Age: {item.age_seconds ?? "n/a"} seconds | Last: {item.last_price ?? "n/a"}</div>
              </article>
            ))}
            {data.freshness.items.length === 0 ? <div className="tile-meta">No freshness items yet.</div> : null}
          </div>
        </article>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <div className="section-kicker">Watchlists</div>
          <h3>Curated baskets</h3>
          <div className="stack tight-stack">
            {data.watchlists.map((watchlist) => (
              <article key={watchlist.id} className="stack-card compact-stack-card">
                <strong>{watchlist.display_name}</strong>
                <div className="tile-meta">{watchlist.watchlist_key} | {watchlist.market_scope} | {watchlist.is_default ? "default" : "custom"}</div>
                <p className="callout">{watchlist.description ?? "No description."}</p>
                <div className="tile-meta">{watchlist.item_count} items | Updated {timeLabel(watchlist.updated_at)}</div>
              </article>
            ))}
            {data.watchlists.length === 0 ? <div className="tile-meta">No watchlist saved yet.</div> : null}
          </div>
        </article>

        <article className="panel">
          <div className="section-kicker">Items and quotes</div>
          <h3>Watchlist items and latest quotes</h3>
          <div className="stack tight-stack">
            {data.watchlist_items.map((item) => (
              <article key={item.id} className="stack-card compact-stack-card">
                <strong>{item.symbol}</strong>
                <div className="tile-meta">{item.watchlist_key} | {item.market} | priority {item.priority}</div>
                <p className="callout">{item.venue ?? "venue n/a"} | {item.currency}</p>
                <div className="tile-meta">{timeLabel(item.updated_at)}</div>
              </article>
            ))}
            {data.watchlist_items.length === 0 ? <div className="tile-meta">No watchlist item saved yet.</div> : null}
          </div>
          <h4 className="subsection-title">Latest quotes</h4>
          <div className="stack tight-stack">
            {data.quotes.map((quote) => (
              <article key={quote.id} className="stack-card compact-stack-card">
                <strong>{quote.symbol}</strong>
                <div className="tile-meta">{quote.provider_key} | {quote.market} | {quote.venue ?? "n/a"}</div>
                <p className="callout">
                  bid {quote.bid ?? "n/a"} | ask {quote.ask ?? "n/a"} | last {quote.last ?? "n/a"} | vol {quote.volume ?? "n/a"}
                </p>
                <div className="tile-meta">{timeLabel(quote.as_of)}</div>
              </article>
            ))}
            {data.quotes.length === 0 ? <div className="tile-meta">No quote snapshot recorded yet.</div> : null}
          </div>
        </article>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <div className="section-kicker">Historical store</div>
          <h3>Recent ingestion runs and bars</h3>
          <div className="stack tight-stack">
            {data.ingestion_runs.map((run) => (
              <article key={run.id} className="stack-card compact-stack-card">
                <strong>{run.provider_key}</strong>
                <div className="tile-meta">
                  {run.adapter_key} | {run.market} | {run.status}
                </div>
                <p className="callout">
                  {run.bar_count} bars | {run.symbols.join(", ") || "no symbols"} | {run.source_ref ?? "manual"}
                </p>
                <div className="tile-meta">Started {timeLabel(run.started_at)}</div>
              </article>
            ))}
            {data.ingestion_runs.length === 0 ? <div className="tile-meta">No historical replay ingested yet.</div> : null}
          </div>
          <h4 className="subsection-title">Recent bars</h4>
          <div className="stack tight-stack">
            {data.historical_bars.slice(0, 8).map((bar) => (
              <article key={bar.id} className="stack-card compact-stack-card">
                <strong>{bar.symbol}</strong>
                <div className="tile-meta">
                  {bar.provider_key} | {bar.market} | {bar.timeframe} | {timeLabel(bar.bar_start)}
                </div>
                <p className="callout">
                  O {bar.open} | H {bar.high} | L {bar.low} | C {bar.close} | Vol {bar.volume ?? "n/a"}
                </p>
              </article>
            ))}
            {data.historical_bars.length === 0 ? <div className="tile-meta">No bars stored yet.</div> : null}
          </div>
        </article>

        <article className="panel">
          <div className="section-kicker">Factors</div>
          <h3>Deterministic factor snapshots</h3>
          <div className="stack tight-stack">
            {data.factor_snapshots.map((factor) => (
              <article key={factor.id} className="stack-card compact-stack-card">
                <strong>{factor.symbol}</strong>
                <div className="tile-meta">
                  {factor.factor_code} | rank {factor.rank ?? "n/a"} | pct{" "}
                  {factor.percentile == null ? "n/a" : `${(factor.percentile * 100).toFixed(0)}%`}
                </div>
                <p className="callout">
                  value {(factor.value * 100).toFixed(2)}% over {factor.lookback_bars} bars | inputs{" "}
                  {factor.input_bar_ids.length}
                </p>
                <div className="tile-meta">As of {timeLabel(factor.as_of)}</div>
              </article>
            ))}
            {data.factor_snapshots.length === 0 ? <div className="tile-meta">No factor snapshots generated yet.</div> : null}
          </div>
        </article>
      </section>
    </>
  );
}
