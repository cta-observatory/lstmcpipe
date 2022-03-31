#!/usr/bin/env python

import yaml
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
        log = yaml.safe_load(f)

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


def test_create_dl1_filenames_dict(create_fake_dl1_structure):
    from ..workflow_management import create_dl1_filenames_dict

    dl1_dirs_gammas = create_dl1_filenames_dict(create_fake_dl1_structure, ['gamma'], ["off0.0deg", "off0.4deg"])

    assert isinstance(dl1_dirs_gammas, dict)
    print(dl1_dirs_gammas)
    assert all(particle in dl1_dirs_gammas for particle in ["gamma_off0.0deg", "gamma_off0.4deg"])

    for key, value in dl1_dirs_gammas.items():
        assert all(sub_key in dl1_dirs_gammas[key] for sub_key in ["training", "testing"])
        for ik in dl1_dirs_gammas[key]:
            if ik == "training":
                assert dl1_dirs_gammas[key][ik]["train_path_and_outname_dl1"].endswith("training.h5")
            else:
                assert dl1_dirs_gammas[key][ik]["test_path_and_outname_dl1"].endswith("testing.h5")

    # Rest of particles
    dl1_dirs_rest = create_dl1_filenames_dict(create_fake_dl1_structure,
                                              ["electron", "gamma-diffuse", "proton"])
    assert isinstance(dl1_dirs_rest, dict)
    assert all(particle in dl1_dirs_rest for particle in ["gamma-diffuse", "proton", "electron"])
    for key, value in dl1_dirs_rest.items():
        assert all(sub_key in dl1_dirs_rest[key] for sub_key in ["training", "testing"])
        for ik in dl1_dirs_rest[key]:
            if ik == "training":
                assert dl1_dirs_rest[key][ik]["train_path_and_outname_dl1"].endswith("training.h5")
            else:
                assert dl1_dirs_rest[key][ik]["test_path_and_outname_dl1"].endswith("testing.h5")
