# Functions used to manage the MC workflow analysis at La Palma

# Enrique Garcia Nov 2019

import os
import sys
import glob
import yaml
import pprint
import calendar
import lstchain
from lstmcpipe.stages import merge_dl1, train_pipe, dl1_to_dl2, dl2_to_irfs
from lstmcpipe.onsite_mc_r0_to_dl1 import main as r0_to_dl1
from lstmcpipe.onsite_mc_hiperta_r0_to_dl1lstchain import main as r0_to_dl1_rta


def batch_r0_to_dl1(input_dir, conf_file, prod_id, particles_loop, source_env, gamma_offsets=None):
    """
    Batch the r0_to_dl1 jobs by particle type.

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
    gamma_offsets : list

    Returns
    -------
    full_log : dict
        Dictionary of dictionaries containing the full log of the batched jobs (jobids as keys) as well as the
        4 more keys (one by particle) with all the jobs associated with each particle.
    debug_log : dict
            dictionary containing minimum information - jobids -  for log_reduced.txt
    all_jobids_from_r0_dl1_stage : str
        string, separated by commas, containing all the jobids of this stage
    """
    full_log = {'log_all_job_ids': {}}
    debug_log = {}
    all_jobids_from_r0_dl1_stage = []

    print("\n ==== START {} ==== \n".format('batch r0_to_dl1_workflow'))

    for particle in particles_loop:
        if particle == 'gamma' and gamma_offsets is not None:
            for off in gamma_offsets:

                gamma_input_dir = os.path.join(input_dir, off)
                _particle = particle + '_' + off

                log, jobids_by_particle = r0_to_dl1(
                    gamma_input_dir.format(particle),  # Particle needs to be gamma w/o the off
                    config_file=conf_file,
                    particle=_particle,
                    prod_id=prod_id,
                    flag_full_workflow=True,
                    source_environment=source_env,
                    offset=off
                )

                full_log['log_all_job_ids'].update(log)
                full_log[_particle] = ','.join(jobids_by_particle)
                all_jobids_from_r0_dl1_stage.append(full_log[_particle])  # Create a list with particles elements

                for jid in jobids_by_particle:
                    debug_log[jid] = f'{_particle} job from r0_to_dl1'

        else:
            _particle = particle
            log, jobids_by_particle = r0_to_dl1(
                input_dir.format(particle),  # Input dir needs particle gamma w/o off
                config_file=conf_file,
                particle=_particle,  # However _particle will contain the gamma_off
                prod_id=prod_id,
                flag_full_workflow=True,
                source_environment=source_env
            )

            # Create dictionary : jobid to full log information, and
            #  the inverse dictionary, particle to the list of all the jobids of that same particle
            full_log['log_all_job_ids'].update(log)
            full_log[_particle] = ','.join(jobids_by_particle)
            all_jobids_from_r0_dl1_stage.append(full_log[_particle])  # Create a list with particles elements

            for jid in jobids_by_particle:
                debug_log[jid] = f'{_particle} job from r0_to_dl1'

    all_jobids_from_r0_dl1_stage = ','.join(all_jobids_from_r0_dl1_stage)  # Create a string to be directly passed

    print("\n ==== END {} ==== \n".format('batch r0_to_dl1_workflow'))

    return full_log, debug_log, all_jobids_from_r0_dl1_stage  # ids_by_particle_ok


