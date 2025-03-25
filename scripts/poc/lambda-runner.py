# This is my best attempt at simulating what AWS Lambda does
# Instead of messing with zipping and unzipping in this experiment, I just copy the files to the .test directory.

from pathlib import Path
import shutil
import sys

print('[lambda-runner]')
print('sys.path:', sys.path)

module_path = Path(__file__).parent
TEST_DIR = module_path / ".test"
PACKAGE_NAME = "zip_in_zip_test"
TEST_PACKAGE_DIR = TEST_DIR / PACKAGE_NAME

shutil.rmtree(TEST_DIR, ignore_errors=True)
shutil.copytree(str(module_path / PACKAGE_NAME), str(TEST_PACKAGE_DIR))
shutil.copytree(str(module_path / "inner_package"), str(TEST_PACKAGE_DIR / ".inner_package"))

sys.path.insert(0, str(TEST_DIR))

import importlib
module = importlib.import_module('zip_in_zip_test.main')
module.__dict__['main']()
