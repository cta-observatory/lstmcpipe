import os
import pytest
import tempfile
from pathlib import Path
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


# --- AllSky configs: fake MC trees to test the source prod checkers off-cluster ---

# (theta, az) of the fake pointing nodes, as they appear in the directory names
fake_pointings = [("10.000", "102.199"), ("23.630", "100.758"), ("32.059", "102.217")]
# node directory names are not consistent particle-wise, see PathConfigAllSkyTraining.load_pointings
node_prefixes = {"GammaDiffuse": "node_corsika_theta", "Protons": "node_theta"}


def make_fake_dl0_training(root, dec):
    """
    Create a fake DL0 training tree containing simtel files, as parsed by `_search_pointings`.

    Returns
    -------
    dict: {particle: [node directory names]}
    """
    node_dirs = {}
    for particle, prefix in node_prefixes.items():
        node_dirs[particle] = []
        for theta, az in fake_pointings:
            node = f"{prefix}_{theta}_az_{az}_"
            simtel_dir = Path(root, "DL0/LSTProd2/TrainingDataset", particle, dec, "sim_telarray", node, "output_v1.4")
            simtel_dir.mkdir(parents=True)
            (simtel_dir / "run1.simtel.gz").touch()
            node_dirs[particle].append(node)
    return node_dirs


def redirect_to_fake_tree(cfg, root, dec):
    """Point a PathConfigAllSkyTraining-like config to a fake tree instead of /fefs/aswg/data/mc"""
    cfg.training_dir = os.path.join(
        str(root), "DL0/LSTProd2/TrainingDataset/{particle}", dec, "sim_telarray/{pointing}/output_v1.4/"
    )
    cfg.base_dir = os.path.join(str(root), "{data_level}/AllSky/{prod_id}/{dataset_type}/{particle}/{dec}/{pointing}/")


def make_fake_source_dl1(root, source_prod_id, dec, node_dirs, missing=()):
    """Create the DL1 directories of the source production, except the nodes listed in `missing`"""
    for particle, nodes in node_dirs.items():
        for node in nodes:
            if node in missing:
                continue
            Path(root, "DL1/AllSky", source_prod_id, "TrainingDataset", particle, dec, node).mkdir(parents=True)


def make_training_dl1ab_config(tmp_path, dec="dec_2276", prod_id="new_prod", source_prod_id="source_prod"):
    """Build a PathConfigAllSkyTrainingDL1ab redirected to a fake tree, without running the checker yet"""
    node_dirs = make_fake_dl0_training(tmp_path, dec)
    cfg = paths_config.PathConfigAllSkyTrainingDL1ab(prod_id, source_prod_id, dec, run_checker=False)
    redirect_to_fake_tree(cfg, tmp_path, dec)
    redirect_to_fake_tree(cfg.source_config, tmp_path, dec)
    return cfg, node_dirs


def test_allsky_training_dl1ab_checker_keeps_complete_prod(tmp_path):
    """All the nodes exist in the source prod: none of them must be removed"""
    cfg, node_dirs = make_training_dl1ab_config(tmp_path)
    make_fake_source_dl1(tmp_path, cfg.source_prod_id, cfg.dec, node_dirs)

    assert len(cfg.pointings) == len(fake_pointings)
    cfg.check_source_prod()
    assert len(cfg.pointings) == len(fake_pointings)
    assert len(cfg.dl1ab) == len(node_prefixes) * len(fake_pointings)


def test_allsky_training_dl1ab_checker_removes_missing_nodes(tmp_path):
    """The node missing from the source prod must be removed, and only that one"""
    cfg, node_dirs = make_training_dl1ab_config(tmp_path)

    # the pointings table is sorted by (alt, az) by the join, so pick the node to drop from the table itself
    dropped = {particle: cfg.pointings[f"dirname_{particle}"][0] for particle in node_prefixes}
    kept = {particle: list(cfg.pointings[f"dirname_{particle}"][1:]) for particle in node_prefixes}
    make_fake_source_dl1(tmp_path, cfg.source_prod_id, cfg.dec, node_dirs, missing=list(dropped.values()))

    with pytest.warns(UserWarning):
        cfg.check_source_prod()

    assert len(cfg.pointings) == len(fake_pointings) - 1
    for particle in node_prefixes:
        assert list(cfg.pointings[f"dirname_{particle}"]) == kept[particle]
        assert dropped[particle] not in cfg.pointings[f"dirname_{particle}"]


def test_all_train_test_dl1b_run_checker_is_forwarded():
    """`run_checker=False` must reach the sub-configs, so that no path is looked up on disk"""
    cfg = paths_config.PathConfigAllTrainTestDL1b("new_prod", "source_prod", ["dec_2276"], run_checker=False)
    assert cfg.dec_list == ["dec_2276"]
    assert cfg.stages == ["train_pipe", "dl1_to_dl2"]


def test_all_train_test_dl1b_checker_keeps_dec_order(tmp_path):
    """Declinations without a merged DL1 in the source prod are dropped, the others keep their order"""
    dec_list = ["dec_2276", "dec_931", "dec_3476", "dec_min_413"]
    cfg = paths_config.PathConfigAllTrainTestDL1b("new_prod", "source_prod", dec_list, run_checker=False)

    class FakeTrainConfig:
        def __init__(self, merged_dl1):
            self.merge_dl1 = [{"output": str(merged_dl1)}]

    existing_dl1 = tmp_path / "dl1_merged.h5"
    existing_dl1.touch()
    missing_dl1 = tmp_path / "does_not_exist.h5"
    cfg.source_configs.train_configs = {
        dec: FakeTrainConfig(missing_dl1 if dec == "dec_3476" else existing_dl1) for dec in dec_list
    }

    with pytest.warns(UserWarning):
        cfg.check_source_prod()

    assert cfg.dec_list == ["dec_2276", "dec_931", "dec_min_413"]


def test_allsky_testing_irf_output_file():
    prod_id = "test_prod"
    dec = "dec_2276"
    node = "node_theta_10.000_az_102.199_"
    cfg = paths_config.PathConfigAllSkyTesting(prod_id, dec)

    irf_file = cfg.irf_output_file(node)
    assert os.path.dirname(irf_file) == cfg.irf_dir(node)
    assert os.path.basename(irf_file) == f"irf_{prod_id}_Gamma_{dec}_{node}.fits.gz"
