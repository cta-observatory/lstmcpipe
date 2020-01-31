#!/usr//bin/env python

# T. Vuillaume,
# Modifications by E. Garcis
# Code to reduce R0 data to DL1 onsite (La Palma cluster)

import random
import argparse
import calendar
import lstchain
from lstchain.io.data_management import *

parser = argparse.ArgumentParser(description="MC R0 to DL1")

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
                    default=0.25
                    )

parser.add_argument('--random_seed', '-seed', action='store', type=str,
                    dest='random_seed',
                    help='Random seed for random processes',
                    default=42,
                    )

parser.add_argument('--n_files_per_dl1', '-nfdl1', action='store', type=str,
                    dest='n_files_per_dl1',
                    help='Number of input files merged in one DL1. If 0, the number of files per DL1 is computed '
                         'based on the size of the DL0 files and the expected reduction factor of 5 '
                         'to obtain DL1 files of ~100 MB. Else, use fixed number of files',
                    default=0,
                    )

parser.add_argument('--prod_id', action='store', type=str,
                    dest='prod_id',
                    help="Production ID. If None, _v00 will be used, indicating an official base production",
                    default=None,
                    )

parser.add_argument('--flag_workflow_mode', '-flag', type=str,
                    dest='flag_workflow_mode',
                    help='Flag to indicate if the code is run within the r0_to_dl2 full workflow, and thus some '
                         'arguments must be returned for the following steps.',
                    default=False
                    )


def main(input_dir, config_file=None, train_test_ratio=0.25, random_seed=42, n_files_per_dl1=0,
         prod_id=None, flag_workflow_mode=False):

    flag_full_workflow = flag_workflow_mode

    today = calendar.datetime.date.today()
    base_prod_id = f'{today.year:04d}{today.month:02d}{today.day:02d}_v{lstchain.__version__}'
    suffix_id = '_v00' if prod_id is None else '_{}'.format(prod_id)
    PROD_ID = base_prod_id + suffix_id
    TRAIN_TEST_RATIO = float(train_test_ratio)
    RANDOM_SEED = random_seed
    NFILES_PER_DL1 = n_files_per_dl1

    DESIRED_DL1_SIZE_MB = 1000

    DL0_DATA_DIR = input_dir

    print("\n ==== START {} ==== \n".format(sys.argv[0]))

    print("Working on DL0 files in {}".format(DL0_DATA_DIR))

    check_data_path(DL0_DATA_DIR)

    raw_files_list = get_input_filelist(DL0_DATA_DIR)

    if NFILES_PER_DL1 == 0:
        size_dl0 = os.stat(raw_files_list[0]).st_size / 1e6
        reduction_dl0_dl1 = 5
        size_dl1 = size_dl0 / reduction_dl0_dl1
        NFILES_PER_DL1 = max(1, int(DESIRED_DL1_SIZE_MB / size_dl1))

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

    RUNNING_DIR = os.path.join(DL0_DATA_DIR.replace('DL0', 'running_analysis'), PROD_ID)

    JOB_LOGS = os.path.join(RUNNING_DIR, 'job_logs')
    # DIR_LISTS_BASE = os.path.join(RUNNING_DIR, 'file_lists')
    DL1_DATA_DIR = os.path.join(RUNNING_DIR, 'DL1')
    # ADD CLEAN QUESTION

    print("\tRUNNING_DIR: \t", RUNNING_DIR)
    print("\tJOB_LOGS DIR: \t", JOB_LOGS)
    print("\tDL1 DATA DIR: \t", DL1_DATA_DIR)

    for directory in [RUNNING_DIR, DL1_DATA_DIR, JOB_LOGS]:
        check_and_make_dir(directory)

    # dumping the training and testing lists and spliting them in sublists for parallel jobs

    for set_type in 'training', 'testing':
        if set_type == 'training':
            list = training_list
        else:
            list = testing_list
        dir_lists = os.path.join(RUNNING_DIR, 'file_lists_' + set_type)
        output_dir = os.path.join(RUNNING_DIR, 'DL1')
        output_dir = os.path.join(output_dir, set_type)
        check_and_make_dir(dir_lists)
        check_and_make_dir(output_dir)
        print("\toutput dir: \t", output_dir)

        number_of_sublists = len(list) // NFILES_PER_DL1 + int(len(list) % NFILES_PER_DL1 > 0)
        for i in range(number_of_sublists):
            output_file = os.path.join(dir_lists, '{}_{}.list'.format(set_type, i))
            with open(output_file, 'w+') as out:
                for line in list[i * NFILES_PER_DL1:NFILES_PER_DL1 * (i + 1)]:
                    out.write(line)
                    out.write('\n')
        print('\t{} files generated for {} list'.format(number_of_sublists, set_type))

        ### LSTCHAIN ###
        counter = 0
        jobid2cmd = {}
        jobid2outfile = {}
        jobid2errfile = {}
        jobid2partype = {}

        for file in os.listdir(dir_lists):
            if set_type == 'training':
                jobo = os.path.join(JOB_LOGS, "job{}_train.o".format(counter))
                jobe = os.path.join(JOB_LOGS, "job{}_train.e".format(counter))
            else:
                jobo = os.path.join(JOB_LOGS, "job{}_test.o".format(counter))
                jobe = os.path.join(JOB_LOGS, "job{}_test.e".format(counter))
            cc = ' -conf {}'.format(config_file) if config_file is not None else ' '
            base_cmd = 'core_list.sh "lstchain_mc_r0_to_dl1 -o {} {}"'.format(output_dir, cc)
            cmd = 'sbatch --parsable -e {} -o {} {} {}'.format(jobe, jobo, base_cmd, os.path.join(dir_lists, file))

            # the command os.popen() INDEED runs the command !
            jobid = os.popen(cmd).read().split('\n')

            # Fill the dictionaries if IN workflow mode
            if flag_full_workflow:
                jobid2cmd[jobid] = cmd
                jobid2outfile[jobid] = jobo
                jobid2errfile[jobid] = jobe
                jobid2partype[jobid] = DL0_DATA_DIR.split('/')[-2]  # Hardcoded, maybe if with 4 elif s ?

            # If you want to see the submitted jobs
            print(f'\t\tSubmitted batch job {jobid}')
            counter += 1

        print("\n\t{} jobs submitted".format(counter))

    # copy this script itself into logs
    shutil.copyfile(sys.argv[0], os.path.join(RUNNING_DIR, os.path.basename(sys.argv[0])))
    # copy config file into logs
    if config_file is not None:
        shutil.copy(config_file, os.path.join(RUNNING_DIR, os.path.basename(config_file)))

    # save file lists into logs
    shutil.move('testing.list', os.path.join(RUNNING_DIR, 'testing.list'))
    shutil.move('training.list', os.path.join(RUNNING_DIR, 'training.list'))

    print("\n ==== END {} ==== \n".format(sys.argv[0]))

    # create log dictionary and return it if IN workflow mode
    if flag_full_workflow:
        jobid2log = {}
        for key in jobid2cmd.keys():
            jobid2log[key] = {}
            jobid2log[key]['particle'] = jobid2partype[key]
            jobid2log[key]['sbatch_command'] = jobid2cmd[key]
            jobid2log[key]['jobe_path'] = jobid2errfile[key]
            jobid2log[key]['jobo_path'] = jobid2outfile[key]

        return jobid2log


if __name__ == '__main__':
    args = parser.parse_args()
    main(args.input_dir,
         args.config_file,
         args.train_test_ratio,
         args.random_seed,
         args.n_files_per_dl1,
         args.prod_id,
         args.flag_workflow_mode
         )
