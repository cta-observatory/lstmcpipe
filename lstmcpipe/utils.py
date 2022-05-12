from pathlib import Path
import subprocess


def rerun_cmd(cmd, outfile, max_ntry=2, subdir_failures='failed_outputs', **run_kwargs):
    """
    rerun r0_to_dl1 process given by `cmd` as long as the exit code is 0 and number of try < max_ntry
    move the failed output file to subdir failed_outputs

    Parameters
    ----------
    cmd: str
    simtel_file: Path
    subdir_failures: str
    outfile: Path
        path to the cmd output file
    max_ntry: int
    run_kwargs: kwargs for subprocess.run
    """
    outfile = Path(outfile)
    ret = -1
    ntry = 1
    while ret != 0 and ntry <= max_ntry:
        ret = subprocess.run(cmd, **run_kwargs)
        if ret.returncode != 0:
            failed_jobs_subdir = Path(outfile.parent).joinpath(subdir_failures)
            if outfile.exists():
                failed_jobs_subdir.mkdir(exist_ok=True)
                outfile_target = failed_jobs_subdir.joinpath(outfile.name)
                print(f"Move failed output file from {outfile} to {outfile_target}. try #{ntry}")
                outfile.rename(outfile_target)
        ntry += 1
