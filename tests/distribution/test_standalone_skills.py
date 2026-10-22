"""Behavioral checks for copied Skills in project-managed environments."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = REPOSITORY_ROOT / "skills"


def copy_skills(target: Path) -> Path:
    copied = target / "skills"
    shutil.copytree(
        SKILLS_ROOT,
        copied,
        ignore=shutil.ignore_patterns(
            ".runtime", ".venv", "node_modules", ".pytest_cache", "__pycache__", "tests"
        ),
    )
    return copied


def test_markdown_links_resolve_in_copied_skills(tmp_path: Path) -> None:
    copied = copy_skills(tmp_path)
    figure = copied / "figure-infrastructure"

    for removed in (
        figure / "scripts" / "setup" / "bootstrap.py",
        figure / "uv.lock",
        figure / "package.json",
        figure / "package-lock.json",
    ):
        assert not removed.exists(), removed

    figure_source = figure / "scripts" / "figure-infrastructure"
    assert (figure_source / "pyproject.toml").is_file()
    assert (figure_source / "python" / "figure_layout" / "__init__.py").is_file()
    assert (figure_source / "javascript" / "figure-layout.js").is_file()
    assert (figure_source / "third_party" / "nature_figure" / "LICENSE").is_file()
    assert not (figure / "pyproject.toml").exists()
    assert (figure / "references" / "deployment.md").is_file()
    assert (figure / "references" / "python-api.md").is_file()
    assert (figure / "references" / "javascript-api.md").is_file()
    assert (figure / "references" / "dependencies.md").is_file()
    assert not (figure / ".runtime").exists()

    for skill_name in ("py-infrastructure", "figure-infrastructure"):
        skill = copied / skill_name
        assert (skill / "LICENSE").read_bytes() == (
            SKILLS_ROOT / skill_name / "LICENSE"
        ).read_bytes()
        for document in skill.rglob("*.md"):
            content = document.read_text(encoding="utf-8")
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", content):
                relative = target.split("#", maxsplit=1)[0]
                if not relative or relative.startswith(("http:", "https:", "mailto:")):
                    continue
                assert (document.parent / relative).is_file(), f"{document}: {relative}"


def test_copied_python_figure_exports_in_project_environment(tmp_path: Path) -> None:
    copied = copy_skills(tmp_path)
    figure = copied / "figure-infrastructure"
    figure_source = figure / "scripts" / "figure-infrastructure"
    project_copy = tmp_path / "utils" / "figure-infrastructure"
    project_copy.parent.mkdir()
    shutil.copytree(figure_source, project_copy)
    source = project_copy / "python"
    output = tmp_path / "figure.png"
    script = textwrap.dedent(
        """
        import json
        import sys
        from pathlib import Path

        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from PIL import Image
        import figure_layout
        from figure_layout import FigureExporter

        source = Path(sys.argv[1]).resolve()
        output = Path(sys.argv[2])
        assert Path(figure_layout.__file__).resolve().is_relative_to(source)
        figure, axis = plt.subplots()
        axis.plot([0, 1, 2], [1, 2, 1], label="series")
        axis.set_xlabel("time")
        axis.set_ylabel("value")
        axis.legend()
        result = FigureExporter().export(figure, output)
        assert result.audit.geometry_status == "passed"
        assert Image.open(output).size == (1004, 709)
        plt.close(figure)
        print(json.dumps({"status": result.audit.geometry_status, "size": [result.width_px, result.height_px]}))
        """
    )
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(source)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [sys.executable, "-c", script, str(source), str(output)],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout.strip().splitlines()[-1]) == {
        "status": "passed",
        "size": [1004, 709],
    }
    assert not (figure / ".runtime").exists()


def test_copied_plotly_figure_exports_in_project_environment(tmp_path: Path) -> None:
    copied = copy_skills(tmp_path)
    figure_source = (
        copied / "figure-infrastructure" / "scripts" / "figure-infrastructure"
    )
    project_copy = tmp_path / "utils" / "figure-infrastructure"
    project_copy.parent.mkdir()
    shutil.copytree(figure_source, project_copy)
    figure_scripts = project_copy / "javascript"
    plotly_bundle = (
        REPOSITORY_ROOT / "node_modules" / "plotly.js-dist-min" / "plotly.min.js"
    )
    script = textwrap.dedent(
        """
        const assert = require("node:assert/strict");
        const { chromium } = require("playwright-core");

        (async () => {
          const [plotly, ...skillScripts] = process.argv.slice(1);
          const browser = await chromium.launch({
            executablePath: process.env.SCI_TEST_BROWSER,
            headless: true
          });
          try {
            const page = await browser.newPage();
            const network = [];
            page.on("request", request => {
              if (/^https?:/i.test(request.url())) network.push(request.url());
            });
            await page.setContent('<div id="plot" style="width:1004px;height:709px"></div>');
            await page.addScriptTag({ path: plotly });
            for (const source of skillScripts) await page.addScriptTag({ path: source });
            const result = await page.evaluate(async () => {
              const plot = document.getElementById("plot");
              await Plotly.newPlot(plot, [
                {x:[0,1,2],y:[1,2,1],mode:"lines+markers",name:"series"}
              ], {xaxis:{title:{text:"time"}},yaxis:{title:{text:"value"}},showlegend:true});
              const before = JSON.stringify({data:plot.data,layout:plot.layout});
              const exported = await exportScientificFigure(plot, {format:"png",preset:"single"});
              const after = JSON.stringify({data:plot.data,layout:plot.layout});
              return {before,after,exported};
            });
            assert.equal(result.before, result.after);
            assert.equal(result.exported.format, "png");
            assert.equal(result.exported.preset, "single");
            assert.equal(result.exported.width, 1004);
            assert.equal(result.exported.height, 709);
            assert.equal(result.exported.audit.geometryStatus, "passed");
            assert.match(result.exported.dataUrl, /^data:image\\/png;base64,/);
            assert.deepEqual(network, []);
            console.log(JSON.stringify({status:result.exported.audit.geometryStatus,width:result.exported.width,height:result.exported.height}));
          } finally {
            await browser.close();
          }
        })().catch(error => { console.error(error); process.exitCode = 1; });
        """
    )
    environment = os.environ.copy()
    environment["SCI_TEST_BROWSER"] = os.environ.get("SCI_TEST_BROWSER") or (
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    )
    result = subprocess.run(
        [
            shutil.which("node") or "node",
            "-e",
            script,
            str(plotly_bundle),
            str(figure_scripts / "ranges.js"),
            str(figure_scripts / "layout.js"),
            str(figure_scripts / "annotations.js"),
            str(figure_scripts / "audit.js"),
            str(figure_scripts / "figure-layout.js"),
        ],
        cwd=REPOSITORY_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout.strip().splitlines()[-1]) == {
        "status": "passed",
        "width": 1004,
        "height": 709,
    }
    assert not (copied / "figure-infrastructure" / ".runtime").exists()


class StandaloneSkillTests(unittest.TestCase):
    def test_standalone_skills_include_mit_license(self) -> None:
        root_license = REPOSITORY_ROOT / "LICENSE"
        for skill_name in ("py-infrastructure", "figure-infrastructure"):
            with self.subTest(skill=skill_name):
                license_path = SKILLS_ROOT / skill_name / "LICENSE"
                self.assertTrue(license_path.is_file(), license_path)
                self.assertEqual(license_path.read_bytes(), root_license.read_bytes())


if __name__ == "__main__":
    unittest.main()