def batch_r0_to_dl1_rta(input_dir, conf_file_rta, prod_id, particles_loop, conf_file_lst, gamma_offsets=None):
    """
    Function to batch the r0_to_dl1 jobs by particle type, using the HiPeRTA code. Files in input_dir MUST had been
     previously converted to *.h5

    It will also create, arrange and return a dictionary with all the log of this stage.

    Parameters
    ----------
    input_dir : str
        Path to the R0 (h5 !) files
    conf_file_rta : str
        Path to a HiPeRTA configuration file. If none is given, a standard configuration is applied
    prod_id : str
        Production ID. If None, _v00 will be used, indicating an official base production. Default = None.
    particles_loop : list
        list with the particles to be processed. Takes the global variable ALL_PARTICLES
    conf_file_lst : str
        Path to a lstchain configuration. JUST to be copied at the same time as the rta_config to `/running_analysis/`.
    gamma_offsets : list

    Returns
    -------
    full_log : dict
        Dictionary of dictionaries containing the full log of the batched jobs (jobids as keys) as well as the
        4 more keys (one by particle) with all the jobs associated with each particle.

    debug_log : dict
            dictionary containing minimum information - jobids -  for log_reduced.txt

    all_jobids_from_r0_dl1_stage : str
        string, separated by commas, containing all the jobids of this stage
    """
    full_log = {'log_all_job_ids': {}}
    debug_log = {}
    all_jobids_from_r0_dl1_stage = []

    print("\n ==== START {} ==== \n".format('HiPeRTA_r0_to_dl1_workflow'))

    for particle in particles_loop:
        if particle == 'gamma' and gamma_offsets is not None:
            for off in gamma_offsets:

                gamma_input_dir = os.path.join(input_dir, off)
                _particle = particle + '_' + off

                log, jobids_by_particle = r0_to_dl1_rta(
                    gamma_input_dir.format(particle),  # Input dir needs particle gamma w/o off
                    particle=_particle,  # However _particle will contain the gamma_off
                    config_rta_file=conf_file_rta,
                    prod_id=prod_id,
                    flag_full_workflow=True,
                    lst_config=conf_file_lst,
                    offset=off
                )

                full_log['log_all_job_ids'].update(log)
                full_log[_particle] = ','.join(jobids_by_particle)
                all_jobids_from_r0_dl1_stage.append(full_log[_particle])  # Create a list with particles elements

                for jid in jobids_by_particle:
                    debug_log[jid] = f'{_particle} job from r0_to_dl1_RTA'

        else:
            _particle = particle
            log, jobids_by_particle = r0_to_dl1_rta(
                input_dir.format(particle),  # Input dir needs particle gamma w/o off
                particle=_particle,  # However _particle will contain the gamma_off
                config_rta_file=conf_file_rta,
                prod_id=prod_id,
                flag_full_workflow=True,
                lst_config=conf_file_lst
            )

            # Create jobid to full log information dictionary.
            # And the inverse dictionary, particle to the list of all the jobids of that same particle
            full_log['log_all_job_ids'].update(log)
            full_log[_particle] = ','.join(jobids_by_particle)
            all_jobids_from_r0_dl1_stage.append(full_log[_particle])  # Create a list with particles elements

            for jid in jobids_by_particle:
                debug_log[jid] = f'{_particle} job from r0_to_dl1_RTA'

    all_jobids_from_r0_dl1_stage = ','.join(all_jobids_from_r0_dl1_stage)  # Create a string to be directly passed

    print("\n ==== END {} ==== \n".format('HiPeRTA_r0_to_dl1_workflow'))

    return full_log, debug_log, all_jobids_from_r0_dl1_stage


