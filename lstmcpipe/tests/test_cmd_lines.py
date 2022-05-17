import subprocess
import tempfile
from lstmcpipe.config.pipeline_config import load_config


def test_generate_config():
    prod_type = 'PathConfigProd5Trans80'
    with tempfile.NamedTemporaryFile() as file:
        cmd = ['lstmcpipe_generate_config', prod_type, '-o', file.name]
    subprocess.run(cmd)
    cfg = load_config(file.name)
    assert cfg['prod_type'] == prod_type
