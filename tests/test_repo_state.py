import json
from pathlib import Path

from quant_evo_nextgen.services.repo_state import RepoStateService


def test_repo_state_counts_strategy_and_memory_files(tmp_path: Path) -> None:
    (tmp_path / "strategies" / "candidates").mkdir(parents=True)
    (tmp_path / "strategies" / "staging").mkdir(parents=True)
    (tmp_path / "strategies" / "production").mkdir(parents=True)
    (tmp_path / "memory" / "principles").mkdir(parents=True)
    (tmp_path / "memory" / "causal").mkdir(parents=True)
    (tmp_path / "evo").mkdir(parents=True)

    (tmp_path / "strategies" / "candidates" / "candidate.py").write_text("print('x')", encoding="utf-8")
    (tmp_path / "strategies" / "staging" / "strategy.py").write_text("print('x')", encoding="utf-8")
    (tmp_path / "strategies" / "production" / ".gitkeep").write_text("", encoding="utf-8")
    (tmp_path / "memory" / "principles" / "alpha.md").write_text("alpha", encoding="utf-8")
    (tmp_path / "memory" / "causal" / "beta.md").write_text("beta", encoding="utf-8")
    (tmp_path / "evo" / "feature_map.json").write_text(
        json.dumps({"stats": {"occupied_cells": 3, "coverage_pct": 0.12, "total_generations": 7}}),
        encoding="utf-8",
    )

    snapshot = RepoStateService(tmp_path).collect()

    assert snapshot.candidates == 1
    assert snapshot.staging == 1
    assert snapshot.production == 0
    assert snapshot.principles == 1
    assert snapshot.causal_cases == 1
    assert snapshot.occupied_feature_cells == 3
    assert snapshot.total_generations == 7