def batch_merge_and_copy_dl1(running_analysis_dir, log_jobs_from_r0_to_dl1, particles_loop, source_env,
                             smart_merge=False, no_image_flag=True, prod_id=None, gamma_offsets=None):
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
    gamma_offsets : list
        list containig the offset of the gammas
    prod_id : str
        prod_id defined in config_MC_prod.yml
    source_env : str
        source environment to select the desired conda environment to run the r0/1_to_dl1 stage.

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
    all_jobs_from_merge_stage = []
    debug_log = {}

    if smart_merge == 'lst' or smart_merge == 'lstchain':
        merge_flag = True
    elif smart_merge == 'rta' or smart_merge == 'hiperta':
        merge_flag = False
    elif smart_merge:
        merge_flag = True
    elif not smart_merge:
        merge_flag = False
    else:
        merge_flag = False

    print("\n ==== START {} ==== \n".format('batch merge_and_copy_dl1_workflow'))

    for particle in particles_loop:
        if particle == 'gamma' and gamma_offsets is not None:
            for off in gamma_offsets:

                gamma_running_analysis_dir = os.path.join(running_analysis_dir, off)
                _particle = particle + '_' + off

                log, jobid_mv_all_dl1, jobid_debug = merge_dl1(
                    gamma_running_analysis_dir.format(particle),
                    particle2jobs_dict=log_jobs_from_r0_to_dl1,
                    particle=_particle,
                    flag_merge=merge_flag,
                    flag_no_image=no_image_flag,
                    prod_id=prod_id,
                    gamma_offset=off,
                    source_environment=source_env
                )

                log_merge_and_copy.update(log)
                all_jobs_from_merge_stage.append(jobid_debug)
                if _particle == 'gamma-diffuse' or _particle == 'proton':
                    jobid_4_train.append(jobid_mv_all_dl1)

                debug_log[jobid_mv_all_dl1] = f'{_particle} merge_and_copy-job - INDEED IT IS JUST PASSED the ' \
                                              f'move_dl1 jobid - that will be send to the train pipe stage. They ' \
                                              f'depend on the following {log_jobs_from_r0_to_dl1[_particle]} ' \
                                              f'r0_t0_dl1 jobs.'
                debug_log[jobid_debug] = f'Are all the {_particle} jobs that have been launched in merge_and_copy_dl1.'

        else:
            _particle = particle

            log, jobid_mv_all_dl1, jobid_debug = merge_dl1(
                running_analysis_dir.format(particle),
                particle2jobs_dict=log_jobs_from_r0_to_dl1,
                particle=_particle,
                flag_merge=merge_flag,
                flag_no_image=no_image_flag,
                prod_id=prod_id,
                source_environment=source_env
            )

            log_merge_and_copy.update(log)
            all_jobs_from_merge_stage.append(jobid_debug)
            if _particle == 'gamma-diffuse' or _particle == 'proton':
                jobid_4_train.append(jobid_mv_all_dl1)

            debug_log[jobid_mv_all_dl1] = f'{_particle} merge_and_copy-job - INDEED IT IS JUST PASSED the ' \
                                          f'move_dl1 jobid - that will be send to the train pipe stage. They depend ' \
                                          f'on the following {log_jobs_from_r0_to_dl1[_particle]} r0_t0_dl1 jobs.'
            debug_log[jobid_debug] = f'Are all the {_particle} jobs that have been launched in merge_and_copy_dl1.'

    jobid_4_train = ','.join(jobid_4_train)
    all_jobs_from_merge_stage = ','.join(all_jobs_from_merge_stage)

    print("\n ==== END {} ==== \n".format('batch merge_and_copy_dl1_workflow'))

    return log_merge_and_copy, jobid_4_train, all_jobs_from_merge_stage, debug_log


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
    model_path : str
        Path with the model's directory
    debug_log : dict
        Debug and summary purposes
    """
    debug_log = {}

    print("\n ==== START {} ==== \n".format('batch mc_train_workflow'))

    gamma_dl1_train_file = log_from_merge['gamma-diffuse']['training']['train_path_and_outname_dl1']
    proton_dl1_train_file = log_from_merge['proton']['training']['train_path_and_outname_dl1']

    log_train, jobid_4_dl1_to_dl2, model_path = train_pipe(
        gamma_dl1_train_file,
        proton_dl1_train_file,
        config_file=config_file,
        source_environment=source_env,
        wait_ids_proton_and_gammas=jobids_from_merge
    )

    debug_log[jobid_4_dl1_to_dl2] = f'The single jobid from train_pipe that depends of {jobids_from_merge} - merge' \
                                    f'_and_copy jobids'

    print("\n ==== END {} ==== \n".format('batch mc_train_workflow'))

    return log_train, jobid_4_dl1_to_dl2, model_path, debug_log


def batch_plot_rf_features(dir_models, config_file, source_env, train_jobid):
    """
    Batches the plot_model_importance.py script that creates a .png with the RF feature's importance models
    after the RF are trained.
    The plot is saved in the same dir in where the modes are stored.

    Parameters
    ----------
    dir_models: str
        Path to model's directory
    config_file: str
        Path to lstchain config file
    source_env: str
        String containing the .bashrc file to source and the conda env to call
    train_jobid: str
        Single jobid from training stage.

    Returns
    -------
    log: dict
        Dictionary with lstmcpipe_plot_models_importance single job id to be passed to debug log.
    """
    log = {}
    print("\n ==== START {} ==== \n".format('batch plot RF features importance'))
    jobe = os.path.join(dir_models, 'job_plot_rf_feat_importance.e')
    jobo = os.path.join(dir_models, 'job_plot_rf_feat_importance.o')

    base_cmd = f'lstmcpipe_plot_models_importance {dir_models} -cf {config_file}'
    cmd = f'sbatch --parsable --dependency=afterok:{train_jobid} -e {jobe} -o {jobo} -J RF_importance ' \
          f' --wrap="export MPLBACKEND=Agg; {source_env} {base_cmd}"'
    jobid = os.popen(cmd).read().strip('\n')

    log[jobid] = 'Single job_id to plot RF feature s importance'

    print(f" Random Forest importance's plot will be saved at:\n   {dir_models}")
    print("\n ==== END {} ==== \n".format('batch plot RF features importance'))

    return log


def batch_dl1_to_dl2(dl1_directory, path_to_models, config_file, jobid_from_training, jobids_from_merge,
                     dict_with_dl1_paths, particles_loop, source_env, gamma_offsets=None):
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
    gamma_offsets : list
        list off gamma offsets

    Returns
    -------
    log_batch_dl1_to_dl2 : dict
        Dictionary containing the log of the batched dl1_to_dl2 jobs
    jobid_4_dl2_to_dl3 : str
        string containing the jobids to be passed to the next stage of the workflow (as a slurm dependency)
    debug_log : dict
        Debug and summary purposes

    """

    log_dl1_to_dl2 = {}
    jobid_for_dl2_to_dl3 = []
    debug_log = {}

    print("\n ==== START {} ==== \n".format('batch dl1_to_dl2_workflow'))

    for particle in particles_loop:

        if particle == 'gamma' and gamma_offsets is not None:
            for off in gamma_offsets:
                gamma_dl1_directory = os.path.join(dl1_directory, off)
                _particle = particle + '_' + off

                log, jobid = dl1_to_dl2(
                    gamma_dl1_directory.format(particle),
                    path_models=path_to_models,
                    config_file=config_file,
                    particle=_particle,
                    wait_jobid_train_pipe=jobid_from_training,
                    wait_jobids_merge=jobids_from_merge,
                    dictionary_with_dl1_paths=dict_with_dl1_paths,
                    source_environment=source_env
                )

                log_dl1_to_dl2.update(log)
                jobid_for_dl2_to_dl3.append(jobid)

                debug_log[jobid] = f'{_particle} job from dl1_to_dl2 that depends both on : {jobid_from_training} ' \
                                   f'training jobs AND from {jobids_from_merge} merge_and_copy_dl1 jobs'

        else:
            _particle = particle
            log, jobid = dl1_to_dl2(
                dl1_directory.format(particle),
                path_models=path_to_models,
                config_file=config_file,
                particle=_particle,
                wait_jobid_train_pipe=jobid_from_training,
                wait_jobids_merge=jobids_from_merge,
                dictionary_with_dl1_paths=dict_with_dl1_paths,
                source_environment=source_env
            )

            log_dl1_to_dl2.update(log)
            jobid_for_dl2_to_dl3.append(jobid)

            debug_log[jobid] = f'{_particle} job from dl1_to_dl2 that depends both on : {jobid_from_training} ' \
                               f'training jobs AND from {jobids_from_merge} merge_and_copy_dl1 jobs'

    jobid_4_dl2_to_dl3 = ','.join(jobid_for_dl2_to_dl3)

    print("\n ==== END {} ==== \n".format('batch dl1_to_dl2_workflow'))

    return log_dl1_to_dl2, jobid_4_dl2_to_dl3, debug_log


