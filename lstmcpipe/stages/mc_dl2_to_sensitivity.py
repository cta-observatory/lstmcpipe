#!/usr/bin/env python

import logging
from pathlib import Path
from ..utils import save_log_to_file, SbatchLstMCStage

log = logging.getLogger(__name__)


def batch_dl2_to_sensitivity(dict_paths, job_ids_from_dl1_dl2, batch_config, logs):
    """
    Batches the dl2_to_sensitivity stage (`stages.script_dl2_to_sensitivity` based in the pyIRF iib) once the
    dl1_to_dl2 stage had finished.

    Parameters
    ----------
    dict_paths : dict
        Core dictionary with {stage: PATHS} information
    job_ids_from_dl1_dl2: str
        Comma-separated string with the job ids from the dl1_to_dl2 stage to be used as a slurm dependency
        to schedule the current stage
    batch_config : dict
        Dictionary containing the (full) source_environment and the slurm_account strings to be passed to
        dl2_to_sensitivity function
    logs: dict
        Dictionary with logs files

    Returns
    -------
    jobid_for_check: str
        Comma-separated jobids batched in the current stage
    """
    log.info('==== START batch mc_dl2_to_sensitivity ====')
    log_dl2_to_sensitivity = {}
    jobid_for_check = []
    debug_log = {}
    for paths in dict_paths:
        job_logs, jobid = dl2_to_sensitivity(
            paths["input"],
            paths["output"],
            batch_configuration=batch_config,
            wait_jobs_dl1_dl2=job_ids_from_dl1_dl2,
            extra_slurm_options=paths.get("extra_slurm_options", None),
        )

        jobid_for_check.append(jobid)
        log_dl2_to_sensitivity.update(job_logs)
        debug_log[jobid] = (
            f"Job_ids from the dl2_to_sensitivity stage and the plot_irfs script that depends on the "
            f"dl1_to_dl2 stage job_ids; {job_ids_from_dl1_dl2} "
        )

    jobid_for_check = ",".join(jobid_for_check)
    save_log_to_file(log_dl2_to_sensitivity, logs["log_file"], "dl2_to_sensitivity")

    save_log_to_file(debug_log, logs["debug_file"], "dl2_to_sensitivity")
    log.info('==== END batch mc_dl2_to_sensitivity ====')
    return jobid_for_check


def dl2_to_sensitivity(input_paths, output, batch_configuration, wait_jobs_dl1_dl2, extra_slurm_options=None):
    """
    Function to run the `script_dl2_to_sensitivity` for the gamma (and the different gamma offsets) and gamma-diffuse
    particles.
    Creates the sensitivity *.fits.gz files and the corresponding sensitivity curve plot.

    Parameters
    ----------
    input_paths: dict
    output: str
    batch_configuration : dict
        Dictionary containing the (full) source_environment and the slurm_account strings to be passed to the
        sbatch commands
    wait_jobs_dl1_dl2: str
        Comma-separated string with the jobs (dependency) to wait for before launching the cmd
    extra_slurm_options: dict
        Extra slurm options to be passed to the sbatch command

    Returns
    -------
    log_dl2_to_sensitivity: dict
        Dictionary with job_id-slurm command key-value pair used for logging
    job_id: str
        String with job_ids batched by the dl2_to_sensitivity script

    """
    g_file = input_paths["gamma_file"]
    p_file = input_paths["proton_file"]
    e_file = input_paths["electron_file"]
    cmd_sens = f"lstmcpipe_dl2_to_sensitivity -g {g_file} -p {p_file} -e {e_file} -o {output}"

    sbatch_dl2_sens = SbatchLstMCStage(
        "dl2_sens",
        wrap_command=cmd_sens,
        slurm_error=Path(output).parent.joinpath("job_dl2_to_sensitivity_%j.e"),
        slurm_output=Path(output).parent.joinpath("job_dl2_to_sensitivity_%j.o"),
        slurm_dependencies=wait_jobs_dl1_dl2,
        extra_slurm_options=extra_slurm_options,
        slurm_account=batch_configuration["slurm_account"],
        source_environment=batch_configuration["source_environment"],
    )

    job_id_dl2_sens = sbatch_dl2_sens.submit()
    log_dl2_to_sensitivity = {job_id_dl2_sens: job_id_dl2_sens.slurm_command}
    jobids_dl2_to_sensitivity = [job_id_dl2_sens]
    log.info(f"Output dir of sensitivity file: {output}")
    log.info(f"Submitted batch job {job_id_dl2_sens}")
    cmd_plot_sens = f'lstmcpipe_plot_irfs -f {output} -o {output.replace(".fits.gz", ".png")}'

    sbatch_plot_sens = SbatchLstMCStage(
        "dl2_sens_plot",
        wrap_command=cmd_plot_sens,
        slurm_error=Path(output).parent.joinpath("job_plot_sensitivity-%j.e"),
        slurm_output=Path(output).parent.joinpath("job_plot_sensitivity-%j.o"),
        slurm_dependencies=job_id_dl2_sens,
        extra_slurm_options=extra_slurm_options,
        slurm_account=batch_configuration["slurm_account"],
        source_environment=batch_configuration["source_environment"],
        backend="export MPLBACKEND=Agg; ",
    )

    job_id_plot_sens = sbatch_plot_sens.submit()
    log_dl2_to_sensitivity[job_id_plot_sens] = sbatch_plot_sens.slurm_command
    jobids_dl2_to_sensitivity.append(job_id_plot_sens)
    log.info(f"Output dir of sensitivity plots: {output}")
    log.info(f"Submitted batch job {job_id_plot_sens}")
    return log_dl2_to_sensitivity, ",".join(jobids_dl2_to_sensitivity)
