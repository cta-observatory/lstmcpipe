#!/usr/bin/env python

import argparse
from os.path import join, basename
from os import environ
from lstmcpipe.utils import rerun_cmd


def main():
    parser = argparse.ArgumentParser(description="Batches the ctapipe-stage1 for all the files " "within a text file.")
    parser.add_argument(
        "--file_list",
        "-f",
        type=str,
        dest="file_list",
        help="Path to file containing list of DL0 simtel files to be processed.",
        required=True,
        nargs="+",
    )
    parser.add_argument(
        "--output_dir",
        "-o",
        type=str,
        dest="output_dir",
        help="ctapipe-stage1 output directory argument.",
        required=True,
    )
    parser.add_argument(
        "--config_file",
        "-c",
        type=str,
        dest="config_file",
        help="ctapipe-stage1 configuration file argument.",
        required=True,
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

            # ctapipe takes the output filename
            # so we need to construct it first
            output = join(args.output_dir, basename(file.replace(".simtel.gz", ".dl1.h5")))

            cmd = ["ctapipe-stage1", f"--input={file}", f"--output={output}"]
            if args.config_file:
                cmd.append("--config={}".format(args.config_file))

            rerun_cmd(cmd, output, max_ntry=2)
