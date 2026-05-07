import importlib
import multiprocessing
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

import pytest

# We have to use importlib here because nested_zip_loader calls load_nested_zip
# at IMPORT TIME, which causes us a world of hurt in these tests if we try to
# import it "normally" here.
LOADER_PATH = Path(__file__).parent.parent / "package_python_function" / "nested_zip_loader.py"
PKG_NAME = "_test_nested_zip"

def _make_deps_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(f"{PKG_NAME}/__init__.py", "LOADED = True\n")

@pytest.fixture()
def lambda_env(tmp_path, monkeypatch):
    """Simulate a Lambda-like layout: a task dir with a package whose __init__.py
    is the nested_zip_loader code, and a .dependencies.zip with the 'real' code."""
    task_dir = tmp_path / "task"
    pkg_dir = task_dir / PKG_NAME
    pkg_dir.mkdir(parents=True)
    shutil.copy(LOADER_PATH, pkg_dir / "__init__.py")
    _make_deps_zip(pkg_dir / ".dependencies.zip")

    tmp_dir = tmp_path / "tmp"
    tmp_dir.mkdir()
    monkeypatch.setenv("TMPDIR", str(tmp_dir))
    tempfile.tempdir = None

    monkeypatch.syspath_prepend(str(task_dir))

    yield tmp_path

    sys.modules.pop(PKG_NAME, None)
    tempfile.tempdir = None

def test_cold_start_extracts(lambda_env):
    mod = importlib.import_module(PKG_NAME)
    assert mod.LOADED is True
    assert (lambda_env / "tmp" / "package-python-function").exists()

def test_warm_start_skips_extraction(lambda_env):
    target_pkg = lambda_env / "tmp" / "package-python-function" / PKG_NAME
    target_pkg.mkdir(parents=True)
    (target_pkg / "__init__.py").write_text("LOADED = 'warm'\n")

    mod = importlib.import_module(PKG_NAME)
    assert mod.LOADED == "warm"

def test_stale_staging_cleaned(lambda_env):
    staging = lambda_env / "tmp" / ".stage.package-python-function"
    staging.mkdir(parents=True)
    (staging / "stale.txt").write_text("leftover")

    importlib.import_module(PKG_NAME)
    assert not staging.exists()

def _worker(task_dir):
    import importlib
    import sys

    sys.path.insert(0, task_dir)
    assert importlib.import_module(PKG_NAME).LOADED is True

def test_concurrent_no_race(lambda_env):
    ctx = multiprocessing.get_context("forkserver")
    procs = [ctx.Process(target=_worker, args=(str(lambda_env / "task"),)) for _ in range(2)]
    for p in procs:
        p.start()
    for p in procs:
        p.join(timeout=10)
        assert p.exitcode == 0, "A race condition occured while extracting."
    assert (lambda_env / "tmp" / "package-python-function").exists()
