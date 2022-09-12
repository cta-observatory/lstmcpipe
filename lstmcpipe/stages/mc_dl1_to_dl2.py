#!/usr/bin/env python

import shutil
import logging
from pathlib import Path
from ..utils import save_log_to_file, SbatchLstMCStage
from ..io.data_management import check_and_make_dir_without_verification

log = logging.getLogger(__name__)


def batch_dl1_to_dl2(dict_paths, config_file, jobid_from_training, batch_config, logs):
    """
    Function to batch the dl1_to_dl2 stage once the lstchain train_pipe batched jobs have finished.

    Parameters
    ----------
    dict_paths : dict
        Core dictionary with {stage: PATHS} information
    config_file : str
        Path to a configuration file. If none is given, a standard configuration is applied
    jobid_from_training : str
        string containing the jobid from the jobs batched in the train_pipe stage, to be passed to the
        dl1_to_dl2 function (as a slurm dependency)
    batch_config : dict
        Dictionary containing the (full) source_environment and the slurm_account strings to be passed to
        dl1_dl2 function
    logs: dict
        Dictionary with logs files

    Returns
    -------
    jobid_for_dl2_to_dl3 : str
        string containing the jobids to be passed to the next stage of the workflow (as a slurm dependency)

    """
    log_dl1_to_dl2 = {}
    jobid_for_dl2_to_dl3 = []
    debug_log = {}
    log.info("==== START batch dl1_to_dl2_workflow ==== \n")
    for paths in dict_paths:
        job_logs, jobid = dl1_to_dl2(
            paths["input"],
            paths["output"],
            path_models=paths["path_model"],
            config_file=config_file,
            wait_jobid_train_pipe=jobid_from_training,
            batch_configuration=batch_config,
            extra_slurm_options=paths.get("extra_slurm_options", None),
        )

        log_dl1_to_dl2.update(job_logs)
        jobid_for_dl2_to_dl3.append(jobid)
        debug_log[jobid] = f"dl1_to_dl2 jobid that depends on : {jobid_from_training} training job"

    jobid_for_dl2_to_dl3 = ",".join(jobid_for_dl2_to_dl3)
    save_log_to_file(log_dl1_to_dl2, logs["log_file"], workflow_step="dl1_to_dl2")
    save_log_to_file(debug_log, logs["debug_file"], workflow_step="dl1_to_dl2")
    log.info("==== END batch dl1_to_dl2_workflow ====")
    return jobid_for_dl2_to_dl3


def dl1_to_dl2(
    input_file,
    output_dir,
    path_models,
    config_file,
    wait_jobid_train_pipe=None,
    batch_configuration='',
    extra_slurm_options=None,
):
    """
    Convert onsite files from dl1 to dl2

    Parameters
    ----------
    input_file : str
        FILE DL1 path
    output_dir : str
        DIR Dl2 path
    path_models : str
        DIR trained models path
    config_file : str
        Path to a configuration file. If none is given, a standard configuration is applied
    wait_jobid_train_pipe : str
        Comma-separated string with the batched jobid from the train stage to indicate the
        dependencies of the current job to be batched
    batch_configuration : dict
        Dictionary containing the (full) source_environment and the slurm_account strings
        to be passed to the sbatch commands
        ! NOTE : train_pipe AND dl1_to_dl2 MUST BE RUN WITH THE SAME ENVIRONMENT
    extra_slurm_options: dict
        Extra slurm options to be passed to the sbatch command

    Returns
    -------
    log_dl1_to_dl2 : dict
        log dictionary containing {jobid: batch_cmd} information

    jobid_dl1_to_dl2 : str
        batched job_id to be passed to later stages

    """
    log.info(f"Working on DL1 files in {Path(input_file).parent.as_posix()}")
    check_and_make_dir_without_verification(output_dir)
    log.info(f"Output dir: {output_dir}")
    cmd = f"lstchain_dl1_to_dl2 -f {input_file} -p {path_models} -o {output_dir}"
    if config_file is not None:
        cmd += f" -c {Path(config_file).resolve().as_posix()}"
    sbatch_dl1_dl2 = SbatchLstMCStage(
        "dl1_to_dl2",
        wrap_command=cmd,
        slurm_error=Path(output_dir).joinpath("dl1_dl2-%j.e").resolve().as_posix(),
        slurm_output=Path(output_dir).joinpath("dl1_dl2-%j.o").resolve().as_posix(),
        slurm_dependencies=wait_jobid_train_pipe,
        extra_slurm_options=extra_slurm_options,
        slurm_account=batch_configuration["slurm_account"],
        source_environment=batch_configuration["source_environment"],
    )

    jobid_dl1_to_dl2 = sbatch_dl1_dl2.submit()
    log_dl1_to_dl2 = {jobid_dl1_to_dl2: sbatch_dl1_dl2.slurm_command}
    log.info(f"Submitted batch job {jobid_dl1_to_dl2}")
    if config_file is not None:
        shutil.copyfile(config_file, Path(output_dir).joinpath(Path(config_file).name))
    return log_dl1_to_dl2, jobid_dl1_to_dl2
