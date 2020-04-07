#!/usr//bin/env python

# E. Garcia, March '20 -  while quarantine
#
# Full workflow from r0 to dl3 - HiPeRTA version
#  wraps together the individual scripts of
#   - onsite_mc_r0_to_dl1 --> hiperta_r0_to_dl1 !
#   - onsite_mc_merge_and_copy_dl1
#   - onsite_mc_train
#   - onsite_mc_dl1_to_dl2
#   - TODO onsite_mc_dl2_to_dl3
#
# usage:
# > python onsite_mc_r0_to_dl3_hiperta.py [-conf_rta CONFIG_FILE_RTA] [-conf_lst CONFIG_FILE_LST] [--prod_id PROD_ID]
#
#   The input_dir is set in the global variable `DL0_DATA_DIR`

import argparse
import calendar
import lstchain
import glob
import pprint
from onsite_mc_hiperta_r0_to_dl1lstchain import main as r0_to_dl1_rta
from onsite_mc_merge_and_copy_dl1 import main as merge_and_copy_dl1
from onsite_mc_train import main as train_pipe
from onsite_mc_dl1_to_dl2 import main as dl1_to_dl2
from data_management import *

#######################################################################################################################
#######################################################################################################################
#BASE_PATH = '/fefs/aswg/data/mc'
# TODO mark for to date version of workflow-rta
BASE_PATH = '/fefs/aswg/workspace/thomas.vuillaume/mchdf5/'

OBS_DATE = '20190415'
POINTING = 'south_pointing'
ALL_PARTICLES = ['electron', 'gamma', 'gamma-diffuse', 'proton']

# source env onsite - can be changed for custom install - Used at 'r0_dl1' (inside the onsite_*) and 'train' stages
# This env MUST be the same for training and dl1_to_dl2 !
source_env = 'source /fefs/aswg/software/virtual_env/.bashrc; conda activate cta;'  # By default


#######################################################################################################################
#######################################################################################################################

def check_and_load_configs(config_rta, config_lst):
    if config_rta is None:
        config_rta = os.path.join(os.path.dirname(__file__), "./hiperta_standard_config.txt")
    else:
        pass

    if config_lst is None:
        config_lst = os.path.join(os.path.dirname(__file__), "./lstchain_standard_config.json")
    else:
        pass

    return config_rta, config_lst


def create_dict_with_filenames(dl1_directory):
    """
    Function that creates a dictionary with the filenames of all the final dl1 files (the same is done
    in the merge_and_copy_dl1 function) so that it can be passed to the rest of the stages, in case the full workflow
    it is not run from the start.

    Parameters
    ----------
    dl1_directory: str
        path to the dl1 directory files

    Returns
    -------
    dl1_filename_directory : dict
        dictionary with the name (and absolute path) of the dl1 files with the name of the particles set as key of the
        dictionary

             dl1_filename_directory[particle].keys() = ['train_path_and_outname_dl1', 'test_path_and_outname_dl1']
    """
    dl1_filename_directory = {}

    for particle in ALL_PARTICLES:
        dl1_filename_directory[particle] = {'training': {}, 'testing': {}}
        dl1_filename_directory[particle]['training']['train_path_and_outname_dl1'] = glob.glob(os.path.join(
            dl1_directory.format(particle), '*training*.h5'))[0]
        dl1_filename_directory[particle]['testing']['test_path_and_outname_dl1'] = glob.glob(os.path.join(
            dl1_directory.format(particle), '*testing*.h5'))[0]

    return dl1_filename_directory


def save_log_to_file(dictionary, output_file, workflow_step=None):
    """
    Dumps a dictionary (log) to a file

    Parameters
    ----------
    dictionary : dict
        The dictionary to be dumped to a file
    output_file : str
        Output file to store the log
    workflow_step : str
        Step of the workflow, to be recorded in the dict

    Returns
    -------
        None
    """
    if workflow_step is None:
        workflow_step = '--'
    with open(output_file, 'a+') as fout:
        fout.write('\n\n  *******************************************\n')
        fout.write(f'   *** Log from the {workflow_step} stage \n')
        fout.write('  *******************************************\n')
        fout.write(pprint.pformat(dictionary))


