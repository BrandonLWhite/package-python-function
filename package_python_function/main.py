import argparse
from pathlib import Path
import logging
import sys

from .packager import Packager
from .reproducible_zipfile import date_time


def main() -> None:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(message)s")

    args = parse_args()

    # Validate $SOURCE_DATE_EPOCH here, so that a bad value fails before any packaging work rather than partway
    # through writing the zip.
    date_time()

    project_path = Path(args.project).resolve()
    venv_path = Path(args.venv_dir).resolve()
    output_dir_path = Path(args.output_dir).resolve()
    output_file_path = Path(args.output).resolve() if args.output else None
    report_file_path = Path(args.report).resolve() if args.report else None
    packager = Packager(venv_path, project_path, output_dir_path, output_file_path, report_file_path)
    packager.package()


def parse_args() -> argparse.Namespace:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("venv_dir", type=str, help="The directory path to the virtual environment to package into a zip file")
    arg_parser.add_argument("--project", type=str, default='pyproject.toml', help="The path to the project's pyproject.toml file. Omit to use pyproject.toml in the current working directory.")
    output_group = arg_parser.add_mutually_exclusive_group()
    output_group.add_argument("--output-dir", type=str, default='.', help="The directory path to save the output zip file. Default is the current working directory.")
    output_group.add_argument("--output", type=str, default='', help="The full file path for the output file. Use this instead of --output-dir if you want total control of the output file path.")
    arg_parser.add_argument("--report", type=str, default='', help="The file path to write a JSON report of the packaging result to. Omit to write no report.")
    return arg_parser.parse_args()
