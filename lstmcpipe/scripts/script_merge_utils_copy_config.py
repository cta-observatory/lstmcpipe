#!/usr/bin/env python

import os
import shutil
import argparse

parser = argparse.ArgumentParser(
    description="Script to copy all the config files of the source directory into the "
    "destination directory."
)

parser.add_argument(
    "--source",
    "-s",
    type=str,
    dest="source",
    help="source argument of move_dir_content",
)

parser.add_argument(
    "--destination",
    "-d",
    type=str,
    dest="dest",
    help="destination argument of move_dir_content",
)


def main():
    args = parser.parse_args()

    # HiPeRTA config is *.txt (<v4.0.0), otherwise is *.yml
    config_files = [
        os.path.join(args.source, f)
        for f in os.listdir(args.source)
        if f.endswith((".json", ".txt")) or f.startswith("hiperta_conf*.yml")
    ]

    for file in config_files:
        shutil.copyfile(file, os.path.join(args.dest, os.path.basename(file)))


if __name__ == "__main__":
    main()
