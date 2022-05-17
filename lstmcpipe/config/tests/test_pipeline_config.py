from lstmcpipe.config import export_env
from lstmcpipe.config.pipeline_config import (
    config_valid,
    complete_lstmcpipe_config,
)
import tempfile
import os
import pytest

# from datetime import datetime

yaml_keys = ["prod_id", "stages_to_run", "prod_type", "workflow_kind", "stages"]
dummy_config = {k: None for k in yaml_keys}
dummy_config["merging_options"] = {"no_image": False}
dummy_config["source_environment"] = {"source_file": "src_file", "conda_env": "env"}


def test_export_env():
    tmp_dir = tempfile.mkdtemp()
    export_env(tmp_dir)
    if not os.path.exists(os.path.join(tmp_dir, "requirements.txt")):
        assert os.path.exists(os.path.join(tmp_dir, "conda_env.yml"))


def test_config_valid():
    """
    Test invalid values for all relevant fields individually.
    This tests values, that are supposed to fail.
    This does not test if no valid configuration is marked
    as invalid!
    """
    with pytest.raises(Exception):
        config_valid(dummy_config)

    valid = dummy_config.copy()
    valid["prod_type"] = "PathConfigProd5Trans80"
    valid["workflow_kind"] = "lstchain"
    valid["stages_to_run"] = ["r0_to_dl1"]
    valid["stages"] = {"r0_to_dl1": [{"input": None, "output": None}]}
    assert config_valid(valid)

    invalid_workflow = valid.copy()
    invalid_workflow["workflow_kind"] = "MARS"
    with pytest.raises(Exception):
        config_valid(invalid_workflow)

    missing_reference = valid.copy()
    missing_reference["stages_to_run"] = ["dl1ab"]
    # dl1ab stage is not described
    with pytest.raises(KeyError):
        config_valid(missing_reference)

    missing_reference["stages"] = {"dl1ab": []}

    missing_reference["dl1_noise_tune_data_run"] = "file"
    with pytest.raises(KeyError):
        config_valid(missing_reference)
    missing_reference["dl1_noise_tune_mc_run"] = "file"
    config_valid(missing_reference)


def test_complete_lstmcpipe_config():
    """
    Test that the file paths are properly set.
    This only tests a subset of the variables, that are set in
    the function.
    """
    config = dummy_config.copy()
    config["workflow_kind"] = "lstchain"
    config["prod_type"] = "PathConfigProd5Trans80"
    config["stages_to_run"] = ["r0_to_dl1"]

    parsed_config = complete_lstmcpipe_config(config)
    # date = datetime.today().strftime("%Y%m%d")
    # TODO test check some paths
    # TODO test check model path
    assert parsed_config["batch_config"]["source_environment"] == "source src_file; conda activate env; "
    assert parsed_config["batch_config"]["slurm_account"] == ""
    assert parsed_config["stages_to_run"] == ["r0_to_dl1"]
    assert parsed_config["workflow_kind"] == "lstchain"

    new_dummy = config.copy()
    new_dummy["slurm_config"] = {"user_account": "aswg"}
    new_parsed_config = complete_lstmcpipe_config(new_dummy)
    assert new_parsed_config["batch_config"]["slurm_account"] == "aswg"
