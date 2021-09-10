#!/usr/bin/env python

import argparse
from lstmcpipe.io.data_management import (
    move_dir_content,
    check_and_make_dir_without_verification,
)

parser = argparse.ArgumentParser(
    description="Script to move a directory and its content after creating the destination"
    " directory."
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

    # check_and_make_dir(args.dest) CANNOT be used because if demands user interaction.
    check_and_make_dir_without_verification(args.dest)
    move_dir_content(args.source, args.dest)


if __name__ == "__main__":
    main()
