from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class SkillSummary:
    skill_id: str
    label: str
    category: str
    path: str


class SkillCatalogService:
    def __init__(self, repo_root: Path, skill_root: str | Path = "skills") -> None:
        self.repo_root = repo_root.resolve()
        raw_root = Path(skill_root)
        self.skill_root = raw_root if raw_root.is_absolute() else (self.repo_root / raw_root).resolve()

    def discover(self) -> list[SkillSummary]:
        if not self.skill_root.exists():
            return []

        skills: list[SkillSummary] = []
        for directory in sorted(self.skill_root.iterdir()):
            if not directory.is_dir():
                continue
            skill_file = directory / "SKILL.md"
            if not skill_file.exists():
                continue
            skills.append(
                SkillSummary(
                    skill_id=directory.name,
                    label=self._label_for_skill(skill_file, directory.name),
                    category=self._category_for_skill(directory.name),
                    path=self._display_path(skill_file),
                )
            )
        return skills

    def find(self, skill_id: str) -> SkillSummary | None:
        normalized = skill_id.strip().lower()
        for skill in self.discover():
            if skill.skill_id.strip().lower() == normalized:
                return skill
        return None

    def required_acquisition_skill_ids(self, *, include_playwright: bool) -> list[str]:
        required = ["search-rss-intake"]
        if include_playwright:
            required.append("playwright-browser-intake")
        return required

    def build_acquisition_guidance(self, *, include_playwright: bool) -> str:
        required_skills = self.required_acquisition_skill_ids(include_playwright=include_playwright)
        available = [self.find(skill_id) for skill_id in required_skills]
        installed = [skill for skill in available if skill is not None]
        missing = [skill_id for skill_id, skill in zip(required_skills, available) if skill is None]

        lines: list[str] = []
        if installed:
            lines.append(
                "Prefer repo skill packs before ad-hoc browsing:"
                + " "
                + "; ".join(f"{skill.skill_id} ({skill.path})" for skill in installed)
                + "."
            )
        if missing:
            lines.append(
                "The acquisition skill pack is incomplete on this runtime; missing:"
                + " "
                + ", ".join(missing)
                + "."
            )
        if include_playwright:
            lines.append(
                "Use the Playwright browser skill only for dynamic pages, anti-bot friction, or missing page content after search/feed attempts."
            )
        return " ".join(lines).strip()

    def _label_for_skill(self, skill_file: Path, fallback: str) -> str:
        try:
            for line in skill_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("# "):
                    return line[2:].strip()
        except OSError:
            return fallback
        return fallback

    def _category_for_skill(self, skill_id: str) -> str:
        if "playwright" in skill_id or "browser" in skill_id:
            return "browser"
        if "search" in skill_id or "rss" in skill_id:
            return "research"
        return "general"

    def _display_path(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.repo_root))
        except ValueError:
            return str(path.resolve())
