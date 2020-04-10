#!/usr//bin/env python

# E. Garcia, Jan '20
#
# Full workflow from r0 to dl3.
#  wraps together the individual scripts of
#   - onsite_mc_r0_to_dl1
#   - onsite_mc_merge_and_copy_dl1
#   - onsite_mc_train
#   - onsite_mc_dl1_to_dl2
#   - TODO onsite_mc_dl2_to_dl3
#
# usage:
# > python onsite_mc_r0_to_dl3.py [-conf_lst LSTCHAIN_CONFIG_FILE] [-conf_rta RTA_CONFIG_FILE] [--prod_id PROD_ID]
#
#   The input_dir is set in the global variable `DL0_DATA_DIR`

import os
import sys
import argparse
import calendar
import lstchain
from data_management import query_continue
from workflow_management import (batch_r0_to_dl1,
                                 batch_r0_to_dl1_rta,
                                 batch_merge_and_copy_dl1,
                                 batch_train_pipe,
                                 batch_dl1_to_dl2,
                                 save_log_to_file,
                                 create_dict_with_filenames
                                 )

#######################################################################################################################
#######################################################################################################################
# choose between :
#  'lst' for lstchain-like workflow  OR
#  'rta' for HiPeRTA-like workflow
WORKFLOW_KIND = 'lst'

BASE_PATH = '/fefs/aswg/data/mc'
# BASE_PATH = '/fefs/aswg/workspace/thomas.vuillaume/mchdf5/' ##

OBS_DATE = '20190415'
POINTING = 'south_pointing'
ALL_PARTICLES = ['electron', 'gamma', 'gamma-diffuse', 'proton']

# source env onsite - can be changed for custom install
source_env = 'source /fefs/aswg/software/virtual_env/.bashrc; conda activate cta;'  # By default

# run and batch all the steps of the code (see above)
DO_r0_to_dl1 = True
DO_merge_and_copy = True
DO_TRAIN_PIPE = True
DO_dl1_to_dl2 = True
# DO_dl2_to_dl3 = True

