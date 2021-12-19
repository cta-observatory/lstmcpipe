#!/usr/bin/env python

# T. Vuillaume,
# Modifications by E. Garcia
# Code to reduce R0 data to DL1 onsite (La Palma cluster)


import os
import time
import shutil
from numpy.random import default_rng
from pathlib import Path
import logging
from lstmcpipe.io.data_management import (
    check_data_path,
    get_input_filelist,
    check_and_make_dir_without_verification,
)
from lstmcpipe.workflow_management import create_slurm_job


log = logging.getLogger(__name__)


def batch_process_dl1(
    input_dir,
    conf_file,
    prod_id,
    particles_loop,
    source_env,
    gamma_offsets=None,
    workflow_kind="lstchain",
    new_production=True,
):
    """
    Batch the dl1 processing jobs by particle type.

    Parameters
    ----------
    input_dir : str
        Path to the r0/DL0 files
    conf_file : str
        Path to a configuration file. If none is given, a standard configuration is applied
    prod_id : str
        Production ID. If None, _v00 will be used, indicating an official base production. Default = None.
    particles_loop : list
        list with the particles to be processed. Takes the global variable ALL_PARTICLES
    source_env : str
        source environment to select the desired conda environment to run the r0/1_to_dl1 stage.
    gamma_offsets : list
    workflow_kind: str
        One of the supported pipelines. Defines the command to be run on r0 files
    new_production: bool
        Whether to analysis simtels or reprocess existing dl1 files.

    Returns
    -------
    full_log : dict
        Dictionary of dictionaries containing the full log of the batched jobs (jobids as keys) as well as the
        4 more keys (one by particle) with all the jobs associated with each particle.
    debug_log : dict
            dictionary containing minimum information - jobids -  for log_reduced.txt
    all_jobids_from_r0_dl1_stage : str
        string, separated by commas, containing all the jobids of this stage
    """
    full_log = {"log_all_job_ids": {}}
    debug_log = {}
    all_jobids_from_dl1_processing_stage = []

    log.info("==== START {} dl1 processing ====".format(workflow_kind))
    time.sleep(1)

    for particle in particles_loop:
        if particle == "gamma" and gamma_offsets is not None:
            for off in gamma_offsets:
                particle_input_dir = os.path.join(input_dir, off).format(particle)
                _particle = particle + "_" + off
                if new_production:
                    job_logs, jobids_by_particle = r0_to_dl1(
                        particle_input_dir,  # Particle needs to be gamma w/o the off
                        config_file=conf_file,
                        particle=_particle,
                        prod_id=prod_id,
                        source_environment=source_env,
                        offset=off,
                        workflow_kind=workflow_kind,
                    )
                else:
                    job_logs, jobids_by_particle = reprocess_dl1(
                        particle_input_dir,  # Particle needs to be gamma w/o the off
                        config_file=conf_file,
                        particle=_particle,
                        prod_id=prod_id,
                        source_environment=source_env,
                        offset=off,
                        workflow_kind=workflow_kind,
                    )
                full_log["log_all_job_ids"].update(job_logs)
                full_log[_particle] = ",".join(jobids_by_particle)
                all_jobids_from_dl1_processing_stage.append(
                    full_log[_particle]
                )  # Create a list with particles elements

                for jid in jobids_by_particle:
                    debug_log[jid] = f"{_particle} job from process_dl1"
        else:
            particle_input_dir = input_dir.format(particle)
            _particle = particle
            if new_production:
                job_logs, jobids_by_particle = r0_to_dl1(
                    particle_input_dir,  # Particle needs to be gamma w/o the off
                    config_file=conf_file,
                    particle=_particle,
                    prod_id=prod_id,
                    source_environment=source_env,
                    workflow_kind=workflow_kind,
                )
            else:
                job_logs, jobids_by_particle = reprocess_dl1(
                    particle_input_dir,  # Particle needs to be gamma w/o the off
                    config_file=conf_file,
                    particle=_particle,
                    prod_id=prod_id,
                    source_environment=source_env,
                    workflow_kind=workflow_kind,
                )
            full_log["log_all_job_ids"].update(job_logs)
            full_log[_particle] = ",".join(jobids_by_particle)
            all_jobids_from_dl1_processing_stage.append(
                full_log[_particle]
            )  # Create a list with particles elements

            for jid in jobids_by_particle:
                debug_log[jid] = f"{_particle} job from r0_to_dl1"
    all_jobids_from_dl1_processing_stage = ",".join(
        all_jobids_from_dl1_processing_stage
    )  # Create a string to be directly passed

    log.info("==== END {} dl1 processing ====".format(workflow_kind))

    return full_log, debug_log, all_jobids_from_dl1_processing_stage


