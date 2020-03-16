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
# > python onsite_mc_r0_to_dl3.py [-conf CONFIG_FILE] [--prod_id PROD_ID]
#
#   The input_dir is set in the global variable `DL0_DATA_DIR`

import argparse
import calendar
import lstchain
import glob
import pprint
from onsite_mc_r0_to_dl1 import main as r0_to_dl1
from onsite_mc_merge_and_copy_dl1 import main as merge_and_copy_dl1
from onsite_mc_train import main as train_pipe
from onsite_mc_dl1_to_dl2 import main as dl1_to_dl2
from data_management import *

#######################################################################################################################
#######################################################################################################################
BASE_PATH = '/fefs/aswg/data/mc'

OBS_DATE = '20190415'
POINTING = 'south_pointing'
ALL_PARTICLES = ['electron', 'gamma', 'gamma-diffuse', 'proton']

# source env onsite - can be changed for custom install
source_env = 'source /fefs/aswg/software/virtual_env/.bashrc; conda activate cta;'  # By default

# run and batch all the steps of the code (see above)
DO_r0_to_r1 = True
DO_merge_and_copy = True
DO_TRAIN_PIPE = True
DO_dl1_to_dl2 = True
# DO_dl2_to_dl3 = True

#######################################################################################################################
#######################################################################################################################


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


def batch_dl2_to_dl3():
    pass


def batch_dl1_to_dl2(dl1_directory, path_to_models, config_file, jobid_from_training, jobids_from_merge,
                     dict_with_dl1_paths):
    """
    Function to batch the dl1_to_dl2 stage once the lstchain train_pipe batched jobs have finished.

    Parameters
    ----------
    dl1_directory : str
        Path to the dl1 directory
    path_to_models : str
        Path to the model directory - should be taken from train_pipe
    config_file : str
        Path to a configuration file. If none is given, a standard configuration is applied
    jobid_from_training : str
        string containing the jobid from the jobs batched in the train_pipe stage, to be passed to the
        dl1_to_dl2 function (as a slurm dependency)
    jobids_from_merge : str
        string containing the jobid from the jobs batched in the merge_and_copy_dl1 stage,
        to be passed to the dl1_to_dl2 function (as a slurm dependency)
    dict_with_dl1_paths : dict
        Indeed the log of the merge_and_copy stage, where the final names of the dl1 files were stored

    Returns
    -------
    log_batch_dl1_to_dl2 : dict
        Dictionary containing the log of the batched dl1_to_dl2 jobs
    jobid_4_dl2_to_dl3 : str
        string containing the jobids to be passed to the next stage of the workflow (as a slurm dependency)
    debug_log : dict
        Debug purposes

    """

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
                                dictionary_with_dl1_paths=dict_with_dl1_paths
                                )

        log_dl1_to_dl2.update(log)
        jobid_4_dl2_to_dl3.append(jobid)

        debug_log[jobid] = f'{particle} job from dl1_to_dl2 that depends both on : {jobid_from_training} training ' \
                           f'jobs AND from {jobids_from_merge} merge_and_copy_dl1 jobs'

    jobid_4_dl2_to_dl3 = ','.join(jobid_4_dl2_to_dl3)

    return log_dl1_to_dl2, jobid_4_dl2_to_dl3, debug_log


