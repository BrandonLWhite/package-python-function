import importlib
from pathlib import Path
import sys
import zipfile


def xtest_local(package_path: str, entrypoint: str) -> None:
    output_path = Path(package_path).parent / 'lambda'
    output_path.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(package_path, 'r') as zip:
        zip.extractall(str(output_path))

    sys.path.insert(0, str(output_path))

    entrypoint_parts = entrypoint.split('.')
    module_name = '.'.join(entrypoint_parts[0:1])
    entry_function = entrypoint_parts[2]
    module = importlib.import_module(module_name)
    print(sys.path)
    module.__dict__[entry_function]()


if __name__ == '__main__':
    xtest_local(sys.argv[1], sys.argv[2])