import sys
import zipfile
from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch

from package_python_function.main import main
from package_python_function.reproducible_zipfile import (
    DEFAULT_DATE_TIME,
    SourceDateEpochError,
)

from .conftest import Data, verify_file_reproducibility

@pytest.mark.parametrize(
    "src_epoch, expected_exception, expected_date_time",
    [
        (None, None, DEFAULT_DATE_TIME),
        ("666666666", None, (1991, 2, 16, 1, 11, 6)),
        ("420", SourceDateEpochError, None),
    ],
    ids=[
        "happy_path",
        "valid_epoch_sets_expected_date_time",
        "too_low_epoch_raises_error",
    ],
)
def test_package_python_function(
    expected_date_time: tuple | None,
    expected_exception: Exception | None,
    monkeypatch: MonkeyPatch,
    src_epoch: str | None,
    test_data: Data,
    tmp_path: Path,
) -> None:
    if src_epoch is not None:
        monkeypatch.setenv("SOURCE_DATE_EPOCH", src_epoch)
    else:
        monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)

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

    if expected_exception is not None:
        with pytest.raises(SourceDateEpochError):
            main()
    else:
        main()

        zip_file = output_dir_path / f"{test_data.pyproject.name.replace('-', '_')}.zip"
        assert zip_file.exists()

        verify_dir = tmp_path / "verify"
        verify_dir.mkdir()
        with zipfile.ZipFile(zip_file, "r") as zip:
            zip.extractall(verify_dir)
            verify_file_reproducibility(zip.infolist(), expected_file_date_time=expected_date_time)

        for file in test_data.project_files:
            if file in test_data.files_excluded_from_bundle:
                assert not (verify_dir / file.path).exists()
            else:
                assert (verify_dir / file.path).exists()

def test_python_package_deterministic_file_ordering(
    test_data: Data,
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
):
    zip_contents: dict[str, list[str]] = {}

    original_iterdir = Path.iterdir

    # Simulate adding the files in a random order
    def shuffled_iterdir(path: Path):
        import random

        results = list(original_iterdir(path))
        random.shuffle(results)
        return iter(results)

    monkeypatch.setattr(Path, "iterdir", shuffled_iterdir)

    for id in ["a", "b"]:
        output = tmp_path / f"output_{id}"
        output.mkdir()
        sys.argv = [
            "test_package_python_function",
            str(test_data.venv_dir),
            "--project",
            str(test_data.pyproject.path),
            "--output-dir",
            str(output),
        ]
        main()
        zip_file = output / f"{test_data.pyproject.name.replace('-', '_')}.zip"
        with zipfile.ZipFile(zip_file, "r") as zip_file:
            zip_contents[id] = [zi.filename for zi in zip_file.infolist()]

    assert zip_contents["a"] == zip_contents["b"], (
        "File ordering in the zip file is not deterministic when the input file order is shuffled."
    )

@pytest.mark.parametrize(
    "src_epoch, expected_exception, expected_date_time",
    [
        (None, None, DEFAULT_DATE_TIME),
        ("666666666", None, (1991, 2, 16, 1, 11, 6)),
        ("420", SourceDateEpochError, None),
    ],
    ids=[
        "happy_path",
        "valid_epoch_sets_expected_date_time",
        "too_low_epoch_raises_error",
    ],
)
def test_package_python_function_nested(
    expected_date_time: tuple | None,
    expected_exception: Exception | None,
    monkeypatch: MonkeyPatch,
    src_epoch: str | None,
    test_data_nested: Data,
    tmp_path: Path,
) -> None:
    if src_epoch is not None:
        monkeypatch.setenv("SOURCE_DATE_EPOCH", src_epoch)
    else:
        monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)

    output_dir_path = tmp_path / "output"
    output_dir_path.mkdir()

    sys.argv = [
        "test_package_python_function",
        str(test_data_nested.venv_dir),
        "--project",
        str(test_data_nested.pyproject.path),
        "--output-dir",
        str(output_dir_path),
    ]

    if expected_exception is not None:
        with pytest.raises(SourceDateEpochError):
            main()
    else:
        main()

        verify_dir = tmp_path / "verify"
        verify_dir.mkdir()

        project_name_snake = test_data_nested.pyproject.name.replace("-", "_")
        ozip = output_dir_path / f"{project_name_snake}.zip"
        assert ozip.exists()

        with zipfile.ZipFile(ozip, "r") as ozip:
            ozip.extractall(verify_dir)
            verify_file_reproducibility(ozip.infolist(), expected_file_date_time=expected_date_time)

            assert (verify_dir / project_name_snake / "__init__.py").exists()
            inner_zip = verify_dir / project_name_snake / ".dependencies.zip"
            assert inner_zip.exists()

            with zipfile.ZipFile(inner_zip, "r") as izip:
                izip.extractall(verify_dir)
                verify_file_reproducibility(izip.infolist(), expected_file_date_time=expected_date_time)

                for file in test_data_nested.project_files:
                    if file in test_data_nested.files_excluded_from_bundle:
                        assert not (verify_dir / file.path).exists()
                    else:
                        assert (verify_dir / file.path).exists()
