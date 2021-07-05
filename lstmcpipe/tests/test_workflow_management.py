from pathlib import Path
from os.path import join, dirname, realpath

PROJECT_DIR = Path(dirname(realpath(__file__))).parent


def test_load_yml_config():
    from ..workflow_management import load_yml_config

    config = load_yml_config(join(PROJECT_DIR, 'config_MC_prod.yml'))
    assert type(config) == dict


def test_parse_config_and_handle_global_vars():
    from ..workflow_management import parse_config_and_handle_global_vars

    config = parse_config_and_handle_global_vars(join(PROJECT_DIR, 'config_MC_prod.yml'))

    keys_read_by_r0_dl3 = ['prod_id', 'prod_type', 'workflow_kind', 'source_environment',
                           'stages_to_run', 'all_particles', 'DL0_data_dir', 'DL1_data_dir',
                           'DL2_data_dir', 'running_analysis_dir', 'gamma_offs', 'merging_no_image']

    assert type(config) == dict
    assert set(keys_read_by_r0_dl3).issubset(list(config.keys()))
