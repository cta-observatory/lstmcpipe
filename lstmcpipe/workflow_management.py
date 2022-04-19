# Functions used to manage the MC workflow analysis at La Palma

# Enrique Garcia Nov 2019

import os
from ruamel.yaml import YAML
import shutil
import logging
from pathlib import Path


log = logging.getLogger(__name__)


def save_log_to_file(dictionary, output_file, workflow_step=None):
    """
    Dumps a dictionary (log) into a dicts of dicts with keys each of the pipeline stages.

    Parameters
    ----------
    dictionary : dict
        The dictionary to be dumped to a file
    output_file : str or Path
        Output file to store the log
    workflow_step : str
        Step of the workflow, to be recorded in the log

    Returns
    -------
        None
    """
    if workflow_step is None:
        workflow_step = "NoKEY"

    dict2log = {workflow_step: dictionary}

    with open(output_file, "a+") as fileout:
        YAML().dump(dict2log, fileout)


def batch_mc_production_check(
    dict_jobids_all_stages,
    log_directory,
    prod_id,
    prod_config_file,
    batch_config,
    logs_files,
):
    """
    Check that the dl1_to_dl2 stage, and therefore, the whole workflow has ended correctly.
    The machine information of each job will be dumped to the file.
    The file will take the form `check_MC_prodID_{prod_id}_OK.txt`

    Parameters
    ----------
    dict_jobids_all_stages : dict
        dict containing the {stage: all_job_ids related} information
    log_directory: Path
    prod_id: str
    prod_config_file: str
    batch_config: dict
    logs_files: dict
        Dictionary with logs files

    Returns
    -------
    jobid : str

    """
    debug_log = {}
    all_pipeline_jobs = []

    source_env = batch_config["source_environment"]
    slurm_account = batch_config["slurm_account"]

    for stage, jobids in dict_jobids_all_stages.items():
        all_pipeline_jobs.append(jobids)
        debug_log.update({f"SUMMARY_{stage}": jobids})

    all_pipeline_jobs = ",".join(all_pipeline_jobs)

    # Copy lstmcpipe config used to log directory
    shutil.copyfile(
        Path(prod_config_file).resolve(),
        log_directory.joinpath(f"config_MC_prod_{prod_id}.yml")
    )

    # Save machine info into the check file
    check_prod_file = log_directory.joinpath(f"check_MC_{prod_id}.txt").absolute().as_posix()

    cmd_wrap = f"touch {check_prod_file}; "
    cmd_wrap += (
        f"sacct --format=jobid,jobname,nodelist,cputime,state,exitcode,avediskread,maxdiskread,avediskwrite,"
        f"maxdiskwrite,AveVMSize,MaxVMSize,avecpufreq,reqmem -j {all_pipeline_jobs} >> {check_prod_file}; "
        f"mv slurm-* IRFFITSWriter.provenance.log {log_directory.absolute().as_posix()} "
    )

    batch_cmd = "sbatch -p short --parsable"
    if slurm_account != "":
        batch_cmd += f" -A {slurm_account}"
    batch_cmd += (
        f" --dependency=afterok:{all_pipeline_jobs} -J prod_check"
        f' --wrap="{source_env} {cmd_wrap}"'
    )

    jobid = os.popen(batch_cmd).read().strip("\n")
    log.info(f"Submitted batch CHECK-job {jobid}")
    debug_log.update({f"prod_check_{jobid}": batch_cmd})

    save_log_to_file(debug_log, logs_files["debug_file"],
                     workflow_step="check_full_workflow")

    return jobid
