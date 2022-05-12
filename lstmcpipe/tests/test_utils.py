from lstmcpipe.utils import rerun_cmd
import tempfile
from pathlib import Path

def test_rerun_cmd():

    with tempfile.TemporaryDirectory() as tmp_dir:
        file, filename = tempfile.mkstemp(dir=tmp_dir)
        cmd = f'echo "1" >> {filename}; rm nonexistingfile'
        # first test: the cmd fails 3 times but the outfile stays in place
        subdir_failures = ''
        rerun_cmd(cmd, filename, max_ntry=3, subdir_failures=subdir_failures, shell=True)
        filename = Path(filename)
        filename = Path(tmp_dir).joinpath(subdir_failures, filename.name)
        assert open(filename).read() == "1\n1\n1\n"
        # 2nd test: the cmd fails and the outfile is move in subdir
        subdir_failures = 'fail'
        rerun_cmd(cmd, filename, max_ntry=3, subdir_failures=subdir_failures, shell=True)
        filename = filename.parent.joinpath(subdir_failures).joinpath(filename.name)
        assert open(filename).read() == "1\n"
        assert filename.exists()
