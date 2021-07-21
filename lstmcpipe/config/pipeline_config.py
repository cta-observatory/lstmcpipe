import os
from pathlib import Path
import yaml
import calendar
import lstchain
import logging


def load_config(config_path):
    with open(config_path) as f:
        loaded_config = yaml.safe_load(f)
    return parse_config_and_handle_global_vars(loaded_config)


def parse_config_and_handle_global_vars(loaded_config):
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
    config = {}

    # Allowed options
    allowed_workflows = ['hiperta', 'lstchain', 'ctapipe']
    allowed_prods = ['prod3', 'prod5']
    allowed_obs_date = ['20190415', '20200629_prod5', '20200629_prod5_trans_80']

    # Check allowed cases
    workflow_kind = loaded_config['workflow_kind']
    if workflow_kind not in allowed_workflows:
        raise ValueError(
            f'Please select an allowed `workflow_kind`: {allowed_workflows}'
        )

    prod_type = loaded_config['prod_type']
    if prod_type not in allowed_prods:
        raise ValueError(
            f'Please selected an allowed production type: {allowed_prods}.'
        )

    obs_date = loaded_config['obs_date']
    # and incompatible possibilities
    if (
            (prod_type == 'prod3' and obs_date != '20190415')
            or (prod_type == 'prod5' and obs_date == '20190415')
    ):
        raise ValueError(
            'This prod_type and obs_date combination is not possible.'
        )

    prod_id = loaded_config.get('prod_id', 'v00')
    stages_to_be_run = loaded_config['stages_to_be_run']
    merging_options = loaded_config['merging_options']['no_image']
    base_path_dl0 = loaded_config['base_path_dl0']
    pointing = loaded_config['pointing']
    zenith = loaded_config['zenith']
    particles = loaded_config['particles']
    offset_gammas = loaded_config['offset_gammas']

    # Prod_id syntax
    t = calendar.datetime.date.today()
    year, month, day = f"{t.year:04d}", f"{t.month:02d}", f"{t.day:02d}"
    if workflow_kind == 'lstchain':
        base_prod_id = f'{year}{month}{day}_v{lstchain.__version__}'
    elif workflow_kind == 'ctapipe':
        import ctapipe
        base_prod_id = f'{year}{month}{day}_vctapipe{ctapipe.__version__}'
    elif workflow_kind == 'hiperta':  # RTA
        # TODO parse version from hiPeRTA module
        base_prod_id = f'{year}{month}{day}_vRTA300_v{lstchain.__version__}'

    # Create the final config structure to be passed to the pipeline
    # 1 - Prod_id
    if 'trans_80' in obs_date:
        suffix_id = '_{}_trans_80_{}'.format(prod_type, prod_id)
    else:
        suffix_id = '_{}_{}'.format(prod_type, prod_id)
    config['prod_id'] = base_prod_id + suffix_id

    # 2 - Parse source environment correctly
    src_env = (f"source {loaded_config['source_environment']['source_file']}; "
               f"conda activate {loaded_config['source_environment']['conda_env']}; "
               )
    config['source_environment'] = src_env

    # 3 - particles loop
    config['source_environment'] = src_env
    config['all_particles'] = particles

    # 3.1 - Gammas' offsets
    if obs_date == '20200629_prod5' or obs_date == '20200629_prod5_trans_80':  # prod5 case
        config['gamma_offs'] = offset_gammas
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
        pointing_zenith = pointing

    else:  # Prod5
        # TODO correct the path for all the prod5_* at the LP_cluster
        #  as they were run as $ZENITH/$POINTING instead of $POINTING/$ZENITH/
        pointing_zenith = os.path.join(zenith, pointing)
        config['gammas_offsets'] = offset_gammas

    if workflow_kind == 'lstchain' or workflow_kind == 'ctapipe':
        config['DL0_data_dir'] = os.path.join(base_path_dl0, 'DL0', obs_date, '{}', pointing_zenith)
    else:  # RTA
        config['DL0_data_dir'] = os.path.join(base_path_dl0, 'R0', obs_date, '{}', pointing_zenith)

    config['running_analysis_dir'] = os.path.join(
        base_path_dl0, 'running_analysis', obs_date, '{}', pointing_zenith, config['prod_id']
    )
    config['analysis_log_dir'] = os.path.join(
        base_path_dl0, 'analysis_logs', obs_date, '{}', pointing_zenith, config['prod_id']
    )
    config['DL1_data_dir'] = os.path.join(
        base_path_dl0, 'DL1', obs_date, '{}', pointing_zenith, config['prod_id']
    )
    config['DL2_data_dir'] = os.path.join(
        base_path_dl0, 'DL2', obs_date, '{}', pointing_zenith, config['prod_id']
    )
    config['IRFs_dir'] = os.path.join(
        base_path_dl0, 'IRF', obs_date, pointing_zenith, config['prod_id']
    )

    if base_path_dl0 == '/fefs/aswg/data/mc':  # lstanalyzer user
        config['model_dir'] = os.path.join(
            '/fefs/aswg/data/', 'models', obs_date, pointing_zenith, config['prod_id']
        )
    else:
        # user case, model dir in same dir as DL0, DL1, DL2, running...
        config['model_dir'] = os.path.join(base_path_dl0, 'models', obs_date, pointing_zenith, config['prod_id'])

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
