# This is my best attempt at simulating what AWS Lambda does
# Instead of messing with zipping and unzipping in this experiment, I just copy the files to the .test directory.

import logging
from pathlib import Path
import shutil
import sys

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("lambda-runner.py")

logger.info('BEGIN')

module_path = Path(__file__).parent
TEST_DIR = module_path / ".test"
PACKAGE_NAME = "zip_in_zip_test"
TEST_PACKAGE_DIR = TEST_DIR / PACKAGE_NAME

shutil.rmtree(TEST_DIR, ignore_errors=True)

# Copy the stub `zip_in_zip_test` package to the .test directory. This simulates the outer ZIP extraction
# that lambda will do.  This is the module that Lambda will import, and where we will do the inner ZIP extraction.
shutil.copytree(str(module_path / PACKAGE_NAME), str(TEST_PACKAGE_DIR))

# Copy the inner package to the .test directory. This simulates the inner ZIP file, but without actually dealing
# with zip/unzip in this experiemen.
shutil.copytree(str(module_path / "inner_package"), str(TEST_PACKAGE_DIR / ".inner_package"))

sys.path.insert(0, str(TEST_DIR))

logger.info('--- Importing entrypoint module ---')
import importlib
module = importlib.import_module('zip_in_zip_test.main')
logger.info('--- Calling entryoint function ---')
module.__dict__['main']()
