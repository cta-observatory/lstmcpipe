#!/usr/bin/env python

import os
import logging
import time


log = logging.getLogger(__name__)


def batch_dl2_to_sensitivity(
    dl2_directory,
    offset_gammas,
    job_ids_from_dl1_dl2,
    log_from_dl1_dl2,
    source_env,
    prod_id,
):
    """
    Batches the dl2_to_sensitivity stage (`stages.script_dl2_to_sensitivity` based in the pyIRF iib) once the
    dl1_to_dl2 stage had finished.

    Parameters
    ----------
    dl2_directory: str
        Base path to DL2 directory to be formatted with particle type
    offset_gammas: list
        list off gamma offsets
    job_ids_from_dl1_dl2: str
        Comma-separated string with the job ids from the dl1_to_dl2 stage to be used as a slurm dependency
        to schedule the current stage
    log_from_dl1_dl2: dict
        Dictionary from dl1_to_dl2 stage with particle path information
    source_env: str
        source environment to select the desired conda environment (source .bashrc + conda activate $ENV)
    prod_id: str
        String with prod_id prefix to complete 'file-naming'

    Returns
    -------
    log_dl2_to_sensitivity: dict
        Dictionary with job_id-slurm command key-value pair used for logging
    jobid_for_check: str
        Comma-separated jobids batched in the current stage
    debug_log: dict
        Dictionary with the job-id and stage explanation to be stored in the debug file
    """
    log.info("==== START {} ====".format("batch mc_dl2_to_sensitivity"))
    time.sleep(1)

    debug_log = {}
    jobid_for_check = []
    log_dl2_to_sensitivity = {}

    for off in offset_gammas:
        job_logs, jobid = dl2_to_sensitivity(
            dl2_directory,
            log_from_dl1_dl2,
            gamma_offset=off,
            prod_id=prod_id,
            source_env=source_env,
            wait_jobs_dl1_dl2=job_ids_from_dl1_dl2,
        )
        jobid_for_check.append(jobid)
        log_dl2_to_sensitivity[f"gamma_{off}"] = job_logs
        debug_log[jobid] = (
            f"Gamma_{off} job_ids from the dl2_to_sensitivity stage and the plot_irfs script that "
            f"depends on the dl1_to_dl2 stage job_ids; {job_ids_from_dl1_dl2}"
        )
        log.info("Jobs for gamma offset {} have been submitted".format(off))
        log.debug(
            f"Gamma_{off} job_ids from the dl2_to_sensitivity stage and the plot_irfs script that "
            f"depends on the dl1_to_dl2 stage job_ids; {job_ids_from_dl1_dl2}"
        )

    jobid_for_check = ",".join(jobid_for_check)

    log.info("==== END {} ====".format("batch mc_dl2_to_sensitivity"))

    return log_dl2_to_sensitivity, jobid_for_check, debug_log


def compose_sensitivity_outdir(dl2_dir, gamma_offset):
    """
    Compute the sensitivity output directory depending on the type of gamma file

    Parameters
    ----------
    dl2_dir: str
        Base path to DL2 directory
    gamma_offset: str
        String to indicate the gamma offset. Either 'off0.0deg' or 'off0.4deg'

    Returns
    -------
    output_sensitivity_dir: str
        Absolute path in where to store the sensitivity.fits.fz files

    """

    allowed_gamma_off = ["off0.0deg", "off0.4deg"]
    if gamma_offset not in allowed_gamma_off:
        log.info(
            f'Please select a valid gamma_offset to compute the IRFS: {" or ".join(allowed_gamma_off)}'
        )
        exit(-1)

    output_sensitivity_dir = os.path.join(
        dl2_dir.replace("/DL2/", "/IRF/").replace("/{}/", "/"), gamma_offset
    )

    os.makedirs(output_sensitivity_dir, exist_ok=True)

    return output_sensitivity_dir


