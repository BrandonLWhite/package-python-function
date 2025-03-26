# This file represents the original module's __init__.py file that gets renamed when creating the innner ZIP.

import logging

logger = logging.getLogger(__name__ + "(__init__.py ORIGINAL)")

logger.info("Hello, I am the original pacakge __init__.py")

GLOBAL_VALUE_IN_INIT_ORIGINAL = "This global is defined in the original __init__.py"

from .other_module import other_module_function