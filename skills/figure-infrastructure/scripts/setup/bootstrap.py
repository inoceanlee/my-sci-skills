"""Install and inspect this Skill's private Python and JavaScript runtimes."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence


class BootstrapError(RuntimeError):
    """Raised when an isolated runtime cannot be installed or verified."""


class BootstrapManager:
    """Manage runtime dependencies beneath one copied Skill directory."""

    COMPONENTS = ("python", "javascript")

    def __init__(self, skill_root: Path | None = None) -> None:
        self.skill_root = (skill_root or Path(__file__).resolve().parents[2]).resolve()
        self.runtime_root = self.skill_root / ".runtime"
        self.python_environment = self.runtime_root / "python" / ".venv"
        self.javascript_root = self.runtime_root / "javascript"
        self.uv_cache = self.runtime_root / "cache" / "uv"
        self.npm_cache = self.runtime_root / "cache" / "npm"
        self.state_path = self.runtime_root / "state.json"

    def check(self, components: Sequence[str]) -> int:
        try:
            for path in self._runtime_paths():
                self._require_inside_skill(path)
        except BootstrapError as error:
            print(f"Error: {error}", file=sys.stderr)
            return 2
        if not self.runtime_root.exists():
            print(f"Runtime not installed: {self.runtime_root}")
            return 2

        missing = False
        for component in components:
            result = self._inspect(component)
            if result is None:
                print(f"{component}: missing or invalid runtime")
                missing = True
            else:
                print(f"{component}: ready")
        return 2 if missing else 0

    def install(self, components: Sequence[str]) -> int:
        for path in self._runtime_paths():
            self._require_inside_skill(path)

        self.runtime_root.mkdir(parents=True, exist_ok=True)
        verified: dict[str, dict[str, str]] = {}
        for component in components:
            if component == "python":
                self._install_python()
            else:
                self._install_javascript()

            result = self._inspect(component)
            if result is None:
                raise BootstrapError(f"Installed {component} runtime failed its verification")
            verified[component] = result

        self._write_state(verified)
        print(f"Installed runtime components: {', '.join(components)}")
        return 0

    def _runtime_paths(self) -> tuple[Path, ...]:
        return (
            self.runtime_root,
            self.python_environment,
            self.javascript_root,
            self.javascript_root / "node_modules",
            self.javascript_root / "package.json",
            self.javascript_root / "package-lock.json",
            self.uv_cache,
            self.npm_cache,
            self.state_path,
            self.state_path.with_suffix(".json.tmp"),
        )

    def _require_inside_skill(self, path: Path) -> None:
        resolved = path.resolve(strict=False)
        if not resolved.is_relative_to(self.skill_root):
            raise BootstrapError(f"Runtime path escapes Skill directory: {path}")

    def _python_executable(self) -> Path:
        executable = "python.exe" if os.name == "nt" else "python"
        scripts = "Scripts" if os.name == "nt" else "bin"
        return self.python_environment / scripts / executable

    def _inspect(self, component: str) -> dict[str, str] | None:
        if component == "python":
            return self._inspect_python()
        return self._inspect_javascript()

    def _inspect_python(self) -> dict[str, str] | None:
        executable = self._python_executable()
        if not executable.is_file():
            return None

        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        script = (
            "from pathlib import Path; import figure_layout; "
            "print(Path(figure_layout.__file__).resolve())"
        )
        try:
            result = subprocess.run(
                [str(executable), "-B", "-c", script],
                cwd=self.skill_root,
                env=environment,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        if result.returncode != 0:
            return None

        import_path = Path(result.stdout.strip()).resolve()
        expected = (self.skill_root / "scripts" / "python" / "figure_layout" / "__init__.py").resolve()
        if import_path != expected:
            return None
        return {"import_path": str(import_path)}

    def _inspect_javascript(self) -> dict[str, str] | None:
        package = self.javascript_root / "node_modules" / "plotly.js-dist-min"
        bundle = package / "plotly.min.js"
        manifest = package / "package.json"
        try:
            self._require_inside_skill(bundle)
            self._require_inside_skill(manifest)
        except BootstrapError:
            return None
        if not bundle.is_file() or not manifest.is_file():
            return None
        try:
            metadata = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if metadata.get("version") != "4.1.2":
            return None
        return {"bundle_path": str(bundle.resolve())}

    @staticmethod
    def _npm_command() -> list[str]:
        npm = shutil.which("npm")
        if npm is None:
            raise BootstrapError("npm executable not found")
        npm_path = Path(npm).resolve()
        if os.name != "nt" or npm_path.suffix.lower() not in {".cmd", ".bat"}:
            return [str(npm_path)]

        node = shutil.which("node")
        npm_cli = npm_path.parent / "node_modules" / "npm" / "bin" / "npm-cli.js"
        if node is None or not npm_cli.is_file():
            raise BootstrapError("Cannot resolve Node.js and npm-cli.js from the npm command")
        return [node, str(npm_cli)]

    def _install_python(self) -> None:
        self.python_environment.parent.mkdir(parents=True, exist_ok=True)
        self.uv_cache.mkdir(parents=True, exist_ok=True)
        environment = os.environ.copy()
        environment["UV_PROJECT_ENVIRONMENT"] = str(self.python_environment)
        environment["UV_CACHE_DIR"] = str(self.uv_cache)
        environment["UV_PYTHON_DOWNLOADS"] = "never"
        self._run(
            [
                "uv",
                "sync",
                "--project",
                str(self.skill_root),
                "--locked",
                "--no-dev",
                "--no-managed-python",
                "--no-python-downloads",
            ],
            environment,
        )

    def _install_javascript(self) -> None:
        self.javascript_root.mkdir(parents=True, exist_ok=True)
        self.npm_cache.mkdir(parents=True, exist_ok=True)
        for manifest in ("package.json", "package-lock.json"):
            source = self.skill_root / manifest
            destination = self.javascript_root / manifest
            self._require_inside_skill(source)
            self._require_inside_skill(destination)
            if not source.is_file():
                raise BootstrapError(f"Required JavaScript manifest is missing: {source}")
            destination.write_bytes(source.read_bytes())

        environment = os.environ.copy()
        environment["npm_config_cache"] = str(self.npm_cache)
        self._run(
            [
                *self._npm_command(),
                "ci",
                "--prefix",
                str(self.javascript_root),
                "--omit=dev",
            ],
            environment,
        )

    def _run(self, command: list[str], environment: dict[str, str]) -> None:
        try:
            result = subprocess.run(
                command,
                cwd=self.skill_root,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as error:
            raise BootstrapError(f"Cannot start {command[0]}: {error}") from error

        if result.stdout:
            print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="" if result.stderr.endswith("\n") else "\n")
        if result.returncode != 0:
            raise BootstrapError(f"{command[0]} exited with code {result.returncode}")

    def _write_state(self, verified: dict[str, dict[str, str]]) -> None:
        state = {"schema_version": 1, "components": verified}
        payload = json.dumps(state, indent=2, sort_keys=True) + "\n"
        temporary = self.state_path.with_suffix(".json.tmp")
        self._require_inside_skill(temporary)
        temporary.write_text(payload, encoding="utf-8")
        temporary.replace(self.state_path)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check", "install"))
    parser.add_argument("--component", choices=("python", "javascript", "all"), default="all")
    try:
        args = parser.parse_args(argv)
    except SystemExit as error:
        return 0 if error.code == 0 else 1
    components = BootstrapManager.COMPONENTS if args.component == "all" else (args.component,)
    manager = BootstrapManager()

    try:
        if args.action == "check":
            return manager.check(components)
        return manager.install(components)
    except BootstrapError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"Error: Runtime filesystem operation failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
