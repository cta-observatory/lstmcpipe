#!/usr/bin/env python

# T. Vuillaume,
# Modifications by E. Garcia
# Code to reduce R0 data to DL1 onsite (La Palma cluster)
#
# usage:
# python onsite_mc_r0_dl1.py INPUT_DIR [-conf config_file] [-ratio train_test_ratio] [--sed random_seed] \
#  [-nfdl1 n_files_per_dl1] [--prod_id prod_id]

import os
import time
import shutil
import random
import argparse
import calendar
import lstchain
from lstmcpipe.data_management import (
    check_data_path,
    get_input_filelist,
    check_and_make_dir,
    check_and_make_dir_without_verification,
    manage_source_env_r0_dl1
)

parser = argparse.ArgumentParser(description="R0 to DL1 MC onsite conversion ")

parser.add_argument('input_dir', type=str,
                    help='path to the files directory to analyse',
                    )

parser.add_argument('--config_file', '-conf', action='store', type=str,
                    dest='config_file',
                    help='Path to a configuration file. If none is given, a standard configuration is applied',
                    default=None
                    )

parser.add_argument('--train_test_ratio', '-ratio', action='store', type=str,
                    dest='train_test_ratio',
                    help='Ratio of training data',
                    default=0.5
                    )

parser.add_argument('--random_seed', '-seed', action='store', type=str,
                    dest='random_seed',
                    help='Random seed for random processes',
                    default=42,
                    )

parser.add_argument('--n_r0_files_per_dl1_job', '-nfdl1', action='store', type=str,
                    dest='n_r0_files_per_dl1_job',
                    help='Number of r0 files processed by each r0_to_dl1 batched stage. '
                         'Default values are defined in the script.',
                    default=0,
                    )

parser.add_argument('--prod_id', action='store', type=str,
                    dest='prod_id',
                    help="Production ID. If None, _v00 will be used, indicating an official base production",
                    default=None,
                    )


