# Ops Assets

Canonical production assets:

- `bin/install-host-deps.sh`
- `bin/bootstrap-node.sh`
- `production/core/docker-compose.core.yml`
- `production/core/docker-compose.edge.yml`
- `production/core/core.env.example`
- `production/core/Caddyfile`
- `production/worker/docker-compose.worker.yml`
- `production/worker/worker.env.example`
- `bin/core-up.sh`
- `bin/core-down.sh`
- `bin/core-smoke.sh`
- `bin/host-preflight.sh`
- `bin/deploy-config.sh`
- `bin/worker-up.sh`
- `bin/worker-down.sh`
- `bin/worker-smoke.sh`
- `bin/backup-postgres.sh`
- `bin/restore-postgres.sh`
- `bin/install-systemd.sh`
- `bin/update-from-github.sh`
- `bin/qe-enter-safe-mode.sh`
- `systemd/quant-evo-core.service`
- `systemd/quant-evo-worker.service`

Canonical docs:

- `docs/next-gen/VPS-DEPLOYMENT-RUNBOOK.md`
- `docs/next-gen/BACKUP-AND-RESTORE-RUNBOOK.md`
- `docs/next-gen/BREAK-GLASS-RUNBOOK.md`

Canonical config helper:

- `sudo ./ops/bin/install-host-deps.sh`
- `./ops/bin/bootstrap-node.sh core`
- `./ops/bin/bootstrap-node.sh worker`
- `./ops/bin/host-preflight.sh core`
- `./ops/bin/deploy-config.sh init core`
- `./ops/bin/deploy-config.sh preflight core ops/production/core/core.env`
- `./ops/bin/host-preflight.sh worker`
- `./ops/bin/deploy-config.sh init worker`
- `./ops/bin/deploy-config.sh preflight worker ops/production/worker/worker.env`
- `./ops/bin/update-from-github.sh core`
- `./ops/bin/update-from-github.sh worker`