#######################################################################################################################
#######################################################################################################################


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="MC R0 to DL3 full workflow")

    parser.add_argument('--config_file_lst', '-conf_lst', action='store', type=str,
                        dest='config_file_lst',
                        help='Path to a lstchain-like configuration file. '
                             'RF classifier and regressor arguments must be declared here !',
                        default=None
                        )

    parser.add_argument('--config_file_rta', '-conf_rta', action='store', type=str,
                        dest='config_file_rta',
                        help='Path to a HiPeRTA-like configuration file.'
                             'Only to be declared if WORKFLOW_KIND = "rta". ',
                        default=None
                        )

    parser.add_argument('--prod_id', action='store', type=str,
                        dest='prod_id',
                        help="Production ID. If None, _v00 will be used, indicating an official base production",
                        default=None,
                        )
    args = parser.parse_args()

    # Global variables

    today = calendar.datetime.date.today()
    if WORKFLOW_KIND == 'lst':
        base_prod_id = f'{today.year:04d}{today.month:02d}{today.day:02d}_v{lstchain.__version__}'
    elif WORKFLOW_KIND == 'rta':
        base_prod_id = f'{today.year:04d}{today.month:02d}{today.day:02d}_vRTA_v{lstchain.__version__}'
    suffix_id = '_v00' if args.prod_id is None else '_{}'.format(args.prod_id)

    PROD_ID = base_prod_id + suffix_id
    RUNNING_ANALYSIS_DIR = os.path.join(BASE_PATH, 'running_analysis', OBS_DATE, '{}', POINTING, PROD_ID)
    ANALYSIS_LOG_DIR = os.path.join(BASE_PATH, 'analysis_logs', OBS_DATE, '{}', POINTING, PROD_ID)
    if WORKFLOW_KIND == 'lst':
        DL0_DATA_DIR = os.path.join(BASE_PATH, 'DL0', OBS_DATE, '{}', POINTING)
    elif WORKFLOW_KIND == 'rta':
        DL0_DATA_DIR = os.path.join(BASE_PATH, 'R1', OBS_DATE, '{}', POINTING)  ##
    DL1_DATA_DIR = os.path.join(BASE_PATH, 'DL1', OBS_DATE, '{}', POINTING, PROD_ID)

    # #################################################
    # ########### Beginning of the workflow ###########
    # #################################################

    print(f'\nThe full r0 to dl3 workflow is going to be run at \n\n   '
          f'\t{DL0_DATA_DIR.format(str("""{""") + ",".join(ALL_PARTICLES) + str("""}"""))}\n\n'
          f'The following directories and all the information within them will be either created or overwritten:\n'
          f'(subdirectories with a same PROD_ID and analysed the same day)\n\n'
          f'\t{RUNNING_ANALYSIS_DIR.format(str("""{""") + ",".join(ALL_PARTICLES) + str("""}"""))}\n'
          f'\t{DL1_DATA_DIR.format(str("""{""") + ",".join(ALL_PARTICLES) + str("""}"""))}\n'
          f'\t{DL1_DATA_DIR.format(str("""{""") + ",".join(ALL_PARTICLES) + str("""}""")).replace("DL1", "DL2")}\n'
          f'\t{ANALYSIS_LOG_DIR.format(str("""{""") + ",".join(ALL_PARTICLES) + str("""}"""))}\n'
          f'\n\tPROD_ID to be used:{PROD_ID}\n'
          )

    query_continue('Are you sure ?')

    log_file = './log_FULL_onsite_mc_r0_to_dl3_v{}_{}.txt'.format(WORKFLOW_KIND, suffix_id)
    debug_file = './log_reduced_v{}_{}.txt'.format(WORKFLOW_KIND, suffix_id)

    # First time opening the log, otherwise --> erase
    if os.path.exists(log_file):
        os.remove(log_file)
    if os.path.exists(debug_file):
        os.remove(debug_file)

    # R0/1 to DL1
    if DO_r0_to_dl1:

        if WORKFLOW_KIND == 'lst':
            log_batch_r0_dl1, debug = batch_r0_to_dl1(DL0_DATA_DIR,
                                                      args.config_file_lst,
                                                      PROD_ID,
                                                      ALL_PARTICLES)
        elif WORKFLOW_KIND == 'rta':
            log_batch_r0_dl1, debug = batch_r0_to_dl1_rta(DL0_DATA_DIR,
                                                          args.config_file_rta,
                                                          PROD_ID,
                                                          ALL_PARTICLES)
        else:
            sys.exit("Choose a valid WORKFLOW_KIND : 'lst' OR 'rta' ")

        save_log_to_file(log_batch_r0_dl1, log_file, 'r0_to_dl1')
        save_log_to_file(debug, debug_file, 'r0_to_dl1')

    # Merge,copy and move DL1 files
    if DO_merge_and_copy:
        log_batch_merge_and_copy, jobs_to_train, jobs_all_dl1_finished, debug = batch_merge_and_copy_dl1(
            RUNNING_ANALYSIS_DIR,
            log_batch_r0_dl1,
            ALL_PARTICLES,
            flag_rta_or_lst=WORKFLOW_KIND)

        save_log_to_file(log_batch_merge_and_copy, log_file, 'merge_and_copy_dl1')
        save_log_to_file(debug, debug_file, 'merge_and_copy_dl1')
    else:
        # Create just the needed dictionary inputs (dl1 files must exist !)
        log_batch_merge_and_copy = create_dict_with_filenames(DL1_DATA_DIR, ALL_PARTICLES)
        jobs_to_train = ''
        jobs_all_dl1_finished = ''

    # Train pipe
    if DO_TRAIN_PIPE:
        log_batch_train_pipe, job_from_train_pipe, model_dir, debug = batch_train_pipe(log_batch_merge_and_copy,
                                                                                       args.config_file_lst,
                                                                                       jobs_to_train,
                                                                                       source_env=source_env
                                                                                       )

        save_log_to_file(log_batch_train_pipe, log_file, 'train_pipe')
        save_log_to_file(debug, debug_file, 'train_pipe')
    else:
        job_from_train_pipe = ''
        model_dir = os.path.join(BASE_PATH, 'models', OBS_DATE, POINTING, PROD_ID)
        log_batch_merge_and_copy = create_dict_with_filenames(DL1_DATA_DIR, ALL_PARTICLES)

    # DL1 to DL2 stage
    if DO_dl1_to_dl2:
        log_batch_dl1_to_dl2, jobs_4_dl2_to_dl3, debug = batch_dl1_to_dl2(DL1_DATA_DIR,
                                                                          model_dir,
                                                                          args.config_file_lst,
                                                                          job_from_train_pipe,  # Single jobid frm train
                                                                          jobs_all_dl1_finished,  # jobids from merge
                                                                          log_batch_merge_and_copy,  # finale dl1 names
                                                                          ALL_PARTICLES,
                                                                          source_env=source_env
                                                                          )

        save_log_to_file(log_batch_dl1_to_dl2, log_file, 'dl1_to_dl2')
        save_log_to_file(debug, debug_file, 'dl1_to_dl2')

