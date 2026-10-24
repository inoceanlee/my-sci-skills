"""Behavioral checks for copied Skills in project-managed environments."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = REPOSITORY_ROOT / "skills"
EXPECTED_SKILLS = {
    "auto-git-commit",
    "deai-comments",
    "oop-first",
    "project-context",
    "py-infrastructure",
    "py-plot-academic",
    "writing-standards",
}


def copy_skills(target: Path) -> Path:
    copied = target / "skills"
    copied.mkdir()
    ignore = shutil.ignore_patterns(
        ".runtime", ".venv", "node_modules", ".pytest_cache", "__pycache__", "tests"
    )
    for skill in SKILLS_ROOT.iterdir():
        if skill.is_dir() and (skill / "SKILL.md").is_file():
            shutil.copytree(skill, copied / skill.name, ignore=ignore)
    return copied


def test_distribution_contains_managed_skills(tmp_path: Path) -> None:
    copied = copy_skills(tmp_path)

    assert {path.name for path in copied.iterdir()} == EXPECTED_SKILLS


def test_copied_skill_links_and_license_resolve(tmp_path: Path) -> None:
    copied = copy_skills(tmp_path)
    for skill_name in EXPECTED_SKILLS:
        skill = copied / skill_name
        assert (skill / "SKILL.md").is_file()

        for document in skill.rglob("*.md"):
            content = document.read_text(encoding="utf-8")
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", content):
                relative = target.split("#", maxsplit=1)[0]
                if not relative or relative.startswith(("http:", "https:", "mailto:")):
                    continue
                assert (document.parent / relative).is_file(), f"{document}: {relative}"

    assert (copied / "py-infrastructure" / "LICENSE").read_bytes() == (
        REPOSITORY_ROOT / "LICENSE"
    ).read_bytes()
