# Most of the tests based on
# https://github.com/cta-observatory/cta-lstchain/blob/master/lstchain/scripts/tests/test_lstchain_scripts.py

import pytest
import subprocess
from importlib.metadata import entry_points


def find_entry_points(package_name):
    """from: https://stackoverflow.com/a/47383763/3838691"""
    entrypoints = [
        ep.name
        for ep in entry_points(group="console_scripts")
        if ep.module.startswith(package_name)
    ]
    return entrypoints


ALL_SCRIPTS = find_entry_points("lstmcpipe")


def run_script(*args):
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8')

    if result.returncode != 0:
        raise ValueError(
            f"Running {args[0]} failed with return code {result.returncode}" f", output: \n {result.stdout}"
        )


@pytest.mark.parametrize("script", ALL_SCRIPTS)
def test_all_help(script):
    """Test for all scripts if at least the help works."""
    run_script(script, "--help")
