# EvoQ First 5 Minutes

This path starts a local paper-only runtime, imports bundled OHLCV data, generates a factor snapshot, and runs one deterministic factor replay backtest.

## 1. Start The Local Runtime

```bash
./ops/tools/start_local.sh
./ops/tools/smoke_local.sh
```

Open:

- Dashboard: `http://127.0.0.1:3000`
- API health: `http://127.0.0.1:8000/healthz`

The local script uses SQLite at `.runtime/evoq-local.db`, sets `QE_DASHBOARD_API_TOKEN=local-dev-token`, and keeps broker execution in simulated/paper mode.

## 2. Import Sample OHLCV Bars

```bash
export EVOQ_API=http://127.0.0.1:8000
export EVOQ_TOKEN=local-dev-token

curl -sS \
  -H "Content-Type: application/json" \
  -H "X-Quant-Evo-Dashboard-Token: ${EVOQ_TOKEN}" \
  --data-binary @sample-data/ohlcv/us-local-replay.json \
  "${EVOQ_API}/api/v1/market-data/replay-bars"
```

The sample contains 130 adjusted daily bars each for `AAPL`, `MSFT`, and `QQQ`.

## 3. Generate Factor Snapshots

```bash
curl -sS \
  -H "Content-Type: application/json" \
  -H "X-Quant-Evo-Dashboard-Token: ${EVOQ_TOKEN}" \
  -d '{"provider_key":"local-replay","factor_code":"momentum_close_return","factor_name":"Close-to-close momentum return","lookback_bars":120,"symbols":["AAPL","MSFT","QQQ"],"created_by":"tutorial"}' \
  "${EVOQ_API}/api/v1/market-data/factors/generate"
```

## 4. Create A Strategy Spec

```bash
HYPOTHESIS_ID="$(
  curl -sS -H "Content-Type: application/json" -H "X-Quant-Evo-Dashboard-Token: ${EVOQ_TOKEN}" \
    -d '{"title":"Sample momentum replay","thesis":"Recent close-to-close momentum can rank a small US equity universe.","target_market":"us_equities","mechanism":"Select the highest momentum symbol after point-in-time factor generation.","created_by":"tutorial"}' \
    "${EVOQ_API}/api/v1/strategy/hypotheses" \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])'
)"

SPEC_ID="$(
  curl -sS -H "Content-Type: application/json" -H "X-Quant-Evo-Dashboard-Token: ${EVOQ_TOKEN}" \
    -d "{\"hypothesis_id\":\"${HYPOTHESIS_ID}\",\"spec_code\":\"sample-momentum-001\",\"title\":\"Sample momentum replay\",\"target_market\":\"us_equities\",\"signal_logic\":\"Long the highest close-to-close momentum symbol in the local replay universe.\",\"created_by\":\"tutorial\"}" \
    "${EVOQ_API}/api/v1/strategy/specs" \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])'
)"
```

## 5. Run The First Factor Replay Backtest

```bash
curl -sS \
  -H "Content-Type: application/json" \
  -H "X-Quant-Evo-Dashboard-Token: ${EVOQ_TOKEN}" \
  -d "{\"strategy_spec_id\":\"${SPEC_ID}\",\"provider_key\":\"local-replay\",\"factor_code\":\"momentum_close_return\",\"top_n\":1,\"cost_model\":{\"fixed_bps\":1,\"commission_bps\":0.5,\"spread_bps\":1,\"participation_rate_slippage_bps\":5,\"square_root_impact_coefficient\":0.1,\"trade_notional\":10000},\"created_by\":\"tutorial\"}" \
  "${EVOQ_API}/api/v1/strategy/backtests/factor-replay"
```

After this, the Dashboard `Data` and `Strategy` pages should show the imported bars, factor snapshots, and the replay backtest gate result.
