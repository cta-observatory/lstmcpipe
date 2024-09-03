"""
Script to generate a mini production tree with symlinks to a few simtel files and the corresponding path config.
This is used to test lstmcpipe on a small prod
"""

from pathlib import Path
from tqdm import tqdm
from datetime import date
import os
import argparse

from lstmcpipe.config import paths_config
from lstmcpipe.utils import dump_lstchain_std_config


def generate_tree(base_dir, working_dir, nfiles):
    """
    Walk the base dir looking for simtels files
    When a directory contains simtels files, it's tree structure is duplicated into the working dir
    and nfiles are symlinked there
    """
    base_dir = Path(base_dir)
    working_dir = Path(working_dir)

    for root, dirs, files in tqdm(os.walk(base_dir)):
        simtel_files = [os.path.join(root, file) for file in files if file.endswith('.simtel.gz')]
        if simtel_files:
            for file in simtel_files[:nfiles]:
                target = working_dir.joinpath(Path(file).relative_to(base_dir))
                target.parent.mkdir(parents=True, exist_ok=True)
                if not target.exists():
                    target.symlink_to(file)


def generate_test_prod5trans80(working_dir, nfiles=5, path_to_config_file='.', overwrite=True):
    base_dir = '/fefs/aswg/workspace/lstmcpipe/data/test_data/mc/DL0/20200629_prod5_trans_80/'
    working_dir = os.path.join(working_dir, 'DL0/20200629_prod5_trans_80/')

    generate_tree(base_dir, working_dir, nfiles)

    pc = paths_config.PathConfigProd5Trans80(f'test_prod_{date.today()}')
    pc.base_dir = os.path.join(
        working_dir, '{data_level}/20200629_prod5_trans_80/{particle}/{zenith}/south_pointing/{prod_id}'
    )
    pc.generate()
    pc.save_yml(os.path.join(path_to_config_file, f'test_prod5trans80_{date.today()}.yaml'), overwrite=overwrite)


