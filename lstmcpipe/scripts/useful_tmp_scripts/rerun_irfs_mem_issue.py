"""
Run python rerun_irfs_mem_issue.py lstmcpipe_config.yaml
"""

from ruamel.yaml import YAML
import sys
from pathlib import Path


yaml = YAML()

filename = Path(sys.argv[1])

cfg = yaml.load(open(filename).read())

cfg['stages_to_run'] = ['dl2_to_irfs']
cfg['stages'].pop('r0_to_dl1', None)
cfg['stages'].pop('merge_dl1', None)
cfg['stages'].pop('train_pipe', None)
cfg['stages'].pop('dl1_to_dl2', None)

to_rerun = []
for p in cfg['stages']['dl2_to_irfs']:
    if not Path(p['output']).is_file():
        print(p['output'])
        p['extra_slurm_options'] = {'mem':'6GB'}
        to_rerun.append(p)

cfg['stages']['dl2_to_irfs'] = to_rerun
print(f"{len(to_rerun)} irfs to re-produce")


output_filename = filename.parent.joinpath(f'{filename.stem}_rerun.yaml')

if to_rerun and not Path(output_filename).exists():
    print(f"Run lstmcpipe -c {output_filename}")
    yaml.dump(cfg, open(output_filename, 'w'))
elif Path(output_filename).exists():
    raise FileExistsError(output_filename)
