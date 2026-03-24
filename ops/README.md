# Ops Assets

This folder contains the deploy and operations tooling for the single-VPS-first product path and the later Core + Worker scale-out shape.

Default owner path:

- start with `./ops/bin/quickstart-single-vps.sh` on one VPS
- add the Worker only when you actually need more isolation or research throughput

## Most Common Commands

### First-time host setup

- `./ops/bin/quickstart-single-vps.sh`
- `sudo ./ops/bin/install-host-deps.sh`
- `./ops/bin/onboard-single-vps.sh`
- `./ops/bin/system-doctor.sh`
- `./ops/bin/bootstrap-node.sh core`
- `./ops/bin/bootstrap-node.sh worker`

### Start and verify

- `./ops/bin/core-up.sh`
- `./ops/bin/core-smoke.sh`
- `./ops/bin/worker-up.sh`
- `./ops/bin/worker-smoke.sh`

### Update from GitHub

- `./ops/bin/update-from-github.sh core`
- `./ops/bin/update-from-github.sh worker`

### Recovery

- `./ops/bin/backup-postgres.sh`
- `./ops/bin/restore-postgres.sh`
- `./ops/bin/qe-enter-safe-mode.sh`

## Important Files

- `production/core/docker-compose.core.yml`
- `production/core/docker-compose.edge.yml`
- `production/core/core.env.example`
- `production/core/Caddyfile`
- `production/worker/docker-compose.worker.yml`
- `production/worker/worker.env.example`
- `systemd/quant-evo-core.service`
- `systemd/quant-evo-worker.service`

## Explicit Preflight Path

If you want the explicit path instead of the guided bootstrap wrapper:

- `./ops/bin/onboard-single-vps.sh --no-start`
- `./ops/bin/host-preflight.sh core`
- `./ops/bin/deploy-config.sh init core`
- `./ops/bin/deploy-config.sh preflight core ops/production/core/core.env`
- `./ops/bin/host-preflight.sh worker`
- `./ops/bin/deploy-config.sh init worker`
- `./ops/bin/deploy-config.sh preflight worker ops/production/worker/worker.env`

## Related Docs

- [docs/next-gen/GITHUB-TO-VPS-DEPLOYMENT.md](../docs/next-gen/GITHUB-TO-VPS-DEPLOYMENT.md)
- [docs/next-gen/VPS-DEPLOYMENT-RUNBOOK.md](../docs/next-gen/VPS-DEPLOYMENT-RUNBOOK.md)
- [docs/next-gen/BACKUP-AND-RESTORE-RUNBOOK.md](../docs/next-gen/BACKUP-AND-RESTORE-RUNBOOK.md)
- [docs/next-gen/BREAK-GLASS-RUNBOOK.md](../docs/next-gen/BREAK-GLASS-RUNBOOK.md)
