from lstmcpipe.config import export_env, load_config
import tempfile
import os
import yaml

def test_export_env():
    tmp_dir = tempfile.mkdtemp()
    export_env(tmp_dir)
    if not os.path.exists(os.path.join(tmp_dir, 'requirements.txt')):
        assert os.path.exists(os.path.join(tmp_dir, 'conda_env.yml'))


def test_parse_config_and_handle_global_vars():
    config_path = "lstmcpipe/config_MC_prod.yml"
    config = load_config(config_path)
    with open("lstmcpipe/config/tests/expected.yaml") as e:
        expected = yaml.safe_load(e)
    for k in config:
        print(k)
        assert config[k] == expected[k]