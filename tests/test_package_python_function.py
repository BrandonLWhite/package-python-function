import sys
import zipfile
from pathlib import Path

import pytest

from package_python_function.main import main
from package_python_function.reproducible_zipfile import SourceDateEpochError

from .conftest import Data, File

EXPECTED_FILE_MODE = 0o644
EXPECTED_FILE_DATE_TIME = (1980, 1, 1, 0, 0, 0)

@pytest.fixture
def test_data(tmp_path: Path):
    files = [
        File.new("project_1/__init__.py"),
        File.new("project_1/project1.py"),
        File.new("small_dependency/__init__.py"),
        File.new("small_dependency/small_dependency.py", "# This is a small dependency"),
    ]
    data = Data.new(project_name="project-1", project_files=files).commit(loc=tmp_path)
    yield data

def test_package_python_function(test_data: Data, tmp_path: Path) -> None:
    output_dir_path = tmp_path / "output"
    output_dir_path.mkdir()

    sys.argv = [
        "test_package_python_function",
        str(test_data.venv_dir),
        "--project",
        str(test_data.pyproject.path),
        "--output-dir",
        str(output_dir_path),
    ]
    main()

    zip_file = output_dir_path / f"{test_data.pyproject.name.replace('-', '_')}.zip"
    assert zip_file.exists()

    verify_dir = tmp_path / "verify"
    verify_dir.mkdir()
    with zipfile.ZipFile(zip_file, "r") as zip:
        zip.extractall(verify_dir)
        for file_info in zip.infolist():
            mode = (file_info.external_attr >> 16) & 0xFFFF
            assert mode == EXPECTED_FILE_MODE
            assert file_info.date_time == EXPECTED_FILE_DATE_TIME

    for file in test_data.project_files:
        assert (verify_dir / file.path).exists()

def test_package_with_src_epoch(test_data: Data, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "666666666")
    expected_file_date_time = (1991, 2, 16, 1, 11, 6)

    output_dir_path = tmp_path / "output"
    output_dir_path.mkdir()

    sys.argv = [
        "test_package_python_function",
        str(test_data.venv_dir),
        "--project",
        str(test_data.pyproject.path),
        "--output-dir",
        str(output_dir_path),
    ]
    main()

    zip_file = output_dir_path / f"{test_data.pyproject.name.replace('-', '_')}.zip"
    assert zip_file.exists()

    verify_dir = tmp_path / "verify"
    verify_dir.mkdir()
    with zipfile.ZipFile(zip_file, "r") as zip:
        zip.extractall(verify_dir)
        for file_info in zip.infolist():
            mode = (file_info.external_attr >> 16) & 0xFFFF
            assert mode == EXPECTED_FILE_MODE
            assert file_info.date_time == expected_file_date_time

    for file in test_data.project_files:
        assert (verify_dir / file.path).exists()

def test_package_with_too_low_src_epoch(test_data: Data, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "420")

    output_dir_path = tmp_path / "output"
    output_dir_path.mkdir()

    sys.argv = [
        "test_package_python_function",
        str(test_data.venv_dir),
        "--project",
        str(test_data.pyproject.path),
        "--output-dir",
        str(output_dir_path),
    ]

    with pytest.raises(SourceDateEpochError):
        main()
