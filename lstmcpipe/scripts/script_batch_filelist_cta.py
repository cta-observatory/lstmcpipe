#!/usr/bin/env python
#SBATCH --output=r0dl1_cta_%A_%a.out
#SBATCH --error=r0dl1_cta_%A_%a.err

import argparse
import subprocess
from os.path import join, basename
from os import environ


def main():
    parser = argparse.ArgumentParser(description="Batches the ctapipe-stage1 for all the files "
                                                 "within a text file.")
    parser.add_argument('--file_list', '-f', type=str,
                        dest='file_list',
                        help='Path to file containing list of DL0 simtel files to be processed.',
                        required=True,
                        nargs="+",)
    parser.add_argument('--output_dir', '-o', type=str,
                        dest='output_dir',
                        help='ctapipe-stage1 output directory argument.',
                        required=True)
    parser.add_argument('--config_file', '-c', type=str,
                        dest='config_file',
                        help='ctapipe-stage1 configuration file argument.',
                        required=True)
    args = parser.parse_args()

    task_id = int(environ["SLURM_ARRAY_TASK_ID"])
    file_for_this_job =  args.file_list[task_id]
    print("Using file: ", file_for_this_job)
    
    with open(file_for_this_job, 'r') as filelist:
        for file in filelist:
            file = file.strip('\n')

            output = join(
                args.output_dir,
                basename(file.replace('.simtel.gz', '.dl1.h5'))
            )

            cmd = ['ctapipe-stage1',
                   f'--input={file}',
                   f'--output={output}'
                   ]
            if args.config_file:
                cmd += '--config={}'.format(args.config_file)
            subprocess.run(cmd)


if __name__ == '__main__':
    main()
