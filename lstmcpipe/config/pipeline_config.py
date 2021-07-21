import os
from pathlib import Path
import yaml
import calendar
import lstchain
import logging


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
    allowed_workflows = ['hiperta', 'lstchain', 'ctapipe']
    allowed_prods = ['prod3', 'prod5']
    allowed_obs_date = ['20190415', '20200629_prod5', '20200629_prod5_trans_80']

    # Load configuration
    workflow_kind = loaded_config['workflow_kind']
    custom_prod_id = loaded_config.get('prod_id', 'v00')
    stages_to_be_run = loaded_config['stages_to_be_run']
    merging_options = loaded_config['merging_options']['no_image']

    base_path_dl0 = loaded_config['base_path_dl0']
    prod_type = loaded_config['prod_type']
    obs_date = loaded_config['obs_date']
    pointing = loaded_config['pointing']
    zenith = loaded_config['zenith']
    particles = loaded_config['particles']
    offset_gammas = loaded_config['offset_gammas']

    # Check allowed cases
    if workflow_kind not in allowed_workflows or prod_type not in allowed_prods:
        raise ValueError(f'Please select an allowed `workflow_kind`: {allowed_workflows} or an - allowed '
                         f'production type: {allowed_prods} in the config YAML file; {yml_file}.'
                         )

    # and incompatible possibilities
    if (prod_type == 'prod3' and obs_date != '20190415') or (prod_type == 'prod5' and obs_date == '20190415'):
        raise ValueError('This prod_type and obs_date combination is not possible.'
                         f'Please change it in the config YAML file; {yml_file}.'
                         )

    # Prod_id syntax
    today = calendar.datetime.date.today()
    if workflow_kind == 'lstchain':
        base_prod_id = f'{today.year:04d}{today.month:02d}{today.day:02d}_v{lstchain.__version__}'
    elif workflow_kind == 'ctapipe':
        import ctapipe
        base_prod_id = f'{today.year:04d}{today.month:02d}{today.day:02d}_v{ctapipe.__version__}'
    elif workflow_kind == 'hiperta':  # RTA
        # TODO parse version from hiPeRTA module
        base_prod_id = f'{today.year:04d}{today.month:02d}{today.day:02d}_vRTA300_v{lstchain.__version__}'
    else:
        raise ValueError('Please select an allowed `workflow_kind`: {allowed_workflows} in the config YAML file; {yml_file}.')

    # Create the final config structure to be passed to the pipeline
    # 1 - Prod_id
    if 'trans_80' in obs_date:
        suffix_id = '_{}_trans_80_{}'.format(prod_type, custom_prod_id)
    else:
        suffix_id = '_{}_{}'.format(prod_type, custom_prod_id)
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
        raise ValueError(
            f'Please select an allowed `obs_date`: {allowed_obs_date} in the config YAML file; {yml_file}.'
        )

    # 4 - Stages to be run
    config['stages_to_run'] = stages_to_be_run
    config['merging_no_image'] = merging_options

    # 5 - production workflow and type
    config['workflow_kind'] = workflow_kind
    config['prod_type'] = prod_type

    # 6 - Global paths
    if prod_type == 'prod3':
        p = pointing

    else:  # Prod5
        # TODO correct the path for all the prod5_* at the LP_cluster
        #  as they were run as $ZENITH/$POINTING instead of $POINTING/$ZENITH/
        p = os.path.join(zenith, pointing)
        config['gammas_offsets'] = offset_gammas

    if workflow_kind == 'lstchain' or workflow_kind =='ctapipe':
        config['DL0_data_dir'] = os.path.join(base_path_dl0, 'DL0', obs_date, '{}', p)
    else:  # RTA
        config['DL0_data_dir'] = os.path.join(base_path_dl0, 'R0', obs_date, '{}', p)

    config['running_analysis_dir'] = os.path.join(
        base_path_dl0, 'running_analysis', obs_date, '{}', p, config['prod_id']
    )
    config['analysis_log_dir'] = os.path.join(
        base_path_dl0, 'analysis_logs', obs_date, '{}', p, config['prod_id']
    )
    config['DL1_data_dir'] = os.path.join(
        base_path_dl0, 'DL1', obs_date, '{}', p, config['prod_id']
    )
    config['DL2_data_dir'] = os.path.join(
        base_path_dl0, 'DL2', obs_date, '{}', p, config['prod_id']
    )
    config['IRFs_dir'] = os.path.join(
        base_path_dl0, 'IRF', obs_date, p, config['prod_id']
    )

    if base_path_dl0 == '/fefs/aswg/data/mc':  # lstanalyzer user
        config['model_dir'] = os.path.join(
            '/fefs/aswg/data/', 'models', obs_date, p, config['prod_id']
        )
    else:
        # user case, model dir in same dir as DL0, DL1, DL2, running...
        config['model_dir'] = os.path.join(base_path_dl0, 'models', obs_date, p, config['prod_id'])

    # print the PATH and prod_id confirmation

#    print(f'\n\n\t ************ - {workflow_kind} {prod_type} - WORKFLOW KIND - ************ \n\n'
#          f'\nSimtel DL0 files are going to be searched at  \n\n   '
#          f'\t{config["DL0_data_dir"].format(str("""{""") + ",".join(config["all_particles"]) + str("""}"""))}\n\n'
#          f'The following directories and all the information within them will be either created or overwritten:\n'
#          f'[subdirectories with a same PROD_ID and analysed the same day]\n\n'
#          f'\t{config["running_analysis_dir"].format(str("""{""") + ",".join(config["all_particles"]) + str("""}"""))}\n'
#          f'\t{config["DL1_data_dir"].format(str("""{""") + ",".join(config["all_particles"]) + str("""}"""))}\n'
#          f'\t{config["DL2_data_dir"].format(str("""{""") + ",".join(config["all_particles"]) + str("""}"""))}\n'
#          f'\t{config["analysis_log_dir"].format(str("""{""") + ",".join(config["all_particles"]) + str("""}"""))}\n'
#          f'\t{config["IRFs_dir"]}\n'
#          f'\t{config["model_dir"]}\n'
#          f'\n\tPROD_ID to be used: {config["prod_id"]}\n'
#          )

    print("Stages to be run:")
    for stage in config['stages_to_run']:
        print(f" - {stage}")
    print(f"   - Merging options. No-image argument: {config['merging_no_image']}")
    print("\n")

    return config
