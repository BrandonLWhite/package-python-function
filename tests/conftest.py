import json
from dataclasses import dataclass
from pathlib import Path
from typing import Self
from zipfile import ZipInfo

import pytest
import tomli_w

from package_python_function.packager import Packager
from package_python_function.python_project import PythonProject
from package_python_function.reproducible_zipfile import (
    DEFAULT_DATE_TIME,
    DEFAULT_FILE_MODE,
)

@dataclass
class File:
    path: Path
    contents: str

    @classmethod
    def new(cls, path: str, contents: str = "") -> Self:
        return cls(path=Path(path), contents=contents)

@dataclass
class Data:
    files_excluded_from_bundle: list[File]  # relative to packages_dir
    project_files: list[File]  # relative to packages_dir
    pyproject: PythonProject
    python_version: str
    venv_dir: Path

    @classmethod
    def new(
        cls,
        project_name: str,
        project_files: list[File],
        files_excluded_from_bundle: list[File],
        python_version: str = "3.13",
    ) -> Self:
        pyproject = _new_python_project(name=project_name)
        return cls(
            files_excluded_from_bundle=files_excluded_from_bundle,
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

def verify_file_reproducibility(file_info: list[ZipInfo], expected_file_date_time=None, expected_file_mode=None):
    if expected_file_date_time is None:
        expected_file_date_time = DEFAULT_DATE_TIME
    if expected_file_mode is None:
        expected_file_mode = DEFAULT_FILE_MODE

    for info in file_info:
        mode = (info.external_attr >> 16) & 0xFFFF
        assert mode == expected_file_mode
        assert info.date_time == expected_file_date_time

@pytest.fixture
def test_files(tmp_path: Path):
    files_excluded_from_bundle = [
        File.new("__pycache__/_virtualenv.cpython-313.pyc"),
        File.new("project_1.dist-info/RECORD"),
        File.new("project_1.dist-info/direct_url.json", contents=json.dumps({"url": str(tmp_path)})),
    ]
    files = [
        File.new("project_1/__init__.py"),
        File.new("project_1/project1.py"),
        File.new("project_1.dist-info/METADATA"),
        File.new("small_dependency/__init__.py"),
        File.new("small_dependency/small_dependency.py", "# This is a small dependency"),
        *files_excluded_from_bundle,
    ]
    yield files, files_excluded_from_bundle, tmp_path

@pytest.fixture
def test_files_nested(test_files):
    files, files_excluded_from_bundle, tmp_path = test_files
    big_files = [
        File.new("gigantic_dependency/__init__.py"),
        File.new("gigantic_dependency/gigantic.py", "a" * Packager.AWS_LAMBDA_MAX_UNZIP_SIZE),
    ]
    yield [*files, *big_files], files_excluded_from_bundle, tmp_path

@pytest.fixture
def test_data(test_files):
    files, files_excluded_from_bundle, loc = test_files
    data = Data.new(
        project_name="project-1",
        project_files=files,
        files_excluded_from_bundle=files_excluded_from_bundle,
    ).commit(loc=loc)
    yield data

@pytest.fixture
def test_data_nested(test_files_nested):
    files, files_excluded_from_bundle, loc = test_files_nested
    data = Data.new(
        project_name="project-1-nested",
        project_files=files,
        files_excluded_from_bundle=files_excluded_from_bundle,
    ).commit(loc=loc)
    yield data
