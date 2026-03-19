# Break-Glass Runbook

## 1. Immediate safe-mode action

If the API is still reachable:

```bash
cd /opt/quant-evo-nextgen
./ops/bin/qe-enter-safe-mode.sh http://127.0.0.1:8000 break-glass-admin "manual takeover"
```

This creates active pause overrides for:

- trading
- evolution
- learning

## 2. If the API is unhealthy

On the core VPS:

```bash
cd /opt/quant-evo-nextgen
docker compose -f ops/production/core/docker-compose.core.yml --env-file ops/production/core/core.env stop supervisor-runner discord-shell
```

On the worker VPS:

```bash
cd /opt/quant-evo-nextgen
./ops/bin/worker-down.sh
```

## 3. After containment

1. Run the doctor endpoint.
2. Check the latest incidents and operator overrides.
3. If broker drift or reconciliation is suspected, run a broker sync before resuming.
4. Do not resume autonomous execution until you understand the trigger.

## 4. Resume criteria

Resume only after all of the following are true:

- doctor is green enough for the intended mode
- no open provider incident is blocking the broker path
- no unexpected pending approval remains
- the broker/account snapshot and reconciliation state are fresh
- the owner understands why safe mode was entered
