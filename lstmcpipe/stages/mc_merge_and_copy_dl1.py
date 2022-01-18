#!/usr//bin/env python3

# T. Vuillaume, 12/09/2019
# merge and copy DL1 data after production
# Modifications by E. Garcia, 21/01/2020


# 1. check job_logs
# 2. check that all files have been created in DL1 based on training and testing lists
# 3. move DL1 files in final place
# 4. merge DL1 files
# 5. move running_dir

import os
import logging
import time
from lstmcpipe.io.data_management import check_job_logs


log = logging.getLogger(__name__)


def batch_merge_and_copy_dl1(
    running_analysis_dir,
    log_jobs_from_r0_to_dl1,
    particles_loop,
    source_env,
    smart_merge=False,
    no_image_flag=True,
    prod_id=None,
    gamma_offsets=None,
    workflow_kind="lstchain",
):
    """
    Function to batch the onsite_mc_merge_and_copy function once the all the r0_to_dl1 jobs (batched by particle type)
    have finished.

    Batch 8 merge_and_copy_dl1 jobs ([train, test] x particle) + the move_dl1 and move_dir jobs (2 per particle).

    Parameters
    ----------
    running_analysis_dir : str
        Directory to dl1 files
    log_jobs_from_r0_to_dl1 : dict
        dictionary of dictionaries containing the log (jobids organized by particle) from the previous stage
        (onsite_mc_r0_to_dl1)
    smart_merge : bool
        flag to indicate whether the merge of the files should be done with `--smart True` or `--smart False`,
        controlling the argument of the `lstchain_merge_hdf5_files.py` script (batched in this function).
    particles_loop : list
        list with the particles to be processed. Takes the global variable ALL_PARTICLES
    no_image_flag : bool
        flag to indicate whether the --no-image argument of the `lstchain_merge_hdf5_files.py` script (batched in
        this function) should be either True or False.
    gamma_offsets : list
        list containing the offset of the gammas
    prod_id : str
        prod_id defined in config_MC_prod.yml
    source_env : str
        source environment to select the desired conda environment to run the r0/1_to_dl1 stage.

    Returns
    -------
    log_merge_and_copy : dict
        Dictionary containing the log of the batched merge_and_copy_dl1 jobs
    jobid_4_train : str
         string containing the jobids to be passed to the next stage of the workflow (as a slurm dependency)
    all_merge : str
        string containing all the jobs to indicate that all the dl1 are correctly finished (for dl1_to_dl2)
    debug_log : dict
        Debug purposes

    """
    log_merge_and_copy = {}
    jobid_4_train = []
    all_jobs_from_merge_stage = []
    debug_log = {}

    log.info("==== START {} ====".format("batch merge_and_copy_dl1_workflow"))
    time.sleep(1)
    if isinstance(smart_merge, str):
        merge_flag = "lst" in smart_merge
    else:
        merge_flag = smart_merge
    log.debug("Merge flag set: {}".format(merge_flag))

    for particle in particles_loop:
        if particle == "gamma" and gamma_offsets is not None:
            for off in gamma_offsets:

                gamma_running_analysis_dir = os.path.join(running_analysis_dir, off)
                _particle = particle + "_" + off

                job_logs, jobid_mv_all_dl1, jobid_debug = merge_dl1(
                    gamma_running_analysis_dir.format(particle),
                    particle2jobs_dict=log_jobs_from_r0_to_dl1,
                    particle=_particle,
                    flag_merge=merge_flag,
                    flag_no_image=no_image_flag,
                    prod_id=prod_id,
                    gamma_offset=off,
                    source_environment=source_env,
                    workflow_kind=workflow_kind,
                )

                log_merge_and_copy.update(job_logs)
                all_jobs_from_merge_stage.append(jobid_debug)
                if _particle == "gamma-diffuse" or _particle == "proton":
                    jobid_4_train.append(jobid_mv_all_dl1)

                debug_log[jobid_mv_all_dl1] = (
                    f"{_particle} merge_and_copy-job - INDEED IT IS JUST PASSED the "
                    f"move_dl1 jobid - that will be send to the train pipe stage. They "
                    f"depend on the following {log_jobs_from_r0_to_dl1[_particle]} "
                    f"r0_t0_dl1 jobs."
                )
                debug_log[
                    jobid_debug
                ] = f"Are all the {_particle} jobs that have been launched in merge_and_copy_dl1."

        else:
            _particle = particle

            job_logs, jobid_mv_all_dl1, jobid_debug = merge_dl1(
                running_analysis_dir.format(particle),
                particle2jobs_dict=log_jobs_from_r0_to_dl1,
                particle=_particle,
                flag_merge=merge_flag,
                flag_no_image=no_image_flag,
                prod_id=prod_id,
                source_environment=source_env,
                workflow_kind=workflow_kind,
            )

            log_merge_and_copy.update(job_logs)
            all_jobs_from_merge_stage.append(jobid_debug)
            if _particle == "gamma-diffuse" or _particle == "proton":
                jobid_4_train.append(jobid_mv_all_dl1)

            debug_log[jobid_mv_all_dl1] = (
                f"{_particle} merge_and_copy-job - INDEED IT IS JUST PASSED the "
                f"move_dl1 jobid - that will be send to the train pipe stage. They depend "
                f"on the following {log_jobs_from_r0_to_dl1[_particle]} r0_t0_dl1 jobs."
            )
            debug_log[
                jobid_debug
            ] = f"Are all the {_particle} jobs that have been launched in merge_and_copy_dl1."

    jobid_4_train = ",".join(jobid_4_train)
    all_jobs_from_merge_stage = ",".join(all_jobs_from_merge_stage)

    log.info("==== END {} ====".format("batch merge_and_copy_dl1_workflow"))

    return log_merge_and_copy, jobid_4_train, all_jobs_from_merge_stage, debug_log