def main(input_dir, config_file=None, train_test_ratio=0.5, random_seed=42, n_r0_files_per_dl1_job=0,
         flag_full_workflow=False, particle=None, prod_id=None, source_environment=None, offset=None):
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
    flag_full_workflow : bool
        Boolean flag to indicate if this script is run as part of the workflow that converts r0 to dl2 files.
    source_environment : str
        path to a .bashrc file to source (can be configurable for custom runs @ mc_r0_to_dl3 script)
         to activate a certain conda environment.
         DEFAULT: `source /fefs/aswg/software/virtual_env/.bashrc; conda activate cta`.
        ! NOTE : train_pipe AND dl1_to_dl2 **MUST** be run with the same environment.

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
    if not flag_full_workflow:

        print(f"\n ==== START {os.path.basename(__file__)} ==== \n")
        # This formatting should be the same as in `onsite_mc_r0_to_dl3.py`
        today = calendar.datetime.date.today()
        base_prod_id = f'{today.year:04d}{today.month:02d}{today.day:02d}_v{lstchain.__version__}'
        suffix_id = '_v00' if prod_id is None else '_{}'.format(prod_id)
        PROD_ID = base_prod_id + suffix_id

    else:
        # Full prod_id is passed as argument
        PROD_ID = prod_id

    TRAIN_TEST_RATIO = float(train_test_ratio)
    RANDOM_SEED = random_seed
    #NFILES_PER_DL1 = n_files_per_dl1
    #DESIRED_DL1_SIZE_MB = 1000

    #N_R0_PER_DL1_JOB = n_r0_files_per_dl1_job

    DL0_DATA_DIR = input_dir

    if source_environment is not None:
        manage_source_env_r0_dl1(source_and_env=source_environment, file=os.path.abspath('./core_list.sh'))

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

    if flag_full_workflow and 'off' in particle:
        # join(BASE_PATH, 'DL0', OBS_DATE, '{particle}', ZENITH, POINTING, 'PLACE_4_PROD_ID', GAMMA_OFF)
        DL0_DATA_DIR = DL0_DATA_DIR.split(offset)[0]   # Take out /off0.Xdeg
        RUNNING_DIR = os.path.join(DL0_DATA_DIR.replace('DL0', 'running_analysis'), PROD_ID, offset)
    else:
        RUNNING_DIR = os.path.join(DL0_DATA_DIR.replace('DL0', 'running_analysis'), PROD_ID)

    JOB_LOGS = os.path.join(RUNNING_DIR, 'job_logs')
    DL1_DATA_DIR = os.path.join(RUNNING_DIR, 'DL1')
    # DIR_LISTS_BASE = os.path.join(RUNNING_DIR, 'file_lists')
    # ADD CLEAN QUESTION

    print("\tRUNNING_DIR: \t", RUNNING_DIR)
    print("\tJOB_LOGS DIR: \t", JOB_LOGS)
    print("\tDL1 DATA DIR: \t", DL1_DATA_DIR)

    for directory in [RUNNING_DIR, DL1_DATA_DIR, JOB_LOGS]:
        if flag_full_workflow:
            check_and_make_dir_without_verification(directory)
        else:
            check_and_make_dir(directory)

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

        if flag_full_workflow:
            check_and_make_dir_without_verification(dir_lists)
            check_and_make_dir_without_verification(output_dir)
        else:
            check_and_make_dir(dir_lists)
            check_and_make_dir(output_dir)

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
            cc = ' -c {}'.format(config_file) if config_file is not None else ' '

            base_cmd = f'core_list.sh "lstchain_mc_r0_to_dl1 -o {output_dir} {cc}"'

            # recover or not the jobid depending of the workflow mode
            if not flag_full_workflow:  # Run interactively

                cmd = f'sbatch -p short -e {jobe} -o {jobo} {base_cmd} {os.path.join(dir_lists, file)}'
                # print(cmd)
                os.system(cmd)

            else:  # flag_full_workflow == True !
                job_name = {'electron': 'r0dl1_e',
                            'gamma': 'r0dl1_g',
                            'gamma-diffuse': 'r0dl1_gd',
                            'proton': 'r0dl1_p',
                            'gamma_off0.0deg': 'g0.0_r0dl1',
                            'gamma_off0.4deg': 'g0.4_r0dl1'
                            }

                if particle == 'proton':
                    queue = 'long'
                else:
                    queue = 'long'  # TODO change to short after prod5 check

                cmd = f'sbatch --parsable -p {queue} -J {job_name[particle]} ' \
                      f'-e {jobe} -o {jobo} {base_cmd} {os.path.join(dir_lists, file)}'

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

        if flag_full_workflow:
            print(f"\n\t{counter} jobs submitted - {particle} {set_type}. "
                  f"From jobid {save_job_ids[0]} - {save_job_ids[-1]}\n")
            time.sleep(1)  # Avoid collapsing LP cluster

    # copy this script and config into working dir
    shutil.copyfile(__file__, os.path.join(RUNNING_DIR, os.path.basename(__file__)))
    if config_file is not None:
        shutil.copyfile(config_file, os.path.join(RUNNING_DIR, os.path.basename(config_file)))

    # save file lists into logs
    shutil.move('testing.list', os.path.join(RUNNING_DIR, 'testing.list'))
    shutil.move('training.list', os.path.join(RUNNING_DIR, 'training.list'))

    # create log dictionary and return it if IN workflow mode
    if flag_full_workflow:
        return jobid2log, jobids_r0_dl1

    else:
        print(f"\n ==== END {os.path.basename(__file__)} ==== \n")


if __name__ == '__main__':
    args = parser.parse_args()
    main(args.input_dir,
         args.config_file,
         args.train_test_ratio,
         args.random_seed,
         args.n_files_per_dl1,
         args.flag_full_workflow
         )