def generate_test_allsky(
    working_dir,
    nfiles=5,
    path_to_config_file='.',
    decs=['dec_4822', 'dec_931'],
    overwrite=True,
):
    allsky_base_dir = '/fefs/aswg/data/mc/'
    allsky_train_base_dir = os.path.join(allsky_base_dir, 'DL0/LSTProd2/')
    # allsky_test_base_dir = os.path.join(allsky_base_dir, 'DL0/LSTProd2/')
    # working_dir_dl0 = os.path.join(working_dir, 'DL0/LSTProd2/')

    generate_tree(allsky_train_base_dir, working_dir, nfiles)

    pc = paths_config.PathConfigAllSkyFull(f'test_prod_{date.today()}', decs)
    pcdl1ab = paths_config.PathConfigAllSkyFullDL1ab(
        f'test_prod_{date.today()}', f'test_prod_{date.today()}_dl1ab', decs, run_checker=False
    )

    # config training dir are replaced with local ones
    for dec in decs:
        pc.train_configs[dec].base_dir = pc.train_configs[dec].base_dir.replace(allsky_base_dir, working_dir)
        pc.train_configs[dec].base_dir = pc.train_configs[dec].base_dir.replace('AllSky', 'LSTProd2')
        pc.test_configs[dec].base_dir = pc.test_configs[dec].base_dir.replace(allsky_base_dir, working_dir)
        pc.test_configs[dec].base_dir = pc.test_configs[dec].base_dir.replace('AllSky', 'LSTProd2')
        pc.train_configs[dec].training_dir = pc.train_configs[dec].training_dir.replace(allsky_base_dir, working_dir)
        pc.test_configs[dec].testing_dir = pc.test_configs[dec].testing_dir.replace(allsky_base_dir, working_dir)

        pcdl1ab.train_configs[dec].base_dir = pcdl1ab.train_configs[dec].base_dir.replace(allsky_base_dir, working_dir)
        pcdl1ab.train_configs[dec].base_dir = pcdl1ab.train_configs[dec].base_dir.replace('AllSky', 'LSTProd2')
        pcdl1ab.train_configs[dec].source_config.base_dir = pcdl1ab.train_configs[dec].source_config.base_dir.replace(allsky_base_dir, working_dir)
        pcdl1ab.train_configs[dec].source_config.base_dir = pcdl1ab.train_configs[dec].source_config.base_dir.replace('AllSky', 'LSTProd2')
        pcdl1ab.test_configs[dec].base_dir = pcdl1ab.test_configs[dec].base_dir.replace(allsky_base_dir, working_dir)
        pcdl1ab.test_configs[dec].base_dir = pcdl1ab.test_configs[dec].base_dir.replace('AllSky', 'LSTProd2')
        pcdl1ab.test_configs[dec].source_config.base_dir = pcdl1ab.test_configs[dec].source_config.base_dir.replace(allsky_base_dir, working_dir)
        pcdl1ab.test_configs[dec].source_config.base_dir = pcdl1ab.test_configs[dec].source_config.base_dir.replace('AllSky', 'LSTProd2')
        pcdl1ab.train_configs[dec].training_dir = pcdl1ab.train_configs[dec].training_dir.replace(allsky_base_dir, working_dir)
        pcdl1ab.train_configs[dec].source_config.training_dir = pcdl1ab.train_configs[dec].source_config.training_dir.replace(allsky_base_dir, working_dir)
        
        pcdl1ab.test_configs[dec].testing_dir =  pcdl1ab.test_configs[dec].testing_dir.replace(allsky_base_dir, working_dir)
        pcdl1ab.test_configs[dec].source_config.testing_dir = pcdl1ab.test_configs[dec].source_config.testing_dir.replace(allsky_base_dir, working_dir)
                
    
    pc.generate()
    for stage_name, stage_steps in pc.paths.items():
        for step in stage_steps:
            step['extra_slurm_options'] = {'partition': 'short'}
    pc.save_yml(os.path.join(path_to_config_file, f'test_LSTProd2_{date.today()}.yaml'), overwrite=overwrite)

    pcdl1ab.generate()
    for stage_name, stage_steps in pcdl1ab.paths.items():
        for step in stage_steps:
            step['extra_slurm_options'] = {'partition': 'short'}
    pcdl1ab.save_yml(os.path.join(path_to_config_file, f'test_LSTProd2_{date.today()}_dl1ab.yaml'), overwrite=overwrite)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Generate test tree')

    parser.add_argument('prod_type', type=str, help='prod5trans80 or lstprod2')
    parser.add_argument('--nfiles', type=int, default=2, help='Number of files')
    parser.add_argument('--path_config_file', type=Path, default='.', help='Path to save the corresponding config file')
    parser.add_argument(
        '--working_dir',
        type=Path,
        default=None,
        help='Your working dir where the DL0 tree will be generated, '
        '(such as /fefs/aswg/workspace/firstname.surname/data/mc/)',
    )

    args = parser.parse_args()

    if args.working_dir is None:
        user = os.environ['USER']
        if user == 'lstanalyzer':
            working_dir = '/fefs/aswg/workspace/lstmcpipe/data/mc'
        else:
            working_dir = f'/fefs/aswg/workspace/{user}/data/mc/'
        if not Path(working_dir).exists():
            raise FileNotFoundError(f"working dir {working_dir} does not exist, provide one")
    else:
        working_dir = args.working_dir
    print(f"working directory: {working_dir}")

    if args.prod_type == 'prod5trans80':
        generate_test_prod5trans80(working_dir, args.nfiles, args.path_config_file)
    elif args.prod_type == 'lstprod2':
        generate_test_allsky(working_dir, args.nfiles, args.path_config_file)
    else:
        raise NotImplementedError("Unknown prod type")

    dump_lstchain_std_config(filename=Path(args.path_config_file, 'lstchain_config.json'), overwrite=True)
