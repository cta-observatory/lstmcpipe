#!/usr/bin/env python

# clean directory for DL1 files with wrong parameters table shape
# see https://github.com/cta-observatory/cta-lstchain/issues/978
# simply delete files with wrong table shape


import logging
from pathlib import Path
from ctapipe.io import read_table
from lstchain.io.io import dl1_params_lstcam_key


def clean_dir(root_dir, ncols=56):
    root_dir = Path(root_dir)
    dl1_files = root_dir.rglob('dl1_*.h5')
    for file in dl1_files:
        param_table = read_table(file, dl1_params_lstcam_key)
        if param_table.to_pandas().shape[1] < ncols:
            logging.warning(f"File {file} will be deleted, its param table shape is {param_table.to_pandas().shape}")
            file.unlink()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Clean dir for faulty DL1 files')
    parser.add_argument('directory', type=Path, help='Input directory')
    parser.add_argument(
        '--ncols', dest='ncols', type=int, default=56, help='Number of expected columns in DL1 parameters table'
    )

    args = parser.parse_args()

    logging.basicConfig(filename='cleandir.log', level=logging.DEBUG)
    logging.info(f'Cleaning directory {args.directory}\n\n')

    clean_dir(args.directory, args.ncols)
