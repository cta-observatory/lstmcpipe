"""
Script to generate a mini production tree with symlinks to a few simtel files and the corresponding path config.
This is used to test lstmcpipe on a small prod
"""

from pathlib import Path
from tqdm import tqdm
from datetime import date
import os

from lstmcpipe.config import paths_config

lstmcpipe_base_dir = Path('/fefs/aswg/workspace/lstmcpipe/data/test_data/mc/')
aswg_base_dir = Path('/fefs/aswg/data/mc/')

nfiles = 4

for particle in tqdm(['gamma-diffuse', 'proton', 'electron', 'gamma']):
    for root, dirs, files in os.walk(aswg_base_dir.joinpath(f'DL0/20200629_prod5_trans_80/{particle}/zenith_20deg/south_pointing')):
        simtel_files = [os.path.join(root, file) for file in files if file.endswith('.simtel.gz')]
        if simtel_files:
            for file in simtel_files[:nfiles]:
                target = lstmcpipe_base_dir.joinpath(Path(file).relative_to(aswg_base_dir))
                target.parent.mkdir(parents=True, exist_ok=True)
                if not target.exists():
                    target.symlink_to(file)
                                     

pc = paths_config.PathConfigProd5Trans80(f'test_prod_{date.today()}')

pc.base_dir = '/fefs/aswg/workspace/lstmcpipe/data/test_data/mc/{data_level}/20200629_prod5_trans_80/{particle}/{zenith}/south_pointing/{prod_id}'

pc.generate()

pc.save_yml(f'test_prod_{date.today()}.yaml', overwrite=True)

