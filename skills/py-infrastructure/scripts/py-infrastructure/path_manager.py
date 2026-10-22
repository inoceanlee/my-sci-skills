from __future__ import annotations

import __main__
from datetime import datetime
from itertools import count
from pathlib import Path, PureWindowsPath

_WINDOWS_RESERVED_BASE_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"}
)
_WINDOWS_RESERVED_PREFIXES = ("COM", "LPT")
_MAX_WINDOWS_COMPONENT_UTF16_UNITS = 255
_WINDOWS_INVALID_CHARACTERS = frozenset('<>:"/\\|?*')


class PathManager:
    """Resolve project roots and create one output directory per process run."""

    def __init__(self, project_root: Path, run_dir: Path) -> None:
        self.project_root = project_root
        self.run_dir = run_dir

    @classmethod
    def initialize(
        cls,
        output_dir: str | Path | None = None,
        run_name: str | None = None,
    ) -> PathManager:
        entry_path = cls._entry_path()
        project_root = cls._find_project_root(entry_path.parent)
        name = run_name if run_name is not None else entry_path.stem
        cls._validate_component(name, "run_name")
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
        base_name = f"{name}-{timestamp}"
        cls._validate_component(base_name, "run_name")
        parent = cls._output_parent(output_dir, project_root)
        parent.mkdir(parents=True, exist_ok=True)
        for suffix in count():
            candidate_name = base_name if suffix == 0 else f"{base_name}-{suffix}"
            cls._validate_component(candidate_name, "run_name")
            run_dir = parent / candidate_name
            try:
                run_dir.mkdir()
            except FileExistsError:
                continue
            return cls(project_root, run_dir)

        raise RuntimeError("Could not create a unique run directory")

    @staticmethod
    def _entry_path() -> Path:
        main_file = getattr(__main__, "__file__", None)
        if main_file:
            entry_path = Path(main_file).expanduser().resolve()
            if entry_path.is_file():
                return entry_path
        return Path.cwd().resolve() / "task.py"

    @staticmethod
    def _find_project_root(start: Path) -> Path:
        directories = (start, *start.parents)
        for marker in (".project-root", "pyproject.toml", ".git"):
            for directory in directories:
                if (directory / marker).exists():
                    return directory
        return start

    @staticmethod
    def _output_parent(output_dir: str | Path | None, project_root: Path) -> Path:
        if output_dir is None:
            return project_root / "output"
        parent = Path(output_dir).expanduser()
        return parent if parent.is_absolute() else project_root / parent

    @staticmethod
    def _validate_component(value: str, argument: str) -> None:
        length_error = (
            f"{argument} exceeds {_MAX_WINDOWS_COMPONENT_UTF16_UNITS} "
            "UTF-16 code units"
        )
        if len(value) > _MAX_WINDOWS_COMPONENT_UTF16_UNITS:
            raise ValueError(length_error)
        utf16_units = sum(
            2 if ord(character) > 0xFFFF else 1 for character in value
        )
        if utf16_units > _MAX_WINDOWS_COMPONENT_UTF16_UNITS:
            raise ValueError(length_error)

        base_name = value.rstrip(" .").split(".", 1)[0].rstrip(" .").upper()
        device_name = base_name in _WINDOWS_RESERVED_BASE_NAMES or (
            len(base_name) == 4
            and base_name[:3] in _WINDOWS_RESERVED_PREFIXES
            and base_name[3] in "123456789¹²³"
        )
        if (
            not value
            or value in {".", ".."}
            or Path(value).name != value
            or PureWindowsPath(value).name != value
            or value.endswith((".", " "))
            or any(
                character in _WINDOWS_INVALID_CHARACTERS or ord(character) < 32
                for character in value
            )
            or device_name
        ):
            raise ValueError(f"{argument} must be a valid single path component")

    def output_path(self, category: str, filename: str) -> Path:
        self._validate_component(category, "category")
        self._validate_component(filename, "filename")
        category_dir = self.run_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)
        return category_dir / filename
