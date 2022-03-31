#!/usr/bin/env python

import argparse
from os import environ
from os.path import join, basename
from lstmcpipe.utils import rerun_cmd


def main():
    parser = argparse.ArgumentParser(
        description="Batches the dl1ab lstchain stage for all the files within a text file."
    )
    parser.add_argument(
        "--file_list",
        "-f",
        type=str,
        dest="file_list",
        help="Path to file containing list of DL0 lstchain file to be processed.",
        required=True,
        nargs="+",
    )
    parser.add_argument(
        "--output_dir",
        "-o",
        type=str,
        dest="output_dir",
        help="lstchain_mc_r0_to_dl1 output directory argument.",
        required=True,
    )
    parser.add_argument(
        "--config_file",
        "-c",
        type=str,
        dest="config_file",
        help="lstchain_mc_r0_to_dl1 configuration file argument.",
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

    # lstchain takes the output dir and constructs filenanmes itself
    with open(file_for_this_job, "r") as filelist:
        for file in filelist:
            file = file.strip("\n")
            # TODO: We need ways to set the pedestal cleaning!
            # or do we? is that not only for observed data?
            output = join(args.output_dir, basename(file))
            # TODO --no-image should be passed by default. To be configurable from lstmcpipe config ?
            cmd = [
                "lstchain_dl1ab",
                "--no-image",
                f"--input-file={file}",
                f"--output-file={output}",
            ]
            if args.config_file:
                cmd.append("--config={}".format(args.config_file))

            rerun_cmd(cmd, output, max_ntry=2)


if __name__ == "__main__":
    main()
