from pathlib import Path
from  lstmcpipe.config import load_config
from lstchain.io.config import read_configuration_file

PROD_CONFIGS_DIR = Path(__file__).parent.joinpath('../../production_configs/')


def test_all_lstmcpipe_configs():
    for lstmcpipe_conf_file in PROD_CONFIGS_DIR.glob('*/*.yml'):
        load_config(lstmcpipe_conf_file)


def test_all_lstchain_configs():
    for lstchain_conf_file in PROD_CONFIGS_DIR.glob('*/*.json'):
        read_configuration_file(lstchain_conf_file)
