#!/usr//bin/env python

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
from .data_management import *


input_dir = '/fefs/aswg/data/mc/running_analysis/20190415/proton/south_pointing/v00/'
job_logs = os.path.join(input_dir, 'job_logs')                


