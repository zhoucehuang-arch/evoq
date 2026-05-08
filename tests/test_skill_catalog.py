from __future__ import annotations

from pathlib import Path

from quant_evo_nextgen.services.skill_catalog import SkillCatalogService


def test_skill_catalog_discovers_repo_skill_packs(tmp_path: Path) -> None:
    skill_dir = tmp_path / "workspace" / "skills" / "search-rss-intake"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Search RSS Intake\n\nUse feeds first.\n", encoding="utf-8")

    service = SkillCatalogService(tmp_path)
    skills = service.discover()

    assert len(skills) == 1
    assert skills[0].skill_id == "search-rss-intake"
    assert skills[0].label == "Search RSS Intake"
    assert skills[0].category == "research"
    assert service.find("SEARCH-RSS-INTAKE") == skills[0]


def test_skill_catalog_guidance_names_missing_acquisition_skills(tmp_path: Path) -> None:
    service = SkillCatalogService(tmp_path)

    guidance = service.build_acquisition_guidance(include_playwright=True)

    assert "search-rss-intake" in guidance
    assert "playwright-browser-intake" in guidance
    assert "missing" in guidance
