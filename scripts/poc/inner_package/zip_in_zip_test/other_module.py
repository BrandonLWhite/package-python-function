import logging

logger = logging.getLogger(__name__)

logger.info("Load")

def other_module_function():
    logger.info("I'm in other_module_function")