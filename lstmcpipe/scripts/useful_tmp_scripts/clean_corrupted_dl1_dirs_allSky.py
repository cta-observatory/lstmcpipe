#!/usr/bin/env python


import subprocess as sp
from pathlib import Path
from lstmcpipe.config.paths_config import PathConfigAllSkyFull

prod_id = '20220511_allsky_std'
list_decs = ['dec_2276', 'dec_3476', 'dec_4822', 'dec_931', 'dec_min_413']
source_env = "source /fefs/aswg/software/conda/etc/profile.d/conda.sh; conda activate lstchain-v0.9.6; "

pcf = PathConfigAllSkyFull(prod_id, list_decs)


def find_train_dirs(config):
    dirs = []
    for dec, train in config.train_configs.items():
        for particle in train.training_particles:
            for pointing in train.pointing_dirs(particle):
                dirs.append(train.dl1_dir(particle, pointing))

    return dirs


def find_test_dirs(config):
    dirs = []
    for dec, test in config.test_configs.items():
        for pointing in test.pointing_dirs():
            dirs.append(test.dl1_dir(pointing))

    return dirs


if __name__ == '__main__':
    train_dirs = find_train_dirs(pcf)
    test_dirs = find_test_dirs(pcf)

    for dir_i in train_dirs + test_dirs:
        if not Path(dir_i).exists():
            continue

        node = dir_i.split('/')[-1]

        error_file = f'./clean_dir_{prod_id}_{node}_%j.e'
        output_file = f'./clean_dir_{prod_id}_{node}_%j.o'

        cmd = f'{source_env} python ./cleandir.py {dir_i}'

        slurm_cmd = f'sbatch --parsable --error={error_file} --output={output_file} --wrap="{cmd}"'

        run_command = sp.Popen(slurm_cmd, shell=True, stdout=sp.PIPE, stderr=sp.STDOUT, encoding='utf-8')
        stdout, _ = run_command.communicate()

        if run_command.returncode != 0:
            raise ValueError(
                f"Running {run_command} failed with return code {run_command.returncode}" f", output:" f" \n {stdout}"
            )
