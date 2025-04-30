from pathlib import Path
import sys
from package_python_function.main import main


PROJECTS_DIR_PATH = Path(__file__).parent / 'projects'


def test_package_python_function(tmp_path: Path) -> None:
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

    assert (output_dir_path / 'project_1.zip').exists()