def batch_dl2_to_irfs(dl2_directory, loop_particles, offset_gammas, config_file, job_ids_from_dl1_dl2,
                      log_from_dl1_dl2, source_env, prod_id):
    """
    Batches the dl2_to_irfs stage (lstchain lstchain_create_irf_files script) once the dl1_to_dl2 stage had finished.

    Parameters
    ----------
    dl2_directory: str
    config_file: str
    loop_particles: list
    offset_gammas: list
    job_ids_from_dl1_dl2: str
    source_env: str
    log_from_dl1_dl2: dict
    prod_id: str

    Returns
    -------
    log_batch_dl2_to_irfs: dict
    jobs_from_dl2_irf: str
    debug_dl2_to_irfs: dict
    """
    print("\n ==== START {} ==== \n".format('batch mc_dl2_to_irfs'))

    debug_log = {}
    jobid_for_check = []
    log_dl2_to_irfs = {}

    for off in offset_gammas:

        log, jobid = dl2_to_irfs(
            dl2_directory,
            config_file=config_file,
            log_from_dl1_dl2=log_from_dl1_dl2,
            irf_point_like=True,
            irf_gamma_offset=off,
            source_env=source_env,
            wait_jobs_dl1dl2=job_ids_from_dl1_dl2,
            prod_id=prod_id
        )

        jobid_for_check.append(jobid)
        log_dl2_to_irfs[f'gamma_{off}'] = log
        debug_log[jobid] = f'Gamma_{off} job_id from the dl2_to_irfs stage that depends of the dl1_to_dl2 stage ' \
                           f'job_ids; {job_ids_from_dl1_dl2}'

    if 'gamma-diffuse' in loop_particles:

        log, jobid = dl2_to_irfs(
            dl2_directory,
            irf_point_like=False,
            config_file=config_file,
            source_env=source_env,
            log_from_dl1_dl2=log_from_dl1_dl2,
            wait_jobs_dl1dl2=job_ids_from_dl1_dl2,
            prod_id=prod_id
        )

        jobid_for_check.append(jobid)
        log_dl2_to_irfs[f'gamma-diffuse'] = log
        debug_log[jobid] = f'Gamma-diffuse job_id from the dl2_to_irfs stage that depends of the dl1_to_dl2 stage ' \
                           f'job_ids; {job_ids_from_dl1_dl2}'

    jobid_for_check = ','.join(jobid_for_check)

    print("\n ==== END {} ==== \n".format('batch mc_dl2_to_irfs'))

    return log_dl2_to_irfs, jobid_for_check, debug_log


