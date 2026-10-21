"""Contracts for standalone Skill runtime manifests and bootstrap checks."""

from __future__ import annotations

import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import tomllib
import unittest
from dataclasses import dataclass
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPOSITORY_ROOT / "skills" / "figure-infrastructure"
BOOTSTRAP = SKILL_ROOT / "scripts" / "setup" / "bootstrap.py"

@dataclass(frozen=True)
class DistributionReport:
    copied_skills_path: Path
    runtime_path: Path
    python_import_path: Path
    js_bundle_path: Path
    artifacts: tuple[Path, ...]
    audit_statuses: tuple[str, ...]
    external_repo_references: tuple[str, ...]


def _isolated_environment(target_temp: Path) -> tuple[dict[str, str], tuple[Path, ...]]:
    environment = os.environ.copy()
    for name in ("PYTHONPATH", "NODE_PATH", "VIRTUAL_ENV"):
        environment.pop(name, None)
    sentinels = (
        target_temp / "outside-python-environment",
        target_temp / "outside-uv-cache",
        target_temp / "outside-npm-cache",
    )
    environment.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "UV_PYTHON_DOWNLOADS": "never",
            "UV_PROJECT_ENVIRONMENT": str(sentinels[0]),
            "UV_CACHE_DIR": str(sentinels[1]),
            "npm_config_cache": str(sentinels[2]),
        }
    )
    return environment, sentinels


def _tool_state() -> dict[str, tuple[int, int]]:
    state = {}
    for name in ("uv", "node", "npm"):
        executable = shutil.which(name)
        if executable is None:
            continue
        metadata = Path(executable).resolve().stat()
        state[name] = (metadata.st_size, metadata.st_mtime_ns)
    return state


def _run_checked(
    command: list[str],
    cwd: Path,
    environment: dict[str, str],
    timeout: int,
    label: str,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"{label} exited with {result.returncode}\n{result.stdout}\n{result.stderr}"
        )
    return result


