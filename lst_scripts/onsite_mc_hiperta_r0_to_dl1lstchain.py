#!/usr//bin/env python
#
# T. Vuillaume,
# Code adapted by E. Garcia 03/20
# Code to reduce R0 data to DL1 onsite (La Palma cluster) - HiPeRTA version
#
# usage:
# python onsite_mc_r0_dl1.py INPUT_DIR [-conf config_rta_file] [-ratio train_test_ratio] [--sed random_seed] \
#  [-nfdl1 n_files_per_dl1] [--prod_id prod_id] [-k keep_rta_output_file]

import os
import time
import shutil
import random
import argparse
import calendar
from distutils.util import strtobool
from data_management import (check_data_path,
                             get_input_filelist,
                             check_and_make_dir,
                             check_and_make_dir_without_verification,
                             )

parser = argparse.ArgumentParser(description="MC R0 to DL1 - MC onsite conversion")

parser.add_argument('input_dir', type=str,
                    help='path to the files directory to analyse',
                    )

parser.add_argument('--config_rta_file', '-conf', action='store', type=str,
                    dest='config_rta_file',
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
                    help='Number of input files merged in one DL1. If 0, the number of files per DL1 is computed based '
                         'on the size of the DL0 files and the expected reduction factor of 5 '
                         'to obtain DL1 files of ~100 MB. Else, use fixed number of files',
                    default=0,
                    )

parser.add_argument('--prod_id', action='store', type=str,
                    dest='prod_id',
                    help="Production ID. If None, _v00 will be used, indicating an official base production",
                    default=None,
                    )

parser.add_argument('--keep_rta_file', '-k',
                    dest='keep_rta_file',
                    type=lambda x: bool(strtobool(x)),
                    help='Keep output of hiperta. Set by default to False',
                    default=False
                    )


