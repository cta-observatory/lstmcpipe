from lstmcpipe import config


def test_base_config():
    cfg = config.base_config()
    assert "source_environment" in cfg