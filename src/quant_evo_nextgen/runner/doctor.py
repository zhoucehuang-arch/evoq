from __future__ import annotations

import json
import sys

from quant_evo_nextgen.config import get_settings
from quant_evo_nextgen.db.session import Database
from quant_evo_nextgen.logging_utils import configure_logging
from quant_evo_nextgen.services.doctor import DoctorService, render_text_report


def run(argv: list[str] | None = None) -> int:
    args = argv or sys.argv[1:]
    json_mode = "--json" in args

    configure_logging()
    settings = get_settings()
    database = Database(settings.postgres_url, echo=settings.db_echo)
    doctor = DoctorService(database.session_factory, settings)
    try:
        report = doctor.run()
    finally:
        database.dispose()

    if json_mode:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_text_report(report))

    return 0 if report["status"] != "fail" else 1


if __name__ == "__main__":
    raise SystemExit(run())
