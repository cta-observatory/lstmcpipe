import pytest
import tempfile
from ruamel.yaml import YAML

from lstmcpipe.config import paths_config
from lstmcpipe.config import pipeline_config

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
    pcfg.stages = ['r0_to_dl1']
    pcfg.paths = {'a': 'rick'}
    with tempfile.NamedTemporaryFile() as f:
        pcfg.save_yml(f.name, overwrite=True)
        read_cfg = YAML().load(open(f.name).read())
    assert read_cfg['prod_type'] == 'PathConfig'
    assert read_cfg['prod_id'] == 'v00'


def test_PathConfigProd5Trans80():
    from lstmcpipe.config.paths_config import PathConfigProd5Trans80

    prod_id = '20210416_v0.7.3_prod5_trans_80_local_taicut_8_4'
    cfg = PathConfigProd5Trans80(prod_id)
    cfg.generate()
    assert cfg.prod_id == prod_id

    assert "/20200629_prod5_trans_80/" in cfg.base_dir
    assert all(stage in default_stages for stage in cfg.stages)
    assert all(particle in default_particles for particle in cfg.particles)
    assert all(offset in default_point_source_offs for offset in cfg.point_src_offsets)
    assert cfg.training_particles == ["gamma-diffuse", "proton"]
    assert cfg.testing_particles == ["gamma", "electron", "proton", "gamma-diffuse"]
    assert cfg.zenith == "zenith_20deg"
    assert (
        cfg.base_dir
        == "/fefs/aswg/data/mc/{data_level}/20200629_prod5_trans_80/{particle}/{zenith}/south_pointing/{prod_id}"
    )
    assert (
        cfg.dl1_dir("gamma")
        == f"/fefs/aswg/data/mc/DL1/20200629_prod5_trans_80/gamma/zenith_20deg/south_pointing/{prod_id}/off0.4deg"
    )
    assert (
        cfg.dl2_dir("gamma")
        == f"/fefs/aswg/data/mc/DL2/20200629_prod5_trans_80/gamma/zenith_20deg/south_pointing/{prod_id}/off0.4deg"
    )
    assert (
        cfg.dl2_output_file("gamma")
        == f"/fefs/aswg/data/mc/DL2/20200629_prod5_trans_80/gamma/zenith_20deg/south_pointing/{prod_id}/off0.4deg/"
        f"dl2_gamma_{prod_id}_test.h5"
    )
    assert (
        cfg.irf_dir("gamma")
        == f"/fefs/aswg/data/mc/IRF/20200629_prod5_trans_80/zenith_20deg/south_pointing/{prod_id}/gamma"
    )
    assert (
        cfg.merge_output_file("gamma", "train")
        == f"/fefs/aswg/data/mc/DL1/20200629_prod5_trans_80/gamma/zenith_20deg/south_pointing/{prod_id}/off0.4deg/"
        f"dl1_gamma_{prod_id}_train.h5"
    )
    assert (
        cfg.merge_output_file("gamma", "test")
        == f"/fefs/aswg/data/mc/DL1/20200629_prod5_trans_80/gamma/zenith_20deg/south_pointing/{prod_id}/off0.4deg/"
        f"dl1_gamma_{prod_id}_test.h5"
    )
    assert cfg.models_path() == f"/fefs/aswg/data/models/20200629_prod5_trans_80/zenith_20deg/south_pointing/{prod_id}"
    assert (
        cfg.r0_dir("gamma")
        == "/fefs/aswg/data/mc/DL0/20200629_prod5_trans_80/gamma/zenith_20deg/south_pointing/off0.4deg"
    )
    assert (
        cfg.sensitivity_file(offset="0.0deg")
        == f"/fefs/aswg/data/mc/IRF/20200629_prod5_trans_80/zenith_20deg/south_pointing/{prod_id}/0.0deg/"
        f"sensitivity_{prod_id}_0.0deg.fits.gz"
    )
    assert (
        cfg.train_dir("gamma")
        == f"/fefs/aswg/data/mc/DL1/20200629_prod5_trans_80/gamma/zenith_20deg/south_pointing/{prod_id}/off0.4deg/train"
    )
    assert (
        cfg.test_dir("gamma")
        == f"/fefs/aswg/data/mc/DL1/20200629_prod5_trans_80/gamma/zenith_20deg/south_pointing/{prod_id}/off0.4deg/test"
    )

    for stg in cfg.stages:
        prop = getattr(cfg, stg)
        assert isinstance(prop, list)

        for path in prop:
            assert isinstance(path, dict)

            if stg == "train_pipe":
                assert isinstance(path["input"], dict)
                assert all(item in ["gamma", "proton"] for item in path["input"])
            elif stg == "train_test_split":
                assert isinstance(path["output"], dict)
                assert all(item in ["train", "test"] for item in path["output"])
            elif stg == 'dl1_to_dl2':
                assert 'path_model' in path
            elif stg == "dl2_to_sensitivity":
                assert isinstance(path["input"], dict)
                assert all(item in ["gamma_file", "proton_file", "electron_file"] for item in path["input"])
            elif stg == "dl2_to_irfs":
                assert "options" in path
                assert isinstance(path["input"], dict)
                assert all(item in ["gamma_file", "proton_file", "electron_file"] for item in path["input"])

        with tempfile.NamedTemporaryFile() as f:
            cfg.save_yml(f.name, overwrite=True)
            pipeline_config.load_config(f.name)
