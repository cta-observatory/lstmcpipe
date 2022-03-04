#!/usr/bin/env python

# T. Vuillaume,
# Modifications by E. Garcia
# Code to reduce R0 data to DL1 onsite (La Palma cluster)


import os
import time
import shutil
import logging
from pathlib import Path
from numpy.random import default_rng
from lstmcpipe.workflow_management import save_log_to_file
from lstmcpipe.io.data_management import (
    check_data_path,
    get_input_filelist,
    check_and_make_dir_without_verification,
)


log = logging.getLogger(__name__)


def batch_process_dl1(
    input_dir,
    conf_file,
    prod_id,
    particles_loop,
    batch_config,
    logs,
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
    batch_config : dict
        Dict with source environment (to select the desired conda environment to run the r0/1_to_dl1 stage),
        and the slurm user account.
    gamma_offsets : list
    workflow_kind: str
        One of the supported pipelines. Defines the command to be run on r0 files
    new_production: bool
        Whether to analysis simtel or reprocess existing dl1 files.
    logs: dict
        Dictionary con logs files

    Returns
    -------
    particle2jobid_dict : dict
        Dictionary of dictionaries containing the full log of the batched jobs (jobids as keys) as well as the
        4 more keys (one by particle) with all the jobs associated with each particle.
    all_jobids_from_r0_dl1_stage : str
        string, separated by commas, containing all the jobids of this stage
    """
    particle2jobid_dict = {"full_logs_all_jobs": {}}
    debug_log = {}
    all_jobids_from_dl1_processing_stage = []

    log.info("==== START {} dl1 processing ====".format(workflow_kind))
    time.sleep(1)

    for particle in particles_loop:
        if particle == "gamma" and gamma_offsets is not None:
            for off in gamma_offsets:
                particle_input_dir = Path(input_dir.format(particle), off).as_posix()
                _particle = particle + "_" + off
                if new_production:
                    job_logs, jobids_by_particle = r0_to_dl1(
                        particle_input_dir,  # Particle needs to be gamma w/o the off
                        config_file=conf_file,
                        particle=_particle,
                        prod_id=prod_id,
                        batch_config=batch_config,
                        offset=off,
                        workflow_kind=workflow_kind,
                    )
                else:
                    job_logs, jobids_by_particle = reprocess_dl1(
                        particle_input_dir,  # Particle needs to be gamma w/o the off
                        config_file=conf_file,
                        particle=_particle,
                        prod_id=prod_id,
                        batch_config=batch_config,
                        offset=off,
                        workflow_kind=workflow_kind,
                    )
                particle2jobid_dict["full_logs_all_jobs"].update(job_logs)
                particle2jobid_dict[_particle] = ",".join(jobids_by_particle)
                all_jobids_from_dl1_processing_stage.append(
                    particle2jobid_dict[_particle]
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
                    batch_config=batch_config,
                    workflow_kind=workflow_kind,
                )
            else:
                job_logs, jobids_by_particle = reprocess_dl1(
                    particle_input_dir,  # Particle needs to be gamma w/o the off
                    config_file=conf_file,
                    particle=_particle,
                    prod_id=prod_id,
                    batch_config=batch_config,
                    workflow_kind=workflow_kind,
                )
            particle2jobid_dict["full_logs_all_jobs"].update(job_logs)
            particle2jobid_dict[_particle] = ",".join(jobids_by_particle)
            all_jobids_from_dl1_processing_stage.append(
                particle2jobid_dict[_particle]
            )  # Create a list with particles elements

            for jid in jobids_by_particle:
                debug_log[jid] = f"{_particle} job from r0_to_dl1"

    all_jobids_from_dl1_processing_stage = ",".join(
        all_jobids_from_dl1_processing_stage
    )  # Create a string to be directly passed

    save_log_to_file(particle2jobid_dict, logs["log_file"], "r0_to_dl1")
    save_log_to_file(debug_log, logs["debug_file"], workflow_step="r0_to_dl1")

    log.info("==== END {} dl1 processing ====".format(workflow_kind))

    return particle2jobid_dict, all_jobids_from_dl1_processing_stage


def r0_to_dl1(
    input_dir,
    config_file=None,
    train_test_ratio=0.5,
    rng=None,
    dl1_files_per_job=None,
    particle=None,
    prod_id=None,
    batch_config=None,
    offset=None,
    workflow_kind="lstchain",
    keep_rta_file=False,
    n_jobs_parallel=50,
    debug_mode=False,
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
    rng : int
        Random seed for random processes. Default = 42
    dl1_files_per_job : int
        Number of r0 files processed by each r0_to_dl1 batched stage. If set to None (Default), see below the `usual
        production` case.n_r0_files_per_dl1_job

        If the number of r0 files found in `input_dir` is less than 100, it is consider to be a test on a small
        production. Therefore, the number of r0 files treated per batched stage (r0_to_dl1 or dl1ab) will be set to 10.

        Usual productions have >=1000 r0 files, in this case, the number of files per job (r0_to_dl1 or dl1ab) will be
        fixed to 50 (in case of gamma and electrons), and 100 for protons. Because of this protons end up in the
        long queue and other particles are submitted to the short queue.
    particle : str
        particle type (gamma/gamma_off/proton/electron). Determines output directory structure, job naming
        and n_r0_files_per_dl1_job if not set explicitly.
    offset : str
        gamma offset
    prod_id :str
        Production ID. If None, _v00 will be used, indicating an official base production. Default = None.
    batch_config : dict
        Dictionary containing the full (source + env) source_environment and the slurm_account strings.
        ! NOTE : train_pipe AND dl1_to_dl2 **MUST** be run with the same environment.
    workflow_kind: str
        One of the supported pipelines. Defines the command to be run on r0 files
    n_jobs_parallel: int
        Number of jobs to be run at the same time per array.

    # HIPERTA ARGUMENTS
    keep_rta_file : bool
        Flag to indicate whether to keep (keep_rta_file = True) or remove (keep_rta_file = Flase ) the
        `dl1v06_reorganized_*.h5` output file (hiperta_r0_dl1 and re-organiser stages).
        Argument to be passed to the hiperta_r0_to_dl1lstchain script.
    debug_mode : bool
        Flag to activate debug_mode. Only compatible with `hiperta` workflow kind, i.e.,
        HiPeRTA functionality. DEFAULT=False.

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

    train_test_ratio = float(train_test_ratio)

    source_environment = batch_config["source_environment"]
    slurm_account = batch_config["slurm_account"]

    if workflow_kind == "lstchain":
        base_cmd = f"{source_environment} lstmcpipe_lst_core_r0_dl1 -c {config_file} "
        jobtype_id = "LST"
    elif workflow_kind == "ctapipe":
        base_cmd = f"{source_environment} lstmcpipe_cta_core_r0_dl1 -c {config_file} "
        jobtype_id = "CTA"
    elif workflow_kind == "hiperta":
        base_cmd = (
            f"{source_environment} lstmcpipe_rta_core_r0_dl1 -c {config_file} "
        )
        if keep_rta_file:
            base_cmd += " --keep_rta_file"
        if debug_mode:
            base_cmd += " --debug_mode"

        jobtype_id = "RTA"
    else:
        base_cmd = ''
        jobtype_id = ''
        log.critical("Please, select an allowed workflow kind.")
        exit(-1)

    job_name = {
        "electron": f"e_{jobtype_id}_r0dl1",
        "gamma": f"g_{jobtype_id}_r0dl1",
        "gamma-diffuse": f"gd_{jobtype_id}_r0dl1",
        "proton": f"p_{jobtype_id}_r0dl1",
        "gamma_off0.0deg": f"g0.0_{jobtype_id}_r0dl1",
        "gamma_off0.4deg": f"g0.4_{jobtype_id}_r0dl1",
    }

    log.info("Working on DL0 files in {}".format(input_dir))

    check_data_path(input_dir)
    raw_files_list = get_input_filelist(input_dir)

    if len(raw_files_list) < 100:
        dl1_files_per_job = 10
    else:
        if "gamma" in input_dir:
            dl1_files_per_job = 25
        elif "gamma-diffuse" in input_dir or "electron" in input_dir:
            dl1_files_per_job = 50
        elif "proton" in input_dir:
            dl1_files_per_job = 50
        else:
            dl1_files_per_job = 50

    if rng is None:
        rng = default_rng()
    rng.shuffle(raw_files_list)

    number_files = len(raw_files_list)
    ntrain = int(number_files * train_test_ratio)
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
        running_dir = (
            Path(str(input_dir).replace("DL0", "running_analysis")).parent
            / prod_id
            / offset
        )
    else:
        running_dir = (
            Path(str(input_dir).replace("DL0", "running_analysis")) / prod_id
        )

    job_logs_dir = running_dir.joinpath("job_logs")
    dl1_output_dir = running_dir.joinpath("DL1")

    log.info("RUNNING_DIR: {}".format(running_dir))
    log.info("JOB_LOGS DIR: {}".format(job_logs_dir))
    log.info("DL1 DATA DIR: {}".format(dl1_output_dir))

    for directory in [running_dir, dl1_output_dir, job_logs_dir]:
        check_and_make_dir_without_verification(directory)

    # dumping the training and testing lists and splitting them in sub-lists for parallel jobs

    jobid2log, jobids_r0_dl1 = submit_dl1_jobs(
        base_cmd=base_cmd,
        file_lists={"testing": testing_list, "training": training_list},
        particle=particle,
        job_name=job_name[particle],
        dl1_files_per_batched_job=dl1_files_per_job,
        running_dir=running_dir,
        job_logs_dir=job_logs_dir,
        n_jobs_parallel=n_jobs_parallel,
        slurm_account=slurm_account
    )

    # copy config into working dir
    if config_file is not None:
        shutil.copyfile(
            config_file, running_dir.joinpath(Path(config_file).name)
        )

    # save file lists into logs
    shutil.move("testing.list", running_dir.joinpath("testing.list"))
    shutil.move("training.list", running_dir.joinpath("training.list"))

    # return it log dictionary
    return jobid2log, jobids_r0_dl1


def reprocess_dl1(
    input_dir,
    config_file=None,
    dl1_files_per_job=50,
    particle=None,
    prod_id=None,
    batch_config=None,
    offset=None,
    workflow_kind="lstchain",
    n_jobs_parallel=50,
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
    batch_config : dict
        Dictionary containing the (full) source_environment and the slurm_account strings.
        ! NOTE : train_pipe AND dl1_to_dl2 **MUST** be run with the same environment.
    workflow_kind: str
        One of the supported pipelines. Defines the command to be run on r0 files
    n_jobs_parallel: int
        Number of jobs to be run at the same time per array.
    dl1_files_per_job: int
        Number of dl1 files to be processed per job array that was batched.

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

    input_dir = Path(input_dir)

    source_environment = batch_config["source_environment"]
    slurm_account = batch_config["slurm_account"]

    if workflow_kind == "lstchain":
        base_cmd = f"{source_environment} lstmcpipe_lst_core_dl1ab -c {config_file} "
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

    log.info("Working on DL1 files in {}".format(input_dir.as_posix()))
    training_input_path = input_dir / "training"
    check_data_path(training_input_path)
    training_list = get_input_filelist(training_input_path)
    ntrain = len(training_list)
    testing_input_path = input_dir / "testing"
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
        running_dir = (
            Path(input_dir.as_posix().replace("DL1", "running_analysis")).parent.parent
            / prod_id
            / offset
        )
    else:
        running_dir = (
            Path(input_dir.as_posix().replace("DL1", "running_analysis")).parent
            / prod_id
        )

    job_logs_dir = running_dir / "job_logs"
    dl1_output_dir = running_dir / "DL1"

    log.info("RUNNING_DIR: {}".format(running_dir))
    log.info("JOB_LOGS DIR: {}".format(job_logs_dir))
    log.info("DL1 DATA DIR: {}".format(dl1_output_dir))

    for directory in [running_dir, dl1_output_dir, job_logs_dir]:
        check_and_make_dir_without_verification(directory)

    # dumping the training and testing lists and splitting them in sub-lists for parallel jobs
    # copy config into working dir
    if config_file is not None:
        shutil.copyfile(
            config_file, running_dir.joinpath(Path(config_file).name)
        )

    # save file lists into logs
    shutil.move("testing.list", running_dir.joinpath("testing.list"))
    shutil.move("training.list", running_dir.joinpath("training.list"))

    jobid2log, jobids_dl1_dl1 = submit_dl1_jobs(
        base_cmd=base_cmd,
        file_lists={"testing": testing_list, "training": training_list},
        particle=particle,
        job_name=job_name[particle],
        dl1_files_per_batched_job=dl1_files_per_job,
        running_dir=running_dir,
        job_logs_dir=job_logs_dir,
        n_jobs_parallel=n_jobs_parallel,
        slurm_account=slurm_account
    )

    # return it log dictionary
    return jobid2log, jobids_dl1_dl1


def submit_dl1_jobs(
    base_cmd,
    file_lists,
    particle,
    job_name,
    dl1_files_per_batched_job,
    running_dir,
    job_logs_dir,
    n_jobs_parallel,
    slurm_account
):
    jobid2log = {}
    jobids_dl1 = []

    # types should be training and testing
    for set_type, list_type in file_lists.items():
        log.debug("Generating list for {} step".format(set_type))
        dir_lists = running_dir.joinpath("file_lists_" + set_type)
        output_dir = running_dir.joinpath("DL1", set_type)

        check_and_make_dir_without_verification(dir_lists)
        check_and_make_dir_without_verification(output_dir)

        log.info("output dir: {}".format(output_dir))

        number_of_sublists = len(list_type) // dl1_files_per_batched_job + int(
            len(list_type) % dl1_files_per_batched_job > 0
        )
        for i in range(number_of_sublists):
            output_file = dir_lists.joinpath("{}_{}.list".format(set_type, i)).as_posix()
            with open(output_file, "w+") as out:
                for line in list_type[
                    i * dl1_files_per_batched_job : dl1_files_per_batched_job * (i + 1)
                ]:
                    out.write(line)
                    out.write("\n")
        log.info(f"{number_of_sublists} files generated for {set_type} list")

        files = [f.as_posix() for f in Path(dir_lists).glob("*")]

        slurm_options = {
            "output": job_logs_dir.joinpath(f"job_%A_%a_{'train' if set_type=='training' else 'test'}.o").as_posix(),
            "error": job_logs_dir.joinpath(f"job_%A_%a_{'train' if set_type=='training' else 'test'}.o").as_posix(),
            "array": f"0-{len(files)-1}%{n_jobs_parallel}",
            "job-name": f"{job_name}"
        }
        if particle == "proton":
            slurm_options.update({"partition": "long"})
        else:
            # Computing time sometimes depends on the machine.
            # e and g_0.X should be working on short, but sometimes runs on timeout.
            slurm_options.update({"partition": "long"})
        # `sbatch -A` is the --account slurm argument
        if slurm_account != '':
            slurm_options.update({"account": slurm_account})

        # start 1 jobarray with all files included. The job selects its file based on its task id
        cmd = f'{base_cmd} -f {" ".join(files)} --output_dir {output_dir}'
        slurm_cmd = "sbatch --parsable "
        for key, value in slurm_options.items():
            slurm_cmd += f"--{key} {value} "
        slurm_cmd += f'--wrap="{cmd}"'
        log.debug(f"Slurm command to start the jobs: {slurm_cmd}")

        jobid = os.popen(slurm_cmd).read().strip("\n")
        log.debug(f"Submitted batch job {jobid}")
        jobids_dl1.append(jobid)

        jobid2log[jobid] = {
            "particle": particle,
            "set_type": set_type,
            "jobe_path": slurm_options["error"],
            "jobo_path": slurm_options["output"],
            "sbatch_command": slurm_cmd
        }

    return jobid2log, jobids_dl1