def batch_train_pipe(log_from_merge, config_file, jobids_from_merge):
    """
    Function to batch the lstchain train_pipe once the proton and gamma-diffuse merge_and_copy_dl1 batched jobs have
    finished.

    Parameters
    ----------
    log_from_merge : dict
        dictionary containing the output name and abs path to the DL1 files, derived in merge_and_copy and saved
        through the log
    config_file : str
        Path to a configuration file. If none is given, a standard configuration is applied
    jobids_from_merge : str
        string containing the jobids (***ONLY from proton and gamma-diffuse***) from the jobs batched in the
         merge_and_copy_dl1 stage, to be passed to the train_pipe function (as a slurm dependency)

    Returns
    -------
    log_train : dict
        Dictionary containing the log of the batched train_pipe jobs
    jobid_4_dl1_to_dl2 : str
        string containing the jobid to be passed to the next stage of the workflow (as a slurm dependency).
        For the next stage, however, it will be needed TRAIN + MERGED jobs
    debug_log : dict
        Debug purposes
    model_path :
        Path with the model's directory

    """
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
    """
    Function to batch the onsite_mc_merge_and_copy function once the all the r0_to_dl1 jobs (batched by particle type)
    have finished.

    Batch 8 merge_and_copy_dl1 jobs ([train, test] x particle) + the move_dl1 and move_dir jobs (2 per particle).

    Parameters
    ----------
    running_analysis_dir : str
        Directory to dl1 files
    log_jobs_from_r0_to_dl1 : dict
        dictionary of dictionaries containing the log (jobids organized by particle) from the previous stage
        (onsite_mc_r0_to_dl1)

    Returns
    -------
    log_merge_and_copy : dict
        Dictionary containing the log of the batched merge_and_copy_dl1 jobs

    jobid_4_train : str
         string containing the jobids to be passed to the next stage of the workflow (as a slurm dependency)
    all_merge : str
        string containing all the jobs to indicate that all the dl1 are correctly finished (for dl1_to_dl2)
    debug_log : dict
        Debug purposes

    """
    log_merge_and_copy = {}
    jobid_4_train = []
    all_merge = []
    debug_log = {}

    for particle in ALL_PARTICLES:
        log, jobid, jobid_debug = merge_and_copy_dl1(running_analysis_dir.format(particle),
                                                     flag_full_workflow=True,
                                                     particle2jobs_dict=log_jobs_from_r0_to_dl1,
                                                     particle=particle
                                                     )

        log_merge_and_copy.update(log)
        all_merge.append(jobid)
        if particle == 'gamma-diffuse' or particle == 'proton':
            jobid_4_train.append(jobid)

        debug_log[jobid] = f'{particle} merge_and_copy-jobs that will go to dl1_to_dl2. They depend on the following ' \
                           f'{log_jobs_from_r0_to_dl1[particle]} r0_t0_dl1 jobs.'
        debug_log[jobid_debug] = f'All the {particle} jobs that have been launched in merge_and_copy_dl1.'

    jobid_4_train = ','.join(jobid_4_train)
    all_merge = ','.join(all_merge)

    return log_merge_and_copy, jobid_4_train, all_merge, debug_log


def check_job_output_logs(dict_particle_jobid):
    """
    # TODO V0.2 - Job management

    Parameters
    ----------
    dict_particle_jobid : dict
        Dictionary coming from batch_r0_to_dl1 with all the information and log of that stage, from where the jobids
        will be retrieved to be checked.

    Returns
    -------
    ids_single_particle_ok : str
        String containing the checked jobids to be passed to the next stage of the workflow (as a slurm dependency)
    debug_log : dict
            Debug purposes

    """
    # dictionary by particle with all the jobids corresponding to each particle

    jobid_dependecies = ','.join(map(str, dict_particle_jobid.keys()))
    cmd = f'sbatch --parsable ---dependency=afterok:{jobid_dependecies} --wrap="python  THE_CODE_TO_PARSE_OUTPUT.py"'
    # TODO V0.2 - Job management & THE_CODE_TO_PARSE_OUTPUT.py

    ids_single_particle_ok = os.popen(cmd).read().split('\n')

    return ids_single_particle_ok


