from dataclasses import dataclass
from pathlib import Path
from typing import Self

import tomli_w

from package_python_function.python_project import PythonProject


@dataclass
class File:
    path: Path
    contents: str

    @classmethod
    def new(cls, path: str, contents: str = "") -> Self:
        return cls(path=Path(path), contents=contents)

@dataclass
class Data:
    project_files: list[File]  # relative to packages_dir
    pyproject: PythonProject
    python_version: str
    venv_dir: Path

    @classmethod
    def new(
        cls,
        project_name: str,
        project_files: list[File],
        python_version: str = "3.13",
    ) -> Self:
        pyproject = _new_python_project(name=project_name)
        return cls(
            project_files=project_files,
            pyproject=pyproject,
            python_version=python_version,
            venv_dir=Path(),
        )

    def commit(self, loc: Path) -> Self:
        venv_dir = loc / "venv"
        packages_dir = venv_dir / "lib" / f"python{self.python_version}" / "site-packages"
        packages_dir.mkdir(parents=True, exist_ok=True)

        pyproj_path = loc / self.pyproject.path
        pyproj_path.parent.mkdir(parents=True, exist_ok=True)
        pyproject_toml = tomli_w.dumps(self.pyproject.toml)
        pyproj_path.write_text(pyproject_toml)

        for file in self.project_files:
            path = packages_dir / file.path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(file.contents)

        # resolve paths fully
        self.venv_dir = venv_dir
        self.pyproject.path = pyproj_path

        return self

def _new_python_project(name: str) -> PythonProject:
    pyproj = PythonProject.__new__(PythonProject)
    pyproj.path = Path(name) / "pyproject.toml"
    pyproj.toml = {
        "project": {"name": name},
        "tool": {"poetry": {"name": name}},
    }
    return pyproj
