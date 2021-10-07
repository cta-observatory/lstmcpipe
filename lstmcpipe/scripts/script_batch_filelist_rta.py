#!/usr/bin/env python

import argparse
import subprocess
from distutils.util import strtobool
import os


def main():
    parser = argparse.ArgumentParser(
        description="Batches the r0_to_dl1 hiperta stage for all the files "
        "within a text file."
    )
    parser.add_argument(
        "--file_list",
        "-f",
        type=str,
        dest="file_list",
        help="Path to file containing list of R0 lstchain file to be processed.",
        required=True,
        nargs="+",
    )
    parser.add_argument(
        "--output_dir",
        "-o",
        type=str,
        dest="output_dir",
        help="hiperta_r0_to_dl1 output directory argument.",
        required=True,
    )
    parser.add_argument(
        "--config_file",
        "-c",
        type=str,
        dest="config_file",
        help="hiperta_r0_to_dl1 configuration file argument.",
        required=True,
    )
    parser.add_argument(
        "--keep_file",
        "-k",
        type=lambda x: bool(strtobool(x)),
        dest="keep_file",
        help="Keep output of hiperta. Set by default to False",
        default=False,
    )
    parser.add_argument(
        "--debug_mode",
        "-d",
        type=lambda x: bool(strtobool(x)),
        dest="debug_mode",
        help="Activate debug mode (add cleaned mask in the output hdf5). Set by default to False",
        default=False,
    )
    args = parser.parse_args()

    task_id = int(os.environ["SLURM_ARRAY_TASK_ID"])
    file_for_this_job = args.file_list[task_id]
    print("Using file: ", file_for_this_job)

    with open(file_for_this_job, "r") as filelist:
        for file in filelist:
            file = file.strip("\n")

            cmd = [
                "lstmcpipe_hiperta_r0_to_dl1lstchain",
                f"-i {file}",
                f"-o {args.output_dir}",
                f"-k {args.keep_file}",
                f"-d {args.debug_mode}",
            ]
            if args.config_file:
                cmd.append("--config={}".format(args.config_file))

            subprocess.run(cmd)


if __name__ == "__main__":
    main()
