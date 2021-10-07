# library of functions used for LST analysis data management

# Thomas Vuillaume, 12/09/2019
# Enrique Garcia 09/04/2020

import os
import sys
import shutil
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
            except:
                sys.stdout.write(
                    "Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n"
                )


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


# def get_metadata_from_mc_data_path(data_path):
#     '''
#     A mc data path is always `/BASE_DIR/data/mc/dlx/<date>/particle_type/pointing/`
#
#     Returns
#     -------
#     dict
#     '''
#
#     if not data_path.startswith(BASE_DIR):
#         data_path = os.path.join(BASE_DIR, data_path)
#     if not os.path.exists(BASE_DIR):
#         raise ValueError("The input path does not exists")
#
#     split = data_path.split('/')
#     if split[-5] != 'mc':
#         raise ValueError("The path structure does not correspond to the intended one")
#
#     dic = {
#         'pointing': split[-1],
#         'particle_type': split[-2],
#         'date': split[-3],
#         'data_level': split[-4],
#     }
#     return dic


def check_data_path(data_path):
    """
    Check if the path to some data exists.
    Raise an Error if the path does not exist, is not a directory or does not contain data.

    Parameters
    ----------
    data_path: str
    """
    if not os.path.exists(data_path):
        raise ValueError("The input directory must exist")
    if get_input_filelist(data_path) == []:
        raise ValueError("The input directory is empty")
    # if not data_path.startswith(BASE_DIR):
    #     raise ValueError("The root directory for the data is supposed to be {}".format(BASE_DIR))


def get_input_filelist(data_path):
    """
    Return list of files in `data_path`

    Parameters
    ----------
    data_path: str

    Returns
    -------
    list of str
    """
    return [
        os.path.abspath(os.path.join(data_path, f))
        for f in os.listdir(data_path)
        if os.path.isfile(os.path.join(data_path, f))
    ]


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
            "The directory {} is not empty. Do you want to remove its content?".format(
                directory
            ),
            default="no",
        )
        if clean:
            shutil.rmtree(directory)
    os.makedirs(directory, exist_ok=True)


def check_and_make_dir_without_verification(directory):
    if os.path.exists(directory) and os.listdir(directory) != []:
        shutil.rmtree(directory)
    os.makedirs(directory, exist_ok=True)


def check_job_logs(job_logs_dir):
    job_logs = [
        os.path.join(job_logs_dir, f)
        for f in os.listdir(job_logs_dir)
        if f.endswith(".e")
    ]
    logs_with_error = []
    for log_filename in job_logs:
        with open(log_filename) as log_file:
            for line in log_file.readlines():

                if (
                    "Remote data cache could not be accessed due to FileNotFoundError"
                    in line
                    or "URLError(" in line
                    or "<urlopen error Unable to open any source!" in line
                    or "ftp error: timeout(" in line
                ):

                    continue  # Known astropy errors, they do not break the workflow

                elif (
                    line.startswith("Error")
                    or line.startswith("ERROR")
                    or "ERROR" in line
                    or "Error" in line
                ):
                    logs_with_error.append(os.path.basename(log_filename))
                    break

    if not logs_with_error == []:
        query_continue(
            "There are errors in the following log files:\n {}\n "
            "Are you sure you want to continue?".format(logs_with_error),
            default="no",
        )


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
