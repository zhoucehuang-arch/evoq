from __future__ import annotations

import asyncio
import logging

from quant_evo_nextgen.config import get_settings
from quant_evo_nextgen.db.session import Database
from quant_evo_nextgen.logging_utils import configure_logging
from quant_evo_nextgen.services.codex_fabric import CodexFabricService


async def main() -> None:
    settings = get_settings()
    configure_logging()
    logger = logging.getLogger("quant_evo_nextgen.runner.codex_fabric")

    database = Database(settings.postgres_url, echo=settings.db_echo)
    if settings.db_bootstrap_on_start:
        database.create_schema()

    service = CodexFabricService(database.session_factory, settings)

    logger.info("codex fabric runner started")
    try:
        while True:
            runs = service.run_next(max_runs=1)
            if runs:
                logger.info(
                    "codex fabric processed run=%s status=%s",
                    runs[0].id,
                    runs[0].status,
                )
            await asyncio.sleep(10)
    finally:
        database.dispose()


if __name__ == "__main__":
    asyncio.run(main())
