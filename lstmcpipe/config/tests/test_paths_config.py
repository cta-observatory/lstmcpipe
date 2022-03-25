import pytest
import tempfile

from lstmcpipe.config import paths_config


@pytest.mark.xfail(raises=NotImplementedError)
def test_path_config_generate_fail():
    pcfg = paths_config.PathConfig()
    pcfg.generate([])


def test_path_config_generate():
    class NewPathConfig(paths_config.PathConfig):
        def __init__(self):
            super().__init__()

        @property
        def stage1(self):
            return {'input': 'input_path', 'output': None}
    pcfg = NewPathConfig()
    pcfg.generate(stages=['stage1']) == {'stage1': {'input': 'input_path', 'output': None}}


def test_path_config_save():
    pcfg = paths_config.PathConfig()
    pcfg.paths = {'a': 'rick'}
    with tempfile.NamedTemporaryFile() as f:
        pcfg.save_yml(f.name, overwrite=True)

def test_PathConfigProd5Trans80():
    # testing with an existing prod
    prod_id = '20210416_v0.7.3_prod5_trans_80_local_taicut_8_4/'
    pcfg = paths_config.PathConfigProd5Trans80(prod_id)
    paths = pcfg.generate()
    dl2p='/fefs/aswg/data/mc/DL2/20200629_prod5_trans_80/proton/zenith_20deg/south_pointing/20210416_v0.7.3_prod5_trans_80_local_taicut_8_4/'
    assert dl2p in [dl1todl2['output'] for dl1todl2 in paths['dl1_to_dl2']]
