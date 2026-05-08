from __future__ import annotations

from pathlib import Path

from quant_evo_nextgen.services.dashboard import DashboardService
from quant_evo_nextgen.services.repo_state import RepoStateService


def test_dashboard_overview_builds_without_runtime_services(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Test Repo\n", encoding="utf-8")

    overview = DashboardService(RepoStateService(tmp_path)).build_overview()

    assert overview.headline
    assert overview.system.mode == "paper_only"
    assert overview.strategy.production == 0
    assert overview.learning.document_count == 0
