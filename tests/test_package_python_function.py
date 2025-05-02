import sys
import zipfile
from pathlib import Path

from package_python_function.main import main

from .conftest import Data, File

EXPECTED_FILE_MODE = 0o644
EXPECTED_FILE_DATE_TIME = (1980, 1, 1, 0, 0, 0)

def test_package_python_function(tmp_path: Path) -> None:
    files = [
        File.new("project_1/__init__.py"),
        File.new("project_1/project1.py"),
        File.new("small_dependency/__init__.py"),
        File.new("small_dependency/small_dependency.py", "# This is a small dependency"),
    ]
    data = Data.new(project_name="project-1", project_files=files).commit(loc=tmp_path)

    output_dir_path = tmp_path / "output"
    output_dir_path.mkdir()

    sys.argv = [
        "test_package_python_function", str(data.venv_dir),
        "--project", str(data.pyproject.path),
        "--output-dir", str(output_dir_path),
    ]
    main()

    zip_file = output_dir_path / "project_1.zip"
    assert zip_file.exists()

    verify_dir = tmp_path / "verify"
    verify_dir.mkdir()
    with zipfile.ZipFile(zip_file, "r") as zip:
        zip.extractall(verify_dir)
        for file_info in zip.infolist():
            mode = (file_info.external_attr >> 16) & 0xFFFF
            assert mode == EXPECTED_FILE_MODE
            assert file_info.date_time == EXPECTED_FILE_DATE_TIME

    for file in data.project_files:
        assert (verify_dir / file.path).exists()