def batch_dl1_to_dl2(dl1_directory, path_to_models, config_file, jobid_from_training, jobids_from_merge,
                     dict_with_dl1_paths):
    log_dl1_to_dl2 = {}
    jobid_4_dl2_to_dl3 = []
    debug_log = {}

    for particle in ALL_PARTICLES:
        log, jobid = dl1_to_dl2(dl1_directory.format(particle),
                                path_models=path_to_models,
                                config_file=config_file,
                                flag_full_workflow=True,
                                particle=particle,
                                wait_jobid_train_pipe=jobid_from_training,
                                wait_jobids_merge=jobids_from_merge,
                                dictionary_with_dl1_paths=dict_with_dl1_paths,
                                source_environment=source_env
                                )

        log_dl1_to_dl2.update(log)
        jobid_4_dl2_to_dl3.append(jobid)

        debug_log[jobid] = f'{particle} job from dl1_to_dl2 that depends both on : {jobid_from_training} training ' \
                           f'jobs AND from {jobids_from_merge} merge_and_copy_dl1 jobs'

    jobid_4_dl2_to_dl3 = ','.join(jobid_4_dl2_to_dl3)

    return log_dl1_to_dl2, jobid_4_dl2_to_dl3, debug_log


def batch_train_pipe(log_from_merge, config_file, jobids_from_merge):
    debug_log = {}

    gamma_dl1_train_file = log_from_merge['gamma-diffuse']['training']['train_path_and_outname_dl1']
    proton_dl1_train_file = log_from_merge['proton']['training']['train_path_and_outname_dl1']

    log_train, jobid_4_dl1_to_dl2, model_path = train_pipe(gamma_dl1_train_file,
                                                           proton_dl1_train_file,
                                                           config_file=config_file,
                                                           source_environment=source_env,
                                                           flag_full_workflow=True,
                                                           wait_ids_proton_and_gammas=jobids_from_merge
                                                           )

    debug_log[jobid_4_dl1_to_dl2] = f'The single jobid from train_pipe that depends of {jobids_from_merge} - merge' \
                                    f'_and_copy jobids'

    return log_train, jobid_4_dl1_to_dl2, model_path, debug_log


def batch_merge_and_copy_dl1(running_analysis_dir, log_jobs_from_r0_to_dl1):
    log_merge_and_copy = {}
    jobid_4_train = []
    all_jobs_from_merge = []
    debug_log = {}

    for particle in ALL_PARTICLES:
        log, jobid, jobid_debug = merge_and_copy_dl1(running_analysis_dir.format(particle),
                                                     flag_full_workflow=True,
                                                     particle2jobs_dict=log_jobs_from_r0_to_dl1,
                                                     particle=particle
                                                     )

        log_merge_and_copy.update(log)
        all_jobs_from_merge.append(jobid)
        if particle == 'gamma-diffuse' or particle == 'proton':
            jobid_4_train.append(jobid)

        debug_log[jobid] = f'{particle} merge_and_copy-jobs that will go to dl1_to_dl2. They depend on the following ' \
                           f'{log_jobs_from_r0_to_dl1[particle]} r0_t0_dl1 jobs.'
        debug_log[jobid_debug] = f'All the {particle} jobs that have been launched in merge_and_copy_dl1.'

    jobid_4_train = ','.join(jobid_4_train)
    all_jobs_from_merge = ','.join(all_jobs_from_merge)

    return log_merge_and_copy, jobid_4_train, all_jobs_from_merge, debug_log


