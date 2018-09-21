import os
import subprocess

import nbformat
import pytest


_TEST_DIR = os.path.abspath(os.path.dirname(__file__))
_EXCLUDE = ["Python_intro.ipynb", "animate-landlab-output.ipynb"]


def all_notebooks():
    notebooks = []
    for root, dirs, files in os.walk(_TEST_DIR):
        for file in files:
            if (
                file.endswith(".ipynb")
                and (file not in _EXCLUDE)
                and ("checkpoint" not in file)
            ):
                notebooks.append(os.path.join(root, file))
    return notebooks


def pytest_generate_tests(metafunc):
    if "notebook" in metafunc.fixturenames:
        metafunc.parametrize("notebook", all_notebooks())


def _notebook_run(path):
    """Execute a notebook via nbconvert and collect output.
       :returns (parsed nb object, execution errors)
    """
    dirname, __ = os.path.split(path)
    os.chdir(dirname)

    in_fn = os.path.split(path)[-1].split(".")[0]
    temp_file_prefix = "output_" + in_fn
    temp_file_out = temp_file_prefix + ".ipynb"

    args = [
        "jupyter",
        "nbconvert",
        "--to",
        "notebook",
        "--execute",
        "--ExecutePreprocessor.kernel_name=python",
        "--ExecutePreprocessor.timeout=None",
        "--output",
        temp_file_prefix,
        path,
    ]
    subprocess.check_call(args)

    nb = nbformat.read(temp_file_out, nbformat.current_nbformat, encoding="UTF-8")

    errors = [
        output
        for cell in nb.cells
        if "outputs" in cell
        for output in cell["outputs"]
        if output.output_type == "error"
    ]
    os.remove(temp_file_out)

    return nb, errors


def test_notebook(tmpdir, notebook):
    with tmpdir.as_cwd():
        nb, errors = _notebook_run(notebook)
        assert not errors
