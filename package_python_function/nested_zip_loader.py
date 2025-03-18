# AWS imposes a 10 second limit on the INIT sequence of a Lambda function.  If this time limit is reached, the process
# is terminated and the INIT is performed again as part of the function's billable invocation.
# Reference: https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html
#
# For this reason, we can be left with an incomplete extraction and so care is taken to avoid inadverently using it.
#
# From https://docs.python.org/3/reference/import.html
# "The module will exist in sys.modules before the loader executes the module code. This is crucial because the module
# code may (directly or indirectly) import itself"

# TODO: Inspired by serverless-python-requirements.

def load_nested_zip() -> None:
    from pathlib import Path
    import sys
    import tempfile
    import importlib

    temp_path = Path(tempfile.gettempdir())

    target_package_path = temp_path / "package-python-function"

    if not target_package_path.exists():
        import zipfile
        import shutil
        import os

        staging_package_path = temp_path / ".stage.package-python-function"

        # TODO BW: Work this out.
        if staging_package_path.exists():
            shutil.rmtree(str(staging_package_path))

        nested_zip_path = Path(__file__).parent / '.requirements.zip'

        zipfile.ZipFile(str(nested_zip_path), 'r').extractall(str(staging_package_path))
        os.rename(str(staging_package_path), str(target_package_path))  # Atomic -- TODO BW DOCME

    # TODO BW: Update this comment
    # We want our path to look like [working_dir, serverless_requirements, ...]
    sys.path.insert(1, target_package_path)
    importlib.reload(sys.modules[__name__])

load_nested_zip()