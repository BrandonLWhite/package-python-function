import logging

logger = logging.getLogger(__name__)

logger.info("Load")

def other_package_module():
    logger.info("Hello from other_package_module")