"""
Purpose: This module is responsible for extracting the nested zip file that contains your code and dependencies for
the Lambda function.
When activated, the content of this file is packaged as your entrypoint's __init__.py module in the
outer ZIP file.

It works by leveraging the Python import system's ability for a module to dynamically replace its code.
When Lambda performs the INIT sequence, it will import the module configured as the entrypoint.  Python will
then first import `the_project/__init__.py``, which is where package-python-function has put the code from
this file.  This code will then extract the nested zip file and replace the module's code with the extracted
code, then trigger a reload of the original module.

From https://docs.python.org/3/reference/import.html
"The module will exist in sys.modules before the loader executes the module code. This is crucial because the module
code may (directly or indirectly) import itself"

Inspired by [serverless-python-requirements](https://github.com/serverless/serverless-python-requirements/blob/master/unzip_requirements.py).

Note:
AWS imposes a 10 second limit on the INIT sequence of a Lambda function.  If this time limit is reached, the process
is terminated and the INIT is performed again as part of the function's billable invocation.
Reference: https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html
For this reason, we can be left with an incomplete extraction and so care is taken to avoid inadverently using it.
"""

def load_nested_zip() -> None:
    import fcntl
    import importlib
    import sys
    import tempfile
    from pathlib import Path

    temp_path = Path(tempfile.gettempdir())

    target_package_path = temp_path / "package-python-function"

    # We use manual locks here to allow target_package_path to stay static,
    # but avoid race conditions when multiple processes try to run this
    # function at the same time.
    lock_path = temp_path / ".package-python-function.lock"

    with open(lock_path, "w") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)

        if not target_package_path.exists():
            import zipfile
            import shutil
            import os

            staging_package_path = temp_path / ".stage.package-python-function"

            if staging_package_path.exists():
                shutil.rmtree(str(staging_package_path))

            nested_zip_path = Path(__file__).parent / ".dependencies.zip"

            with zipfile.ZipFile(str(nested_zip_path), "r") as nested_zip:
                nested_zip.extractall(str(staging_package_path))

            # The idea here is that we don't rename the path until everything has been successfully extracted.
            # This is expected to be an atomic operation.  That way, if AWS terminates us during the extraction,
            # we won't try and use the incomplete extraction.
            os.rename(str(staging_package_path), str(target_package_path))

    # Lambda sets up the sys.path like this:
    #    ['/var/task', '/opt/python/lib/python3.13/site-packages', '/opt/python',
    #     '/var/lang/lib/python3.13/site-packages', '/var/runtime', ...]
    # Where the first entry is the directory where Lambda extracted the zip file
    # Refer to https://docs.aws.amazon.com/lambda/latest/dg/python-package.html#python-package-searchpath
    # We then replace the first entry with the directory where we extracted the nested zip file so that sys.path
    # becomes:
    #    ['/tmp/package-python-function', '/opt/python/lib/python3.13/site-packages', '/opt/python',
    #     '/var/lang/lib/python3.13/site-packages', '/var/runtime', ...]
    # Then we trigger a reload on the current module so that the original module code is loaded.
    sys.path[0] = str(target_package_path)
    importlib.reload(sys.modules[__name__])

load_nested_zip()
