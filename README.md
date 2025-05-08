# package-python-function
Python command-line (CLI) tool to package a Python function for deploying to AWS Lambda, and possibly other cloud platforms.

This tool builds a ZIP file from a virtual environment with all dependencies installed that are to be included in the final deployment asset. If the content is larger than AWS Lambda's maximum unzipped package size of 250 MiB, This tool will then employ the ZIP-inside-ZIP (nested-ZIP) workaround. This allows deploying Lambdas with large dependency packages, especially those with native code compiled extensions like Pandas, PyArrow, etc. The ZIP files are generated [reproducibly](#a-note-on-reproducability), ensuring that the same source will always generate a ZIP file with the same hash.

This technique was originally pioneered by [serverless-python-requirements](https://github.com/serverless/serverless-python-requirements), which is a NodeJS (JavaScript) plugin for the [Serverless Framework](https://github.com/serverless/serverless). The technique has been improved here to not require any special imports in your entrypoint source file. That is, no changes are needed to your source code to leverage the nested ZIP deployment.

The motivation for this Python tool is to achieve the same results as [serverless-python-requirements](https://www.serverless.com/plugins/serverless-python-requirements) but with a purely Python tool. This can simplify and speed up developer and CI/CD workflows.

One important thing that this tool does not do is build the target virtual environment and install all of the dependencies. You must first generate that with a tool like [Poetry](https://github.com/python-poetry/poetry) and the [poetry-plugin-bundle](https://github.com/python-poetry/poetry-plugin-bundle).

## Example command sequence
```shell
poetry bundle venv .build/.venv --without dev
package-python-function .build/.venv --output-dir .build/lambda
```

The output will be a .zip file with the same name as your project from your `pyproject.toml` file (with dashes replaced
with underscores).

## Installation
Use [pipx](https://github.com/pypa/pipx) to install:

```shell
pipx install package-python-function
```

## Usage / Arguments
```shell
package-python-function venv_dir [--project PROJECT] [--output-dir OUTPUT_DIR] [--output OUTPUT]
```

- `venv_dir` [Required]: The path to the virtual environment to package.
- `--project` [Optional]: Path to the `pyproject.toml` file. Omit to use the `pyproject.toml` file in the current working directory.

One of the following must be specified:
- `--output`: The full output path of the final zip file.
- `--output-dir`: The output directory for the final zip file. The name of the zip file will be based on the project's
name in the `pyproject.toml` file (with dashes replaced with underscores).

## Notes on Reproducibility

### Timestamps

The ZIP files generated adhere with [reproducible builds](https://reproducible-builds.org/docs/archives/). This means that file permissions and timestamps are modified inside the ZIP, such that the ZIP will have a deterministic hash. By default, the date is set to `1980-01-01`.

Additionally, the tool respects the standardized `$SOURCE_DATE_EPOCH` [environment variable](https://reproducible-builds.org/docs/source-date-epoch/), which will allow you to set that date as needed.

One important caveat is that ZIP files do not support files with timestamps earlier than `1980-01-01` inside them, due to MS-DOS compatibility. Therefore, the tool will throw a `SourceDateEpochError` is `$SOURCE_DATE_EPOCH` is below `315532800`.

### Files with embedded full paths

In testing, we found that several file types can leak information from the machine that generated the virtual environment.

To get around this, the tool removes the following files:

```gitignore
**/__pycache/
**/*.dist-info/direct_url.json
**/*.dist-info/RECORD
**/*.pyc
**/*.pyo
```
