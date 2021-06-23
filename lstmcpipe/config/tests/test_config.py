from lstmcpipe.config import export_env
import tempfile
import os


def test_export_env():
    tmp_dir = tempfile.mkdtemp()
    export_env(tmp_dir)
    if not os.path.exists(os.path.join(tmp_dir, 'requirements.txt')):
        assert os.path.exists(os.path.join(tmp_dir, 'conda_env.yml'))