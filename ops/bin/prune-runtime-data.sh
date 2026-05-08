#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
RETENTION_DAYS="${QE_DATA_RETENTION_DAYS:-90}"
DRY_RUN="${QE_DATA_RETENTION_DRY_RUN:-true}"

if [[ ! "${RETENTION_DAYS}" =~ ^[0-9]+$ ]] || [[ "${RETENTION_DAYS}" -le 0 ]]; then
  echo "QE_DATA_RETENTION_DAYS must be a positive integer." >&2
  exit 2
fi

cd "${ROOT_DIR}"
python - "${RETENTION_DAYS}" "${DRY_RUN}" <<'PY'
from __future__ import annotations

from datetime import UTC, datetime, timedelta
import os
import sys

from sqlalchemy import create_engine, text

retention_days = int(sys.argv[1])
dry_run = sys.argv[2].strip().lower() not in {"0", "false", "no"}
database_url = os.getenv("QE_POSTGRES_URL")
if not database_url:
    raise SystemExit("QE_POSTGRES_URL is required.")

cutoff = datetime.now(tz=UTC) - timedelta(days=retention_days)
targets = [
    ("obs_heartbeat", "recorded_at"),
    ("md_quote_snapshot", "as_of"),
    ("exec_market_calendar_state", "created_at"),
    ("exec_broker_sync_run", "created_at"),
    ("exec_reconciliation_run", "checked_at"),
]

engine = create_engine(database_url)
with engine.begin() as connection:
    for table, column in targets:
        count = connection.scalar(
            text(f"select count(*) from {table} where {column} < :cutoff"),
            {"cutoff": cutoff},
        )
        print(f"{table}: {count or 0} rows older than {cutoff.isoformat()}")
        if not dry_run and count:
            connection.execute(
                text(f"delete from {table} where {column} < :cutoff"),
                {"cutoff": cutoff},
            )

print("Dry run only. Set QE_DATA_RETENTION_DRY_RUN=false to delete rows." if dry_run else "Prune complete.")
PY