def batch_r0_to_dl1_rta(input_dir, conf_file, prod_id):
    full_log = {'jobid_log': {}}
    debug_log = {}

    for particle in ALL_PARTICLES:
        log, jobids_by_particle = r0_to_dl1_rta(input_dir.format(particle),
                                                config_file=conf_file,
                                                prod_id=prod_id,
                                                flag_full_workflow=True
                                                )

        # Create jobid to full log information dictionary.
        # And the inverse dictionary, particle to the list of all the jobids of that same particle
        full_log['jobid_log'].update(log)
        full_log[particle] = jobids_by_particle

        for jid in jobids_by_particle:
            debug_log[jid] = f'{particle} job from r0_to_dl1_RTA'

    return full_log, debug_log


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="MC R0 to DL3 full workflow - HiPeCTA r0_to_dl1 version !!")

    parser.add_argument('--config_file_rta', '-conf_rta', action='store', type=str,
                        dest='config_file_rta',
                        help='Path to a hipeCTA-like configuration file.',
                        default=None
                        )

    parser.add_argument('--config_file_lst', '-conf_lst', action='store', type=str,
                        dest='config_file_lst',
                        help='Path to a lstchain-like configuration file. '
                             'RF classifier and regressor arguments must be declared here !',
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
    base_prod_id = f'{today.year:04d}{today.month:02d}{today.day:02d}_RTA_v00_lstchain_{lstchain.__version__}'
    suffix_id = '_v00' if args.prod_id is None else '_{}'.format(args.prod_id)

    # Missing global variables, some dependent of args.

    PROD_ID = base_prod_id + suffix_id
    RUNNING_ANALYSIS_DIR = os.path.join(BASE_PATH, 'running_analysis', OBS_DATE, '{}', POINTING, PROD_ID)
    ANALYSIS_LOG_DIR = os.path.join(BASE_PATH, 'analysis_logs', OBS_DATE, '{}', POINTING, PROD_ID)
    # DL0_DATA_DIR = os.path.join(BASE_PATH, 'DL0', OBS_DATE, '{}', POINTING)
    #
    # TODO mark for to date version of workflow-rta
    DL0_DATA_DIR = os.path.join(BASE_PATH, 'R1', OBS_DATE, '{}', POINTING)
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
          )

    query_continue('Are you sure ?')

    log_file = './log_FULL_onsite_mc_r0_to_dl3_vRTA.txt'
    debug_file = './log_reduced_vRTA.txt'

    # First time opening the log --> erase
    if os.path.exists(log_file):
        os.remove(log_file)
    if os.path.exists(debug_file):
        os.remove(debug_file)

    # check and load standard configs if None
    rta_config, lst_config = check_and_load_configs(args.config_file_rta,
                                                    args.config_file_lst
                                                    )

    # r0 to dl1 - RTA version
    log_batch_r0_dl1, debug_r0_dl1 = batch_r0_to_dl1_rta(DL0_DATA_DIR,
                                                         rta_config,
                                                         args.prod_id
                                                         )
    save_log_to_file(log_batch_r0_dl1, log_file, 'r0_to_dl1_vRTA')
    save_log_to_file(debug_r0_dl1, debug_file, 'r0_to_dl1_vRTA')

    # Merge and copy
    log_batch_merge_and_copy, jobs_to_train, jobs_all_dl1_finished, \
     debug_merge = batch_merge_and_copy_dl1(RUNNING_ANALYSIS_DIR,
                                            log_batch_r0_dl1
                                            )
    save_log_to_file(log_batch_merge_and_copy, log_file, 'merge_and_copy_dl1')
    save_log_to_file(debug_merge, debug_file, 'merge_and_copy_dl1')

    # Train pipe
    log_batch_train_pipe, job_to_dl1_dl2, model_dir, debug_train_pipe = batch_train_pipe(log_batch_merge_and_copy,
                                                                                         lst_config,
                                                                                         jobs_to_train
                                                                                         )
    save_log_to_file(log_batch_train_pipe, log_file, 'train_pipe')
    save_log_to_file(debug_train_pipe, debug_file, 'train_pipe')

    # dl1 to dl2
    log_batch_dl1_to_dl2, jobs_to_dl2_dl3, debug_dl1_dl2 = batch_dl1_to_dl2(DL1_DATA_DIR,
                                                                            model_dir,
                                                                            lst_config,
                                                                            job_to_dl1_dl2,
                                                                            jobs_all_dl1_finished,
                                                                            log_batch_merge_and_copy
                                                                            )
    save_log_to_file(log_batch_dl1_to_dl2, log_file, 'dl1_to_dl2')
    save_log_to_file(debug_dl1_dl2, debug_file, 'dl1_to_dl2')
