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


def test_is_allsky_config():
    """The AllSky productions must be recognised from the class inheritance, not from the class name"""
    from lstmcpipe.config import paths_config
    from lstmcpipe.scripts.lstmcpipe_generate_config import is_allsky_config, list_config_classes

    assert not is_allsky_config(paths_config.PathConfigProd5Trans80)
    assert not is_allsky_config(paths_config.PathConfigProd5Trans80DL1ab)
    assert is_allsky_config(paths_config.PathConfigAllSkyFull)
    assert is_allsky_config(paths_config.PathConfigAllSkyFullDL1ab)
    # this one is an AllSky production although it has no `AllSky` in its name
    assert is_allsky_config(paths_config.PathConfigAllTrainTestDL1b)

    # a class named AllSky must always be detected as one
    for class_name in list_config_classes():
        if "AllSky" in class_name:
            assert is_allsky_config(getattr(paths_config, class_name))