def r0_to_dl1(
    input_dir,
    config_file=None,
    train_test_ratio=0.5,
    rng=None,
    n_parallel_dl1_jobs=None,
    particle=None,
    prod_id=None,
    source_environment=None,
    offset=None,
    workflow_kind="lstchain",
    keep_rta_file=False,
    n_jobs_parallel=20,
):
    """
    R0 to DL1 MC onsite conversion.
    Organizes files and launches slurm jobs in two slurm arrays.


    Parameters
    ----------
    input_dir : str
        path to the files directory to analyse
    config_file :str
        Path to a configuration file. If none is given, the standard configuration of the selected pipeline is applied
    train_test_ratio: float
        Ratio of training data. Default = 0.5
    random_seed : int
        Random seed for random processes. Default = 42
    n_r0_files_per_dl1_job : int
        Number of r0 files processed by each r0_to_dl1 batched stage. If set to None (Default), see below the `usual
        production` case.n_r0_files_per_dl1_job

        If the number of r0 files found in `input_dir` is less than 100, it is consider to be a test on a small
        production. Therefore, the number of r0 files treated per batched stage will be set to 10.

        Usual productions have =>1000 r0 files, in this case, the number of files per job will be fixed to 50 (in case
        of gamma and electrons), and 100 for protons. Because of this protons end up in the long queue and other particles
        are submitted to the short queue.
    particle : str
        particle type (gamma/gamma_off/proton/electron). Determines output directory structure, job naming
        and n_r0_files_per_dl1_job if not set explicitly.
    offset : str
        gamma offset
    prod_id :str
        Production ID. If None, _v00 will be used, indicating an official base production. Default = None.
    source_environment : str
        path to a .bashrc file to source (can be configurable for custom runs @lstmcpipe_start script)
        and command to activate a certain conda environment.
        Passed to the core script of the selected pipeline and activated there.
        Has no effect for hiperta currently
        ! NOTE : train_pipe AND dl1_to_dl2 **MUST** be run with the same environment.
    workflow_kind: str
        One of the supported pipelines. Defines the command to be run on r0 files
    keep_rta_file : bool
        Argument to be passed to the hiperta_r0_to_dl1lstchain script, which runs the hiperta_r0_dl1 and
        re-organiser stage
    n_jobs_parallel: int
        Number of jobs to be run at the same time per array.

    Returns
    -------
    jobid2log : dict
        A dictionary of dictionaries containing the full log information of the script. The first `layer` contains
        only the each jobid that the scripts has batched.

            dict[jobid] = information

        The second layer contains, organized by jobid,
             - the kind of particle that corresponded to the jobid
             - the command that was run to batch the job into the server
             - the path to both the output and error files (job_`jobid`.o and job_`jobid`.e) that were generated
                 when the job was send to the cluster

             dict[jobid].keys() = ['particle', 'sbatch_command', 'jobe_path', 'jobo_path']
    jobids_r0_dl1
        A list of all the jobs sent by particle (including test and train set types).
    """

    log.info("Starting R0 to DL1 processing for particle {}".format(particle))

    PROD_ID = prod_id
    TRAIN_TEST_RATIO = float(train_test_ratio)
    DL0_INPUT_DIR = input_dir

    if workflow_kind == "lstchain":
        base_cmd = f"{source_environment} lstmcpipe_lst_core_r0_dl1 -c {config_file} "
        jobtype_id = "LST"
    elif workflow_kind == "ctapipe":
        base_cmd = f"{source_environment} lstmcpipe_cta_core_r0_dl1 -c {config_file} "
        jobtype_id = "CTA"
    elif workflow_kind == "hiperta":
        rta_source_env = (
            "source /home/enrique.garcia/.bashrc; conda activate rta_2night"
        )
        base_cmd = (
            f"{rta_source_env} lstmcpipe_rta_core_r0_dl1 -k {keep_rta_file} -d False "
        )
        jobtype_id = "RTA"
    else:
        log.critical("Please, selected an allowed workflow kind.")
        exit(-1)

    job_name = {
        "electron": f"e_{jobtype_id}_r0dl1",
        "gamma": f"g_{jobtype_id}_r0dl1",
        "gamma-diffuse": f"gd_{jobtype_id}_r0dl1",
        "proton": f"p_{jobtype_id}_r0dl1",
        "gamma_off0.0deg": f"g0.0_{jobtype_id}_r0dl1",
        "gamma_off0.4deg": f"g0.4_{jobtype_id}_r0dl1",
    }

    log.info("Working on DL0 files in {}".format(DL0_INPUT_DIR))

    check_data_path(DL0_INPUT_DIR)
    raw_files_list = get_input_filelist(DL0_INPUT_DIR)

    if len(raw_files_list) < 100:
        n_parallel_dl1_jobs = 10

    if not n_parallel_dl1_jobs:
        if len(raw_files_list) < 100:
            n_parallel_dl1_jobs = 10
        else:
            if "gamma" in input_dir:
                n_parallel_dl1_jobs = 25
            elif "gamma-diffuse" in input_dir or "electron" in input_dir:
                n_parallel_dl1_jobs = 50
            elif "proton" in input_dir:
                n_parallel_dl1_jobs = 100
            else:
                n_parallel_dl1_jobs = 50

    if rng is None:
        rng = default_rng()
    rng.shuffle(raw_files_list)

    number_files = len(raw_files_list)
    ntrain = int(number_files * TRAIN_TEST_RATIO)
    ntest = number_files - ntrain

    training_list = raw_files_list[:ntrain]
    testing_list = raw_files_list[ntrain:]

    log.info("{} raw R0 files".format(number_files))
    log.info("{} R0 files in training dataset".format(ntrain))
    log.info("{} R0 files in test dataset".format(ntest))

    with open("training.list", "w+") as newfile:
        for f in training_list:
            newfile.write(f)
            newfile.write("\n")

    with open("testing.list", "w+") as newfile:
        for f in testing_list:
            newfile.write(f)
            newfile.write("\n")

    if "off" in particle:
        # Take out /off0.Xdeg
        RUNNING_DIR = (
            Path(str(DL0_INPUT_DIR).replace("DL0", "running_analysis")).parent
            / PROD_ID
            / offset
        )
    else:
        RUNNING_DIR = (
            Path(str(DL0_INPUT_DIR).replace("DL0", "running_analysis")) / PROD_ID
        )

    JOB_LOGS = os.path.join(RUNNING_DIR, "job_logs")
    DL1_OUTPUT_DIR = os.path.join(RUNNING_DIR, "DL1")
    # DIR_LISTS_BASE = os.path.join(RUNNING_DIR, 'file_lists')
    # ADD CLEAN QUESTION

    log.info("RUNNING_DIR: {}".format(RUNNING_DIR))
    log.info("JOB_LOGS DIR: {}".format(JOB_LOGS))
    log.info("DL1 DATA DIR: {}".format(DL1_OUTPUT_DIR))

    for directory in [RUNNING_DIR, DL1_OUTPUT_DIR, JOB_LOGS]:
        check_and_make_dir_without_verification(directory)

    # dumping the training and testing lists and splitting them in sub-lists for parallel jobs

    jobid2log, jobids_r0_dl1 = submit_dl1_jobs(
        base_cmd,
        {"testing": testing_list, "training": training_list},
        particle,
        job_name[particle],
        n_parallel_dl1_jobs,
        DL1_OUTPUT_DIR,
        RUNNING_DIR,
        JOB_LOGS,
    )

    # copy config into working dir
    if config_file is not None:
        shutil.copyfile(
            config_file, os.path.join(RUNNING_DIR, os.path.basename(config_file))
        )

    # save file lists into logs
    shutil.move("testing.list", os.path.join(RUNNING_DIR, "testing.list"))
    shutil.move("training.list", os.path.join(RUNNING_DIR, "training.list"))

    # return it log dictionary
    return jobid2log, jobids_r0_dl1


