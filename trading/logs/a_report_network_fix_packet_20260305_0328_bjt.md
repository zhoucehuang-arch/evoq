# A Report - Network Reliability Fix Packet

- generated_at_bjt: 2026-03-05T03:28:00+08:00
- search_provider: one-search(searxng-compat)
- fallback_status: provider_up_primary
- source_quality: medium
- freshness: real-time probe
- corroboration: config+probe dual evidence

## Summary
- Root cause fixed: one-search backend dependency at `localhost:8888` was down.
- Action: deployed local SearXNG-compatible bridge and restored query responses.

## Probe
- provider_up: `http://127.0.0.1:8888/health` => `status=ok`
- sample_query: `http://127.0.0.1:8888/search?q=adp+jobs+report&format=json` => success with results
