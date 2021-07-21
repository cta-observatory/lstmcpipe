#!/usr/bin/env python

# T. Vuillaume,
# Modifications by E. Garcia
# Code to reduce R0 data to DL1 onsite (La Palma cluster)


import os
import time
import shutil
import random
from lstmcpipe.io.data_management import (
    check_data_path,
    get_input_filelist,
    check_and_make_dir_without_verification,
    manage_source_env_r0_dl1
)


def r0_to_dl1(input_dir, config_file=None, train_test_ratio=0.5, random_seed=42, n_r0_files_per_dl1_job=0,
              particle=None, prod_id=None, source_environment=None, offset=None, workflow_kind='lstchain', keep_rta_file=False):
    """
    R0 to DL1 MC onsite conversion.


    Parameters
    ----------
    input_dir : str
        path to the files directory to analyse
    config_file :str
        Path to a configuration file. If none is given, a standard configuration is applied
    train_test_ratio :int
        Ratio of training data. Default = 0.5
    random_seed : int
        Random seed for random processes. Default = 42
    n_r0_files_per_dl1_job : int
        Number of r0 files processed by each r0_to_dl1 batched stage. If set to 0 (Default), see below the `usual
        production` case.n_r0_files_per_dl1_job

        If the number of r0 files found in `input_dir` is less than 100, it is consider to be a test on a small
        production. Therefore, the number of r0 files treated per batched stage will be set to 10.

        Usual productions have =>1000 r0 files, in this case, the number of batched jobs will be fixed to 50 (in case
        of gamma and electrons), 80 for (gamma-diffuse) and 125 to protons. This means that there will be batched a
        total of 50+50+80+125 = 305 jobs only for the r0_to_dl1 stage. (there are 1k r0 files for gammas (although 2
        offsets, thus 2k files), 2k r0 files for gd and e- and 5k for protons).

        Default = 0

    particle : str
        particle type for `flag_full_workflow` = True
    offset : str
        gamma offset
    prod_id :str
        Production ID. If None, _v00 will be used, indicating an official base production. Default = None.
    source_environment : str
        path to a .bashrc file to source (can be configurable for custom runs @ mc_r0_to_dl3 script)
         to activate a certain conda environment.
         DEFAULT: `source /fefs/aswg/software/virtual_env/.bashrc; conda activate cta`.
        ! NOTE : train_pipe AND dl1_to_dl2 **MUST** be run with the same environment.
    workflow_kind: str
        One of the supported pipelines. Defines the command to be run on r0 files
    keep_rta_file : bool
        Argument to be passed to the hiperta_r0_to_dl1lstchain script, which runs the hiperta_r0_dl1 and
        re-organiser stage
    Returns
    -------

    jobid2log : dict (if flag_full_workflow is True)

        A dictionary of dictionaries containing the full log information of the script. The first `layer` contains
        only the each jobid that the scripts has batched.

            dict[jobid] = information

        The second layer contains, organized by jobid,
             - the kind of particle that corresponded to the jobid
             - the command that was run to batch the job into the server
             - the path to both the output and error files (job_`jobid`.o and job_`jobid`.e) that were generated
                 when the job was send to the cluster

             dict[jobid].keys() = ['particle', 'sbatch_command', 'jobe_path', 'jobo_path']

             ****  otherwise : (if flag_full_workflow is False, by default) ****
            None is returned -- THIS IS APPLIED FOR THE ARGUMENTS SHOWN BELOW TOO

    jobids_r0_dl1

        A list of all the jobs sent by particle (including test and train set types).

    """

    PROD_ID = prod_id

    if workflow_kind == 'lstchain':
        core_file = 'core_list.sh'
        cc = ' -c {}'.format(config_file) if config_file is not None else ' '
        base_cmd = f'{core_file} "lstchain_mc_r0_to_dl1 {cc}"'
        jobtype_id = 'LST'
    elif workflow_kind == 'ctapipe':
        core_file = 'core_list_ctapipe.sh'
        cc = ' --config {}'.format(config_file) if config_file is not None else ' '
        base_cmd = f'{core_file} "ctapipe-stage1 {cc}"'
        jobtype_id = 'CTA'
    elif workflow_kind == 'hiperta':
        # TODO for the moment is only user enrique.garcia who has installed HiPeRTA  ##
        core_file = 'core_list_hiperta.sh'
        cc = ' -c {}'.format(config_file) if config_file is not None else ' '
        base_cmd = f'{core_file} "/home/enrique.garcia/software/lstmcpipe/lstmcpipe/hiperta/' \
                  f'hiperta_r0_to_dl1lstchain.py  -k {keep_rta_file} {cc}"'
        jobtype_id = 'RTA'

    TRAIN_TEST_RATIO = float(train_test_ratio)
    RANDOM_SEED = random_seed
    #NFILES_PER_DL1 = n_files_per_dl1
    #DESIRED_DL1_SIZE_MB = 1000

    #N_R0_PER_DL1_JOB = n_r0_files_per_dl1_job

    DL0_DATA_DIR = input_dir

    if source_environment is not None:
        manage_source_env_r0_dl1(source_and_env=source_environment, file=os.path.abspath(f"./{core_file}"))

    ##############################################################################

    print(f"Working on DL0 files in {DL0_DATA_DIR}")

    check_data_path(DL0_DATA_DIR)

    raw_files_list = get_input_filelist(DL0_DATA_DIR)

    if len(raw_files_list) < 100:
        N_R0_PER_DL1_JOB = 10
    elif n_r0_files_per_dl1_job == 0:
        if 'gamma' in input_dir:
            N_R0_PER_DL1_JOB = 25
        elif 'gamma-diffuse' in input_dir or 'electron' in input_dir:
            N_R0_PER_DL1_JOB = 50
        elif 'proton' in input_dir:
            N_R0_PER_DL1_JOB = 125
        else:
            N_R0_PER_DL1_JOB = 50
    else:
        N_R0_PER_DL1_JOB = n_r0_files_per_dl1_job

    # if NFILES_PER_DL1 == 0:
    #     size_dl0 = os.stat(raw_files_list[0]).st_size / 1e6
    #     reduction_dl0_dl1 = 5
    #     size_dl1 = size_dl0 / reduction_dl0_dl1
    #     NFILES_PER_DL1 = max(1, int(DESIRED_DL1_SIZE_MB / size_dl1))

    random.seed(RANDOM_SEED)
    random.shuffle(raw_files_list)

    number_files = len(raw_files_list)
    ntrain = int(number_files * TRAIN_TEST_RATIO)
    ntest = number_files - ntrain

    training_list = raw_files_list[:ntrain]
    testing_list = raw_files_list[ntrain:]

    print("\t{} raw files".format(number_files))
    print("\t{} files in training dataset".format(ntrain))
    print("\t{} files in test dataset".format(ntest))

    with open('training.list', 'w+') as newfile:
        for f in training_list:
            newfile.write(f)
            newfile.write('\n')

    with open('testing.list', 'w+') as newfile:
        for f in testing_list:
            newfile.write(f)
            newfile.write('\n')

    if 'off' in particle:
        # join(BASE_PATH, 'DL0', OBS_DATE, '{particle}', ZENITH, POINTING, 'PLACE_4_PROD_ID', GAMMA_OFF)
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

    print("\tRUNNING_DIR: \t", RUNNING_DIR)
    print("\tJOB_LOGS DIR: \t", JOB_LOGS)
    print("\tDL1 DATA DIR: \t", DL1_DATA_DIR)

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

        print("\toutput dir: \t", output_dir)

        number_of_sublists = len(list_type) // N_R0_PER_DL1_JOB + int(len(list_type) % N_R0_PER_DL1_JOB > 0)
        for i in range(number_of_sublists):
            output_file = os.path.join(dir_lists, '{}_{}.list'.format(set_type, i))
            with open(output_file, 'w+') as out:
                for line in list_type[i * N_R0_PER_DL1_JOB:N_R0_PER_DL1_JOB * (i + 1)]:
                    out.write(line)
                    out.write('\n')
        print(f'\t{number_of_sublists} files generated for {set_type} list')

        # LSTCHAIN #
        counter = 0
        save_job_ids = []

        for file in os.listdir(dir_lists):
            if set_type == 'training':
                jobo = os.path.join(JOB_LOGS, f"job{counter}_train.o")
                jobe = os.path.join(JOB_LOGS, f"job{counter}_train.e")
            else:
                jobo = os.path.join(JOB_LOGS, f"job{counter}_test.o")
                jobe = os.path.join(JOB_LOGS, f"job{counter}_test.e")

            job_name = {'electron': f'e_{jobtype_id}_r0dl1',
                        'gamma': f'g_{jobtype_id}_r0dl1',
                        'gamma-diffuse': f'gd_{jobtype_id}_r0dl1',
                        'proton': f'p_{jobtype_id}_r0dl1',
                        'gamma_off0.0deg': f'g0.0_{jobtype_id}_r0dl1',
                        'gamma_off0.4deg': f'g0.4_{jobtype_id}_r0dl1'
                        }

            if particle == 'proton':
                queue = 'long'
            else:
                queue = 'short'

            cmd = f'sbatch --parsable -p {queue} -J {job_name[particle]} ' \
                  f'-e {jobe} -o {jobo} {base_cmd} {output_dir} {os.path.join(dir_lists, file)}'

            jobid = os.popen(cmd).read().strip('\n')
            jobids_r0_dl1.append(jobid)

            # Fill the dictionaries if IN workflow mode
            jobid2log[jobid] = {}
            jobid2log[jobid]['particle'] = particle
            jobid2log[jobid]['set_type'] = set_type
            jobid2log[jobid]['jobe_path'] = jobe
            jobid2log[jobid]['jobo_path'] = jobo
            jobid2log[jobid]['sbatch_command'] = cmd

            # print(f'\t\t{cmd}')
            # print(f'\t\tSubmitted batch job {jobid}')
            save_job_ids.append(jobid)

            counter += 1

        print(f"\n\t{counter} jobs submitted - {particle} {set_type}. "
              f"From jobid {save_job_ids[0]} - {save_job_ids[-1]}\n")
        time.sleep(1)  # Avoid collapsing LP cluster

    # copy config into working dir
    if config_file is not None:
        shutil.copyfile(config_file, os.path.join(RUNNING_DIR, os.path.basename(config_file)))

    # save file lists into logs
    shutil.move('testing.list', os.path.join(RUNNING_DIR, 'testing.list'))
    shutil.move('training.list', os.path.join(RUNNING_DIR, 'training.list'))

    # return it log dictionary
    return jobid2log, jobids_r0_dl1
