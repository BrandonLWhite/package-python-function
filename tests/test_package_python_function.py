import sys
import zipfile
from pathlib import Path

from package_python_function.main import main

PROJECTS_DIR_PATH = Path(__file__).parent / 'projects'

def test_package_python_function(tmp_path: Path) -> None:
    EXPECTED_FILE_MODE = 0o644
    EXPECTED_FILE_DATE_TIME = (1980, 1, 1, 0, 0, 0)

    project_file_path = PROJECTS_DIR_PATH / 'project-1' / 'pyproject.toml'

    venv_dir_path = tmp_path / 'venv'
    packages_dir = venv_dir_path / 'lib' / 'python3.11' / 'site-packages'
    packages_dir.mkdir(parents=True)

    primary_package_dir = packages_dir / 'project_1'
    primary_package_dir.mkdir()
    (primary_package_dir / '__init__.py').touch()
    (primary_package_dir / 'project1.py').touch()

    small_dependency_dir = packages_dir / 'small_dependency'
    small_dependency_dir.mkdir()
    (small_dependency_dir / '__init__.py').touch()
    (small_dependency_dir / 'small_dependency.py').write_text("# This is a small dependency")

    output_dir_path = tmp_path / 'output'
    output_dir_path.mkdir()

    sys.argv = [
        "test_package_python_function",
        str(venv_dir_path),
        "--project", str(project_file_path),
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

        assert verify_dir / "project_1" / "__init__.py"
        assert verify_dir / "project_1" / "project1.py"
        assert verify_dir / "small_dependency" / "__init__.py"
        assert verify_dir / "small_dependency" / "small_dependency.py"
