#!/usr//bin/env python3

# E. Garcia, 12/02/2020

import argparse
from .data_management import move_dir_content, check_and_make_dir_without_verification
import os
import shutil
from distutils.util import strtobool

parser = argparse.ArgumentParser(description="Batch the check_and_make_dir and move_dir_content stage of the "
                                             "merge_and_copy_dl1 script.")

parser.add_argument('--source', '-s', type=str,
                    dest='source',
                    help='source argument of move_dir_content',
                    )

parser.add_argument('--destination', '-d', type=str,
                    dest='dest',
                    help='destination argument of move_dir_content',
                    )

parser.add_argument('--copy_conf', type=lambda x: bool(strtobool(x)),
                    dest='copy_conf',
                    help='Boolean. Copy the config used to the args.dest directory',
                    default=False
                    )

if __name__ == '__main__':
    args = parser.parse_args()

    if not args.copy_conf:

        # check_and_make_dir(args.dest) CANNOT be used because if demands user interaction.

        check_and_make_dir_without_verification(args.dest)
        move_dir_content(args.source, args.dest)

    else:  # Re use the same script to copy the config file to the final_dir

        config_files = [os.path.join(args.source, f) for f in os.listdir(args.source) if f.endswith('.json')]
        for file in config_files:
            shutil.copyfile(file, os.path.join(args.dest, os.path.basename(file)))
