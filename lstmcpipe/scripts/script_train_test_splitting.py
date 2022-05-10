#!/usr/bin/env python

import shutil
import argparse
from pathlib import Path
from sklearn.model_selection import train_test_split

parser = argparse.ArgumentParser(
    description="Script to move a directory and its content after creating the destination" " directory."
)

parser.add_argument(
    "--input_dir",
    "-i",
    type=Path,
    dest="input_dir",
    help="Splitting input dir",
)

parser.add_argument(
    "--outdir_test",
    "--otest",
    type=Path,
    dest="outdir_test",
    help="Output directory for test dataset",
)

parser.add_argument(
    "--outdir_train",
    "--otrain",
    type=Path,
    dest="outdir_train",
    help="Output directory for train dataset",
)

parser.add_argument("--ratio", "-r", type=float, dest="ratio", help="Train-test splitting ratio", default=0.5)

parser.add_argument(
    "--log_dir", "-l", type=Path, dest="log_dir", help="Directory to store training and testing filelists"
)


def write_filelist(filelist, outdir, dataset=""):
    """
    Write all files within filelist in `{dataset}`.list file at outdir

    Parameters
    ----------
    filelist : list
        list of files to be written
    outdir : Path
        Output directory Path
    dataset : str
        'training' or 'testing' dataset list
    """
    with open(outdir.joinpath(f"{dataset}.list"), "w+") as newfile:
        for file in filelist:
            newfile.write(file)
            newfile.write("\n")


def move_files(filelist, outdir):
    """
    Move all files within filelist to outdir

    Parameters
    ----------
    filelist : list
        list of files to be written
    outdir : Path
        Output directory Path
    """
    for file in filelist:
        shutil.move(file, outdir)


def main():
    args = parser.parse_args()

    file_list = [
        file.resolve().as_posix()
        for file in Path(args.input_dir).iterdir()
        if file.is_file() and file.name.endswith(".h5")
    ]

    train, test = train_test_split(file_list, random_state=42, test_size=float(args.ratio), shuffle=True)

    write_filelist(train, args.log_dir, dataset="training")
    write_filelist(test, args.log_dir, dataset="testing")
    move_files(train, args.outdir_train)
    move_files(test, args.outdir_test)


if __name__ == "__main__":
    main()
