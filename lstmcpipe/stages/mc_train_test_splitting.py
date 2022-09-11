#!/usr/bin/env python

import shutil
import logging
from pathlib import Path
from ..utils import save_log_to_file, SbatchLstMCStage

log = logging.getLogger(__name__)


def batch_train_test_splitting(
    dict_paths,
    jobids_from_r0dl1,
    batch_config,
    logs,
):
    """

    Parameters
    ----------
    dict_paths: dict
    jobids_from_r0dl1: str
    batch_config: dict
        Dictionary containing the (full) source_environment and the slurm_account strings to be passed
        to `merge_dl1` and `compose_batch_command_of_script` functions.
    logs: dict
        Dictionary with logs files

    Returns
    -------

    """
    log_splitting = {}
    debug_log = {}
    jobids_for_merging = []

    log.info("==== START {} ====".format("batch train_test_splitting"))

    for paths in dict_paths:
        job_logs, jobid = train_test_split(
            paths["input"],
            paths["output"],
            wait_jobid_r0_dl1=jobids_from_r0dl1,
            batch_configuration=batch_config,
            extra_slurm_options=paths.get("extra_slurm_options", None),
        )

        log_splitting.update(job_logs)
        jobids_for_merging.append(jobid)
        debug_log[jobid] = f"Train test splitting jobid that depends on : {jobids_from_r0dl1}"

    jobids_for_merging = ",".join(jobids_for_merging)

    save_log_to_file(log_splitting, logs["log_file"], workflow_step="dl1_to_dl2")
    save_log_to_file(debug_log, logs["debug_file"], workflow_step="dl1_to_dl2")

    log.info("==== END {} ====".format("batch train_test_splitting"))

    return jobids_for_merging


def train_test_split(
    input_dir,
    output_dirs,
    batch_configuration,
    wait_jobid_r0_dl1=None,
    extra_slurm_options=None,
):
    """

    Parameters
    ----------
    input_dir: str
    output_dirs: dict
    batch_configuration: dict
    wait_jobid_r0_dl1: str
    extra_slurm_options: dict
        Extra slurm options to be passed to the sbatch command

    Returns
    -------

    """
    log_splitting = {}

    input_dir = Path(input_dir).resolve()

    log.info("\nSplitting files within the {} dir".format(input_dir.as_posix()))

    # create train, test output directories
    test_dir = Path(output_dirs["test"]).resolve()
    train_dir = Path(output_dirs["train"]).resolve()
    for direct in [test_dir, train_dir]:
        if direct.exists() and any(direct.iterdir()):
            shutil.rmtree(direct)
    train_dir.mkdir(exist_ok=True, parents=True)
    test_dir.mkdir(exist_ok=True, parents=True)

    # tt ratio
    if "ratio" not in output_dirs:
        ratio = 0.5
    else:
        ratio = output_dirs["ratio"]

    cmd = (
        f"lstmcpipe_train_test_split -i {input_dir} --otest {test_dir}"
        f" --otrain {train_dir} -r {ratio} -l {test_dir.parent}"
    )

    sbatch_tt_splitting = SbatchLstMCStage(
        "train_test_splitting",
        wrap_command=cmd,
        slurm_error=Path(input_dir).joinpath(input_dir, "split_tt_%j.e"),
        slurm_output=Path(input_dir).joinpath(input_dir, "split_tt_%j.o"),
        slurm_dependencies=wait_jobid_r0_dl1,
        extra_slurm_options=extra_slurm_options,
        slurm_account=batch_configuration["slurm_account"],
        source_environment=batch_configuration["source_environment"],
    )

    jobid_split = sbatch_tt_splitting.submit()
    log_splitting.update({jobid_split: sbatch_tt_splitting.slurm_command})

    log.info(f"\nSplitting files from {input_dir} dir into testing {test_dir} dir and training {train_dir} dir.")
    log.info(f"Submitted batch job {jobid_split}")

    return log_splitting, jobid_split


def check_empty_dir(directory):
    """
    Check if a directory is empty. If not, erase all its content.

    Parameters
    ----------
    directory : Path
        Path to dir to check
    """
    if any(directory.iterdir()):
        for item in directory.iterdir():
            item.unlink()
    else:
        pass