def load_yml_config(yml_file):
    """
    Reads a yaml file and parses the global variables to run a MC production

    Parameters
    ----------
    yml_file : str
        path to the production configuration file; `config_mc_r0_dl3.yml` by default

    Returns
    -------
    config : dict
        dictionary containing the MC global variables and general config
    """
    with open(yml_file) as f:
        try:
            config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(e)
            exit()

    return config


def parse_config_and_handle_global_vars(yml_file):
    """
    Handles global paths and variables, as well as all the exceptions, depending on kind of MC prod to be run.
    Composes the final path tree to be passed to each stage

    Parameters
    ----------
    yml_file : str
        path to the MC prod YAML config file

    Returns
    -------
    config : dict
        Dictionary with all the variables needed along the r0_to_dl3 workflow

    """
    loaded_config = load_yml_config(yml_file)
    config = {}

    # Allowed options
    allowed_workflows = ['hiperta', 'lstchain']
    allowed_prods = ['prod3', 'prod5']
    allowed_obs_date = ['20190415', '20200629_prod5', '20200629_prod5_trans_80']

    # Load configuration
    workflow_kind = loaded_config['workflow_kind']
    custom_prod_id = loaded_config['prod_id']
    stages_to_be_run = loaded_config['stages_to_be_run']
    merging_options = loaded_config['merging_options']['no_image']

    base_path_dl0 = loaded_config['base_path_dl0']
    prod_type = loaded_config['prod_type']
    obs_date = str(loaded_config['obs_date'])
    pointing = loaded_config['pointing']
    zenith = loaded_config['zenith']
    particles = loaded_config['particles']
    offset_gammas = loaded_config['offset_gammas']

    # Check allowed cases
    if workflow_kind not in allowed_workflows or prod_type not in allowed_prods:
        print(f'\nPlease select an \n\t - allowed `workflow_kind`: {allowed_workflows} or an \n\t - allowed production '
              f'type: {allowed_prods} in the config YAML file; {yml_file}.')
        sys.exit(-1)

    # and incompatible possibilities
    if (prod_type == 'prod3' and obs_date != '20190415') or (prod_type == 'prod5' and obs_date == '20190415'):
        print(f'\nThis prod_type and obs_date combination is not possible.\n'
              f'Please change it in the config YAML file; {yml_file}.')
        sys.exit(-1)

    # Prod_id syntax
    today = calendar.datetime.date.today()
    if workflow_kind == 'lstchain':
        base_prod_id = f'{today.year:04d}{today.month:02d}{today.day:02d}_v{lstchain.__version__}'
    elif workflow_kind == 'hiperta':  # RTA
        # TODO parse version from hiPeRTA module
        base_prod_id = f'{today.year:04d}{today.month:02d}{today.day:02d}_vRTA300_v{lstchain.__version__}'
    else:
        print(f'\n\tPlease select an allowed `workflow_kind`: {allowed_workflows} in the config YAML file; {yml_file}.')
        sys.exit(-1)

    # Create the final config structure to be passed to the pipeline
    # 1 - Prod_id
    if 'trans_80' in obs_date:
        suffix_id = '_{}_trans_80_v00'.format(prod_type) if custom_prod_id is None else '_{}_trans_80_{}'.format(
            prod_type, custom_prod_id)
    else:
        suffix_id = '_{}_v00'.format(prod_type) if custom_prod_id is None else '_{}_{}'.format(prod_type,
                                                                                               custom_prod_id)
    config['prod_id'] = base_prod_id + suffix_id

    # 2 - Parse source environment correctly
    config['source_environment'] = f"source {loaded_config['source_environment']['source_file']}; " \
                                   f"conda activate {loaded_config['source_environment']['conda_env']}; "

    # 3 - particles loop
    config['all_particles'] = particles

    # 3.1 - Gammas' offsets
    if obs_date == '20200629_prod5' or obs_date == '20200629_prod5_trans_80':  # prod5 case
        config['gamma_offs'] = loaded_config['offset_gammas']
    elif obs_date == '20190415' or prod_type == 'prod3':
        config['gamma_offs'] = None
    else:
        print(f'\n\tPlease select an \n\tallowed `obs_date`: {allowed_obs_date} in the config YAML file; {yml_file}.')
        sys.exit(-1)

    # 4 - Stages to be run
    config['stages_to_run'] = stages_to_be_run
    config['merging_no_image'] = merging_options

    # 5 - production workflow and type
    config['workflow_kind'] = workflow_kind
    config['prod_type'] = prod_type

    # 6 - Global paths
    if prod_type == 'prod3':
        if workflow_kind == 'lstchain':
            config['DL0_data_dir'] = os.path.join(base_path_dl0, 'DL0', obs_date, '{}', pointing)
        else:  # RTA
            config['DL0_data_dir'] = os.path.join(base_path_dl0, 'R0', obs_date, '{}', pointing)

        config['running_analysis_dir'] = os.path.join(
            base_path_dl0, 'running_analysis', obs_date, '{}', pointing, config['prod_id']
        )
        config['analysis_log_dir'] = os.path.join(
            base_path_dl0, 'analysis_logs', obs_date, '{}', pointing, config['prod_id']
        )
        config['DL1_data_dir'] = os.path.join(
            base_path_dl0, 'DL1', obs_date, '{}', pointing, config['prod_id']
        )
        config['DL2_data_dir'] = os.path.join(
            base_path_dl0, 'DL2', obs_date, '{}', pointing, config['prod_id']
        )
        config['IRFs_dir'] = os.path.join(
            base_path_dl0, 'IRF', obs_date, pointing, config['prod_id']
        )

        if base_path_dl0 == '/fefs/aswg/data/mc':  # lstanalyzer user
            config['model_dir'] = os.path.join('/fefs/aswg/data/', 'models', obs_date, pointing, config['prod_id'])
        else:
            # user case, model dir in same dir as DL0, DL1, DL2, running...
            config['model_dir'] = os.path.join(base_path_dl0, 'models', obs_date, pointing, config['prod_id'])

    else:  # Prod5
        # TODO correct the path for all the prod5_* at the LP_cluster
        #  as they were run as $ZENITH/$POINTING instead of $POINTING/$ZENITH/

        config['gammas_offsets'] = offset_gammas

        if workflow_kind == 'lstchain':
            config['DL0_data_dir'] = os.path.join(base_path_dl0, 'DL0', obs_date, '{}', zenith, pointing)
        else:  # RTA
            config['DL0_data_dir'] = os.path.join(base_path_dl0, 'R0', obs_date, '{}', zenith, pointing)

        config['running_analysis_dir'] = os.path.join(
            base_path_dl0, 'running_analysis', obs_date, '{}', zenith, pointing, config['prod_id']
        )
        config['analysis_log_dir'] = os.path.join(
            base_path_dl0, 'analysis_logs', obs_date, '{}', zenith, pointing, config['prod_id']
        )
        config['DL1_data_dir'] = os.path.join(
            base_path_dl0, 'DL1', obs_date, '{}', zenith, pointing, config['prod_id']
        )
        config['DL2_data_dir'] = os.path.join(
            base_path_dl0, 'DL2', obs_date, '{}', zenith, pointing, config['prod_id']
        )
        config['IRFs_dir'] = os.path.join(
            base_path_dl0, 'IRF', obs_date, zenith, pointing, config['prod_id']
        )

        if base_path_dl0 == '/fefs/aswg/data/mc':  # lstanalyzer user
            config['model_dir'] = os.path.join(
                '/fefs/aswg/data/', 'models', obs_date, zenith, pointing, config['prod_id']
            )
        else:
            # user case, model dir in same dir as DL0, DL1, DL2, running...
            config['model_dir'] = os.path.join(base_path_dl0, 'models', obs_date, zenith, pointing, config['prod_id'])

    # print the PATH and prod_id confirmation

    print(f'\n\n\t ************ - {workflow_kind} {prod_type} - WORKFLOW KIND - ************ \n\n'
          f'\nSimtel DL0 files are going to be searched at  \n\n   '
          f'\t{config["DL0_data_dir"].format(str("""{""") + ",".join(config["all_particles"]) + str("""}"""))}\n\n'
          f'The following directories and all the information within them will be either created or overwritten:\n'
          f'[subdirectories with a same PROD_ID and analysed the same day]\n\n'
          f'\t{config["running_analysis_dir"].format(str("""{""") + ",".join(config["all_particles"]) + str("""}"""))}\n'
          f'\t{config["DL1_data_dir"].format(str("""{""") + ",".join(config["all_particles"]) + str("""}"""))}\n'
          f'\t{config["DL2_data_dir"].format(str("""{""") + ",".join(config["all_particles"]) + str("""}"""))}\n'
          f'\t{config["analysis_log_dir"].format(str("""{""") + ",".join(config["all_particles"]) + str("""}"""))}\n'
          f'\t{config["IRFs_dir"]}\n'
          f'\t{config["model_dir"]}\n'
          f'\n\tPROD_ID to be used: {config["prod_id"]}\n'
          )

    print("Stages to be run:")
    for stage in config['stages_to_run']:
        print(f" - {stage}")
    print(f"   - Merging options. No-image argument: {config['merging_no_image']}")
    print("\n")

    return config


