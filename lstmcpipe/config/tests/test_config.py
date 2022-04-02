from lstmcpipe import config


def test_base_config():
    cfg = config.base_config()
    assert all(key in cfg for key in ["source_environment", "workflow_kind", "prod_id", "slurm_config"])
