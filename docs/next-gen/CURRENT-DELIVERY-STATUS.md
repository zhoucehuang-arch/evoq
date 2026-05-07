# Current Delivery Status

## Date

2026-05-07

## Summary

Repository-side implementation is ready for local dashboard-first paper-mode operation and GitHub-to-VPS deployment hardening.

The system now has a deterministic quant backbone in addition to the earlier governance/runtime shell:

- local replay market data
- historical bars
- factor snapshots
- PIT factor replay backtests
- cost/slippage and baseline gates
- input-bar lineage
- execution readiness with stale quote blocking

## What Is Working In The Repository

- dashboard-first owner flow across Workbench, Research, Strategy, Data, Trading, Learning, Evolution, System, and Incidents
- local Windows startup and smoke tooling under `ops/tools`
- market data provider registry, watchlists, quote snapshots, freshness, replay bars, and historical bars
- deterministic factors: `momentum_close_return`, `reversal_close_return`, `realized_volatility`, `dollar_volume_liquidity`
- strategy lifecycle records for hypothesis, spec, backtest, paper, promotion, and withdrawal
- PIT factor replay backtest with costs, slippage, baseline comparison, input-bar lineage, and equity curve
- execution readiness checks for market session, broker snapshot, reconciliation, provider incidents, overrides, and stale quotes
- report-only live-readiness endpoint that cannot place orders
- Codex-backed execution fabric for implementation/testing/docs/evolution tasks
- single-VPS-first deployment docs and Core/Worker scale-out material
- backup, restore, break-glass, security, support, contribution, issue, and PR guidance

## What Was Verified In This Repository

- `npm run build` passed in `apps/dashboard-web`
- `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ops\tools\run_tests.ps1 -q` passed with `135` tests
- `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ops\tools\smoke_local.ps1` passed after local runtime restart
- `git diff --check` passed

## What Still Has To Be Verified On Real VPS Nodes

- actual Core deployment on the target Linux host
- actual Worker deployment, if two-node topology is chosen
- real secrets and relay configuration
- real private-network connectivity between Core and Worker
- real broker sync on the target deployment
- restore drill and break-glass rehearsal
- real restart behavior under systemd
- paper-mode broker behavior with the owner's chosen credentials and market mode

## Conservative Boundaries Still In Place

- live trading is not the default path
- CN live broker execution is not shipped and must remain paper-first
- broker integrations require environment-specific verification
- LLM output cannot bypass quant, paper, risk, or approval gates
- backtests cannot pass without cost assumptions, baseline comparison, PIT controls, and data lineage
- stale existing market data blocks execution readiness after the 48-hour threshold

## Practical Conclusion

For repository work, EvoQ is ready to publish as a coherent dashboard-first quant/LLM project.

For live operation, the remaining work is environment truth: deploy on the target VPS, configure real secrets, run smoke/doctor/broker sync, rehearse restore and break-glass, and stay in paper mode until evidence and approvals are clean.
