import logging

logger = logging.getLogger(__name__)

logger.info("main.py: Load")

from zip_in_zip_test import GLOBAL_VALUE_IN_INIT_ORIGINAL, other_module_function
from other_package.other_package_module import other_package_module

def main():
    logger.info("Hello from main!")
    logger.info(GLOBAL_VALUE_IN_INIT_ORIGINAL)
    other_module_function()
    other_package_module()