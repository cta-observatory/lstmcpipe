import ctadata
import fnmatch
from functools import wraps
from ctadata.api_client import APIClient


def ensure_agent_running(func):
    """
    Decorator to ensure the ctadata agent is running before executing a function.
    Automatically starts the agent if needed.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_agent()
        return func(*args, **kwargs)
    return wrapper


def start_agent():
    """
    Start the CTA data agent if not already running
    """
    api = APIClient(dev_instance=False)
    api.start_agent_daemon()


@ensure_agent_running
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


@ensure_agent_running
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


@ensure_agent_running
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


@ensure_agent_running
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


@ensure_agent_running
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


@ensure_agent_running
def get_file(remote_path, local_path):
    """
    Download a file from dCache to local path

    Parameters
    ----------
    remote_path: str
        path to the file on dCache
    local_path: str
        path to save the file locally
    """
    ctadata.fetch_and_save_file(remote_path,  save_to_fn=local_path)


@ensure_agent_running
def get_dir(remote_dir, local_dir):
    """
    Download all files from a remote directory to a local directory

    Parameters
    ----------
    remote_dir: str
        path to the remote directory on dCache
    local_dir: str
        path to the local directory
    """
    ctadata.fetch_and_save_dir(remote_dir, save_to_fn=local_dir, recursive=True)