def reprocess_dl1(
    input_dir,
    config_file=None,
    n_parallel_dl1_jobs=50,
    particle=None,
    prod_id=None,
    source_environment=None,
    offset=None,
    workflow_kind="lstchain",
    n_jobs_parallel=20,
):
    """
    Reprocessing of existing dl1 files.
    Organizes files and launches slurm jobs in two slurm arrays.
    The same train/test split performed with the earlier r0 to dl1
    processing is used.

    Parameters
    ----------
    input_dir : str
        path to the files directory to analyse
    config_file :str
        Path to a configuration file. If none is given, the standard configuration of the selected pipeline is applied
    particle : str
        particle type (gamma/gamma_off/proton/electron). Determines output directory structure, job naming
        and n_r0_files_per_dl1_job if not set explicitly.
    offset : str
        gamma offset
    prod_id :str
        Production ID. If None, _v00 will be used, indicating an official base production. Default = None.
    source_environment : str
        path to a .bashrc file to source (can be configurable for custom runs @lstmcpipe_start script)
        and command to activate a certain conda environment.
        Passed to the core script of the selected pipeline and activated there.
        Has no effect for hiperta currently
        ! NOTE : train_pipe AND dl1_to_dl2 **MUST** be run with the same environment.
    workflow_kind: str
        One of the supported pipelines. Defines the command to be run on r0 files
    n_jobs_parallel: int
        Number of jobs to be run at the same time per array.

    Returns
    -------
    jobid2log : dict
        A dictionary of dictionaries containing the full log information of the script. The first `layer` contains
        only the each jobid that the scripts has batched.

            dict[jobid] = information

        The second layer contains, organized by jobid,
             - the kind of particle that corresponded to the jobid
             - the command that was run to batch the job into the server
             - the path to both the output and error files (job_`jobid`.o and job_`jobid`.e) that were generated
                 when the job was send to the cluster

             dict[jobid].keys() = ['particle', 'sbatch_command', 'jobe_path', 'jobo_path']
    jobids_dl1_dl1
        A list of all the jobs sent by particle (including test and train set types).
    """

    log.info("Starting DL1 to DL1 processing for particle {}".format(particle))

    PROD_ID = prod_id
    DL1_INPUT_DIR = Path(input_dir)

    if workflow_kind == "lstchain":
        base_cmd = f"{source_environment} lstmcpipe_lst_core_dl1_dl1 -c {config_file} "
        jobtype_id = "LST"
    elif workflow_kind == "ctapipe":
        base_cmd = f"{source_environment} lstmcpipe_cta_core_r0_dl1 -c {config_file} "
        jobtype_id = "CTA"
    else:
        log.critical("Please, selected an allowed workflow kind.")
        exit(-1)

    job_name = {
        "electron": f"e_{jobtype_id}_dl1dl1",
        "gamma": f"g_{jobtype_id}_dl1dl1",
        "gamma-diffuse": f"gd_{jobtype_id}_dl1dl1",
        "proton": f"p_{jobtype_id}_dl1dl1",
        "gamma_off0.0deg": f"g0.0_{jobtype_id}_dl1dl1",
        "gamma_off0.4deg": f"g0.4_{jobtype_id}_dl1dl1",
    }

    log.info("Working on DL1 files in {}".format(DL1_INPUT_DIR))
    training_input_path = DL1_INPUT_DIR / "training"
    check_data_path(training_input_path)
    training_list = get_input_filelist(training_input_path)
    ntrain = len(training_list)
    testing_input_path = DL1_INPUT_DIR / "testing"
    check_data_path(testing_input_path)
    testing_list = get_input_filelist(testing_input_path)
    ntest = len(testing_list)

    log.info("{} DL1 files in training dataset".format(ntrain))
    log.info("{} DL1 files in test dataset".format(ntest))

    with open("training.list", "w+") as newfile:
        for f in training_list:
            newfile.write(f)
            newfile.write("\n")

    with open("testing.list", "w+") as newfile:
        for f in testing_list:
            newfile.write(f)
            newfile.write("\n")

    if "off" in particle:
        # Take out /off0.Xdeg
        RUNNING_DIR = (
            Path(str(DL1_INPUT_DIR).replace("DL1", "running_analysis")).parent.parent
            / PROD_ID
            / offset
        )
    else:
        RUNNING_DIR = (
            Path(str(DL1_INPUT_DIR).replace("DL1", "running_analysis")).parent / PROD_ID
        )

    JOB_LOGS = RUNNING_DIR / "job_logs"
    DL1_OUTPUT_DIR = RUNNING_DIR / "DL1"

    log.info("RUNNING_DIR: {}".format(RUNNING_DIR))
    log.info("JOB_LOGS DIR: {}".format(JOB_LOGS))
    log.info("DL1 DATA DIR: {}".format(DL1_OUTPUT_DIR))

    for directory in [RUNNING_DIR, DL1_OUTPUT_DIR, JOB_LOGS]:
        check_and_make_dir_without_verification(directory)

    # dumping the training and testing lists and splitting them in sub-lists for parallel jobs
    # copy config into working dir
    if config_file is not None:
        shutil.copyfile(
            config_file, os.path.join(RUNNING_DIR, os.path.basename(config_file))
        )

    # save file lists into logs
    shutil.move("testing.list", os.path.join(RUNNING_DIR, "testing.list"))
    shutil.move("training.list", os.path.join(RUNNING_DIR, "training.list"))

    jobid2log, jobids_dl1_dl1 = submit_dl1_jobs(
        base_cmd,
        {"testing": testing_list, "training": training_list},
        particle,
        job_name[particle],
        n_parallel_dl1_jobs,
        DL1_OUTPUT_DIR,
        RUNNING_DIR,
        JOB_LOGS,
    )

    # return it log dictionary
    return jobid2log, jobids_dl1_dl1


