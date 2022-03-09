# Functions used to manage the MC workflow analysis at La Palma

# Enrique Garcia Nov 2019

import os
import yaml
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
        yaml.dump(dict2log, fileout)


def create_dl1_filenames_dict(dl1_directory, particles_loop, gamma_offsets=None):
    """
    Function that creates a dictionary with the filenames of all the final dl1 files (the same is done
    in the merge_and_copy_dl1 function) so that it can be passed to the rest of the stages, in case the full workflow
    it is not run from the start.

    Parameters
    ----------
    dl1_directory: str
        path to the dl1 directory files
    particles_loop : list
        list with the particles to be processed. Takes the global variable ALL_PARTICLES
    gamma_offsets : list

    Returns
    -------
    dl1_filename_directory : dict
        dictionary with the name (and absolute path) of the dl1 files with the name of the particles set as key of the
        dictionary

             dl1_filename_directory[particle].keys() = ['train_path_and_outname_dl1', 'test_path_and_outname_dl1']
    """
    dl1_filename_directory = {}

    for particle in particles_loop:
        if gamma_offsets is not None and particle == "gamma":
            for off in gamma_offsets:
                _particle = particle + "_" + off
                dl1_filename_directory[_particle] = {"training": {}, "testing": {}}

                dl1_filename_directory[_particle]["training"][
                    "train_path_and_outname_dl1"
                ] = next(
                    Path(dl1_directory.format(particle), off).glob("*training*.h5")
                ).resolve().as_posix()
                dl1_filename_directory[_particle]["testing"][
                    "test_path_and_outname_dl1"
                ] = next(
                    Path(dl1_directory.format(particle), off).glob("*testing*.h5")
                ).resolve().as_posix()
        else:
            dl1_filename_directory[particle] = {"training": {}, "testing": {}}
            dl1_filename_directory[particle]["training"][
                "train_path_and_outname_dl1"
            ] = next(Path(dl1_directory.format(particle)).glob("*training*.h5")
                     ).resolve().as_posix()
            dl1_filename_directory[particle]["testing"][
                "test_path_and_outname_dl1"
            ] = next(Path(dl1_directory.format(particle)).glob("*testing*.h5")
                     ).resolve().as_posix()

    return dl1_filename_directory


def batch_mc_production_check(
    jobids_from_r0_to_dl1,
    jobids_from_merge,
    jobids_from_train_pipe,
    jobids_from_dl1_to_dl2,
    jobids_from_dl2_to_irf,
    jobids_from_dl2_to_sensitivity,
    prod_id,
    log_directory,
    prod_config_file,
    last_stage,
    batch_config,
    logs_files,
):
    """
    Check that the dl1_to_dl2 stage, and therefore, the whole workflow has ended correctly.
    The machine information of each job will be dumped to the file.
    The file will take the form `check_MC_prodID_{prod_id}_OK.txt`

    Parameters
    ----------
    jobids_from_r0_to_dl1 : str
        jobs from the dl1_to_dl2 stage
    prod_id : str
        MC Production ID.
    jobids_from_merge :  str
    jobids_from_train_pipe : str
    jobids_from_dl1_to_dl2: str
    jobids_from_dl2_to_irf: str
    jobids_from_dl2_to_sensitivity: str
    log_directory: Path
    prod_config_file: str
    last_stage: str
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

    jobids_stages = {
        "r0_to_dl1": jobids_from_r0_to_dl1,
        "merge_and_copy_dl1": jobids_from_merge,
        "train_pipe": jobids_from_train_pipe,
        "dl1_to_dl2": jobids_from_dl1_to_dl2,
        "dl2_to_irfs": jobids_from_dl2_to_irf,
        "dl2_to_sensitivity": jobids_from_dl2_to_sensitivity,
    }

    if jobids_from_r0_to_dl1 != "":
        all_pipeline_jobs.append(jobids_from_r0_to_dl1)
    if jobids_from_merge != "":
        all_pipeline_jobs.append(jobids_from_merge)
    if jobids_from_train_pipe != "":
        all_pipeline_jobs.append(jobids_from_train_pipe)
    if jobids_from_dl1_to_dl2 != "":
        all_pipeline_jobs.append(jobids_from_dl1_to_dl2)
    if jobids_from_dl2_to_irf != "":
        all_pipeline_jobs.append(jobids_from_dl2_to_irf)
    if jobids_from_dl2_to_sensitivity != "":
        all_pipeline_jobs.append(jobids_from_dl2_to_sensitivity)

    all_pipeline_jobs = ",".join(all_pipeline_jobs)

    which_last_stage = jobids_stages[last_stage]

    # Save machine info into the check file
    check_prod_file = log_directory.joinpath(f"check_MC_{prod_id}.txt").name
    save_lstmcpipe_config = log_directory.joinpath(f"config_MC_prod_{prod_id}.yml")

    # Copy lstmcpipe config used
    shutil.copyfile(Path(prod_config_file).resolve(), save_lstmcpipe_config)

    cmd_wrap = f"touch {check_prod_file}; "
    cmd_wrap += (
        f"sacct --format=jobid,jobname,nodelist,cputime,state,exitcode,avediskread,maxdiskread,avediskwrite,"
        f"maxdiskwrite,AveVMSize,MaxVMSize,avecpufreq,reqmem -j {all_pipeline_jobs} >> {check_prod_file}; "
        f"mv slurm-* IRFFITSWriter.provenance.log {log_directory.name};"
    )

    batch_cmd = "sbatch -p short --parsable"
    if slurm_account != "":
        batch_cmd += f" -A {slurm_account}"
    batch_cmd += (
        f" --dependency=afterok:{which_last_stage} -J prod_check"
        f' --wrap="{source_env} {cmd_wrap}"'
    )

    jobid = os.popen(batch_cmd).read().strip("\n")
    log.info(f"Submitted batch CHECK-job {jobid}")

    # and in case the code brakes, here there is a summary of all the jobs by stages
    debug_log[
        jobid
    ] = "single jobid batched to check the check command worked correctly."
    debug_log["sbatch_cmd"] = batch_cmd
    debug_log["SUMMARY_r0_dl1"] = jobids_from_r0_to_dl1
    debug_log["SUMMARY_merge"] = jobids_from_merge
    debug_log["SUMMARY_train_pipe"] = jobids_from_train_pipe
    debug_log["SUMMARY_dl1_dl2"] = jobids_from_dl1_to_dl2
    debug_log["SUMMARY_dl2_irfs"] = jobids_from_dl2_to_irf
    debug_log["SUMMARY_dl2_sensitivity"] = jobids_from_dl2_to_sensitivity

    save_log_to_file(debug_log, logs_files["debug_file"],
                     workflow_step="check_full_workflow")

    return jobid
