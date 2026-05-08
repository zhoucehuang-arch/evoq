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

Retention:

- Default: `QE_BACKUP_RETENTION_DAYS=30`
- Set `QE_BACKUP_RETENTION_DAYS=0` to disable automatic pruning.
- Set `QE_BACKUP_DIR=/path/to/backups` to write artifacts outside the repository checkout.

## Runtime Data Retention

Dry-run old operational-row pruning:

```bash
cd /opt/evoq
QE_POSTGRES_URL=postgresql+psycopg://... ./ops/bin/prune-runtime-data.sh
```

Defaults:

- `QE_DATA_RETENTION_DAYS=90`
- `QE_DATA_RETENTION_DRY_RUN=true`

Set `QE_DATA_RETENTION_DRY_RUN=false` only after reviewing the dry-run counts. The script prunes old heartbeat, quote snapshot, market calendar, broker sync, and reconciliation rows; it does not delete strategy evidence, approvals, incidents, or audit artifacts.

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