def save_log_to_file(dictionary, output_file, log_format, workflow_step=None):
    """
    Dumps a dictionary (log) into a dicts of dicts with keys each of the pipeline stages.

    Parameters
    ----------
    dictionary : dict
        The dictionary to be dumped to a file
    output_file : str
        Output file to store the log
    log_format : str
        The way the data will be dumped to the output file. Either using yaml or just writing a dictionary as plain text
    workflow_step : str
        Step of the workflow, to be recorded in the log

    Returns
    -------
        None
    """
    if workflow_step is None:
        workflow_step = 'NoKEY'

    dict2log = {workflow_step: dictionary}

    if log_format == 'yml':
        with open(output_file, 'a+') as fileout:
            yaml.dump(dict2log, fileout)
    else:
        with open(output_file, 'a+') as fout:
            fout.write('\n\n  *******************************************\n')
            fout.write(f'   *** Log from the {workflow_step} stage \n')
            fout.write('  *******************************************\n')
            fout.write(pprint.pformat(dict2log))


def create_dict_with_dl1_filenames(dl1_directory, particles_loop, gamma_offsets=None):
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
    gamma_offsets : list

    Returns
    -------
    dl1_filename_directory : dict
        dictionary with the name (and absolute path) of the dl1 files with the name of the particles set as key of the
        dictionary

             dl1_filename_directory[particle].keys() = ['train_path_and_outname_dl1', 'test_path_and_outname_dl1']
    """
    dl1_filename_directory = {}

    for particle in particles_loop:
        if gamma_offsets is not None and particle == 'gamma':
            for off in gamma_offsets:
                _particle = particle + off
                dl1_filename_directory[_particle] = {'training': {}, 'testing': {}}

                dl1_filename_directory[_particle]['training']['train_path_and_outname_dl1'] = \
                    glob.glob(os.path.join(
                        os.path.join(off, dl1_directory.format(particle)),
                        '*training*.h5'
                    ))[0]
                dl1_filename_directory[_particle]['testing']['test_path_and_outname_dl1'] = \
                    glob.glob(os.path.join(
                        os.path.join(off, dl1_directory.format(particle)),
                        '*testing*.h5'
                    ))[0]
        else:
            dl1_filename_directory[particle] = {'training': {}, 'testing': {}}
            dl1_filename_directory[particle]['training']['train_path_and_outname_dl1'] = \
                glob.glob(os.path.join(dl1_directory.format(particle), '*training*.h5'))[0]
            dl1_filename_directory[particle]['testing']['test_path_and_outname_dl1'] = \
                glob.glob(os.path.join(dl1_directory.format(particle), '*testing*.h5'))[0]

    return dl1_filename_directory


def batch_mc_production_check(jobids_from_r0_to_dl1, jobids_from_merge, jobids_from_train_pipe,
                              jobids_from_dl1_to_dl2, jobids_from_dl2_to_irf, prod_id, log_file, log_debug_file,
                              scancel_file):
    """
    Check that the dl1_to_dl2 stage, and therefore, the whole workflow has ended correctly.
    The machine information of each job will be dumped to the file.
    The file will take the form `check_MC_prodID_{prod_id}_OK.txt`

    Parameters
    ----------
    jobids_from_r0_to_dl1 : str
        jobs from the dl1_to_dl2 stage
    prod_id : str
        MC Production ID.
    jobids_from_merge :  str
    jobids_from_train_pipe : str
    jobids_from_dl1_to_dl2: str
    jobids_from_dl2_to_irf: str
    log_file: str
    log_debug_file: str
    scancel_file: str

    Returns
    -------
    debug_log : dict
        Dict with the jobid of the batched job to be stored in the `debug file`

    """
    debug_log = {}
    all_pipeline_jobs = []

    if jobids_from_r0_to_dl1 != '':
        all_pipeline_jobs.append(jobids_from_r0_to_dl1)
    if jobids_from_merge != '':
        all_pipeline_jobs.append(jobids_from_merge)
    if jobids_from_train_pipe != '':
        all_pipeline_jobs.append(jobids_from_train_pipe)
    if jobids_from_dl1_to_dl2 != '':
        all_pipeline_jobs.append(jobids_from_dl1_to_dl2)

    if jobids_from_dl2_to_irf != '':
        all_pipeline_jobs.append(jobids_from_dl2_to_irf)
        last_stage = jobids_from_dl2_to_irf
    else:  # RTA case. Although this should be improved
        last_stage = jobids_from_dl1_to_dl2

    all_pipeline_jobs = ','.join(all_pipeline_jobs)

    # Save machine info into the check file
    cmd_wrap = f'touch check_MC_{prod_id}.txt; '
    cmd_wrap += f'sacct --format=jobid,jobname,nodelist,cputime,state,exitcode,avediskread,maxdiskread,avediskwrite,' \
                f'maxdiskwrite,AveVMSize,MaxVMSize,avecpufreq,reqmem -j {all_pipeline_jobs} >> ' \
                f'check_MC_{prod_id}.txt; mkdir -p logs_{prod_id}; ' \
                f'mv slurm-* check_MC_{prod_id}.txt logs_{prod_id}; ' \
                f'rm {scancel_file}; ' \
                f'cp config_MC_prod.yml logs_{prod_id}/config_MC_prod_{prod_id}.yml; ' \
                f'mv {log_file} {log_debug_file} IRFFITSWriter.provenance.log logs_{prod_id};'

    batch_cmd = f'sbatch -p short --parsable --dependency=afterok:{last_stage} -J prod_check ' \
                f'--wrap="{cmd_wrap}"'

    jobid = os.popen(batch_cmd).read().strip('\n')
    print(f'\n\tSubmitted batch CHECK-job {jobid}\n')

    # and in case the code brakes, here there is a summary of all the jobs by stages
    debug_log[jobid] = 'single jobid batched to check that all the dl1_to_dl2 stage jobs finish correctly.'
    debug_log['sbatch_cmd'] = cmd_wrap
    debug_log['SUMMARY_r0_dl1'] = jobids_from_r0_to_dl1
    debug_log['SUMMARY_merge'] = jobids_from_merge
    debug_log['SUMMARY_train_pipe'] = jobids_from_train_pipe
    debug_log['SUMMARY_dl1_dl2'] = jobids_from_dl1_to_dl2
    debug_log['SUMMARY_dl2_irfs'] = jobids_from_dl2_to_irf

    return jobid, debug_log


def create_log_files(production_id):
    """
    Manages filenames (and overwrites if needed) log files.

    Parameters
    ----------
    production_id : str
        production identifier of the MC production to be launched

    Returns
    -------
    log_file: str
         path and filename of full log file
    debug_file: str
        path and filename of reduced (debug) log file
    scancel_file: str
        path and filename of bash file to cancel all the scheduled jobs
    """
    log_file = f'./log_onsite_mc_r0_to_dl3_{production_id}.yml'
    debug_file = f'./log_reduced_{production_id}.yml'
    scancel_file = f'./scancel_{production_id}.sh'

    # scancel prod file needs chmod +x rights !
    open(scancel_file, 'w').close()
    os.chmod(scancel_file, 0o755)  # -rwxr-xr-x

    # If the file exists, i,e., the pipeline has been relaunched, erase it
    if os.path.exists(log_file):
        os.remove(log_file)
    if os.path.exists(debug_file):
        os.remove(debug_file)

    return log_file, debug_file, scancel_file


def update_scancel_file(scancel_filename, jobids_to_update):
    """
    Bash file containing the slurm command to cancel multiple jobs.
    The file will be updated after every batched stage and will be erased in case the whole MC prod succeed without
    errors.

    Parameters
    ----------
    scancel_filename: str
        filename that cancels the whole MC production
    jobids_to_update: str
        job_ids to be included into the the file
    """
    if os.stat(scancel_filename).st_size == 0:
        with open(scancel_filename, 'r+') as f:
            f.write(f'scancel {jobids_to_update}')

    else:
        with open(scancel_filename, 'a') as f:
            f.write(f',{jobids_to_update}')

