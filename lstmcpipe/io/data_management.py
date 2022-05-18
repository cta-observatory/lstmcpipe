# library of functions used for LST analysis data management

import os
import sys
import shutil
from pathlib import Path
from distutils.util import strtobool


def query_yes_no(question, default="yes"):
    """
    Ask a yes/no question via raw_input() and return their answer.

    Parameters
    ----------
    question: str
        question to the user
    default: str - "yes", "no" or None
        resumed answer if the user just hits <Enter>.
        "yes" or "no" will set a default answer for the user
        None will require a clear answer from the user
    Returns
    -------
    bool - True for "yes", False for "no"
    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == "":
            return valid[default]
        else:
            try:
                return bool(strtobool(choice))
            except:  # noqa
                sys.stdout.write("Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n")


def query_continue(question, default="no"):
    """
    Ask a question and if the answer is no, exit the program.
    Calls `query_yes_no`.

    Parameters
    ----------
    question: str
    default: str

    Returns
    -------
    bool - answer from query_yes_no
    """
    answer = query_yes_no(question, default=default)
    if not answer:
        sys.exit("Program stopped by user")
    else:
        return answer


def check_data_path(data_path, glob=None):
    """
    Check if the path to some data exists.
    Raise an Error if the path does not exist, is not a directory or does not contain data.

    Parameters
    ----------
    data_path: str
    glob: str
        Glob pattern to be passed
    """
    if not Path(data_path).exists():
        raise ValueError(f"The input directory {data_path} must exist")
    if not get_input_filelist(data_path, glob_pattern=glob):
        raise ValueError(f"The input directory {data_path} is empty")


def get_input_filelist(data_path, glob_pattern=None):
    """
    Return list of files in `data_path`

    Parameters
    ----------
    data_path: str
        Directory path
    glob_pattern: str
        Glob the given pattern. To Glob recursively, add "**/" in front of the string

    Returns
    -------
    list
    """
    if glob_pattern is None:
        _path = Path(data_path).iterdir()
    else:
        _path = Path(data_path).glob(str(glob_pattern))

    return [file.resolve().as_posix() for file in _path]


def check_and_make_dir(directory):
    """
    Check if a directory exists or contains data before to makedir.
    If exists, query the user to remove its content.

    Parameters
    ----------
    directory: str
        path to a directory
    """
    if os.path.exists(directory) and os.listdir(directory) != []:
        clean = query_continue(
            "The directory {} is not empty. Do you want to remove its content?".format(directory),
            default="no",
        )
        if clean:
            shutil.rmtree(directory)
    os.makedirs(directory, exist_ok=True)


def check_and_make_dir_without_verification(directory):
    if os.path.exists(directory) and os.listdir(directory) != []:
        shutil.rmtree(directory)
    os.makedirs(directory, exist_ok=True)


def check_files_in_dir_from_file(directory, file):
    """
    Check that a list of files from a file exist in a dir

    Parameters
    ----------
    directory
    file

    Returns
    -------

    """
    with open(file) as f:
        lines = f.readlines()

    files_in_dir = os.listdir(directory)
    files_not_in_dir = []
    for line in lines:
        filename = os.path.basename(line.rstrip("\n"))
        if filename not in files_in_dir:
            files_not_in_dir.append(filename)

    return files_not_in_dir


def read_lines_file(file):
    with open(file) as f:
        lines = [line.rstrip("\n") for line in f]
    return lines


def move_dir_content(src, dest):
    files = os.listdir(src)
    for f in files:
        shutil.move(os.path.join(src, f), dest)
    os.rmdir(src)


if __name__ == "__main__":
    pass
