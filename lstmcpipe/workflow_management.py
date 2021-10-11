# Functions used to manage the MC workflow analysis at La Palma

# Enrique Garcia Nov 2019

import os
import yaml
import pprint
import logging
from pathlib import Path


log = logging.getLogger(__name__)


def save_log_to_file(dictionary, output_file, log_format, workflow_step=None):
    """
    Dumps a dictionary (log) into a dicts of dicts with keys each of the pipeline stages.

    Parameters
    ----------
    dictionary : dict
        The dictionary to be dumped to a file
    output_file : str
        Output file to store the log
    log_format : str
        The way the data will be dumped to the output file. Either using yaml or just writing a dictionary as plain text
    workflow_step : str
        Step of the workflow, to be recorded in the log

    Returns
    -------
        None
    """
    if workflow_step is None:
        workflow_step = "NoKEY"

    dict2log = {workflow_step: dictionary}

    if log_format == "yml":
        with open(output_file, "a+") as fileout:
            yaml.dump(dict2log, fileout)
    else:
        with open(output_file, "a+") as fout:
            fout.write("\n\n  *******************************************\n")
            fout.write(f"   *** Log from the {workflow_step} stage \n")
            fout.write("  *******************************************\n")
            fout.write(pprint.pformat(dict2log))


def create_dict_with_dl1_filenames(dl1_directory, particles_loop, gamma_offsets=None):
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
                _particle = particle + off
                dl1_filename_directory[_particle] = {"training": {}, "testing": {}}

                dl1_filename_directory[_particle]["training"][
                    "train_path_and_outname_dl1"
                ] = next(
                    Path(off) / dl1_directory.format(particle).glob("*training*.h5")
                )
                dl1_filename_directory[_particle]["testing"][
                    "test_path_and_outname_dl1"
                ] = next(
                    Path(off) / dl1_directory.format(particle).glob("*testing*.h5")
                )
        else:
            dl1_filename_directory[particle] = {"training": {}, "testing": {}}
            dl1_filename_directory[particle]["training"][
                "train_path_and_outname_dl1"
            ] = next(Path(dl1_directory.format(particle)).glob("*training*.h5"))
            dl1_filename_directory[particle]["testing"][
                "test_path_and_outname_dl1"
            ] = next(Path(dl1_directory.format(particle)).glob("*testing*.h5"))

    return dl1_filename_directory


def batch_mc_production_check(
    jobids_from_r0_to_dl1,
    jobids_from_merge,
    jobids_from_train_pipe,
    jobids_from_dl1_to_dl2,
    jobids_from_dl2_to_irf,
    jobids_from_dl2_to_sensitivity,
    prod_id,
    log_file,
    log_debug_file,
    scancel_file,
    prod_config_file,
    last_stage,
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
    log_file: str
    log_debug_file: str
    scancel_file: str
    prod_config_file: str
    last_stage: str

    Returns
    -------
    debug_log : dict
        Dict with the jobid of the batched job to be stored in the `debug file`

    """
    debug_log = {}
    all_pipeline_jobs = []

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
    cmd_wrap = f"touch check_MC_{prod_id}.txt; "
    cmd_wrap += (
        f"sacct --format=jobid,jobname,nodelist,cputime,state,exitcode,avediskread,maxdiskread,avediskwrite,"
        f"maxdiskwrite,AveVMSize,MaxVMSize,avecpufreq,reqmem -j {all_pipeline_jobs} >> "
        f"check_MC_{prod_id}.txt; mkdir -p logs_{prod_id}; "
        f"rm {scancel_file}; "
        f"cp {Path(prod_config_file).resolve()} logs_{prod_id}/config_MC_prod_{prod_id}.yml; "
        f"mv slurm-* check_MC_{prod_id}.txt {log_file} {log_debug_file} IRFFITSWriter.provenance.log logs_{prod_id};"
    )

    batch_cmd = (
        f"sbatch -p short --parsable --dependency=afterok:{which_last_stage} -J prod_check "
        f'--wrap="{cmd_wrap}"'
    )

    jobid = os.popen(batch_cmd).read().strip("\n")
    log.info(f"Submitted batch CHECK-job {jobid}")

    # and in case the code brakes, here there is a summary of all the jobs by stages
    debug_log[
        jobid
    ] = "single jobid batched to check that all the dl1_to_dl2 stage jobs finish correctly."
    debug_log["sbatch_cmd"] = batch_cmd
    debug_log["SUMMARY_r0_dl1"] = jobids_from_r0_to_dl1
    debug_log["SUMMARY_merge"] = jobids_from_merge
    debug_log["SUMMARY_train_pipe"] = jobids_from_train_pipe
    debug_log["SUMMARY_dl1_dl2"] = jobids_from_dl1_to_dl2
    debug_log["SUMMARY_dl2_irfs"] = jobids_from_dl2_to_irf
    debug_log["SUMMARY_dl2_sensitivity"] = jobids_from_dl2_to_sensitivity

    return jobid, debug_log


def create_log_files(production_id):
    """
    Manages filenames (and overwrites if needed) log files.

    Parameters
    ----------
    production_id : str
        production identifier of the MC production to be launched

    Returns
    -------
    log_file: str
         path and filename of full log file
    debug_file: str
        path and filename of reduced (debug) log file
    scancel_file: str
        path and filename of bash file to cancel all the scheduled jobs
    """
    log_file = Path(f"./log_onsite_mc_r0_to_dl3_{production_id}.yml")
    debug_file = Path(f"./log_reduced_{production_id}.yml")
    scancel_file = Path(f"./scancel_{production_id}.sh")

    # scancel prod file needs chmod +x rights !
    scancel_file.touch()
    scancel_file.chmod(0o755)  # -rwxr-xr-x

    # If the file exists, i,e., the pipeline has been relaunched, erase it
    if log_file.exists():
        log_file.unlink()
    if debug_file.exists():
        debug_file.unlink()

    return log_file, debug_file, scancel_file


def update_scancel_file(scancel_file, jobids_to_update):
    """
    Bash file containing the slurm command to cancel multiple jobs.
    The file will be updated after every batched stage and will be erased in case the whole MC prod succeed without
    errors.

    Parameters
    ----------
    scancel_file: pathlib.Path
        filename that cancels the whole MC production
    jobids_to_update: str
        job_ids to be included into the the file
    """
    if scancel_file.stat().st_size == 0:
        with open(scancel_file, "r+") as f:
            f.write(f"scancel {jobids_to_update}")

    else:
        with open(scancel_file, "a") as f:
            f.write(f",{jobids_to_update}")
