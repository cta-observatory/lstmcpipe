#!/usr/bin/env python

import os
import shutil
import argparse
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


def main():
    args = parser.parse_args()

    # HiPeRTA config is *.yml
    config_files = [os.path.join(args.source, f) for f in os.listdir(args.source) if f.endswith(('.json', '.yml'))]

    for file in config_files:
        shutil.copyfile(file, os.path.join(args.dest, os.path.basename(file)))


if __name__ == '__main__':
    main()
