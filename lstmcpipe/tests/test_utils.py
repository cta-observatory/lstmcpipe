from lstmcpipe.utils import rerun_cmd
import tempfile
from pathlib import Path
import subprocess
import sys

def test_rerun_cmd():
    def faulty_func(outfile):
        sys.exit(-1)


    with tempfile.TemporaryDirectory() as tmp_dir:
        file, filename = tempfile.mkstemp()
        cmd = f'echo "1" >> {filename}; rm nonexistingfile'
        # first test: the cmd fails 3 times but the outfile stays in place
        subdir_failures = ''
        rerun_cmd(cmd, filename, max_ntry=3, subdir_failures=subdir_failures)
        filename = Path(filename)
        filename = filename.parent.joinpath(subdir_failures).joinpath(filename.name)
        assert open(filename).read() == "1\n1\n1\n"
        # 2nd test: the cmd fails and the outfile is move in subdir
        subdir_failures = 'fail'
        rerun_cmd(cmd, filename, max_ntry=3, subdir_failures=subdir_failures)
        filename = filename.parent.joinpath(subdir_failures).joinpath(filename.name)
        assert open(filename).read() == "1\n"
        assert filename.exists()
