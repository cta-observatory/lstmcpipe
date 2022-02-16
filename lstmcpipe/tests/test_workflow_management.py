#!/usr/bin/env python

import yaml
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


def test_create_log_files():
    from ..workflow_management import create_log_files
    logs, scancel_file = create_log_files('dummy_prodID')

    assert "log_file" in logs.keys()
    assert "debug_file" in logs.keys()

    assert isinstance(logs["log_file"], Path)
    assert isinstance(logs["debug_file"], Path)
    assert isinstance(scancel_file, Path)

    assert scancel_file.exists()


def test_update_scancel_file():
    from ..workflow_management import create_log_files, update_scancel_file
    _, scancel_file = create_log_files("dummy_prodID")

    update_scancel_file(scancel_file, "1234")
    with open(scancel_file) as f:
        lines = f.readlines()
    assert lines == ["scancel 1234"]

    update_scancel_file(scancel_file, "5678")
    with open(scancel_file) as f:
        lines = f.readlines()
    assert lines == ["scancel 1234,5678"]
