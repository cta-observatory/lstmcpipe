#!/usr/bin/env python

import os
import shutil
import logging
from pathlib import Path
from lstmcpipe.workflow_management import save_log_to_file
from lstmcpipe.io.data_management import check_and_make_dir_without_verification


log = logging.getLogger(__name__)


def batch_train_pipe(
        dict_paths,
        jobids_from_merge,
        config_file,
        batch_config,
        logs
):
    """
    Function to batch the lstchain train_pipe once the proton and gamma-diffuse merge_and_copy_dl1 batched jobs have
    finished.

    Parameters
    ----------
    dict_paths : dict
        Core dictionary with {stage: PATHS} information
    config_file : str
        Path to a configuration file. If none is given, a standard configuration is applied
    jobids_from_merge : str
        string containing the jobids (***ONLY from proton and gamma-diffuse***) from the jobs batched in the
         merge_and_copy_dl1 stage, to be passed to the train_pipe function (as a slurm dependency)
    batch_config : dict
        Dictionary containing the (full) source_environment and the slurm_account strings to be passed to
        the `train_pipe` function.
    logs: dict
        Dictionary with logs files

    Returns
    -------
    jobid_4_dl1_to_dl2 : str
        string containing the jobid to be passed to the next stage of the workflow (as a slurm dependency).
        For the next stage, however, it will be needed TRAIN + MERGED jobs
    """
    log_train = {}
    debug_train = {}
    jobid_for_dl1_to_dl2 = []

    log.info("==== START {} ====".format("batch mc_train_workflow"))

    for paths in dict_paths:

        gamma_dl1_train_file = paths["input"]["gamma"]
        proton_dl1_train_file = paths["input"]["proton"]
        models_dir = paths["output"]

        job_logs, jobid = train_pipe(
            gamma_dl1_train_file,
            proton_dl1_train_file,
            models_dir,
            config_file=config_file,
            batch_configuration=batch_config,
            wait_jobs_dl1=jobids_from_merge,
            slurm_options=paths.get("slurm_options", None),
        )

        log_train.update(job_logs)
        jobid_for_dl1_to_dl2.append(jobid)

        debug_train[jobid] = (
            f"The single jobid from train_pipe that depends of {jobids_from_merge} - merge"
            f"_and_copy jobids"
        )

    jobid_for_dl1_to_dl2 = ",".join(jobid_for_dl1_to_dl2)

    save_log_to_file(log_train, logs["log_file"], workflow_step="train_pipe")
    save_log_to_file(debug_train, logs["debug_file"], workflow_step="train_pipe")

    log.info("==== END {} ====".format("batch mc_train_workflow"))

    return jobid_for_dl1_to_dl2


def batch_plot_rf_features(
        dict_paths,
        config_file,
        batch_configuration,
        train_jobid,
        logs,
    ):
    """
    Batches the plot_model_importance.py script that creates a .png with the RF feature's importance models
    after the RF are trained.
    The plot is saved in the same dir in where the modes are stored.

    Parameters
    ----------
     dict_paths : dict
        Core dictionary with {stage: PATHS} information
    config_file: str
        Path to lstchain config file
    batch_configuration : dict
        Dictionary containing the (full) source_environment and the slurm_account strings.
    train_jobid: str
        Single jobid from training stage.
    logs: dict
        Dictionary with logs files

    Returns
    -------
    jobid : str
        jobid of batched stage
    """
    log_rf_feat = {}
    log_debug = {}
    all_jobs_plot_rf_feat = []

    log.info("==== START {} ====".format("batch plot RF features importance"))

    source_env = batch_configuration["source_environment"]
    slurm_account = batch_configuration["slurm_account"]

    for path in dict_paths:
        models_dir = path["output"]

        jobe = Path(models_dir).joinpath("job_plot_rf_feat_importance.e").resolve().as_posix()
        jobo = Path(models_dir).joinpath(models_dir, "job_plot_rf_feat_importance.o").resolve().as_posix()

        batch_cmd = f"lstmcpipe_plot_models_importance {models_dir} -cf {config_file}"

        slurm_cmd = "sbatch --parsable --mem=16G "
        if slurm_account != "":
            slurm_cmd += f" -A {slurm_account}"
        slurm_cmd += (
            f" --dependency=afterok:{train_jobid} -e {jobe} -o {jobo} "
            f' -J RF_importance --wrap="export MPLBACKEND=Agg; {source_env} {batch_cmd}"'
        )
        jobid = os.popen(slurm_cmd).read().strip("\n")

        log_rf_feat[jobid] = slurm_cmd
        log_debug[jobid] = "Single job_id to plot RF feature s importance"
        all_jobs_plot_rf_feat.append(jobid)

    all_jobs_plot_rf_feat = ','.join(all_jobs_plot_rf_feat)

    save_log_to_file(log_rf_feat, logs["log_file"],
                     workflow_step="plot_RF_features_importance")
    save_log_to_file(log_debug, logs["debug_file"],
                     workflow_step="plot_RF_features_importance")

    log.info(" Random Forest importance's plot will be saved at: {}".format(models_dir))
    log.info("==== END {} ====".format("batch plot RF features importance"))

    return all_jobs_plot_rf_feat