def sensitivity_io(
    dl2_directory, log_from_dl1_dl2, gamma_offset="off0.0deg", prod_id=None
):
    """
    Manages the i/o arguments and parameters to be passed to the batch_dl2_to_sensitivity function.

    Parameters
    ----------
    dl2_directory: str
        Base path to DL2 directory
    log_from_dl1_dl2: dict
        Dictionary with particle abs path created in previous stages #TODO to be changed by a glob.glob ?
    gamma_offset: str
        String to indicate the gamma offset if gamma_point_like == True. Either 'off0.0deg' or 'off0.4deg'
    prod_id: str
        String with prod_id prefix to complete 'file-naming'

    Returns
    -------
    gamma_file: str
        Absolute path to DL2 gamma test file
    proton_file: str
        Absolute path to DL2 proton test file
    electron_file: str
        Absolute path to DL2 electron test file
    output_directory: str
        Absolute path with output directory
    output_sensitivity_filename: str
        Output filename

    """
    output_directory = compose_sensitivity_outdir(dl2_directory, gamma_offset)

    # Find paths to DL2 files
    proton_file = log_from_dl1_dl2["proton"]["dl2_test_path"]
    electron_file = log_from_dl1_dl2["electron"]["dl2_test_path"]

    if gamma_offset == "off0.0deg":
        gamma_file = log_from_dl1_dl2["gamma_off0.0deg"]["dl2_test_path"]
    else:
        # gamma_offset == 'off0.4deg'. No other case possible, it has been checked in 'compose_sensitivity_outdir'
        gamma_file = log_from_dl1_dl2["gamma_off0.4deg"]["dl2_test_path"]

    # Create output filenames
    if prod_id is None:
        output_sensitivity_filename = os.path.join(
            output_directory, "sensitivity.fits.gz"
        )
    else:
        output_sensitivity_filename = os.path.join(
            output_directory,
            f'{prod_id.replace(".", "")}_gamma_{gamma_offset.replace(".", "")}_sensitivity.fits.gz',
        )

    return (
        gamma_file,
        proton_file,
        electron_file,
        output_directory,
        output_sensitivity_filename,
    )


def dl2_to_sensitivity(
    dl2_dir,
    log_from_dl1_dl2,
    gamma_offset="off0.0deg",
    prod_id=None,
    source_env="",
    wait_jobs_dl1_dl2="",
):
    """
    Function to run the `script_dl2_to_sensitivity` for the gamma (and the different gamma offsets) and gamma-diffuse
    particles.
    Creates the sensitivity *.fits.gz files and the corresponding sensitivity curve plot.

    Parameters
    ----------
    dl2_dir: str
        Base path to DL2 directory
    log_from_dl1_dl2: dict
        Dictionary with particle abs path created in previous stages #TODO to be changed by a glob.glob ?
    gamma_offset: str
        String to indicate the gamma offset if gamma_point_like == True. Either 'off0.0deg' or 'off0.4deg'
    prod_id: str
        String with prod_id prefix to complete 'filenaming'
    source_env: str
        Source environment (source .bashrc + conda activate env) to be used in the slurm cmd
    wait_jobs_dl1_dl2: str
        Comma-separated string with the jobs (dependency) to wait for before launching the cmd

    Returns
    -------
    log_dl2_to_sensitivity: dict
        Dictionary with job_id-slurm command key-value pair used for logging
    job_id: str
        String with job_ids batched by the dl2_to_sensitivity script

    """
    log_dl2_to_sensitivity = {}
    jobids_dl2_to_sensitivity = []
    job_name = gamma_offset.replace(".", "").replace("off", "").replace("deg", "")

    g_file, p_file, e_file, out_dir, out_file = sensitivity_io(
        dl2_dir, log_from_dl1_dl2, gamma_offset, prod_id
    )

    # TODO Move the base commands into scripts so that we can use subprocess properly(makes splitting the string easier)
    # create sensitivity files
    base_cmd_sens = f"lstmcpipe_dl2_to_sensitivity -g {g_file} -p {p_file} -e {e_file} -o {out_file}"
    jobo_sens = os.path.join(out_dir, f"job_dl2_to_sensitivity_gamma_{gamma_offset}.o")
    jobe_sens = os.path.join(out_dir, f"job_dl2_to_sensitivity_gamma_{gamma_offset}.e")
    cmd_sens = (
        f"sbatch --parsable -p short --dependency=afterok:{wait_jobs_dl1_dl2} -e {jobe_sens} -o {jobo_sens} "
        f' -J {job_name}_sensitivity --wrap="{source_env} {base_cmd_sens}"'
    )

    job_id_dl2_sens = os.popen(cmd_sens).read().strip("\n")
    log_dl2_to_sensitivity[job_id_dl2_sens] = cmd_sens
    jobids_dl2_to_sensitivity.append(job_id_dl2_sens)

    # Create plot from sensitivity files
    base_cmd_plot = (
        f'lstmcpipe_plot_irfs -f {out_file} -o {out_file.replace(".fits.gz", ".png")}'
    )
    jobe_plot = os.path.join(out_dir, f"job_plot_sensitivity_gamma_{gamma_offset}.e")
    jobo_plot = os.path.join(out_dir, f"job_plot_sensitivity_gamma_{gamma_offset}.o")
    cmd_plot = (
        f"sbatch --parsable -p short --dependency=afterok:{job_id_dl2_sens} -e {jobe_plot} -o {jobo_plot}"
        f' -J {job_name}_sens_plot --wrap="export MPLBACKEND=Agg; {source_env} {base_cmd_plot}"'
    )

    job_id_plot_sens = os.popen(cmd_plot).read().strip("\n")
    log_dl2_to_sensitivity[job_id_plot_sens] = cmd_plot
    jobids_dl2_to_sensitivity.append(job_id_plot_sens)

    return log_dl2_to_sensitivity, ",".join(jobids_dl2_to_sensitivity)
