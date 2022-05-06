#!/usr/bin/env python

import os
import shutil
import logging
from pathlib import Path
from lstmcpipe.workflow_management import save_log_to_file

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
            slurm_options=paths.get("slurm_options", None),
        )

        log_splitting.update(job_logs)
        jobids_for_merging.append(jobid)
        debug_log[jobid] = (
            f"Train test splitting jobid that depends on : {jobids_from_r0dl1}"
        )

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
        slurm_options=None,
):
    """

    Parameters
    ----------
    input_dir: str
    output_dirs: dict
    batch_configuration: dict
    wait_jobid_r0_dl1: str
    slurm_options: str
        Extra slurm options to be passed to the sbatch command

    Returns
    -------

    """
    source_env = batch_configuration["source_environment"]
    slurm_account = batch_configuration["slurm_account"]

    log_splitting = {}

    input_dir = Path(input_dir).resolve()

    log.info("Splitting files within the {} dir".format(input_dir.as_posix()))

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

    cmd = f"{source_env} lstmcpipe_train_test_split -i {input_dir} --otest {test_dir}" \
          f" --otrain {train_dir} -r {ratio} -l {test_dir.parent}"

    # TODO check these dirs
    jobe = Path(input_dir).joinpath(input_dir, "split_tt_%j.e")
    jobo = Path(input_dir).joinpath(input_dir, "split_tt_%j.o")

    batch_cmd = "sbatch --parsable"
    if slurm_options is not None:
        batch_cmd += f" {slurm_options}"
    else:
        batch_cmd += " -p short"
    if slurm_account != "":
        batch_cmd += f" -A {slurm_account}"
    if wait_jobid_r0_dl1 is not None:
        batch_cmd += f" --dependency=afterok:{wait_jobid_r0_dl1}"
    batch_cmd += f' -J splitting_train_test -e {jobe} -o {jobo} --wrap="{cmd}"'

    jobid_split = os.popen(batch_cmd).read().strip("\n")
    log_splitting.update({jobid_split: batch_cmd})

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
