# library of functions used to the management of the MC workflow analysis at la Palma

# Enrique Garcia Nov 2019

import os
import glob
import pprint
from onsite_mc_r0_to_dl1 import main as r0_to_dl1
from onsite_mc_hiperta_r0_to_dl1lstchain import main as r0_to_dl1_rta
from onsite_mc_merge_and_copy_dl1 import main as merge_and_copy_dl1
from onsite_mc_train import main as train_pipe
from onsite_mc_dl1_to_dl2 import main as dl1_to_dl2


def batch_r0_to_dl1(input_dir, conf_file, prod_id, particles_loop, source_env):
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
    particles_loop : list
        list with the particles to be processed. Takes the global variable ALL_PARTICLES
    source_env : str
        source environment to select the desired conda environment to run the r0/1_to_dl1 stage.

    Returns
    -------
    full_log : dict
        Dictionary of dictionaries containing the full log of the batched jobs (jobids as keys) as well as the
        4 more keys (one by particle) with all the jobs associated with each particle.

    debug_log : dict
            dictionary containing minimum information - jobids -  for log_reduced.txt

    # ids_by_particle_ok : str  # TODO in V0.2 - Job management
    #     a string (of chained jobids separated by ',' and without spaces between each element), to be passed to the
    #     the next stage of the workflow (as a slurm dependency).

    """
    full_log = {'jobid_log': {}}
    # ids_by_particle_ok = []
    debug_log = {}

    print("\n ==== START {} ==== \n".format('batch r0_to_dl1_workflow'))

    for particle in particles_loop:
        log, jobids_by_particle = r0_to_dl1(input_dir.format(particle),
                                            config_file=conf_file,
                                            prod_id=prod_id,
                                            flag_full_workflow=True,
                                            source_environment=source_env
                                            )

        # Create dictionary : jobid to full log information, and
        #  the inverse dictionary, particle to the list of all the jobids of that same particle
        full_log['jobid_log'].update(log)
        full_log[particle] = jobids_by_particle

        for jid in jobids_by_particle:
            debug_log[jid] = f'{particle} job from r0_to_dl1'

        # TODO in V0.2 - Job management : how to launch the check of files and what to pass to merge (4 ids or ~300)
        # jobid_summary = check_job_output_logs(full_log[particle])  # full_log is a dict of dicts
        # ids_by_particle_ok.append(jobid_summary)

    print("\n ==== END {} ==== \n".format('batch r0_to_dl1_workflow'))

    return full_log, debug_log  # ids_by_particle_ok


def batch_r0_to_dl1_rta(input_dir, conf_file_rta, prod_id, particles_loop, conf_file_lst):
    """
    Function to batch the r0_to_dl1 jobs by particle type, using the HiPeRTA code. Files in input_dir MUST had been
     previously converted to *.h5

    It will also create, arrange and return a dictionary with all the log of this stage.

    Parameters
    ----------
    input_dir : str
        Path to the R1 (h5 !) files

    conf_file_rta : str
        Path to a HiPeRTA configuration file. If none is given, a standard configuration is applied

    prod_id : str
        Production ID. If None, _v00 will be used, indicating an official base production. Default = None.

    particles_loop : list
        list with the particles to be processed. Takes the global variable ALL_PARTICLES

    conf_file_lst : str
        Path to a lstchain configuration. JUST to be copied at the same time as the rta_config to `/running_analysis/`.

    Returns
    -------
    full_log : dict
        Dictionary of dictionaries containing the full log of the batched jobs (jobids as keys) as well as the
        4 more keys (one by particle) with all the jobs associated with each particle.

    debug_log : dict
            dictionary containing minimum information - jobids -  for log_reduced.txt

    """
    full_log = {'jobid_log': {}}
    debug_log = {}

    print("\n ==== START {} ==== \n".format('HiPeRTA_r0_to_dl1_workflow'))

    for particle in particles_loop:
        log, jobids_by_particle = r0_to_dl1_rta(input_dir.format(particle),
                                                config_file=conf_file_rta,
                                                prod_id=prod_id,
                                                flag_full_workflow=True,
                                                lst_config=conf_file_lst
                                                )

        # Create jobid to full log information dictionary.
        # And the inverse dictionary, particle to the list of all the jobids of that same particle
        full_log['jobid_log'].update(log)
        full_log[particle] = jobids_by_particle

        for jid in jobids_by_particle:
            debug_log[jid] = f'{particle} job from r0_to_dl1_RTA'

    print("\n ==== END {} ==== \n".format('HiPeRTA_r0_to_dl1_workflow'))

    return full_log, debug_log


# def check_job_output_logs(dict_particle_jobid):
#     """
#     # TODO V0.2 - Job management
#
#     Parameters
#     ----------
#     dict_particle_jobid : dict
#         Dictionary coming from batch_r0_to_dl1 with all the information and log of that stage, from where the jobids
#         will be retrieved to be checked.
#
#     Returns
#     -------
#     ids_single_particle_ok : str
#         String containing the checked jobids to be passed to the next stage of the workflow (as a slurm dependency)
#     debug_log : dict
#             Debug purposes
#
#     """
#     # TODO log_batch_r0_dl1 take place also in the job management
#
#     # dictionary by particle with all the jobids corresponding to each particle
#
#     jobid_dependecies = ','.join(map(str, dict_particle_jobid.keys()))
#     cmd = f'sbatch --parsable ---dependency=afterok:{jobid_dependecies} --wrap="python  THE_CODE_TO_PARSE_OUTPUT.py"'
#     # TODO V0.2 - Job management & THE_CODE_TO_PARSE_OUTPUT.py
#
#     ids_single_particle_ok = os.popen(cmd).read().split('\n')
#
#     return ids_single_particle_ok