def submit_dl1_jobs(
    base_cmd,
    file_lists,
    particle,
    job_name,
    n_parallel_dl1_jobs,
    DL1_DATA_DIR,
    RUNNING_DIR,
    JOB_LOGS,
):
    jobid2log = {}
    jobids_dl1 = []

    # types should be training and testing
    for set_type, list_type in file_lists.items():
        log.debug("Generating list for {} step".format(set_type))
        dir_lists = os.path.join(RUNNING_DIR, "file_lists_" + set_type)
        output_dir = os.path.join(RUNNING_DIR, "DL1")
        output_dir = os.path.join(output_dir, set_type)

        check_and_make_dir_without_verification(dir_lists)
        check_and_make_dir_without_verification(output_dir)

        log.info("output dir: {}".format(output_dir))

        number_of_sublists = len(list_type) // n_parallel_dl1_jobs + int(
            len(list_type) % n_parallel_dl1_jobs > 0
        )
        for i in range(number_of_sublists):
            output_file = os.path.join(dir_lists, "{}_{}.list".format(set_type, i))
            with open(output_file, "w+") as out:
                for line in list_type[
                    i * n_parallel_dl1_jobs : n_parallel_dl1_jobs * (i + 1)
                ]:
                    out.write(line)
                    out.write("\n")
        log.info(f"{number_of_sublists} files generated for {set_type} list")

        files = [f.as_posix() for f in Path(dir_lists).glob("*")]

        slurm_options = {}
        slurm_options["output"] = os.path.join(
            JOB_LOGS, f"job_%A_%a_{'train' if set_type=='training' else 'test'}.o"
        )
        slurm_options["error"] = os.path.join(
            JOB_LOGS, f"job_%A_%a_{'train' if set_type=='training' else 'test'}.e"
        )
        if particle == "proton":
            slurm_options["partition"] = "short"
        else:
            slurm_options["partition"] = "short"
        slurm_options["array"] = f"0-{len(files)-1}%{n_parallel_dl1_jobs}"
        slurm_options["job-name"] = f"{job_name}"

        # start 1 jobarray with all files included. The job selects its file based on its task id
        cmd = f'{base_cmd} -f {" ".join(files)} --output_dir {output_dir}'
        slurm_cmd = create_slurm_job(cmd, slurm_options)
        log.debug(f"Slurm command to start the jobs: {slurm_cmd}")

        jobid = os.popen(slurm_cmd).read().strip("\n")
        log.debug(f"Submitted batch job {jobid}")
        jobids_dl1.append(jobid)

        jobid2log[jobid] = {}
        jobid2log[jobid]["particle"] = particle
        jobid2log[jobid]["set_type"] = set_type
        jobid2log[jobid]["jobe_path"] = slurm_options["error"]
        jobid2log[jobid]["jobo_path"] = slurm_options["output"]
        jobid2log[jobid]["sbatch_command"] = slurm_cmd

    return jobid2log, jobids_dl1
