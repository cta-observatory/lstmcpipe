#!/usr/bin/env python

# T. Vuillaume,
# Modifications by E. Garcia
# Code to reduce R0 data to DL1 onsite (La Palma cluster)


import os
import time
import shutil
from numpy.random import default_rng
from pathlib import Path
import subprocess
import logging
from lstmcpipe.io.data_management import (
    check_data_path,
    get_input_filelist,
    check_and_make_dir_without_verification
)


log = logging.getLogger(__name__)


def r0_to_dl1(input_dir, config_file=None, train_test_ratio=0.5, rng=None, n_r0_files_per_dl1_job=None,
              particle=None, prod_id=None, source_environment=None, offset=None, workflow_kind='lstchain', keep_rta_file=False,
              n_jobs_parallel=20):
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

    PROD_ID = prod_id

    if workflow_kind == 'lstchain':
        base_cmd = f'{source_environment} lstmcpipe_lst_core_r0_dl1 -c {config_file} '
        jobtype_id = 'LST'
    elif workflow_kind == 'ctapipe':
        base_cmd = f'{source_environment} lstmcpipe_cta_core_r0_dl1 -c {config_file} '
        jobtype_id = 'CTA'
    elif workflow_kind == 'hiperta':
        rta_source_env = 'source /home/enrique.garcia/.bashrc; conda activate rta_2night'
        base_cmd = f'{rta_source_env} lstmcpipe_rta_core_r0_dl1 -k {keep_rta_file} -d False '
        jobtype_id = 'RTA'
    else:
        log.critical("Please, selected an allowed workflow kind.")
        exit(-1)

    job_name = {'electron': f'e_{jobtype_id}_r0dl1',
                'gamma': f'g_{jobtype_id}_r0dl1',
                'gamma-diffuse': f'gd_{jobtype_id}_r0dl1',
                'proton': f'p_{jobtype_id}_r0dl1',
                'gamma_off0.0deg': f'g0.0_{jobtype_id}_r0dl1',
                'gamma_off0.4deg': f'g0.4_{jobtype_id}_r0dl1'
                }


    TRAIN_TEST_RATIO = float(train_test_ratio)

    DL0_DATA_DIR = input_dir

    ##############################################################################

    log.info(f"Working on DL0 files in {DL0_DATA_DIR}")

    check_data_path(DL0_DATA_DIR)

    raw_files_list = get_input_filelist(DL0_DATA_DIR)

    if len(raw_files_list) < 100:
        n_r0_per_dl1_job = 10
    
    if not n_r0_files_per_dl1_job:
        if len(raw_files_list) < 100:
            n_r0_per_dl1_job = 10
        else:
            if 'gamma' in input_dir:
                n_r0_per_dl1_job = 2 # TODO: change back to 25, this is for testing the array 
            elif 'gamma-diffuse' in input_dir or 'electron' in input_dir:
                n_r0_per_dl1_job = 50
            elif 'proton' in input_dir:
                n_r0_per_dl1_job = 125
            else:
                n_r0_per_dl1_job = 50

    # for debugging, TODO remove later
    n_r0_per_dl1_job = 2
    n_jobs_parallel = 3

    if rng is None:
        rng = default_rng()
    rng.shuffle(raw_files_list)

    number_files = len(raw_files_list)
    ntrain = int(number_files * TRAIN_TEST_RATIO)
    ntest = number_files - ntrain

    training_list = raw_files_list[:ntrain]
    testing_list = raw_files_list[ntrain:]

    log.info("{} raw files".format(number_files))
    log.info("{} files in training dataset".format(ntrain))
    log.info("{} files in test dataset".format(ntest))

    with open('training.list', 'w+') as newfile:
        for f in training_list:
            newfile.write(f)
            newfile.write('\n')

    with open('testing.list', 'w+') as newfile:
        for f in testing_list:
            newfile.write(f)
            newfile.write('\n')

    if 'off' in particle:
        DL0_DATA_DIR = DL0_DATA_DIR.split(offset)[0]   # Take out /off0.Xdeg
        RUNNING_DIR = os.path.join(
                DL0_DATA_DIR.replace(
                    'R0' if workflow_kind == 'hiperta' else 'DL0',
                    'running_analysis'),
                PROD_ID,
                offset
                )
    else:
        RUNNING_DIR = os.path.join(
                DL0_DATA_DIR.replace(
                    'R0' if workflow_kind == 'hiperta' else 'DL0',
                    'running_analysis'),
                PROD_ID,
                )

    JOB_LOGS = os.path.join(RUNNING_DIR, 'job_logs')
    DL1_DATA_DIR = os.path.join(RUNNING_DIR, 'DL1')
    # DIR_LISTS_BASE = os.path.join(RUNNING_DIR, 'file_lists')
    # ADD CLEAN QUESTION

    log.info("RUNNING_DIR: {}".format(RUNNING_DIR))
    log.info("JOB_LOGS DIR: {}".format(JOB_LOGS))
    log.info("DL1 DATA DIR: {}".format(DL1_DATA_DIR))

    for directory in [RUNNING_DIR, DL1_DATA_DIR, JOB_LOGS]:
        check_and_make_dir_without_verification(directory)

    # dumping the training and testing lists and splitting them in sub-lists for parallel jobs

    jobid2log = {}
    jobids_r0_dl1 = []

    for set_type in 'training', 'testing':
        if set_type == 'training':
            list_type = training_list
        else:
            list_type = testing_list
        dir_lists = os.path.join(RUNNING_DIR, 'file_lists_' + set_type)
        output_dir = os.path.join(RUNNING_DIR, 'DL1')
        output_dir = os.path.join(output_dir, set_type)

        check_and_make_dir_without_verification(dir_lists)
        check_and_make_dir_without_verification(output_dir)

        log.info("output dir: {}".format(output_dir))

        number_of_sublists = len(list_type) // n_r0_per_dl1_job + int(len(list_type) % n_r0_per_dl1_job > 0)
        for i in range(number_of_sublists):
            output_file = os.path.join(dir_lists, '{}_{}.list'.format(set_type, i))
            with open(output_file, 'w+') as out:
                for line in list_type[i * n_r0_per_dl1_job:n_r0_per_dl1_job * (i + 1)]:
                    out.write(line)
                    out.write('\n')
        log.info(f'{number_of_sublists} files generated for {set_type} list')

        save_job_ids = []

        files = [f.resolve().as_posix() for f in Path(dir_lists).glob("*")]

        if set_type == 'training':
            jobo = os.path.join(JOB_LOGS, "job_%A_%a_train.o")
            jobe = os.path.join(JOB_LOGS, "job_%A_%a_train.e")
        else:
            jobo = os.path.join(JOB_LOGS, f"job_%A_%a_test.o")
            jobe = os.path.join(JOB_LOGS, f"job_%A_%a_test.e")

        if particle == 'proton':
            queue = 'long'
        else:
            queue = 'short'

        slurm_options = f"--array=[0-{len(files)-1}]%{n_jobs_parallel} "
        slurm_options += f"-p {queue} "
        slurm_options += f"-e {jobe} "
        slurm_options += f"-o {jobo} "
        slurm_options += f"-J {job_name[particle]} "

        cmd = f'sbatch --parsable {slurm_options} --wrap="{base_cmd} -f {" ".join(files)} --output_dir {output_dir}"'

        jobid = os.popen(cmd).read().strip('\n')
        jobids_r0_dl1.append(jobid)

        jobid2log[jobid] = {}
        jobid2log[jobid]['particle'] = particle
        jobid2log[jobid]['set_type'] = set_type
        jobid2log[jobid]['jobe_path'] = jobe
        jobid2log[jobid]['jobo_path'] = jobo
        jobid2log[jobid]['sbatch_command'] = cmd

        log.info(f'{cmd}')
        log.info(f'Submitted batch job {jobid}')
        save_job_ids.append(jobid)

    # copy config into working dir
    if config_file is not None:
        shutil.copyfile(
            config_file,
            os.path.join(RUNNING_DIR, os.path.basename(config_file))
        )

    # save file lists into logs
    shutil.move('testing.list', os.path.join(RUNNING_DIR, 'testing.list'))
    shutil.move('training.list', os.path.join(RUNNING_DIR, 'training.list'))

    # return it log dictionary
    return jobid2log, jobids_r0_dl1
