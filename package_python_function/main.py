import argparse
from pathlib import Path

from .packager import Packager


def main() -> None:
    args = parse_args()
    project_path = Path(args.project).resolve()
    venv_path = Path(args.venv).resolve()
    output_dir_path = Path(args.output_dir).resolve()
    output_file_path = Path(args.output).resolve() if args.output else None
    packager = Packager(venv_path, project_path, output_dir_path, output_file_path)
    packager.package()


def parse_args() -> argparse.Namespace:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("venv", type=str)
    arg_parser.add_argument("--project", type=str, default='pyproject.toml')
    arg_parser.add_argument("--output-dir", type=str, default='.')
    arg_parser.add_argument("--output", type=str, default='')
    return arg_parser.parse_args()