def compose_batch_command_of_script(
    source, destination, script, particle, wait_jobs, suffix
):
    """
    Creates the slurm command of the 'cmd' script

    Parameters
    ----------
    source: str
        Source directory
    destination: str
        Destination directory
    script: str
        Script to be used in the slurm command. Either 'lstmcpipe_utils_move_dir' or 'lstmcpipe_utils_cp_config'
    particle: str
        Particle type for slurm job-naming
    suffix: str
        Suffix to indicate the kind of job
    wait_jobs: str
        Job-id to be used as dependency in the batched slurm command

    Returns
    -------
    batch_cmd: str
        Full slurm batch command ready to batched the script argument

    """
    cmd = f"{script} -s {source} -d {destination}"

    jobe = f"slurm-{particle}_{suffix}.e"
    jobo = f"slurm-{particle}_{suffix}.o"

    batch_cmd = (
        f"sbatch --parsable -p short -J {particle}_{suffix} -e {jobe} -o {jobo} "
        f'--dependency=afterok:{wait_jobs} --wrap="{cmd}"'
    )

    return batch_cmd


def merge_dl1(
    input_dir,
    particle2jobs_dict,
    particle=None,
    flag_merge=False,
    flag_no_image=True,
    prod_id=None,
    gamma_offset=None,
    source_environment=None,
    workflow_kind="lstchain",
):
    """
    Merge and copy DL1 data after production.

        1. check job_logs
        2. check that all files have been created in DL1 based on training and testing lists
        3. move DL1 files in final place
        4. merge DL1 files
        5. move running_dir


    Parameters
    ----------
    input_dir : str
        path to the DL1 files directory to merge, copy and move.  Compulsory argument.
    particle2jobs_dict : dict
        Dictionary used to retrieve the r0 to dl1 jobids that were sent in the previous step of the r0-dl3 workflow.
        This script will NOT start until all the jobs sent before have finished.
    particle : str
        Type of particle used to create the log and dictionary
    flag_merge : bool
        Flag to indicate whether the `--smart` argument of the `lstchain_merge_hdf5_files.py` script must be set to
        True (smart merge) or False (auto merge).
        Default set to True.
    flag_no_image : bool
        Flaf to indicate whether the `--no-image` argument of the `lstchain_merge_hdf5_files.py` script must be set to
        True (--no-image True) or False (--no-image False).
        Default set to True.
    prod_id : str
        prod_id for output filename.
    gamma_offset : str
        if gamma files have various off0.Xdeg observations, include the offset within the filename for completeness.
    source_environment : str
        path to a .bashrc file to source (can be configurable for custom runs @ mc_r0_to_dl3 script)
         to activate a certain conda environment.
         DEFAULT: `source /fefs/aswg/software/virtual_env/.bashrc; conda activate cta`.
        ! NOTE : train_pipe AND dl1_to_dl2 **MUST** be run with the same environment.
    workflow_kind: str
        One of the supported pipelines. Defines the command to be run on r0 files


    Returns
    -------

    log_merge : dict
        dictionary of dictionaries containing the log information of this script and the jobid of the batched job,
        separated by particle

         - log_merge[particle][set_type].keys() = ['logs_script_test or logs_script_train',
                                        'train_path_and_outname_dl1 or test_path_and_outname_dl1', 'jobid']
    return_jobids4train : str
        jobid of the batched job to be send (for dependencies purposes) to the next stage of the workflow
        (train_pipe), by particle
    return_jobids_debug ; str
        jobids to store in log_reduced.txt - Mainly debug purposes.

    """

    log_merge = {particle: {"training": {}, "testing": {}}}

    wait_r0_dl1_jobs = particle2jobs_dict[particle]

    return_jobids4train = []
    return_jobids_debug = []

    job_name = {
        "electron": "e_merge",
        "gamma": "g_merge",
        "gamma-diffuse": "gd_merge",
        "proton": "p_merge",
        "gamma_off0.0deg": "g0.0_merge",
        "gamma_off0.4deg": "g0.4_merge",
    }

    JOB_LOGS = os.path.join(input_dir, "job_logs")
    training_filelist = os.path.join(input_dir, "training.list")
    running_DL1_dir = os.path.join(input_dir, "DL1")
    final_DL1_dir = input_dir.replace("running_analysis", "DL1")
    logs_destination_dir = input_dir.replace("running_analysis", "analysis_logs")

    # 1. check job logs
    check_job_logs(JOB_LOGS)

    # 2. check that all files have been created in DL1 based on training and testing lists
    # just check number of files first:
    # TODO Create check before merging files ?

    log.info("merging starts - {}".format(particle))

    # 3. merge DL1 files
    wait_both_merges = []

    for set_type in ["testing", "training"]:
        tdir = os.path.join(running_DL1_dir, set_type)

        # just need to take the base name of the file, so we read a processed bunch and take first file
        with open(training_filelist, "r") as f:
            output_filename = f.readline()

        output_filename = "dl1_" + os.path.basename(output_filename.split("_run")[0])
        if particle == "gamma-diffuse":
            output_filename = output_filename.replace("gamma", "gamma-diffuse")
        if "_off" in particle:
            output_filename += f"_{gamma_offset}"
        output_filename += f"_{prod_id}_{set_type}"
        output_filename += ".h5"

        output_filename = os.path.join(running_DL1_dir, output_filename)
        log.info("merge output: {}".format(output_filename))

        # After the workflow the files will be moved, will not stay at output_filename
        if set_type == "training":
            log_merge[particle][set_type]["train_path_and_outname_dl1"] = os.path.join(
                final_DL1_dir, os.path.basename(output_filename)
            )
        else:
            log_merge[particle][set_type]["test_path_and_outname_dl1"] = os.path.join(
                final_DL1_dir, os.path.basename(output_filename)
            )

        cmd = "sbatch --parsable -p short"
        if wait_r0_dl1_jobs != "":
            cmd += " --dependency=afterok:" + wait_r0_dl1_jobs

        cmd += (
            f" -J {job_name[particle]} -e slurm-{job_name[particle]}-{set_type}.o "
            f'-o slurm-{job_name[particle]}-{set_type}.e --wrap="{source_environment} '
            f'lstchain_merge_hdf5_files -d {tdir} -o {output_filename} --no-image {flag_no_image}'
        )

        if workflow_kind == "lstchain":
            cmd += '"'  # Close " of wrap
        elif workflow_kind == "hiperta":
            cmd += f'--smart {flag_merge}"'  # HiPeRTA workflow still uses --smart flag
        else:
            cmd += (
                f" -J {job_name[particle]} -e slurm-{job_name[particle]}-{set_type}.o "
                f'-o slurm-{job_name[particle]}-{set_type}.e --wrap="{source_environment} '
            )
            if flag_no_image:
                cmd += f'ctapipe-merge --input-dir {tdir} --output {output_filename} --skip-images --skip-simu-images"'
            else:
                cmd += f'ctapipe-merge --input-dir {tdir} --output {output_filename}"'

        jobid_merge = os.popen(cmd).read().strip("\n")
        log_merge[particle][set_type][jobid_merge] = cmd

        log.info(f"Submitted batch job {jobid_merge} -- {particle}, {set_type}")

        wait_both_merges.append(jobid_merge)
        return_jobids_debug.append(jobid_merge)

    # Out of testing/training loop !

    # 4., 5. & 6. in the case of the full workflow are done in a separate sbatch to wait merge, the three steps:
    # 4 --> move DL1 files in final place
    # 5 --> copy lstchain config file in final_dir too
    # 6 --> move running_dir as logs

    log.info("DL1 files will be moved to {}".format(final_DL1_dir))

    # 4 --> move DL1 files in final place
    wait_both_merges = ",".join(wait_both_merges)
    cmd_mv_dl1 = compose_batch_command_of_script(
        running_DL1_dir,
        final_DL1_dir,
        script="lstmcpipe_utils_move_dir",
        particle=job_name[particle].split("_")[0],
        suffix="mv_dl1_files",
        wait_jobs=wait_both_merges,
    )

    jobid_move_dl1 = os.popen(cmd_mv_dl1).read().strip("\n")
    log_merge[particle][set_type][jobid_move_dl1] = cmd_mv_dl1

    log.info(
        f"Submitted batch job {jobid_move_dl1}. It will move dl1 files when {wait_both_merges} finish."
    )

    # 5 --> copy lstchain config file in final_dir too
    cmd_cp_conf = compose_batch_command_of_script(
        input_dir,
        final_DL1_dir,
        script="lstmcpipe_utils_cp_config",
        particle=job_name[particle].split("_")[0],
        suffix="cp_config",
        wait_jobs=jobid_move_dl1,
    )

    jobid_copy_conf = os.popen(cmd_cp_conf).read().strip("\n")
    log_merge[particle][set_type][jobid_copy_conf] = cmd_cp_conf

    log.info(
        f"Submitted batch job {jobid_copy_conf}. It will copy the used config when {jobid_move_dl1} finish."
    )

    # 6 --> move running_dir to final analysis_logs
    cmd_mv_dir = compose_batch_command_of_script(
        input_dir,
        logs_destination_dir,
        script="lstmcpipe_utils_move_dir",
        particle=job_name[particle].split("_")[0],
        suffix="mv_dl1_dir",
        wait_jobs=jobid_copy_conf,
    )

    jobid_move_log = os.popen(cmd_mv_dir).read().strip("\n")
    log_merge[particle][set_type][jobid_move_log] = cmd_mv_dir

    log.info(
        f"Submitted batch job {jobid_move_log}. It will move running_dir when {jobid_copy_conf} finish."
    )

    return_jobids4train.append(jobid_move_dl1)

    return_jobids_debug.append(jobid_move_dl1)
    return_jobids_debug.append(jobid_move_log)
    return_jobids_debug.append(jobid_copy_conf)

    log.info("LOGS will be moved to {}".format(logs_destination_dir))

    # Little clarification (it will not be clear in log). These keys are stored here for 2 purposes:
    # 1 - train_pipe recover final dl1 names and path.
    # 2 - dl1_to_dl2 recover the jobids of the merged dl1 files; (all dl1 files MUST be merged and moved
    # to dl1_dir), so instead of storing the jobid that merges all the *particle*_dl1 (jobid_merge), it will
    # be store the jobid that move the dl1 final file to dl1_dir. Until this step is not finished, the workflow
    # cannot continue.

    return_jobids4train = ",".join(return_jobids4train)
    return_jobids_debug = ",".join(return_jobids_debug)

    return log_merge, return_jobids4train, return_jobids_debug
