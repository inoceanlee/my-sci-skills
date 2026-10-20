"""Adapter for vendored, byte-exact Nature Figure PDF QA commands."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys

_UPSTREAM_SHA = "233ed09957d32d8cf45dd96c495663c5c5d8e447"
_DEFAULT_SCRIPTS = Path(__file__).resolve().parents[2] / "third_party" / "nature_figure"


@dataclass(frozen=True)
class NatureAudit:
    status: str
    issues: tuple[str, ...] = ()
    minimum_glyph_pt: float | None = None
    collision_verdict: str | None = None
    text_run_count: int = 0
    upstream_commit: str = _UPSTREAM_SHA


def _run(script: Path, pdf: Path, args: tuple[str, ...] = ()) -> dict | None:
    try:
        proc = subprocess.run(
            [sys.executable, str(script), str(pdf), "--json", *args],
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
            timeout=30,
        )
        if proc.returncode not in (0, 1):
            return None
        return json.loads(proc.stdout)
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return None


def audit_nature_pdf(
    path: str | Path, *, strict: bool = False, minimum_pt: float = 5,
) -> NatureAudit:
    """Never report PASS unless both upstream PDF audits can inspect the file."""
    pdf = Path(path)
    scripts = _DEFAULT_SCRIPTS
    collision = scripts / "audit_figure_collisions.py"
    fonts = scripts / "audit_pdf_text.py"
    if not pdf.is_file() or not collision.is_file() or not fonts.is_file():
        return NatureAudit("not_auditable", issues=("NATURE_SOURCE_UNAVAILABLE",))
    geometry = _run(collision, pdf)
    text = _run(fonts, pdf, ("--min-pt", str(minimum_pt)))
    if (not isinstance(geometry, dict) or not isinstance(text, dict) or
            not geometry.get("auditable") or not text.get("auditable") or
            text.get("warnings")):
        return NatureAudit("not_auditable", issues=("NATURE_QA_NOT_AUDITABLE",))
    verdict = str(geometry.get("verdict") or "")
    if verdict == "NOT AUDITABLE" or verdict not in {
            "PASS", "REVIEW REQUIRED", "FIX BEFORE DELIVERY"}:
        return NatureAudit("not_auditable", issues=("NATURE_QA_NOT_AUDITABLE",))
    count = int(text.get("below_minimum_count", 0))
    issues = []
    if verdict == "FIX BEFORE DELIVERY":
        kinds = [str(item.get("kind", "unknown")) for item in geometry.get("findings", [])]
        issues.extend("COLLISION:" + kind for kind in kinds)
    elif strict and verdict == "REVIEW REQUIRED":
        issues.append("COLLISION_WARN")
    if count:
        issues.append("FONT_TOO_SMALL")
    return NatureAudit(
        status="failed" if issues else "passed",
        issues=tuple(issues),
        minimum_glyph_pt=text.get("minimum_found_pt"),
        collision_verdict=verdict,
        text_run_count=int(text.get("text_run_count", 0)),
    )
