# DL1 to DL2 onsite (La Palma cluster)


import sys
import os
import shutil
import random
import argparse
import calendar
from lstchain.io.data_management import *


parser = argparse.ArgumentParser(description="MC R0 to DL1")


parser.add_argument('input_dir', type=str,
                    help='path to the files directory to analyse',
                   )

parser.add_argument('--path_models', '-pm', action='store', type=str,
                    dest='path_models',
                    help='path to the trained models',
                    default=None,
                    )

parser.add_argument('--config_file', '-conf', action='store', type=str,
                    dest='config_file',
                    help='Path to a configuration file. If none is given, a standard configuration is applied',
                    default=None
                    )

args = parser.parse_args()


def main():

    input_dir = args.input_dir
    output_dir = args.input_dir.replace('DL1', 'DL2')

    check_and_make_dir(output_dir)

    print(f"Output dir: {output_dir}")

    file_list = [os.path.join(input_dir, f) for f in os.listdir(args.input_dir) if f.startswith('dl1_')]

    query_continue(f"{len(file_list)} jobs,  ok?")

    for file in file_list:
        cmd = f'lstchain_mc_dl1_to_dl2 -f {file} -p {args.path_models} -o {output_dir}'
        if args.config_file is not None:
            cmd += f'-conf {args.config_file}'

        print(cmd)
        # os.system(cmd)


if __name__ == '__main__':
    main()