def batch_merge_and_copy_dl1(running_analysis_dir, log_jobs_from_r0_to_dl1, particles_loop, smart_merge=False,
                             no_image_flag=True):
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

    smart_merge : bool
        flag to indicate whether the merge of the files should be done with `--smart True` or `--smart False`,
        controlling the argument of the `lstchain_merge_hdf5_files.py` script (batched in this function).

    particles_loop : list
        list with the particles to be processed. Takes the global variable ALL_PARTICLES

    no_image_flag : bool
        flag to indicate whether the --no-image argument of the `lstchain_merge_hdf5_files.py` script (batched in
        this function) should be either True or False. 

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

    if smart_merge == 'lst':
        merge_flag = True
    elif smart_merge == 'rta':
        merge_flag = False
    elif smart_merge:
        merge_flag = True
    elif not smart_merge:
        merge_flag = False
    else:
        merge_flag = False

    print("\n ==== START {} ==== \n".format('batch merge_and_copy_dl1_workflow'))

    for particle in particles_loop:
        log, jobid, jobid_debug = merge_and_copy_dl1(running_analysis_dir.format(particle),
                                                     flag_full_workflow=True,
                                                     particle2jobs_dict=log_jobs_from_r0_to_dl1,
                                                     particle=particle,
                                                     flag_merge=merge_flag,
                                                     flag_no_image=no_image_flag
                                                     )

        log_merge_and_copy.update(log)
        all_merge.append(jobid)
        if particle == 'gamma-diffuse' or particle == 'proton':
            jobid_4_train.append(jobid)

        debug_log[jobid] = f'{particle} merge_and_copy-jobs that will go to dl1_to_dl2. They depend on the following ' \
                           f'{log_jobs_from_r0_to_dl1[particle]} r0_t0_dl1 jobs.'
        debug_log[jobid_debug] = f'Are all the {particle} jobs that have been launched in merge_and_copy_dl1.'

    jobid_4_train = ','.join(jobid_4_train)
    all_merge = ','.join(all_merge)

    print("\n ==== END {} ==== \n".format('batch merge_and_copy_dl1_workflow'))

    return log_merge_and_copy, jobid_4_train, all_merge, debug_log


def batch_train_pipe(log_from_merge, config_file, jobids_from_merge, source_env):
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

    source_env : str
        source environment to select the desired conda environment to run train_pipe and dl1_to_dl2 stages

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

    print("\n ==== START {} ==== \n".format('batch mc_train_workflow'))

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

    print("\n ==== END {} ==== \n".format('batch mc_train_workflow'))

    return log_train, jobid_4_dl1_to_dl2, model_path, debug_log


def batch_dl1_to_dl2(dl1_directory, path_to_models, config_file, jobid_from_training, jobids_from_merge,
                     dict_with_dl1_paths, particles_loop, source_env):
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

    particles_loop : list
        list with the particles to be processed. Takes the global variable ALL_PARTICLES

    source_env : str
        source environment to select the desired conda environment to run train_pipe and dl1_to_dl2 stages

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
    jobid_for_dl2_to_dl3 = []
    debug_log = {}

    print("\n ==== START {} ==== \n".format('batch dl1_to_dl2_workflow'))

    for particle in particles_loop:
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
        jobid_for_dl2_to_dl3.append(jobid)

        debug_log[jobid] = f'{particle} job from dl1_to_dl2 that depends both on : {jobid_from_training} training ' \
                           f'jobs AND from {jobids_from_merge} merge_and_copy_dl1 jobs'

    jobid_4_dl2_to_dl3 = ','.join(jobid_for_dl2_to_dl3)

    print("\n ==== END {} ==== \n".format('batch dl1_to_dl2_workflow'))

    return log_dl1_to_dl2, jobid_4_dl2_to_dl3, debug_log


def batch_dl2_to_dl3():
    pass


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


def create_dict_with_filenames(dl1_directory, particles_loop):
    """
    Function that creates a dictionary with the filenames of all the final dl1 files (the same is done
    in the merge_and_copy_dl1 function) so that it can be passed to the rest of the stages, in case the full workflow
    it is not run from the start.

    Parameters
    ----------
    dl1_directory: str
        path to the dl1 directory files

    particles_loop : list
        list with the particles to be processed. Takes the global variable ALL_PARTICLES

    Returns
    -------
    dl1_filename_directory : dict
        dictionary with the name (and absolute path) of the dl1 files with the name of the particles set as key of the
        dictionary

             dl1_filename_directory[particle].keys() = ['train_path_and_outname_dl1', 'test_path_and_outname_dl1']
    """
    dl1_filename_directory = {}

    for particle in particles_loop:
        dl1_filename_directory[particle] = {'training': {}, 'testing': {}}
        dl1_filename_directory[particle]['training']['train_path_and_outname_dl1'] = glob.glob(os.path.join(
            dl1_directory.format(particle), '*training*.h5'))[0]
        dl1_filename_directory[particle]['testing']['test_path_and_outname_dl1'] = glob.glob(os.path.join(
            dl1_directory.format(particle), '*testing*.h5'))[0]

    return dl1_filename_directory