def run_distribution_smoke(
    source_skills: Path,
    target_temp: Path,
    components: tuple[str, ...],
) -> DistributionReport:
    allowed = {"python", "javascript"}
    if not components or len(set(components)) != len(components) or not set(components) <= allowed:
        raise ValueError("components must contain unique python and/or javascript entries")

    source_skills = source_skills.resolve()
    target_temp = target_temp.resolve()
    target_temp.mkdir(parents=True, exist_ok=True)
    copied_skills_path = target_temp / "copied" / "skills"
    copied_skills_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        source_skills,
        copied_skills_path,
        ignore=shutil.ignore_patterns(
            ".runtime", ".venv", "node_modules", ".pytest_cache", "__pycache__", "tests"
        ),
    )

    figure_skill = copied_skills_path / "figure-infrastructure"
    runtime_path = figure_skill / ".runtime"
    environment, sentinels = _isolated_environment(target_temp)
    bootstrap = figure_skill / "scripts" / "setup" / "bootstrap.py"

    initial_check = subprocess.run(
        [sys.executable, str(bootstrap), "check"],
        cwd=figure_skill,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if initial_check.returncode != 1 or "Runtime not installed:" not in initial_check.stdout:
        raise AssertionError(
            "fresh copy did not report missing runtime\n"
            f"{initial_check.stdout}\n{initial_check.stderr}"
        )
    if runtime_path.exists():
        raise AssertionError("bootstrap check created the runtime directory")

    tool_state = _tool_state()
    install_command = [sys.executable, str(bootstrap), "install"]
    if len(components) == 1:
        install_command.extend(("--component", components[0]))
    _run_checked(install_command, figure_skill, environment, 900, "bootstrap install")
    if _tool_state() != tool_state:
        raise AssertionError("package-manager executable changed during isolated install")
    if any(path.exists() for path in sentinels):
        raise AssertionError("bootstrap wrote outside the copied Skill runtime")

    for component, cache_name in (("python", "uv"), ("javascript", "npm")):
        if component in components and not (runtime_path / "cache" / cache_name).is_dir():
            raise AssertionError(f"{component} cache is missing from the copied Skill runtime")

    check_command = [sys.executable, str(bootstrap), "check"]
    if len(components) == 1:
        check_command.extend(("--component", components[0]))
    checked = _run_checked(check_command, figure_skill, environment, 30, "bootstrap check")
    for component in components:
        if f"{component}: ready" not in checked.stdout:
            raise AssertionError(f"bootstrap check did not report {component}: ready")

    if "python" in components:
        python_environment = runtime_path / "python" / ".venv"
        python_executable = python_environment / (
            "Scripts/python.exe" if os.name == "nt" else "bin/python"
        )
        if not python_executable.is_file():
            raise AssertionError(f"private Python interpreter is missing: {python_executable}")

        artifacts_dir = target_temp / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        python_script = textwrap.dedent(
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
            from figure_layout.layout import LayoutPolicy

            output_dir = Path(__ARTIFACT_DIR__)
            output_dir.mkdir(parents=True, exist_ok=True)
            exporter = FigureExporter()
            figure, axis = plt.subplots()
            axis.plot([0, 1, 2], [0, 1, 4], label="series")
            axis.set_xlabel("x")
            axis.set_ylabel("y")
            axis.legend()
            original = (
                tuple(figure.get_size_inches()),
                tuple(axis.get_xlim()),
                tuple(axis.get_ylim()),
                tuple(axis.lines[0].get_xydata().ravel()),
                tuple(axis.get_position().bounds),
                figure.dpi,
            )
            outputs = []
            for preset, suffix in (
                ("single", "png"),
                ("double", "svg"),
                ("double", "pdf"),
            ):
                path = output_dir / f"python-{preset}.{suffix}"
                result = exporter.export(
                    figure,
                    path,
                    kind="line",
                    preset=preset,
                    layout_policy=LayoutPolicy(mode="compact"),
                )
                outputs.append({
                    "path": str(path.resolve()),
                    "format": result.format,
                    "preset": result.preset,
                    "width": result.width_px,
                    "height": result.height_px,
                    "status": result.audit.geometry_status,
                })
            unchanged = original == (
                tuple(figure.get_size_inches()),
                tuple(axis.get_xlim()),
                tuple(axis.get_ylim()),
                tuple(axis.lines[0].get_xydata().ravel()),
                tuple(axis.get_position().bounds),
                figure.dpi,
            )
            if not unchanged:
                raise AssertionError("FigureExporter changed source data or layout")
            with Image.open(outputs[0]["path"]) as image:
                if image.size != (1004, 709):
                    raise AssertionError(f"wrong single-column PNG size: {image.size}")
            if any(
                item["status"] != "passed" or
                item["width"] != (1004 if item["preset"] == "single" else 2126) or
                item["height"] != (709 if item["preset"] == "single" else 1241)
                for item in outputs
            ):
                raise AssertionError(f"supported exports failed checks: {outputs}")

            image_figure, image_axis = plt.subplots()
            image_axis.imshow([[1, 2], [3, 4]])
            image_path = output_dir / "python-nonauditable.png"
            image_result = exporter.export(
                image_figure,
                image_path,
                kind="heatmap",
                preset="single",
                layout_policy=LayoutPolicy(mode="compact"),
            )
            image_status = image_result.audit.geometry_status
            if image_status != "not_auditable":
                raise AssertionError(f"image geometry was misreported: {image_status}")
            outputs.append({
                "path": str(image_path.resolve()),
                "format": "png",
                "preset": "single",
                "width": image_result.width_px,
                "height": image_result.height_px,
                "status": image_status,
            })
            plt.close(figure)
            plt.close(image_figure)
            print(json.dumps({
                "import_path": str(Path(figure_layout.__file__).resolve()),
                "sys_path": sys.path,
                "source_unchanged": unchanged,
                "outputs": outputs,
            }))
            """
        ).replace("__ARTIFACT_DIR__", repr(str(artifacts_dir)))
        python_script_path = target_temp / "python-smoke.py"
        python_script_path.write_text(python_script, encoding="utf-8")
        python_result = _run_checked(
            [str(python_executable), "-B", str(python_script_path)],
            figure_skill,
            environment,
            180,
            "copied Figure Skill Python smoke",
        )
        python_report = json.loads(python_result.stdout)
        python_import_path = Path(python_report["import_path"]).resolve()
        if not python_import_path.is_relative_to(figure_skill.resolve()):
            raise AssertionError(f"figure_layout imported outside copied Skill: {python_import_path}")
        if not python_report["source_unchanged"]:
            raise AssertionError("Python export changed the source figure")
        for output in python_report["outputs"]:
            expected = (1004, 709) if output["preset"] == "single" else (2126, 1241)
            if (output["width"], output["height"]) != expected:
                raise AssertionError(f"wrong Python export dimensions: {output}")
            if not Path(output["path"]).is_file():
                raise AssertionError(f"Python export is missing: {output['path']}")
        python_outputs = tuple(Path(output["path"]) for output in python_report["outputs"])
        python_statuses = tuple(output["status"] for output in python_report["outputs"])
    else:
        python_import_path = figure_skill / "scripts" / "python" / "figure_layout" / "__init__.py"
        python_report = {"sys_path": []}
        python_outputs = ()
        python_statuses = ()

    contract_root = target_temp / "py-infrastructure-contract"
    copied_infrastructure = (
        copied_skills_path / "py-infrastructure" / "scripts" / "infrastructure"
    )
    utils = contract_root / "utils"
    utils.mkdir(parents=True, exist_ok=True)
    (utils / "__init__.py").touch()
    shutil.copytree(copied_infrastructure, utils / "infrastructure")
    (contract_root / ".project-root").touch()
    contract_script = textwrap.dedent(
        """
        from pathlib import Path
        from utils.infrastructure import Infrastructure

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
    )
    contract_result = _run_checked(
        [sys.executable, "-c", contract_script],
        contract_root,
        environment,
        60,
        "copied py-infrastructure contract",
    )
    contract_outputs = tuple((contract_root / "artifacts").rglob("summary.txt"))
    if len(contract_outputs) != 1 or contract_outputs[0].read_text(encoding="utf-8") != "contract ok\n":
        raise AssertionError(
            f"copied py-infrastructure contract output is invalid: "
            f"{contract_result.stdout}\n{contract_result.stderr}"
        )

    js_bundle_path = (
        runtime_path
        / "javascript"
        / "node_modules"
        / "plotly.js-dist-min"
        / "plotly.min.js"
    )
    js_outputs: tuple[Path, ...] = ()
    js_statuses: tuple[str, ...] = ()
    js_source_requests: tuple[str, ...] = ()
    if "javascript" in components:
        if not js_bundle_path.is_file():
            raise AssertionError(f"private Plotly bundle is missing: {js_bundle_path}")
        if (runtime_path / "javascript" / "node_modules" / "playwright-core").exists():
            raise AssertionError("playwright-core was installed into the Skill runtime")
        node_executable = shutil.which("node")
        playwright_package = REPOSITORY_ROOT / "node_modules" / "playwright-core"
        if node_executable is None or not playwright_package.is_dir():
            raise AssertionError("repository test runtime is missing Node.js or playwright-core")
        browser_executable = os.environ.get("SCI_TEST_BROWSER") or (
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        )
        if not Path(browser_executable).is_file():
            raise AssertionError(f"headless browser is missing: {browser_executable}")

        script_paths = (
            js_bundle_path,
            figure_skill / "scripts" / "javascript" / "ranges.js",
            figure_skill / "scripts" / "javascript" / "layout.js",
            figure_skill / "scripts" / "javascript" / "annotations.js",
            figure_skill / "scripts" / "javascript" / "audit.js",
            figure_skill / "scripts" / "javascript" / "figure-layout.js",
        )
        script_tags = "\n".join(
            f'<script src="{html.escape(path.resolve().as_uri(), quote=True)}"></script>'
            for path in script_paths
        )
        page_path = target_temp / "offline-plotly-smoke.html"
        page_path.write_text(
            "<!doctype html><meta charset=\"utf-8\"><div id=\"plot\"></div>\n"
            + script_tags
            + """
            <script>
              window.ready = Plotly.newPlot(
                document.getElementById("plot"),
                [{
                  type: "scatter",
                  mode: "lines+markers",
                  x: [0, 1, 2],
                  y: [0, 1, 4],
                  name: "series"
                }],
                {
                  xaxis: {title: {text: "x"}},
                  yaxis: {title: {text: "y"}},
                  showlegend: true
                },
                {staticPlot: true, responsive: false}
              );
            </script>
            """,
            encoding="utf-8",
        )
        js_artifacts_dir = target_temp / "artifacts"
        js_artifacts_dir.mkdir(parents=True, exist_ok=True)
        browser_script = textwrap.dedent(
            """
            "use strict";
            const assert = require("node:assert/strict");
            const fs = require("node:fs");
            const path = require("node:path");
            const {pathToFileURL} = require("node:url");
            const {chromium} = require(__PLAYWRIGHT_PATH__);

            const pagePath = __PAGE_PATH__;
            const outputDir = __OUTPUT_DIR__;
            const sourceSkillsUrl = __SOURCE_SKILLS_URL__.toLowerCase();
            const browserPath = __BROWSER_PATH__;
            const networkRequests = [];
            const localRequests = [];
            const bytesFromDataUrl = value => {
              const comma = value.indexOf(",");
              assert.ok(comma > 0, "invalid data URL");
              const header = value.slice(0, comma);
              const payload = value.slice(comma + 1);
              return header.includes(";base64")
                ? Buffer.from(payload, "base64")
                : Buffer.from(decodeURIComponent(payload), "utf8");
            };

            (async () => {
              const browser = await chromium.launch({
                executablePath: browserPath,
                headless: true
              });
              try {
                const page = await browser.newPage();
                page.on("request", request => {
                  const url = request.url();
                  if (/^https?:/i.test(url)) networkRequests.push(url);
                  if (url.startsWith("file://")) localRequests.push(url);
                });
                await page.goto(pathToFileURL(pagePath).href);
                await page.evaluate(() => window.ready);
                const result = await page.evaluate(async () => {
                  const ensure = (condition, message) => {
                    if (!condition) throw new Error(message);
                  };
                  const graph = document.getElementById("plot");
                  const before = JSON.stringify({
                    data: graph.data,
                    layout: graph.layout,
                    range: graph._fullLayout.xaxis.range
                  });
                  const outputs = [];
                  for (const preset of ["single", "double"]) {
                    for (const format of ["png", "svg"]) {
                      const exported = await window.exportScientificFigure(graph, {
                        format,
                        preset,
                        layoutPolicy: {mode: "compact"}
                      });
                      const expected = preset === "single"
                        ? [1004, 709] : [2126, 1241];
                      ensure(exported.width === expected[0], "wrong Plotly width");
                      ensure(exported.height === expected[1], "wrong Plotly height");
                      ensure(
                        exported.audit.geometryStatus === "passed",
                        JSON.stringify(exported.audit.geometryIssues)
                      );
                      outputs.push({
                        preset,
                        format,
                        width: exported.width,
                        height: exported.height,
                        status: exported.audit.geometryStatus,
                        dataUrl: exported.dataUrl
                      });
                    }
                  }
                  const after = JSON.stringify({
                    data: graph.data,
                    layout: graph.layout,
                    range: graph._fullLayout.xaxis.range
                  });
                  ensure(before === after, "export changed the source Plotly graph");
                  ensure(
                    document.querySelectorAll("[data-sci-export]").length === 0,
                    "temporary export graph remained in the page"
                  );

                  const curve = document.createElement("div");
                  document.body.appendChild(curve);
                  await Plotly.newPlot(
                    curve,
                    [{
                      type: "scatter",
                      mode: "lines",
                      x: [0, 1, 2],
                      y: [0, 1, 4],
                      line: {shape: "spline"}
                    }],
                    {xaxis: {title: {text: "x"}}, yaxis: {title: {text: "y"}}},
                    {staticPlot: true, responsive: false}
                  );
                  const unsupported = await window.exportScientificFigure(curve, {
                    format: "png",
                    preset: "single"
                  });
                  ensure(
                    unsupported.audit.geometryStatus === "not_auditable",
                    JSON.stringify(unsupported.audit.geometryIssues)
                  );
                  outputs.push({
                    preset: "single",
                    format: "png",
                    width: unsupported.width,
                    height: unsupported.height,
                    status: unsupported.audit.geometryStatus,
                    dataUrl: unsupported.dataUrl,
                    name: "plotly-nonauditable.png"
                  });
                  Plotly.purge(curve);
                  curve.remove();
                  return outputs;
                });

                const artifacts = [];
                for (const output of result) {
                  const name = output.name || `plotly-${output.preset}.${output.format}`;
                  const bytes = bytesFromDataUrl(output.dataUrl);
                  if (output.format === "png") {
                    const expected = output.preset === "single"
                      ? [1004, 709] : [2126, 1241];
                    assert.equal(bytes.readUInt32BE(16), expected[0]);
                    assert.equal(bytes.readUInt32BE(20), expected[1]);
                  } else {
                    const svg = bytes.toString("utf8");
                    assert.match(
                      svg,
                      new RegExp(`viewBox="0 0 ${output.width} ${output.height}"`)
                    );
                  }
                  const artifactPath = path.join(outputDir, name);
                  fs.writeFileSync(artifactPath, bytes);
                  artifacts.push({
                    path: artifactPath,
                    status: output.status,
                    format: output.format,
                    width: output.width,
                    height: output.height
                  });
                }
                assert.deepEqual(networkRequests, []);
                const externalSourceRequests = localRequests.filter(url =>
                  url.toLowerCase().startsWith(sourceSkillsUrl)
                );
                assert.deepEqual(externalSourceRequests, []);
                process.stdout.write(JSON.stringify({
                  artifacts,
                  externalSourceRequests,
                  networkRequests
                }));
              } finally {
                await browser.close();
              }
            })().catch(error => {
              console.error(error.stack || error);
              process.exitCode = 1;
            });
            """
        )
        replacements = {
            "__PLAYWRIGHT_PATH__": json.dumps(str(playwright_package.resolve())),
            "__PAGE_PATH__": json.dumps(str(page_path.resolve())),
            "__OUTPUT_DIR__": json.dumps(str(js_artifacts_dir.resolve())),
            "__SOURCE_SKILLS_URL__": json.dumps(source_skills.as_uri() + "/"),
            "__BROWSER_PATH__": json.dumps(str(Path(browser_executable).resolve())),
        }
        for placeholder, value in replacements.items():
            browser_script = browser_script.replace(placeholder, value)
        browser_script_path = target_temp / "plotly-smoke.cjs"
        browser_script_path.write_text(browser_script, encoding="utf-8")
        browser_result = _run_checked(
            [node_executable, str(browser_script_path)],
            target_temp,
            environment,
            300,
            "copied Plotly browser smoke",
        )
        browser_report = json.loads(browser_result.stdout)
        js_source_requests = tuple(browser_report["externalSourceRequests"])
        js_outputs = tuple(Path(item["path"]) for item in browser_report["artifacts"])
        js_statuses = tuple(item["status"] for item in browser_report["artifacts"])

    external_references = []
    if "python" in components:
        repository_root = REPOSITORY_ROOT.resolve()
        for entry in python_report["sys_path"]:
            resolved = Path(entry or ".").resolve()
            if (
                resolved.is_relative_to(repository_root)
                and not resolved.is_relative_to(copied_skills_path.resolve())
            ):
                external_references.append(str(resolved))
        if not python_import_path.is_relative_to(
            (copied_skills_path / "figure-infrastructure").resolve()
        ):
            external_references.append(str(python_import_path))
    external_references.extend(js_source_requests)
    return DistributionReport(
        copied_skills_path=copied_skills_path,
        runtime_path=runtime_path,
        python_import_path=python_import_path,
        js_bundle_path=js_bundle_path,
        artifacts=(*contract_outputs, *python_outputs, *js_outputs),
        audit_statuses=(*python_statuses, *js_statuses),
        external_repo_references=tuple(dict.fromkeys(external_references)),
    )



class StandaloneSkillTests(unittest.TestCase):
    def test_figure_skill_docs_are_complete_and_self_contained(self) -> None:
        skill_document = SKILL_ROOT / "SKILL.md"
        deployment_document = SKILL_ROOT / "references" / "deployment.md"
        self.assertTrue(skill_document.is_file(), skill_document)
        self.assertTrue(deployment_document.is_file(), deployment_document)

        skill_text = skill_document.read_text(encoding="utf-8")
        deployment_text = deployment_document.read_text(encoding="utf-8")
        for document, text in (
            (skill_document, skill_text),
            (deployment_document, deployment_text),
        ):
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
                relative_path = target.split("#", maxsplit=1)[0]
                if not relative_path or relative_path.startswith(("http:", "https:", "mailto:")):
                    continue
                self.assertTrue(
                    (document.parent / relative_path).is_file(),
                    f"{document.name} links to missing file: {relative_path}",
                )

        for required in (
            "references/capability-matrix.md",
            "bootstrap.py check",
            "bootstrap.py install",
            "from figure_layout import FigureExporter",
            "preserve",
            "compact",
            "not_auditable",
            "MIT",
            "Apache-2.0",
        ):
            self.assertIn(required, skill_text)
        self.assertNotIn("docs/", skill_text)
        self.assertNotIn("tests/", skill_text)

        script_order = (
            "plotly.min.js",
            "ranges.js",
            "layout.js",
            "annotations.js",
            "audit.js",
            "figure-layout.js",
        )
        positions = [deployment_text.index(name) for name in script_order]
        self.assertEqual(positions, sorted(positions))

    def test_python_skill_documents_copy_and_platform_prerequisites(self) -> None:
        skill_document = REPOSITORY_ROOT / "skills" / "py-infrastructure" / "SKILL.md"
        text = skill_document.read_text(encoding="utf-8")

        for required in (
            "scripts/infrastructure/",
            "Windows",
            "Linux",
            "macOS",
            "标准库",
        ):
            self.assertIn(required, text)

        self.assertTrue(
            (
                REPOSITORY_ROOT
                / "skills"
                / "py-infrastructure"
                / "scripts"
                / "infrastructure"
            ).is_dir()
        )

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
            empty_path = Path(temporary) / "empty-bin"
            empty_path.mkdir()
            env = os.environ.copy()
            env["PATH"] = str(empty_path)
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
            self.assertIn("Runtime not installed:", result.stdout)
            skill_document = SKILL_ROOT / "SKILL.md"
            self.assertIn(
                "Runtime not installed:",
                skill_document.read_text(encoding="utf-8"),
            )
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

    def test_bootstrap_rejects_corrupted_python_lock(self) -> None:
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
            (copied_skill / "uv.lock").write_text(
                "this is not valid toml = [",
                encoding="utf-8",
            )
            outside_environment = root / "outside-python-environment"
            outside_cache = root / "outside-uv-cache"
            environment = os.environ.copy()
            environment.pop("PYTHONPATH", None)
            environment.pop("VIRTUAL_ENV", None)
            environment.update(
                {
                    "UV_PROJECT_ENVIRONMENT": str(outside_environment),
                    "UV_CACHE_DIR": str(outside_cache),
                    "UV_PYTHON_DOWNLOADS": "never",
                    "PYTHONDONTWRITEBYTECODE": "1",
                }
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(copied_skill / "scripts" / "setup" / "bootstrap.py"),
                    "install",
                    "--component",
                    "python",
                ],
                cwd=copied_skill,
                env=environment,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )

            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("uv.lock", result.stderr)
            self.assertFalse(outside_environment.exists())
            self.assertFalse(outside_cache.exists())

    @unittest.skipUnless(
        os.environ.get("SCI_RUN_STANDALONE_INSTALL") == "1",
        "requires isolated uv/npm installation and network access",
    )
    def test_bootstrap_install_isolated_and_removal_owns_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            report = run_distribution_smoke(
                REPOSITORY_ROOT / "skills",
                target,
                ("python", "javascript"),
            )

            copied_figure = report.copied_skills_path / "figure-infrastructure"
            self.assertEqual(
                report.runtime_path,
                copied_figure / ".runtime",
            )
            self.assertTrue(report.python_import_path.is_file())
            self.assertTrue(report.python_import_path.is_relative_to(copied_figure))
            self.assertTrue(report.js_bundle_path.is_file())
            self.assertTrue(report.js_bundle_path.is_relative_to(copied_figure))
            self.assertEqual(report.external_repo_references, ())
            self.assertCountEqual(
                report.audit_statuses,
                ("passed",) * 7 + ("not_auditable",) * 2,
            )
            self.assertCountEqual(
                {path.name for path in report.artifacts},
                {
                    "summary.txt",
                    "python-single.png",
                    "python-double.svg",
                    "python-double.pdf",
                    "python-nonauditable.png",
                    "plotly-single.png",
                    "plotly-single.svg",
                    "plotly-double.png",
                    "plotly-double.svg",
                    "plotly-nonauditable.png",
                },
            )
            self.assertTrue(all(path.is_file() for path in report.artifacts))
            self.assertFalse((report.copied_skills_path / "figure-infrastructure" / "tests").exists())

            shutil.rmtree(report.copied_skills_path)
            self.assertFalse(report.runtime_path.exists())
            self.assertTrue((SKILL_ROOT / "scripts" / "setup" / "bootstrap.py").is_file())
            self.assertTrue(
                (
                    REPOSITORY_ROOT
                    / "skills"
                    / "py-infrastructure"
                    / "scripts"
                    / "infrastructure"
                    / "__init__.py"
                ).is_file()
            )

            restored = run_distribution_smoke(
                REPOSITORY_ROOT / "skills",
                target / "reinstalled",
                ("python", "javascript"),
            )
            self.assertTrue(restored.runtime_path.is_dir())
            self.assertTrue(restored.python_import_path.is_relative_to(
                restored.copied_skills_path / "figure-infrastructure"
            ))
            self.assertTrue(restored.js_bundle_path.is_relative_to(
                restored.copied_skills_path / "figure-infrastructure"
            ))


if __name__ == "__main__":
    unittest.main()
