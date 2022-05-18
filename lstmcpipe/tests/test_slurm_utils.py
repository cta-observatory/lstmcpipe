import pytest
from ..slurm_utils import SbatchLstMCStage, run_command


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
        sbatch.slurm_command == 'sbatch --parsable --job-name=r0_dl1 --partition=long --array=0-0%100  '
        '--error=./slurm-%j.e --output=./slurm-%j.o   --wrap="command to be batched"'
    )

    sbatch.slurm_options = "-A lstrta -p xxl --mem 160G --cpus-per-task=32"
    assert (
        sbatch.slurm_command == 'sbatch --parsable --job-name=r0_dl1 -A lstrta -p xxl --mem 160G --cpus-per-task=32 '
        '--error=./slurm-%j.e --output=./slurm-%j.o   --wrap="command to be batched"'
    )

    sbatch.slurm_options = None
    sbatch.check_slurm_dependencies("123,243,345,456")
    assert sbatch.slurm_dependencies == "--dependency=afterok:123,243,345,456"

    sbatch.compose_wrap_command(
        wrap_command="python args",
        source_env="source .bashrc_file; conda activate   ",
        backend="  export MPLBACKEND=Agg    ",
    )
    assert sbatch.wrap_cmd == '--wrap="export MPLBACKEND=Agg; source .bashrc_file; conda activate; python args"'

    with pytest.raises(ValueError):
        sbatch.submit()  # slurm not installed
        sbatch.stage_default_options("invented_stage")
        sbatch.check_slurm_dependencies(slurm_deps="123,,234")

    stages = sbatch._valid_stages
    for stage in stages:
        sbatch.stage_default_options(stage)
        assert "--job-name=" in sbatch.job_name
        assert "--partition=" in sbatch.slurm_command
