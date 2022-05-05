#!/usr/bin/env python

# DL2 to IRFs stage for the R0 to IRFs full MC production workflow.
# As all the previous stages, this script make use of the lstchain entry points to batch each workflow stage.

import os
import shutil
import logging
from pathlib import Path
from lstmcpipe.workflow_management import save_log_to_file
from lstmcpipe.io.data_management import check_and_make_dir_without_verification


log = logging.getLogger(__name__)


def batch_dl2_to_irfs(
    dict_paths,
    config_file,
    job_ids_from_dl1_dl2,
    batch_config,
    logs,
):
    """
    Batches the dl2_to_irfs stage (lstchain lstchain_create_irf_files script) once the dl1_to_dl2 stage had finished.

    Parameters
    ----------
    dict_paths : dict
        Core dictionary with {stage: PATHS} information
    config_file: str
        Path to lstchain-like config file
    job_ids_from_dl1_dl2: str
        Comma-separated string with the job ids from the dl1_to_dl2 stage to be used as a slurm dependency
        to schedule the current stage
    batch_config : dict
        Dictionary containing the (full) source_environment and the slurm_account strings to be passed to
        dl2_to_irfs function
    logs: dict
        Dictionary with logs files

    Returns
    -------
    jobs_from_dl2_irf: str
        Comma-separated jobids batched in the current stage
    """
    log.info("==== START {} ====".format("batch mc_dl2_to_irfs"))

    log_dl2_to_irfs = {}
    jobid_for_check = []
    debug_log = {}

    for paths in dict_paths:

        job_logs, jobid = dl2_to_irfs(
            paths["input"]["gamma_file"],
            paths["input"]["electron_file"],
            paths["input"]["proton_file"],
            paths["output"],
            config_file=config_file,
            irf_point_like=paths["options"],
            batch_configuration=batch_config,
            wait_jobs_dl1dl2=job_ids_from_dl1_dl2,
            slurm_options=paths.get("slurm_options", None),
        )

        log_dl2_to_irfs.update(log_dl2_to_irfs)
        jobid_for_check.append(jobid)
        debug_log[jobid] = (
            f"jobid from dl2_to_irfs stage that depends of the dl1_to_dl2 stage "
            f"job_ids; {job_ids_from_dl1_dl2}"
        )

    jobid_for_check = ",".join(jobid_for_check)

    save_log_to_file(log_dl2_to_irfs, logs["log_file"], workflow_step="dl2_to_irfs")
    save_log_to_file(debug_log, logs["debug_file"], workflow_step="dl2_to_irfs")

    log.info("==== END {} ====".format("batch mc_dl2_to_irfs"))

    return jobid_for_check


def dl2_to_irfs(
    gamma_file,
    electron_file,
    proton_file,
    outfile,
    config_file,
    irf_point_like,
    batch_configuration,
    wait_jobs_dl1dl2,
    slurm_options=None
):
    """
    Batches interactively the lstchain `lstchain_create_irf_files` entry point.

    Parameters
    ----------
    gamma_file: str
    electron_file: str
    proton_file: str
    outfile: str
    config_file: str
        Path to a configuration file. If none is given, a standard configuration is applied
    irf_point_like: str
        MC prod configuration argument to create IRFs: {True: gamma, False: gamma-diffuse}.
    batch_configuration : dict
        Dictionary containing the (full) source_environment and the slurm_account strings to be passed to the
        sbatch commands
    wait_jobs_dl1dl2: str
        Comma separated string with the job ids of previous stages (dl1_to_dl2 stage) to be passed as dependencies to
        the create_irfs_files job to be batched.
    slurm_options: str
        Extra slurm options to be passed to the sbatch command

    Returns
    -------
    log_dl2_to_irfs: dict
        Dictionary-wise log containing {'job_id': 'batched_cmd'} items
    job_id_dl2_irfs: str
        Job-id of the batched job to be passed to the last (MC prod check) stage of the workflow.
    """
    source_env = batch_configuration["source_environment"]
    slurm_account = batch_configuration["slurm_account"]
    
    output_dir = Path(outfile).parent

    log_dl2_to_irfs = {}

    check_and_make_dir_without_verification(output_dir)

    cmd = (
        f"lstchain_create_irf_files {irf_point_like} -g {gamma_file} -o {outfile} "
    )
    if proton_file is not None:
        cmd += f" -p {proton_file}"
    if electron_file is not None:
        cmd += f" -e {electron_file}"

    if config_file:
        cmd += f" --config={config_file}"

    log.info(f"Output dir IRF of {gamma_file}: {output_dir}")

    jobe = Path(output_dir).joinpath("job_dl2_to_irfs-%j.e").resolve().as_posix()
    jobo = Path(output_dir).joinpath("job_dl2_to_irfs-%j.o").resolve().as_posix()

    batch_cmd = "sbatch --parsable"
    if slurm_options is not None:
        batch_cmd += f" {slurm_options}"
    else:
        batch_cmd += " -p short"
    if slurm_account != "":
        batch_cmd += f" -A {slurm_account}"
    batch_cmd += (
        f" --dependency=afterok:{wait_jobs_dl1dl2} -J dl2_IRF"
        f' -e {jobe} -o {jobo} --wrap="{source_env} {cmd}"'
    )

    job_id_dl2_irfs = os.popen(batch_cmd).read().strip("\n")
    log_dl2_to_irfs.update({job_id_dl2_irfs: batch_cmd})

    # Copy config into working dir
    if config_file:
        shutil.copyfile(
            config_file,
            Path(output_dir).joinpath(Path(config_file).name)
        )

    return log_dl2_to_irfs, job_id_dl2_irfs
