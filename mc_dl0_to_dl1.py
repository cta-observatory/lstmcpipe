#!/usr//bin/env python

# T. Vuillaume, 20/06/2019

# Choose the selected options


## TODO:
#   - clean the code
#   - prints --> logs
#   - main
#   - test it

####################################### OPTIONS #######################################

## env ##
# source / fefs / aswg / software / scripts / source_env.sh
# lstchain_repo = "/fefs/home/thomas.vuillaume/software/cta-observatory/cta-lstchain"


import sys
import os
from distutils.util import strtobool
import shutil
import random


DL0_DATA_DIR = sys.argv[1]


### global variables - do not change unless you know what you are doing
BASE_DIR = '/fefs/aswg/'
PROD_ID = 'v00'
TRAIN_TEST_RATIO = 0.25
RANDOM_SEED = 42




def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        else:
            try:
                return bool(strtobool(choice))
            except:
                sys.stdout.write("Please respond with 'yes' or 'no' "
                                 "(or 'y' or 'n').\n")


def get_metadata_from_mc_data_path(data_path):
    '''
    A mc data path is always `/BASE_DIR/data/mc/dlx/<date>/particle_type/pointing/`

    Returns
    -------
    dict
    '''

    if not data_path.startswith(BASE_DIR):
        data_path = os.path.join(BASE_DIR, data_path)
    if not os.path.exists(BASE_DIR):
        raise ValueError("The input path does not exists")

    split = data_path.split('/')
    if split[-5] != 'mc':
        raise ValueError("The path structure does not correspond to the intended one")

    dic = {
        'pointing': split[-1],
        'particle_type': split[-2],
        'date': split[-3],
        'data_level': split[-4],
    }
    return dic


def check_data_path(data_path):
    if not os.path.exists(data_path):
        raise ValueError("The input directory must exist")
    if len(get_input_filelist(data_path)) == 0:
        raise ValueError("The input directory is empty")
    if not data_path.startswith(BASE_DIR):
        raise ValueError("The root directory for the data is supposed to be {}".format(BASE_DIR))


def make_output_data_dirs(data_path):

    check_data_path(data_path=data_path)
    for i in [1, 2, 3]:
        new_path = data_path.replaces('dl0', 'dl{}'.format(i))
        new_path = os.path.join(new_path, PROD_ID)
        os.makedirs(new_path, exist_ok=True)

def make_dl1_output_dir(data_path):
    new_path = data_path.replaces('dl0', 'dl{}'.format(i))
    new_path = os.path.join(new_path, PROD_ID)
    os.makedirs(new_path, exist_ok=True)


def get_input_filelist(data_path):
    return [os.abspath(os.path.join(data_path, f)) for f in os.listdir(data_path) if os.path.isfile(f)]


if __name__ == '__main__':

    check_data_path(DL0_DATA_DIR)

    # make_output_data_dirs(DL0_DATA_DIR)
    DL1_DATA_DIR = os.path.join(DL0_DATA_DIR.replaces('dl0', 'dl1'), PROD_ID)
    os.makedirs(DL1_DATA_DIR)

    raw_files_list = get_input_filelist(DL0_DATA_DIR)
    random.seed(RANDOM_SEED)
    random.shuffle(raw_files_list)

    number_files = len(raw_files_list)
    ntrain = int(number_files * TRAIN_TEST_RATIO)
    ntest = number_files - ntrain

    training_list = raw_files_list[:ntrain]
    testing_list = raw_files_list[ntrain:]

    print("{} raw files".format(number_files))
    print("{} files in training dataset".format(ntrain))
    print("{} files in test dataset".format(ntest))

    with open('training.list', 'w+') as newfile:
        for f in training_list:
            newfile.write(f)
            newfile.write('\n')

    with open('testing.list', 'w+') as testfile:
        for f in testing_list:
            newfile.write(f)
            newfile.write('\n')


    RUNNING_DIR = os.path.join(DL0_DATA_DIR.replaces('DL0', 'running_analysis'), PROD_ID)
    # LOG_DIR = os.path.join(DL0_DATA_DIR.replaces('DL0', 'analysis_logs'), PROD_ID) - this one should be handled by the cleaning script
    JOB_LOGS = os.path.join(RUNNING_DIR, 'job_logs')
    # DIR_LISTS_BASE = os.path.join(RUNNING_DIR, 'file_lists')

    def check_and_make_dir(dir):
        if os.path.exists(dir) and os.listdir(dir)==[]:
            clean = query_yes_no("The directory {} is not empty. Do you want to remove its content?", default='yes')
            if clean:
                shutil.rmtree(dir)
        os.makedirs(dir, exist_ok=True)

    for dir in [DL1_DATA_DIR, RUNNING_DIR, JOB_LOGS]:
        check_and_make_dir(dir)


    NFILES_PER_DL1 = 10


    ## dumping the training and testing lists and spliting them in sublists for parallel jobs

    for l in 'training', 'testing':
        if l == 'training':
            list = training_list
        else:
            list = testing_list
        dir_lists = os.path.join(RUNNING_DIR, 'file_lists_'+l)
        output_dir = os.path.join(RUNNING_DIR, l)
        check_and_make_dir(dir_lists)
        check_and_make_dir(output_dir)
        print("output dir: ", output_dir)

        number_of_sublists = len(list)//NFILES_PER_DL1+int(len(list)%NFILES_PER_DL1>0)
        for i in range(number_of_sublists):
            output_file = os.path.join(dir_lists, '/{}.list'.format(i))
            with open(output_file, 'w+') as out:
                for line in list[i*NFILES_PER_DL1:NFILES_PER_DL1*(i+1)]:
                    out.write(line)
                    out.write('\n')
            print('{} files generated for {} list'.format(number_of_sublists, l))


    ### LSTCHAIN ###
    counter = 0

    for file in os.listdir(dir_lists):
        jobo = os.path.join(JOB_LOGS, "job{}.o".format(counter))
        jobe = os.path.join(JOB_LOGS, "job{}.e".format(counter))
        cmd = 'sbatch -e {} -o {} lstchain_core.sh {} {}'.format(
            jobe,
            jobo,
            os.path.join(dir_lists, file),
            DL1_DATA_DIR,
        )
        # os.system(cmd)
        print(cmd)
        counter+=1

        shutil.copyfile(sys.argv[0], RUNNING_DIR)




## protons ##
# raw_data_dir="/fefs/aswg/data/mc/DL0/20190415/proton/south_pointing"
# output_dir_base="/fefs/aswg/data/mc/DL1/20190822/proton/south_pointing"
# nfiles_per_job="10"

## gamma diffuse ##
# raw_data_dir="/fefs/aswg/data/mc/DL0/20190415/gamma-diffuse/south_pointing"
# output_dir_base="/fefs/aswg/data/mc/DL1/20190822/gamma-diffuse/south_pointing"
# nfiles_per_job="10"


## gamma ps ##
# raw_data_dir = "/fefs/aswg/data/mc/DL0/20190415/gamma/south_pointing"
# output_dir_base = "/fefs/aswg/data/mc/DL1/20190822/gamma/south_pointing"
# nfiles_per_job = "2"
#
# inv_test_ratio = 2  # the train/test split ratio is 1/inv_test_ratio
#
# #######################################################################################
#
#
