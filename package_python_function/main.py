import argparse
from pathlib import Path

from .packager import Packager


def main() -> None:
    args = parse_args()
    project_path = Path(args.project).resolve()
    venv_path = Path(args.venv_dir).resolve()
    output_dir_path = Path(args.output_dir).resolve()
    output_file_path = Path(args.output).resolve() if args.output else None
    packager = Packager(venv_path, project_path, output_dir_path, output_file_path)
    packager.package()


def parse_args() -> argparse.Namespace:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("venv_dir", type=str, help="The directory path to the virtual environment to package into a zip file")
    arg_parser.add_argument("--project", type=str, default='pyproject.toml', help="The path to the project's pyproject.toml file. Omit to use pyproject.toml in the current working directory.")
    arg_parser.add_argument("--output-dir", type=str, default='.', help="The directory path to save the output zip file. Default is the current working directory.")
    arg_parser.add_argument("--output", type=str, default='', help="The full file path for the output file. Use this instead of --output-dir if you want total control of the output file path.")
    return arg_parser.parse_args()
