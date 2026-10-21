"""Contracts for standalone Skill runtime manifests and bootstrap checks."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPOSITORY_ROOT / "skills" / "figure-infrastructure"
BOOTSTRAP = SKILL_ROOT / "scripts" / "setup" / "bootstrap.py"


class StandaloneSkillTests(unittest.TestCase):
    def test_skill_manifest_runtime_only(self) -> None:
        with (SKILL_ROOT / "pyproject.toml").open("rb") as stream:
            python_manifest = tomllib.load(stream)
        with (SKILL_ROOT / "uv.lock").open("rb") as stream:
            python_lock = tomllib.load(stream)
        javascript_manifest = json.loads((SKILL_ROOT / "package.json").read_text(encoding="utf-8"))
        javascript_lock = json.loads(
            (SKILL_ROOT / "package-lock.json").read_text(encoding="utf-8")
        )

        self.assertEqual(python_manifest["project"]["requires-python"], ">=3.12,<3.15")
        self.assertNotIn("dev", python_manifest.get("dependency-groups", {}))
        self.assertNotIn("pytest", {package["name"] for package in python_lock["package"]})
        self.assertEqual(
            javascript_manifest.get("dependencies"),
            {"plotly.js-dist-min": "4.1.2"},
        )
        self.assertNotIn("devDependencies", javascript_manifest)
        self.assertNotIn("scripts", javascript_manifest)
        self.assertEqual(
            javascript_lock["packages"][""].get("dependencies"),
            {"plotly.js-dist-min": "4.1.2"},
        )
        self.assertNotIn("playwright-core", javascript_lock["packages"])

    def test_bootstrap_check_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied_skill = Path(temporary) / "figure-infrastructure"
            shutil.copytree(
                SKILL_ROOT,
                copied_skill,
                ignore=shutil.ignore_patterns(
                    ".runtime", ".venv", "node_modules", ".pytest_cache", "__pycache__"
                ),
            )
            env = os.environ.copy()
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            result = subprocess.run(
                [sys.executable, str(copied_skill / "scripts" / "setup" / "bootstrap.py"), "check"],
                cwd=copied_skill,
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertFalse((copied_skill / ".runtime").exists())

    def test_bootstrap_reports_missing_package_managers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            copied_skill = root / "figure-infrastructure"
            shutil.copytree(
                SKILL_ROOT,
                copied_skill,
                ignore=shutil.ignore_patterns(
                    ".runtime", ".venv", "node_modules", ".pytest_cache", "__pycache__"
                ),
            )
            empty_path = root / "empty-bin"
            empty_path.mkdir()
            env = os.environ.copy()
            env["PATH"] = str(empty_path)
            env["PYTHONDONTWRITEBYTECODE"] = "1"

            for component, message in (
                ("python", "Cannot start uv"),
                ("javascript", "npm executable not found"),
            ):
                with self.subTest(component=component):
                    result = subprocess.run(
                        [
                            sys.executable,
                            str(copied_skill / "scripts" / "setup" / "bootstrap.py"),
                            "install",
                            "--component",
                            component,
                        ],
                        cwd=copied_skill,
                        env=env,
                        capture_output=True,
                        text=True,
                        timeout=30,
                        check=False,
                    )
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertIn(message, result.stderr)

            self.assertTrue((copied_skill / ".runtime").is_dir())

    @unittest.skipUnless(
        os.environ.get("SCI_RUN_STANDALONE_INSTALL") == "1",
        "requires isolated uv/npm installation and network access",
    )
    def test_bootstrap_install_isolated_and_removal_owns_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            copied_skill = root / "skills" / "figure-infrastructure"
            copied_skill.parent.mkdir()
            shutil.copytree(
                SKILL_ROOT,
                copied_skill,
                ignore=shutil.ignore_patterns(
                    ".runtime", ".venv", "node_modules", ".pytest_cache", "__pycache__"
                ),
            )
            outside_environment = root / "outside-python-environment"
            outside_uv_cache = root / "outside-uv-cache"
            outside_npm_cache = root / "outside-npm-cache"
            env = os.environ.copy()
            env.pop("PYTHONPATH", None)
            env.pop("NODE_PATH", None)
            env.pop("VIRTUAL_ENV", None)
            env.update(
                {
                    "UV_PROJECT_ENVIRONMENT": str(outside_environment),
                    "UV_CACHE_DIR": str(outside_uv_cache),
                    "npm_config_cache": str(outside_npm_cache),
                    "PYTHONDONTWRITEBYTECODE": "1",
                    "UV_PYTHON_DOWNLOADS": "never",
                }
            )
            result = subprocess.run(
                [sys.executable, str(copied_skill / "scripts" / "setup" / "bootstrap.py"), "install"],
                cwd=copied_skill,
                env=env,
                capture_output=True,
                text=True,
                timeout=900,
                check=False,
            )

            runtime = copied_skill / ".runtime"
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue((runtime / "python" / ".venv").is_dir())
            self.assertTrue(
                (
                    runtime
                    / "javascript"
                    / "node_modules"
                    / "plotly.js-dist-min"
                    / "plotly.min.js"
                ).is_file()
            )
            self.assertFalse(
                (runtime / "javascript" / "node_modules" / "playwright-core").exists()
            )
            self.assertTrue((runtime / "cache" / "uv").is_dir())
            self.assertTrue((runtime / "cache" / "npm").is_dir())
            self.assertFalse(outside_environment.exists())
            self.assertFalse(outside_uv_cache.exists())
            self.assertFalse(outside_npm_cache.exists())

            checked = subprocess.run(
                [
                    sys.executable,
                    str(copied_skill / "scripts" / "setup" / "bootstrap.py"),
                    "check",
                ],
                cwd=copied_skill,
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)

            shutil.rmtree(copied_skill)
            self.assertFalse(runtime.exists())


if __name__ == "__main__":
    unittest.main()
