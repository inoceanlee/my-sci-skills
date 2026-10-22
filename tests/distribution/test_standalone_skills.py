"""Behavioral checks for copied Skills in project-managed environments."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = REPOSITORY_ROOT / "skills"


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


def test_distribution_contains_only_py_infrastructure(tmp_path: Path) -> None:
    copied = copy_skills(tmp_path)

    assert sorted(path.name for path in copied.iterdir()) == ["py-infrastructure"]


def test_copied_skill_links_and_license_resolve(tmp_path: Path) -> None:
    copied = copy_skills(tmp_path)
    skill = copied / "py-infrastructure"
    assert (skill / "SKILL.md").is_file()
    assert (skill / "LICENSE").read_bytes() == (
        REPOSITORY_ROOT / "LICENSE"
    ).read_bytes()

    for document in skill.rglob("*.md"):
        content = document.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", content):
            relative = target.split("#", maxsplit=1)[0]
            if not relative or relative.startswith(("http:", "https:", "mailto:")):
                continue
            assert (document.parent / relative).is_file(), f"{document}: {relative}"