def batch_r0_to_dl1(input_dir, conf_file, prod_id):
    """
    Function to batch the r0_to_dl1 jobs by particle type.

    The function will also create, arrange and return a dictionary with all the log of this stage.
    Finally # TODO in V0.2 - Job management
    the jobids of the batched jobs will be checked to confirm that there were no Error within the batched jobs.

    Parameters
    ----------
    input_dir : str
        Path to the DL0 files
    conf_file : str
        Path to a configuration file. If none is given, a standard configuration is applied
    prod_id : str
        Production ID. If None, _v00 will be used, indicating an official base production. Default = None.


    Returns
    -------
    full_log : dict
        Dictionary of dictionaries containing the full log of the batched jobs (jobids as keys) as well as the
        4 more keys (one by particle) with all the jobs associated with each particle.

    ids_by_particle_ok : str  # TODO in V0.2 - Job management
        a string (of chained jobids separated by ',' and without spaces between each element), to be passed to the
        the next stage of the workflow (as a slurm dependency).
    debug_log : dict
            dictionary containing minimum information - jobids -  for log_reduced.txt

    """
    full_log = {'jobid_log': {}}
    ids_by_particle_ok = []
    debug_log = {}

    for particle in ALL_PARTICLES:
        log, jobids_by_particle = r0_to_dl1(input_dir.format(particle),
                                            config_file=conf_file,
                                            prod_id=prod_id,
                                            flag_full_workflow=True
                                            )

        # Create jobid to full log information dictionary
        # And the inverse dictionary, particle to the list of all the jobids of that same particle
        full_log['jobid_log'].update(log)
        full_log[particle] = jobids_by_particle

        for jid in jobids_by_particle:
            debug_log[jid] = f'{particle} job from r0_to_dl1'

        # TODO in V0.2 - Job management
        # jobid_summary = check_job_output_logs(full_log[particle])  # full_log is a dict of dicts
        # ids_by_particle_ok.append(jobid_summary)

        # how to launch the check of files and what to pass to merge (4 ids or ~300)

    return full_log, ids_by_particle_ok, debug_log


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="MC R0 to DL3 full workflow")

    parser.add_argument('--config_file', '-conf', action='store', type=str,
                        dest='config_file',
                        help='Path to a configuration file. If none is given, a standard configuration is applied',
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
    base_prod_id = f'{today.year:04d}{today.month:02d}{today.day:02d}_v{lstchain.__version__}'
    suffix_id = '_v00' if args.prod_id is None else '_{}'.format(args.prod_id)

    # Missing global variables, some dependent of args.

    PROD_ID = base_prod_id + suffix_id
    RUNNING_ANALYSIS_DIR = os.path.join(BASE_PATH, 'running_analysis', OBS_DATE, '{}', POINTING, PROD_ID)
    ANALYSIS_LOG_DIR = os.path.join(BASE_PATH, 'analysis_logs', OBS_DATE, '{}', POINTING, PROD_ID)
    DL0_DATA_DIR = os.path.join(BASE_PATH, 'DL0', OBS_DATE, '{}', POINTING)
    DL1_DATA_DIR = os.path.join(BASE_PATH, 'DL1', OBS_DATE, '{}', POINTING, PROD_ID)

    # #################################################
    # ########### Beginning of the workflow ###########
    # #################################################

    print(f'\nThe full r0 to dl3 workflow is going to be run at \n\n   '
          f'{DL0_DATA_DIR.format("{electron/gamma/gamma-diff/protons}")}.\n\n'
          f'All the subdirectories will be overwritten , i.e., all the previous runs (with a same PROD_ID) !')

    query_continue('Are you sure ?')

    log_file = './log_FULL_onsite_mc_r0_to_dl3.txt'
    debug_file = './log_reduced.txt'

    if DO_r0_to_r1:  # TODO V0.2 Job management : _ jobids to check if they have finished without erros
        log_batch_r0_dl1, _, debug = batch_r0_to_dl1(DL0_DATA_DIR,
                                                     args.config_file,
                                                     args.prod_id)

        # First time opening the log --> erase
        if os.path.exists(log_file):
            os.remove(log_file)
        if os.path.exists(debug_file):
            os.remove(debug_file)
        save_log_to_file(log_batch_r0_dl1, log_file, 'r0_to_dl1')
        save_log_to_file(debug, debug_file, 'r0_to_dl1')

    if DO_merge_and_copy:
        # TODO log_batch_r0_dl1 take place also in the job management
        log_batch_merge_and_copy, jobs_to_train, jobs_all_dl1_finished,\
         debug = batch_merge_and_copy_dl1(RUNNING_ANALYSIS_DIR, log_batch_r0_dl1)

        save_log_to_file(log_batch_merge_and_copy, log_file, 'merge_and_copy_dl1')
        save_log_to_file(debug, debug_file, 'merge_and_copy_dl1')
    else:
        # Create just the needed dictionary inputs (dl1 files must exist !)
        log_batch_merge_and_copy = create_dict_with_filenames(DL1_DATA_DIR)
        jobs_to_train = ''
        jobs_all_dl1_finished = ''

    if DO_TRAIN_PIPE:
        log_batch_train_pipe, job_from_train_pipe, model_dir, debug = batch_train_pipe(log_batch_merge_and_copy,
                                                                                       args.config_file,
                                                                                       jobs_to_train)

        save_log_to_file(log_batch_train_pipe, log_file, 'train_pipe')
        save_log_to_file(debug, debug_file, 'train_pipe')
    else:
        job_from_train_pipe = ''
        model_dir = os.path.join(BASE_PATH, 'models', OBS_DATE, POINTING, PROD_ID)
        log_batch_merge_and_copy = create_dict_with_filenames(DL1_DATA_DIR)

    if DO_dl1_to_dl2:
        log_batch_dl1_to_dl2, jobs_4_dl2_to_dl3, debug = batch_dl1_to_dl2(DL1_DATA_DIR,
                                                                          model_dir,
                                                                          args.config_file,
                                                                          job_from_train_pipe,  # Single jobid frm train
                                                                          jobs_all_dl1_finished,  # jobids from merge
                                                                          log_batch_merge_and_copy  # finale dl1 names
                                                                          )

        save_log_to_file(log_batch_dl1_to_dl2, log_file, 'dl1_to_dl2')
        save_log_to_file(debug, debug_file, 'dl1_to_dl2')

    # if DO_dl2_to_dl3:  # TODO to be done in V0.3
    #     batch_dl2_to_dl3()
