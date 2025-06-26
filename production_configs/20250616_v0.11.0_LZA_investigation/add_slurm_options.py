import sys
from pathlib import Path
from ruamel.yaml import YAML


def add_slurm_options(config_file):
    """
    Add SLURM options to each step in the given YML config file.
    This should ease job handling on the cluster, allowing some jobs to be scheduled in a 12h window.
    It also uses the `--nice` SLURM option to give priority to lstosa jobs.
    """
    yaml = YAML()
    yaml.preserve_quotes = True
    config = yaml.load(open(config_file))

    for stage_name, stage in config['stages'].items():
        for ii, step in enumerate(stage):
            slurm_options = step.get('extra_slurm_options', {})
            if 'time' not in slurm_options:
                if stage_name == 'r0_to_dl1':
                    slurm_options['time'] = '11:30:00'
                elif stage_name == 'train_pipe':
                    slurm_options['time'] = '02-00:00:00'
                elif stage_name == 'dl1ab':
                    slurm_options['time'] = '08:00:00'
                elif stage_name == 'merge_dl1' and ('GammaDiffuse' in step['input'] or 'Protons' in step['input']):
                    slurm_options['time'] = '08:00:00'
                else:
                    slurm_options['partition'] = 'short'
            if 'nice' not in slurm_options:
                slurm_options['nice'] = 10
            stage[ii]['extra_slurm_options'] = slurm_options

    with open(config_file, 'w') as f:
        yaml.dump(config, f)


if __name__ == '__main__':
    for cfg_file in Path('.').glob('NSB-*/lstmcpipe*.yml'):
        add_slurm_options(cfg_file)
