#!/usr//bin/env python3

import argparse
import os
import shutil


def move_dir_content(src, dest):
    files = os.listdir(src)
    for f in files:
        shutil.move(os.path.join(src, f), dest)
    os.rmdir(src)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="same functions as in merge_and_copy copied here so that"
                                                 "they can be batched.")

    parser.add_argument(' --dl1_dir', type=str,
                        dest='final_dl1_dir',
                        help='final_DL1_dir',
                        )

    parser.add_argument('--run_dl1', type=str,
                        dest='running_DL1_dir',
                        help='running_DL1_dir'
                        )

    parser.add_argument('--logs_dir', type=str,
                        dest='logs_destination_dir',
                        help='logs_destination_dir'
                        )

    parser.add_argument('--indir', type=str,
                        dest='input_dir',
                        help='input_dir'
                        )
    args = parser.parse_args()

    move_dir_content(args.running_DL1_dir, args.final_dl1_dir)
    move_dir_content(args.input_dir, args.logs_destination_dir)
