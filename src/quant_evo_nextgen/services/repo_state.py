from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(slots=True)
class RepoStateSnapshot:
    generated_at: datetime
    repo_root: Path
    candidates: int
    staging: int
    production: int
    principles: int
    causal_cases: int
    occupied_feature_cells: int
    feature_coverage_pct: float
    total_generations: int


class RepoStateService:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root

    def collect(self) -> RepoStateSnapshot:
        feature_map = self._load_feature_map()

        return RepoStateSnapshot(
            generated_at=datetime.now(tz=UTC),
            repo_root=self.repo_root,
            candidates=self._count_files(self.repo_root / "strategies" / "candidates"),
            staging=self._count_files(self.repo_root / "strategies" / "staging"),
            production=self._count_files(self.repo_root / "strategies" / "production"),
            principles=self._count_files(self.repo_root / "memory" / "principles"),
            causal_cases=self._count_files(self.repo_root / "memory" / "causal"),
            occupied_feature_cells=feature_map["occupied_feature_cells"],
            feature_coverage_pct=feature_map["feature_coverage_pct"],
            total_generations=feature_map["total_generations"],
        )

    def _count_files(self, directory: Path) -> int:
        if not directory.exists():
            return 0

        count = 0
        for path in directory.rglob("*"):
            if not path.is_file():
                continue
            if path.name == ".gitkeep":
                continue
            count += 1
        return count

    def _load_feature_map(self) -> dict[str, int | float]:
        feature_map_path = self.repo_root / "evo" / "feature_map.json"
        if not feature_map_path.exists():
            return {
                "occupied_feature_cells": 0,
                "feature_coverage_pct": 0.0,
                "total_generations": 0,
            }

        raw = json.loads(feature_map_path.read_text(encoding="utf-8"))
        stats = raw.get("stats", {})
        occupied_feature_cells = int(stats.get("occupied_cells", len(raw.get("cells", {}))))
        feature_coverage_pct = float(stats.get("coverage_pct", 0.0))
        total_generations = int(stats.get("total_generations", 0))

        return {
            "occupied_feature_cells": occupied_feature_cells,
            "feature_coverage_pct": feature_coverage_pct,
            "total_generations": total_generations,
        }
