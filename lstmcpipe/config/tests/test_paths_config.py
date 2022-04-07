import pytest
import tempfile

from lstmcpipe.config import paths_config

default_stages = [
    "r0_to_dl1",
    "train_test_split",
    "merge_dl1",
    "train_pipe",
    "dl1_to_dl2",
    "dl2_to_sensitivity",
    "dl2_to_irfs",
]

default_particles = [
    "gamma-diffuse",
    "proton",
    "gamma",
    "electron",
    "proton",
]

default_point_source_offs = [
    "off0.0deg",
    "off0.4deg",
]


@pytest.mark.xfail(raises=NotImplementedError)
def test_path_config_generate_fail():
    pcfg = paths_config.PathConfig('v00')
    pcfg.generate()


def test_path_config_generate():
    class NewPathConfig(paths_config.PathConfig):
        def __init__(self, prod_id):
            super().__init__(prod_id)
            self.stages = ['stage1']
        @property
        def stage1(self):
            return {'input': 'input_path', 'output': None}
    pcfg = NewPathConfig('v00')
    pcfg.generate() == {'stage1': {'input': 'input_path', 'output': None}}


def test_path_config_save():
    pcfg = paths_config.PathConfig('v00')
    pcfg.paths = {'a': 'rick'}
    with tempfile.NamedTemporaryFile() as f:
        pcfg.save_yml(f.name, overwrite=True)


def test_PathConfigProd5Trans80():
    # testing with an existing prod
    prod_id = '20210416_v0.7.3_prod5_trans_80_local_taicut_8_4/'
    pcfg = paths_config.PathConfigProd5Trans80(prod_id)
    paths = pcfg.generate()
    dl2p = '/fefs/aswg/data/mc/DL2/20200629_prod5_trans_80/proton/zenith_20deg/south_pointing/20210416_v0.7.3_prod5_trans_80_local_taicut_8_4/'
    assert dl2p in [dl1todl2['output'] for dl1todl2 in paths['dl1_to_dl2']]
    assert pcfg.prod_id == prod_id


def test_PathConfigProd5Trans80_default():
    from lstmcpipe.config.paths_config import PathConfigProd5Trans80
    prod_id = 'dummy_prodid'
    cfg = PathConfigProd5Trans80(prod_id)

    assert "/20200629_prod5_trans_80/" in cfg.base_dir
    # TODO assert all stages in default_stages are in cfg
    # TODO assert all particles in default_particles are in cfg
    # TODO assert all offs in default_point_like_off are in cfg

    for stg in cfg.stages:
        assert isinstance(stg, list)
        for item in stg:
            assert isinstance(item, dict)

    # TODO assert default paths (including {}} for classes


