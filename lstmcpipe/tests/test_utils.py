import json
import pytest
import tempfile
from pathlib import Path
from ruamel.yaml import YAML
from lstmcpipe.utils import rerun_cmd, dump_lstchain_std_config, SbatchLstMCStage, run_command


@pytest.fixture(scope="session")
def mc_gamma_testfile():
    """Get a simulated test file."""
    return "test_data/mc/simtel_theta_20_az_180_gdiffuse_10evts.simtel.gz"


def test_save_log_to_file(tmp_path):
    from ..utils import save_log_to_file

    outfile_yml = Path(tmp_path, 'dummy_log.yml')

    dummy_log = {'dummy_jobid': 'sbatch --parsable --wrap="sleep 10"'}
    save_log_to_file(dummy_log, outfile_yml)

    assert outfile_yml.exists()
    with open(outfile_yml) as f:
        log = YAML().load(f)

    assert "NoKEY" in log.keys()
    assert isinstance(log["NoKEY"], dict)
    assert "dummy_jobid" in log["NoKEY"].keys()
    assert dummy_log["dummy_jobid"] == log["NoKEY"]["dummy_jobid"]


def test_rerun_cmd():
    with tempfile.TemporaryDirectory() as tmp_dir:
        file, filename = tempfile.mkstemp(dir=tmp_dir)
        cmd = f'echo "1" >> {filename}; rm nonexistingfile'

        # first test: the cmd fails 3 times but the outfile stays in place
        subdir_failures = ""
        try:
            n_tries = rerun_cmd(cmd, filename, max_ntry=3, subdir_failures=subdir_failures, shell=True)
            filename = Path(filename)
            filename = Path(tmp_dir).joinpath(subdir_failures, filename.name)
            assert open(filename).read() == "1\n1\n1\n"
            assert n_tries == 3
        except Exception as e:
            assert isinstance(e, RuntimeError)

        # 2nd test: the cmd fails and the outfile is moved in subdir
        subdir_failures = "fail"
        try:
            rerun_cmd(cmd, filename, max_ntry=3, subdir_failures=subdir_failures, shell=True)
            filename = filename.parent.joinpath(subdir_failures).joinpath(filename.name)
            assert open(filename).read() == "1\n"
            assert filename.exists()
        except Exception as e:
            assert isinstance(e, RuntimeError)


def test_rerun_cmd_lstchain_mc_r0_to_dl1(mc_gamma_testfile):
    with tempfile.TemporaryDirectory() as tmp_dir:
        cmd = ['lstchain_mc_r0_to_dl1', '-o', tmp_dir, '-f', mc_gamma_testfile]
        outfilename = 'dl1_' + Path(mc_gamma_testfile).name.replace('.simtel.gz', '.h5')
        outfile = Path(tmp_dir, outfilename)
        # first try should succeed
        ntry = rerun_cmd(cmd, outfile, max_ntry=3)
        assert ntry == 1
        # second try should fail because the outfile already exists
        ntry = rerun_cmd(cmd, outfile, max_ntry=3, subdir_failures='failed_outputs')
        assert ntry == 2
        assert Path(tmp_dir, 'failed_outputs', outfilename).exists()


def test_run_command():
    cmd = run_command("echo 'this is the command to be passed'")
    assert cmd == "this is the command to be passed"


@pytest.mark.xfail(raises=ValueError)
def test_fail_run_command():
    run_command("echoo 'this command will fail'")


def test_sbatch_lst_mc_stage():
    with pytest.raises(TypeError):
        SbatchLstMCStage()
        SbatchLstMCStage("merge")

    sbatch = SbatchLstMCStage(stage="r0_to_dl1", wrap_command="command to be batched")
    assert (
        sbatch.slurm_command == 'sbatch --parsable --partition=long --job-name=r0_dl1 --array=0-0%100 '
        '--error=./slurm-%j.e --output=./slurm-%j.o  --wrap="command to be batched' + ' || exit ' + r'\$?"'
    )

    sbatch.extra_slurm_options = {'account': 'lstrta', 'partition': 'xxl', 'mem': '160G', 'cpus-per-task': 32}
    assert (
        sbatch.slurm_command == 'sbatch --parsable --partition=xxl --job-name=r0_dl1 --array=0-0%100 '
        '--error=./slurm-%j.e --output=./slurm-%j.o --account=lstrta --mem=160G '
        '--cpus-per-task=32  --wrap="command to be batched' + ' || exit ' + r'\$?"'
    )

    sbatch.extra_slurm_options = None
    sbatch.slurm_dependencies = "123,243,345,456"
    assert sbatch._construct_slurm_dependencies() == "--dependency=afterok:123:243:345:456"

    sbatch.compose_wrap_command(
        wrap_command="python args",
        source_env="source .bashrc_file; conda activate   ",
        backend="  export MPLBACKEND=Agg    ",
    )
    assert (
        sbatch.wrap_cmd
        == '--wrap="export MPLBACKEND=Agg; source .bashrc_file; conda activate; python args' + ' || exit ' + r'\$?"'
    )

    with pytest.raises(ValueError):
        sbatch.submit()  # slurm not installed
        sbatch.stage_default_options("dummy_stage")
        sbatch.set_slurm_dependencies(slurm_deps="123,,234")

    stages = sbatch._valid_stages
    for stage in stages:
        assert "--job-name=" in sbatch.slurm_command
        assert "--partition=" in sbatch.slurm_command


def test_dump_lstchain_std_config():
    with tempfile.TemporaryDirectory() as tmpdir:
        outfile = Path(tmpdir).joinpath('cfg.json')
        dump_lstchain_std_config(filename=outfile, allsky=False)
        assert json.load(outfile.open())['GlobalPeakWindowSum']['apply_integration_correction']
        dump_lstchain_std_config(filename=outfile, allsky=True, overwrite=True)
        assert 'alt_tel' in json.load(outfile.open())['energy_regression_features']
