# This works perfectly!

print('zip_in_zip_test.__init__: BEGIN.  This is the loader.')
print("module_path:", __file__)

from pathlib import Path
import importlib
import sys

module_path = Path(__file__).parent

# This works if I insert at zero.
# Why does the serverless-python-requirements insist on inserting at 1?
# From https://docs.aws.amazon.com/lambda/latest/dg/python-package.html#python-package-searchpath:
#   "By default, the first location the runtime searches is the directory into which your .zip deployment package is decompressed and mounted (/var/task)""
# sys.path.insert(0, str(module_path / ".inner_package"))

# This also works.  I am thinking this is the best way, because we need to unmount the original decompressed directory
# since it contains the load __init__.py.
sys.path[0] = str(module_path / ".inner_package")


# The following two approaches works too, and are safe.
# From https://docs.python.org/3/reference/import.html
# "The module will exist in sys.modules before the loader executes the module code. This is crucial because the module
# code may (directly or indirectly) import itself"

# This works too.
# del sys.modules[__name__]
# importlib.import_module(__name__)

# This also works.  I think this is the best way.
importlib.reload(sys.modules[__name__])

print('zip_in_zip_test.__init__: END')