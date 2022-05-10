#!/usr/bin/env python

import shutil
from pathlib import Path
from lstmcpipe import prod_logs, __version__


def backup_log(file):
    """
    Backups a log file.
    This scenario should only happens if a MC prod is relaunched because it failed.

    Parameters
    ----------
    file : Path
        Path object to the file to be 'backup-ed'
    """
    if file.exists():
        counter = 0
        save_file = Path(file.parent, f"BACKUP_{counter:02d}_{file.name}")

        while save_file.exists():
            counter += 1
            save_file = Path(file.parent, f"BACKUP_{counter:02d}_{file.name}")

        shutil.copyfile(file, save_file)


def create_log_dir(prod_id):
    """

    Parameters
    ----------
    prod_id : str
        production identifier of the MC production to be launched

    Returns
    -------
    log_dir : Path
        Path to `prod_id` log directory
    """
    log_dir = prod_logs.joinpath(f"logs_{prod_id}")
    log_dir.mkdir(exist_ok=True, parents=True)
    return log_dir


def create_log_files(production_id):
    """
    Manages filenames (and overwrites if needed) log files.

    Parameters
    ----------
    production_id : str
        production identifier of the MC production to be launched

    Returns
    -------
    logs_files: dict
        Dictionary containing
            log_file: Path - path and filename of full log file
            debug_file: Path - path and filename of reduced (debug) log file
    scancel_file: Path
        path and filename of bash file to cancel all the scheduled jobs
    lstmcpipe_log_dir : Path
        Path to prod_ID log directory
    """
    lstmcpipe_log_dir = create_log_dir(production_id)
    log_file = lstmcpipe_log_dir.joinpath(f"log_lstmcpipe_v{__version__}_{production_id}.yml")
    debug_file = lstmcpipe_log_dir.joinpath(f"log_reduced_{production_id}.yml")
    scancel_file = lstmcpipe_log_dir.joinpath(f"scancel_{production_id}.sh")

    # scancel prod file needs chmod +x rights !
    if scancel_file.exists():
        backup_log(scancel_file)
        scancel_file.unlink()
    scancel_file.touch()
    scancel_file.chmod(0o755)  # -rwxr-xr-x

    # If the file exists, i,e., the pipeline has been relaunched, save logs erase it
    if log_file.exists():
        backup_log(log_file)
        log_file.unlink()
    if debug_file.exists():
        backup_log(debug_file)
        debug_file.unlink()

    logs_files = {"log_file": log_file, "debug_file": debug_file}

    return logs_files, scancel_file, lstmcpipe_log_dir


def update_scancel_file(scancel_file, jobids_to_update):
    """
    Bash file containing the slurm command to cancel multiple jobs.
    The file will be updated after every batched stage and will be erased in case the whole MC prod succeed without
    errors.

    Parameters
    ----------
    scancel_file: pathlib.Path
        filename that cancels the whole MC production
    jobids_to_update: str
        job_ids to be included into the the file
    """
    if scancel_file.stat().st_size == 0:
        with open(scancel_file, "r+") as f:
            f.write(f"scancel {jobids_to_update}")

    else:
        with open(scancel_file, "a") as f:
            f.write(f",{jobids_to_update}")
