#!/usr//bin/env python3

# T. Vuillaume, 12/09/2019
# merge and copy DL1 data after 


# lstchain_dir="/home/thomas.vuillaume/software/cta-observatory/cta-lstchain"


# input_dir='/fefs/aswg/data/mc/DL1/20190822/gamma-diffuse/south_pointing/training/'
# output_file='/fefs/aswg/data/mc/DL1/20190822/gamma-diffuse/south_pointing/dl1_20190822_proton_training.h5'

# # input_dir=$1
# # output_file=$2

# python $lstchain_dir/scripts/merge_hdf5_files.py -d $input_dir -o $output_file




# 1. check job_logs
# 2. check that all files have been created in DL1 based on training and testing lists
# 3. move DL1 files in final place
# 4. merge DL1 files
# 5. move running_dir 


import os
import sys
from data_management import *


input_dir = '/Users/thomasvuillaume/Work/CTA/Data/test_lst_script/running_analysis/70deg20deg/v00'

JOB_LOGS = os.path.join(input_dir, 'job_logs')
training_filelist = os.path.join(input_dir, 'training.list')
testing_filelist = os.path.join(input_dir, 'testing.list')
running_DL1_dir = os.path.join(input_dir, 'DL1')
DL1_training_dir = os.path.join(running_DL1_dir, 'training')
DL1_testing_dir = os.path.join(running_DL1_dir, 'testing')
final_DL1_dir = input_dir.replace('running_analysis', 'DL1')


check_and_make_dir(final_DL1_dir)


def check_files_in_dir_from_file(dir, file):
    """
    Check that a list of files from a file exist in a dir

    Parameters
    ----------
    dir
    file

    Returns
    -------

    """
    with open(file) as f:
        lines = f.readlines()

    files_in_dir = os.listdir(dir)
    files_not_in_dir = []
    for line in lines:
        if os.path.basename(line) not in files_in_dir:
            files_not_in_dir.append(os.path.basename(line))

    return files_not_in_dir



# 1. check job logs
check_job_logs(JOB_LOGS)


# 2. check that all files have been created in DL1 based on training and testing lists
tf = check_files_in_dir_from_file(DL1_training_dir, training_filelist)
if  tf != []:
    query_yes_no("{} files from the training list are not in the `DL1/training` directory:\n{} "
                 "Continue ?".format(len(tf),tf))

tf = check_files_in_dir_from_file(DL1_testing_dir, testing_filelist)
if tf != []:
    query_yes_no("{} files from the testing list are not in the `DL1/training` directory:\n{} "
                 "Continue ?".format(len(tf), tf))

# 3. merge DL1 files
#TODO : after merging of DL1 files PR in lstchain

# 4. move DL1 files in final place
shutil.move(running_DL1_dir, final_DL1_dir)

# 5. move running_dir as logs
destination_dir = input_dir.replace('running_analysis', 'analysis_logs')
shutil.move(input_dir, destination_dir)


print("End of DL1 merging and cleaning. You may find the saved files in in {}".format(destination_dir))
