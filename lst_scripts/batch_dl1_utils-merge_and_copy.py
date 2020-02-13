#!/usr//bin/env python3

# E. Garcia, 12/02/2020

import argparse
from .data_management import move_dir_content, check_and_make_dir_without_verification

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

if __name__ == '__main__':
    args = parser.parse_args()

    # check_and_make_dir(args.dest) CANNOT be used because if demands user interaction.

    check_and_make_dir_without_verification(args.dest)
    move_dir_content(args.source, args.dest)
