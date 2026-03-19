from __future__ import annotations

import asyncio
import logging

from quant_evo_nextgen.config import get_settings
from quant_evo_nextgen.db.session import Database
from quant_evo_nextgen.logging_utils import configure_logging
from quant_evo_nextgen.services.codex_fabric import CodexFabricService
from quant_evo_nextgen.services.dashboard import DashboardService
from quant_evo_nextgen.services.evolution import EvolutionService
from quant_evo_nextgen.services.execution import ExecutionService
from quant_evo_nextgen.services.learning import LearningService
from quant_evo_nextgen.services.repo_state import RepoStateService
from quant_evo_nextgen.services.state_store import StateStore
from quant_evo_nextgen.services.strategy_lab import StrategyLabService
from quant_evo_nextgen.services.supervisor import SupervisorService


async def main() -> None:
    settings = get_settings()
    configure_logging()
    logger = logging.getLogger("quant_evo_nextgen.runner.supervisor")

    database = Database(settings.postgres_url, echo=settings.db_echo)
    if settings.db_bootstrap_on_start:
        database.create_schema()

    state_store = StateStore(database.session_factory)
    state_store.bootstrap_reference_data(settings)
    codex_fabric_service = CodexFabricService(database.session_factory, settings)
    learning_service = LearningService(database.session_factory)
    strategy_service = StrategyLabService(database.session_factory)
    execution_service = ExecutionService(database.session_factory, settings)
    evolution_service = EvolutionService(database.session_factory)
    dashboard_service = DashboardService(
        RepoStateService(settings.resolved_repo_root),
        state_store,
        codex_fabric_service,
        learning_service,
        strategy_service,
        execution_service,
        evolution_service,
    )
    supervisor_service = SupervisorService(
        state_store=state_store,
        dashboard_service=dashboard_service,
        settings=settings,
        codex_fabric_service=codex_fabric_service,
        learning_service=learning_service,
        strategy_service=strategy_service,
        execution_service=execution_service,
        evolution_service=evolution_service,
    )

    logger.info("supervisor runner started for repo root %s", settings.resolved_repo_root)
    try:
        while True:
            results = supervisor_service.run_due_loops(max_loops=3)
            if results:
                logger.info(
                    "supervisor tick completed loops=%s",
                    ", ".join(f"{result.loop_key}:{result.status}" for result in results),
                )
            await asyncio.sleep(min(settings.heartbeat_interval_seconds, 15))
    finally:
        database.dispose()


if __name__ == "__main__":
    asyncio.run(main())
