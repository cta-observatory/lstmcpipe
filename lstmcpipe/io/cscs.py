import ctadata
import fnmatch


def list_files_in_dir(directory, pattern="*"):
    """
    List all files in a directory matching a pattern and returns their full paths

    Parameters
    ----------
    directory: str
        path to a directory
    pattern: str
        glob pattern to match files

    Returns
    -------
    matched_files: list
        list of files in the directory matching the pattern
    """
    all_files =  ctadata.list_dir(directory)
    matched_files = [f for f in all_files if fnmatch.fnmatch(f, pattern)]
    return [directory + f for f in matched_files]


def list_simtel_files_in_dir(directory):
    """
    List all simtel files in a directory and returns their full paths

    Parameters
    ----------
    directory: str
        path to a directory

    Returns
    -------
    simtel_files: list
        list of simtel files in the directory
    """
    return list_files_in_dir(directory, pattern="*.simtel.gz")


def list_h5_files_in_dir(directory):
    """
    List all h5 files in a directory and returns their full paths

    Parameters
    ----------
    directory: str
        path to a directory

    Returns
    -------
    h5_files: list
        list of h5 files in the directory
    """
    return list_files_in_dir(directory, pattern="*.h5")


def list_dl1_files_in_dir(directory):
    """
    List all dl1 files in a directory and returns their full paths

    Parameters
    ----------
    directory: str
        path to a directory

    Returns
    -------
    dl1_files: list
        list of dl1 files in the directory
    """
    return list_files_in_dir(directory, pattern="dl1*.h5")


def list_dl2_files_in_dir(directory):
    """
    List all dl2 files in a directory and returns their full paths

    Parameters
    ----------
    directory: str
        path to a directory

    Returns
    -------
    dl2_files: list
        list of dl2 files in the directory
    """
    return list_files_in_dir(directory, pattern="dl2*.h5")