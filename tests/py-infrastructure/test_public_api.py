"""Agent-facing API contract for the Python infrastructure Skill."""

from __future__ import annotations

import inspect
import shutil
import sys
from importlib import import_module
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
INFRASTRUCTURE_SOURCE = (
    REPOSITORY_ROOT / "skills" / "py-infrastructure" / "scripts" / "py-infrastructure"
)


@pytest.fixture(scope="module")
def infrastructure(tmp_path_factory: pytest.TempPathFactory):
    project_root = tmp_path_factory.mktemp("copied-py-infrastructure")
    utils = project_root / "utils"
    utils.mkdir()
    (utils / "__init__.py").touch()
    shutil.copytree(INFRASTRUCTURE_SOURCE, utils / "py-infrastructure")

    previous_utils = sys.modules.pop("utils", None)
    sys.path.insert(0, str(project_root))
    try:
        yield import_module("utils.py-infrastructure")
    finally:
        sys.path.remove(str(project_root))
        for module_name in tuple(sys.modules):
            if module_name == "utils.py-infrastructure" or module_name.startswith(
                "utils.py-infrastructure."
            ):
                sys.modules.pop(module_name)
        sys.modules.pop("utils", None)
        if previous_utils is not None:
            sys.modules["utils"] = previous_utils


def test_infrastructure_exports_its_supported_entry_point(infrastructure) -> None:
    assert "Infrastructure" in infrastructure.__all__


def test_initialize_keeps_documented_parameters_and_defaults(infrastructure) -> None:
    Infrastructure = infrastructure.Infrastructure
    parameters = inspect.signature(Infrastructure.initialize).parameters

    assert list(parameters) == [
        "output_dir",
        "memory_enabled",
        "sample_interval_ms",
        "run_name",
    ]
    assert parameters["output_dir"].default is None
    assert parameters["memory_enabled"].default is True
    assert parameters["sample_interval_ms"].default == 100
    assert parameters["run_name"].default is None


def test_initialized_infrastructure_exposes_supported_operations(
    tmp_path: Path, infrastructure
) -> None:
    Infrastructure = infrastructure.Infrastructure
    infra = Infrastructure.initialize(output_dir=tmp_path, memory_enabled=False)
    try:
        assert callable(infra.output_path)
        assert infra.logger is not None
        assert callable(infra.errors.scope)
        assert callable(infra.timer.scope)
        assert callable(infra.memory.scope)
        assert callable(infra.close)
    finally:
        infra.close()
