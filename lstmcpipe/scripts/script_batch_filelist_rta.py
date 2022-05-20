#!/usr/bin/env python

import argparse
import subprocess
from os import environ


def main():
    parser = argparse.ArgumentParser(
        description="Batches the r0_to_dl1 hiperta stage for all the files " "within a text file."
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
        action="store_true",
        dest="keep_file",
        help="Keep output of hiperta. Set by default to False",
    )
    parser.add_argument(
        "--debug_mode",
        "-d",
        action="store_true",
        dest="debug_mode",
        help="Activate debug mode (add cleaned mask in the output hdf5). Set by default to False",
    )
    args = parser.parse_args()

    task_id = int(environ.get("SLURM_ARRAY_TASK_ID", -1))
    # Running script manually:
    if len(args.file_list) == 1 and task_id == -1:
        file_for_this_job = args.file_list[0]
    else:
        file_for_this_job = args.file_list[task_id]
    print("Processing files in: ", file_for_this_job)

    with open(file_for_this_job, "r") as filelist:
        for file in filelist:
            file = file.strip("\n")

            cmd = [
                "lstmcpipe_hiperta_r0_to_dl1lstchain",
                f"--infile={file}",
                f"--outdir={args.output_dir}",
                f"--config={args.config_file}",
            ]

            if args.keep_file:
                cmd.append("--keep_file")
            if args.debug_mode:
                cmd.append("--debug_mode")

            subprocess.run(cmd)


if __name__ == "__main__":
    main()
