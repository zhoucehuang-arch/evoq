# Backup And Restore Runbook

## Backup

Run on the Core VPS:

```bash
cd /opt/evoq
./ops/bin/backup-postgres.sh
```

Artifacts:

- `.qe/backups/postgres-<timestamp>.sql`
- `.qe/backups/runtime-<timestamp>.tgz`

Minimum policy:

- nightly
- before every upgrade
- before changing broker environment

## Restore

Run on the Core VPS:

```bash
cd /opt/evoq
./ops/bin/restore-postgres.sh .qe/backups/postgres-YYYYMMDDTHHMMSSZ.sql .qe/backups/runtime-YYYYMMDDTHHMMSSZ.tgz
./ops/bin/core-up.sh
./ops/bin/core-smoke.sh
```

## What Restore Covers

- Postgres runtime state
- `.qe/` workspace state
- saved Core env file inside the runtime archive at `ops/production/core/core.env`

## Limits

- This flow is implemented in-repo but has not yet been exercised on a real Linux VPS inside this session.
- Always restore into `safe_mode` or paper-first posture before resuming autonomous trading.
