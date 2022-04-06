#!/usr/bin/env python

from ruamel.yaml import YAML
import pytest
from pathlib import Path


def test_save_log_to_file():
    from ..workflow_management import save_log_to_file
    outfile_yml = Path('dummy_log.yml')

    dummy_log = {
        'dummy_jobid': 'sbatch --parsable --wrap="sleep 10"'
    }
    save_log_to_file(dummy_log, outfile_yml)

    assert outfile_yml.exists()
    with open(outfile_yml) as f:
        log = YAML().load(f)

    assert "NoKEY" in log.keys()
    assert isinstance(log["NoKEY"], dict)
    assert "dummy_jobid" in log["NoKEY"].keys()
    assert dummy_log["dummy_jobid"] == log["NoKEY"]["dummy_jobid"]


@pytest.fixture()
def create_fake_dl1_structure(tmp_path):
    fake_dl1_dir = tmp_path.joinpath("DL1", "{}")

    gamma_off = ["off0.0deg", "off0.4deg"]
    dataset = ["training", "testing"]

    for particle in ["electron", "gamma-diffuse", "proton", "gamma"]:
        if particle == "gamma":
            for off in gamma_off:
                _particle = particle + "_" + off
                _subdir = Path(str(fake_dl1_dir).format(particle), off)
                _subdir.mkdir(parents=True)
                for i_set in dataset:
                    with open(_subdir.joinpath(f"dl1_{_particle}_dummy_{i_set}.h5"), "w"):
                        pass
        else:
            _subdir = Path(str(fake_dl1_dir).format(particle))
            _subdir.mkdir(parents=True)
            for i_set in dataset:
                with open(_subdir.joinpath(f"dl1_{particle}_dummy_{i_set}.h5"), "w"):
                    pass

    return fake_dl1_dir.as_posix()