def main(input_dir, config_rta_file=None, train_test_ratio=0.5, random_seed=42, n_r0_files_per_dl1_job=0,
         flag_full_workflow=False, particle=None, prod_id=None, offset=None, keep_rta_file=False, lst_config=None):
    """
    same as for r0_to_dl1 lst-like but with the exceptions of rta

    Parameters
    ----------
    input_dir : str
        path to the files directory to analyse
    config_rta_file : str
        Path to a HiPeRTA configuration file. If none is given, a standard configuration is applied
    train_test_ratio : int
        Ratio of training data. Default = 0.5
    random_seed : int
        Random seed for random processes. Default = 42
    n_r0_files_per_dl1_job : int
        Number of r0 files processed by each r0_to_dl1 batched stage. If set to 0 (Default), see below the `usual
        production` case.n_r0_files_per_dl1_job
    particle : str
        particle type for `flag_full_workflow` = True
    offset : str
        gamma offset
    prod_id :str
        Production ID. If None, _v00 will be used, indicating an official base production. Default = None.
    flag_full_workflow : bool
        Boolean flag to indicate if this script is run as part of the workflow that converts r0 to dl2 files.
    keep_rta_file : bool
        Argument to be passed to the hiperta_r0_to_dl1lstchain script, which runs the hiperta_r0_dl1 and
        re-organiser stage
    lst_config: str
        path used just to copy the config to `running analysis`

    Returns
    -------

    """

    if not flag_full_workflow:
        # This formatting should be the same as in `onsite_mc_r0_to_dl3_hiperta.py`
        print("\n ==== START {} ==== \n".format(os.path.basename(__file__)))
        today = calendar.datetime.date.today()
        base_prod_id = f'{today.year:04d}{today.month:02d}{today.day:02d}_vRTA'
        suffix_id = '_v00' if prod_id is None else '_{}'.format(prod_id)
        PROD_ID = base_prod_id + suffix_id
    else:
        # Full prod_id is passed as argument
        PROD_ID = prod_id

    TRAIN_TEST_RATIO = float(train_test_ratio)
    RANDOM_SEED = random_seed
    #NFILES_PER_DL1 = int(n_files_per_dl1)
    #DESIRED_DL1_SIZE_MB = 1000

    DL0_DATA_DIR = input_dir

    ##############################################################################

    print("Working on MCHDF5 R0 files in {}".format(DL0_DATA_DIR))

    check_data_path(DL0_DATA_DIR)

    raw_files_list = get_input_filelist(DL0_DATA_DIR)

    if len(raw_files_list) < 100:
        N_R0_PER_DL1_JOB = 10
    elif args.n_r0_files_per_dl1_job == 0:
        if 'gamma' in input_dir:
            N_R0_PER_DL1_JOB = 25
        elif 'gamma-diffuse' in input_dir or 'electron' in input_dir:
            N_R0_PER_DL1_JOB = 50
        elif 'proton' in input_dir:
            N_R0_PER_DL1_JOB = 125
        else:
            N_R0_PER_DL1_JOB = 50
    else:
        N_R0_PER_DL1_JOB = args.n_r0_files_per_dl1_job

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
        DL0_DATA_DIR = DL0_DATA_DIR.split(offset)[0]  # Take out /off0.Xdeg
        RUNNING_DIR = os.path.join(DL0_DATA_DIR.replace('R0', 'running_analysis'), PROD_ID, offset)
    else:
        RUNNING_DIR = os.path.join(DL0_DATA_DIR.replace('R0', 'running_analysis'), PROD_ID)

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
    jobids_RTA_r0_dl1_reorganized = []

    for set_type in 'training', 'testing':
        if set_type == 'training':
            list = training_list
        else:
            list = testing_list
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

        number_of_sublists = len(list) // N_R0_PER_DL1_JOB + int(len(list) % N_R0_PER_DL1_JOB > 0)
        for i in range(number_of_sublists):
            output_file = os.path.join(dir_lists, '{}_{}.list'.format(set_type, i))
            with open(output_file, 'w+') as out:
                for line in list[i * N_R0_PER_DL1_JOB:N_R0_PER_DL1_JOB * (i + 1)]:
                    out.write(line)
                    out.write('\n')
        print('\t{} files generated for {} list'.format(number_of_sublists, set_type))

        # HiPeRTA ###
        counter = 0
        save_job_ids = []

        for file in os.listdir(dir_lists):
            if set_type == 'training':
                jobo = os.path.join(JOB_LOGS, "job{}_train.o".format(counter))
                jobe = os.path.join(JOB_LOGS, "job{}_train.e".format(counter))
            else:
                jobo = os.path.join(JOB_LOGS, "job{}_test.o".format(counter))
                jobe = os.path.join(JOB_LOGS, "job{}_test.e".format(counter))

            # TODO for the moment is only user enrique.garcia who has installed HiPeRTA  ##
            cc = ' -c {}'.format(config_rta_file) if config_rta_file is not None else ' '
            base_cmd = f'core_list_hiperta.sh "/home/enrique.garcia/software/LST_scripts/lst_scripts/' \
                       f'hiperta_r0_to_dl1lstchain.py -o {output_dir} -k {keep_rta_file} {cc}"'

            # recover or not the jobid depending of the workflow mode
            if not flag_full_workflow:

                cmd = f'sbatch -p short -e {jobe} -o {jobo} {base_cmd} {os.path.join(dir_lists, file)}'

                # print(cmd)
                os.system(cmd)

            else:  # flag_full_workflow == True !
                job_name = {'electron': 'e_RTA-r0dl1',
                            'gamma': 'g_RTA-r0dl1',
                            'gamma-diffuse': 'gd_RTA-r0dl1',
                            'proton': 'p_RTA-r0dl1',
                            'gamma_off0.0deg': 'g0.0_RTA-r0dl1',
                            'gamma_off0.4deg': 'g0.4_RTA-r0dl1'
                            }

                if particle == 'proton':
                    queue = 'long'
                else:
                    queue = 'long'  # TODO change to short after prod5 check

                cmd = f'sbatch --parsable -p {queue} -J {job_name[particle]} ' \
                      f'-e {jobe} -o {jobo} {base_cmd} {os.path.join(dir_lists, file)}'

                jobid = os.popen(cmd).read().strip('\n')
                jobids_RTA_r0_dl1_reorganized.append(jobid)

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

    # copy this script itself into logs
    shutil.copyfile(__file__, os.path.join(RUNNING_DIR, os.path.basename(__file__)))
    # copy config file into logs
    if config_rta_file is not None:
        shutil.copy(config_rta_file, os.path.join(RUNNING_DIR, os.path.basename(config_rta_file)))
    if lst_config is not None:
        shutil.copy(lst_config, os.path.join(RUNNING_DIR, os.path.basename(lst_config)))

    # save file lists into logs
    shutil.move('testing.list', os.path.join(RUNNING_DIR, 'testing.list'))
    shutil.move('training.list', os.path.join(RUNNING_DIR, 'training.list'))

    # create log dictionary and return it if IN workflow mode
    if flag_full_workflow:
        return jobid2log, jobids_RTA_r0_dl1_reorganized

    else:
        print("\n ==== END {} ==== \n".format(os.path.basename(__file__)))


if __name__ == '__main__':
    args = parser.parse_args()
    main(args.input_dir,
         args.config_rta_file,
         args.train_test_ratio,
         args.random_seed,
         args.n_files_per_dl1,
         args.prod_id,
         args.keep_rta_file
         )
