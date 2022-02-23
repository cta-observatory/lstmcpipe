import pytest
from pathlib import Path
from  lstmcpipe.config import load_config

PROD_CONFIGS_DIR = Path(__file__).parent.joinpath('../../production_configs/')


def test_all_lstmcpipe_configs():
    for lstmcpipe_conf_file in PROD_CONFIGS_DIR.glob('*/*.yml'):
        load_config(lstmcpipe_conf_file)


@pytest.importorskip("lstchain", reason="lstchain not installed")
def test_all_lstchain_configs():
    from lstchain.io.config import read_configuration_file
    for lstchain_conf_file in PROD_CONFIGS_DIR.glob('*/*.json'):
        read_configuration_file(lstchain_conf_file)
