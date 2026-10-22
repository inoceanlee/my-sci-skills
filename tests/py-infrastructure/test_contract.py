"""Public API contract for the reusable Python infrastructure Skill."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[2] / "skills" / "py-infrastructure"
SOURCE = SKILL_ROOT / "scripts" / "py-infrastructure"


class InfrastructureContractTest(unittest.TestCase):
    def test_skill_copy_exposes_documented_api(self) -> None:
        self.assertTrue((SOURCE / "__init__.py").is_file(), "Skill runtime missing")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            utils = root / "utils"
            utils.mkdir()
            (utils / "__init__.py").touch()
            shutil.copytree(SOURCE, utils / "py-infrastructure")
            (root / ".project-root").touch()

            script = """
from pathlib import Path
from importlib import import_module
Infrastructure = import_module("utils.py-infrastructure").Infrastructure

infra = Infrastructure.initialize(
    output_dir=Path("artifacts"),
    memory_enabled=False,
    run_name="contract",
)
try:
    with infra.errors.scope("save"):
        with infra.timer.scope("save"):
            with infra.memory.scope("save"):
                destination = infra.output_path("metrics", "summary.txt")
                destination.write_text("contract ok\\n", encoding="utf-8")
    infra.logger.info("Saved: %s", destination)
finally:
    infra.close()
"""
            result = subprocess.run(
                [sys.executable, "-c", script],
                cwd=root,
                text=True,
                capture_output=True,
                timeout=60,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            outputs = list((root / "artifacts").rglob("summary.txt"))
            self.assertEqual(len(outputs), 1, outputs)
            self.assertEqual(outputs[0].read_text(encoding="utf-8"), "contract ok\n")


if __name__ == "__main__":
    unittest.main()