def train_pipe(
    gamma_dl1_train_file,
    proton_dl1_train_file,
    models_dir,
    config_file=None,
    batch_configuration='',
    wait_jobs_dl1=None,
    slurm_options=None,
):
    """
    Train RF from MC DL1 data (onsite LaPalma cluster)

    Parameters
    ----------
    gamma_dl1_train_file: str
        FILE path to the gamma
    proton_dl1_train_file: str
        FILE path to the proton
    models_dir:
        DIR trained models output path
    config_file: str
        Path to a configuration file. If none is given, a standard configuration is applied
    batch_configuration : dict
        Dictionary containing the (full) source_environment and the slurm_account strings to be passed to the
        sbatch commands
        ! NOTE : train_pipe AND dl1_to_dl2 MUST BE RUN WITH THE SAME ENVIRONMENT
    wait_jobs_dl1 : str
        A string (of chained job_ids separated by ',' and without spaces between each element), containing
        all the job_ids of the merging stage
    slurm_options: str
        Extra slurm options to be passed to the sbatch command

    Returns
    -------
    log_train : dict
        dictionary containing the jobid of the batched job as key and the run command (the lstchain_mc_train
        command with all its corresponding arguments) as value.

    jobid_train : str
        jobid of the batched job to be send (for dependencies purposes) to the next stage of the
        workflow (onsite_mc_dl1_to_dl2)
    """
    log_train = {}

    source_environment = batch_configuration["source_environment"]
    slurm_account = batch_configuration["slurm_account"]

    log.info("Models will be placed in {}".format(models_dir))
    check_and_make_dir_without_verification(models_dir)

    cmd = (
        f" {source_environment} lstchain_mc_trainpipe --fg {gamma_dl1_train_file}"
        f" --fp {proton_dl1_train_file} -o {models_dir}"
    )

    if config_file is not None:
        cmd = cmd + " -c {}".format(config_file)

    jobo = Path(models_dir).joinpath("train_job.o").resolve().as_posix()
    jobe = Path(models_dir).joinpath("train_job.e").resolve().as_posix()

    # 'sbatch --parsable --dependency=afterok:{wait_ids_proton_and_gammas} -e {jobe} -o {jobo} --wrap="{base_cmd}"'
    batch_cmd = "sbatch --parsable"
    # For training, we'd need at least 32G (AllSky) and long queue, user can change this value, though.
    if slurm_options is not None:
        batch_cmd += f" {slurm_options}"
    else:
        batch_cmd += " -p long --mem=32G "
    if slurm_account != "":
        batch_cmd += f" -A {slurm_account}"
    if wait_jobs_dl1 != "":
        batch_cmd += " --dependency=afterok:" + wait_jobs_dl1
    batch_cmd += f' -J train_pipe -e {jobe} -o {jobo} --wrap="{cmd}" '

    jobid_train = os.popen(batch_cmd).read().strip("\n")
    log_train[jobid_train] = batch_cmd

    # copy config into working dir
    if config_file is not None:
        shutil.copyfile(
            config_file,
            Path(models_dir).joinpath(Path(config_file).name)
        )

    return log_train, jobid_train
