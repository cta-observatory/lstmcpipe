#!/usr//bin/env python

# T. Vuillaume,
# Modifications by E. Garcia
# Code train models from DL1 files onsite (La Palma cluster)

import os
import shutil
import logging
import time
from lstmcpipe.io.data_management import check_and_make_dir_without_verification


log = logging.getLogger(__name__)


def batch_train_pipe(log_from_merge, config_file, jobids_from_merge, source_env):
    """
    Function to batch the lstchain train_pipe once the proton and gamma-diffuse merge_and_copy_dl1 batched jobs have
    finished.

    Parameters
    ----------
    log_from_merge : dict
        dictionary containing the output name and abs path to the DL1 files, derived in merge_and_copy and saved
        through the log
    config_file : str
        Path to a configuration file. If none is given, a standard configuration is applied
    jobids_from_merge : str
        string containing the jobids (***ONLY from proton and gamma-diffuse***) from the jobs batched in the
         merge_and_copy_dl1 stage, to be passed to the train_pipe function (as a slurm dependency)
    source_env : str
        source environment to select the desired conda environment to run train_pipe and dl1_to_dl2 stages

    Returns
    -------
    log_train : dict
        Dictionary containing the log of the batched train_pipe jobs
    jobid_4_dl1_to_dl2 : str
        string containing the jobid to be passed to the next stage of the workflow (as a slurm dependency).
        For the next stage, however, it will be needed TRAIN + MERGED jobs
    model_path : str
        Path with the model's directory
    debug_log : dict
        Debug and summary purposes
    """
    debug_log = {}

    log.info("==== START {} ====".format("batch mc_train_workflow"))
    time.sleep(1)

    gamma_dl1_train_file = log_from_merge["gamma-diffuse"]["training"][
        "train_path_and_outname_dl1"
    ]
    proton_dl1_train_file = log_from_merge["proton"]["training"][
        "train_path_and_outname_dl1"
    ]

    log_train, jobid_4_dl1_to_dl2, model_path = train_pipe(
        gamma_dl1_train_file,
        proton_dl1_train_file,
        config_file=config_file,
        source_environment=source_env,
        wait_ids_proton_and_gammas=jobids_from_merge,
    )

    debug_log[jobid_4_dl1_to_dl2] = (
        f"The single jobid from train_pipe that depends of {jobids_from_merge} - merge"
        f"_and_copy jobids"
    )

    log.info("==== END {} ====".format("batch mc_train_workflow"))

    return log_train, jobid_4_dl1_to_dl2, model_path, debug_log


def batch_plot_rf_features(dir_models, config_file, source_env, train_jobid):
    """
    Batches the plot_model_importance.py script that creates a .png with the RF feature's importance models
    after the RF are trained.
    The plot is saved in the same dir in where the modes are stored.

    Parameters
    ----------
    dir_models: str
        Path to model's directory
    config_file: str
        Path to lstchain config file
    source_env: str
        String containing the .bashrc file to source and the conda env to call
    train_jobid: str
        Single jobid from training stage.

    Returns
    -------
    log: dict
        Dictionary with lstmcpipe_plot_models_importance single job id to be passed to debug log.
    """
    logs = {}
    log.info("==== START {} ====".format("batch plot RF features importance"))
    time.sleep(1)
    jobe = os.path.join(dir_models, "job_plot_rf_feat_importance.e")
    jobo = os.path.join(dir_models, "job_plot_rf_feat_importance.o")

    base_cmd = f"lstmcpipe_plot_models_importance {dir_models} -cf {config_file}"
    cmd = (
        f"sbatch --parsable --dependency=afterok:{train_jobid} -e {jobe} -o {jobo} -J RF_importance "
        f' --wrap="export MPLBACKEND=Agg; {source_env} {base_cmd}"'
    )
    jobid = os.popen(cmd).read().strip("\n")

    logs[jobid] = "Single job_id to plot RF feature s importance"

    log.info(" Random Forest importance's plot will be saved at: {}".format(dir_models))
    log.info("==== END {} ====".format("batch plot RF features importance"))

    return logs


def train_pipe(
    gamma_dl1_train_file,
    proton_dl1_train_file,
    config_file=None,
    source_environment=None,
    wait_ids_proton_and_gammas=None,
):
    """
    Train RF from MC DL1 data (onsite LaPalma cluster)

    Parameters
    ----------
    gamma_dl1_train_file: str
        path to the gamma file
    proton_dl1_train_file: str
        path to the proton file
    config_file: str
        Path to a configuration file. If none is given, a standard configuration is applied
    source_environment : str
        path to a .bashrc file (lstanalyzer user by default - can be configurable for custom runs) to activate a
        certain conda environment. By default : `conda activate cta`.
        ! NOTE : train_pipe AND dl1_to_dl2 MUST BE RUN WITH THE SAME ENVIRONMENT
    wait_ids_proton_and_gammas : str
        a string (of chained jobids separated by ',' and without spaces between each element), to indicate the
        dependencies of the job to be batched

    Returns
    -------
    log_train : dict
        dictionary containing the jobid of the batched job as key and the run command (the lstchain_mc_train
        command with all its corresponding arguments) as value.

    jobid_train : str
        jobid of the batched job to be send (for dependencies purposes) to the next stage of the
        workflow (onsite_mc_dl1_to_dl2)

    models_dir : str
        Path with the directory where the models are stored

    """
    log_train = {}

    dl1_proton_dir = os.path.dirname(os.path.abspath(proton_dl1_train_file))

    # check if it path follows the established paths (lstchain-like) or not (rta-like) ##
    if dl1_proton_dir.find("/mc/DL1/") > 0:
        models_dir = dl1_proton_dir.replace("/mc/DL1", "/models")
    else:
        models_dir = dl1_proton_dir.replace("/DL1", "/models")
    models_dir = models_dir.replace("/proton/", "/")

    log.info("Models will be placed in {}".format(models_dir))
    check_and_make_dir_without_verification(models_dir)

    cmd = ""
    if source_environment is not None:
        cmd += source_environment

    cmd += (
        f" lstchain_mc_trainpipe --fg {os.path.abspath(gamma_dl1_train_file)}"
        f" --fp {os.path.abspath(proton_dl1_train_file)} -o {models_dir}"
    )

    if config_file is not None:
        cmd = cmd + " -c {}".format(config_file)

    jobo = os.path.join(models_dir, "train_job.o")
    jobe = os.path.join(models_dir, "train_job.e")

    # TODO dry-run option ?
    # if dry_run:
    #     print(cmd)

    # 'sbatch --parsable --dependency=afterok:{wait_ids_proton_and_gammas} -e {jobe} -o {jobo} --wrap="{base_cmd}"'
    batch_cmd = "sbatch --parsable -p long"
    if wait_ids_proton_and_gammas != "":
        batch_cmd += " --dependency=afterok:" + wait_ids_proton_and_gammas
    batch_cmd += f' -J train_pipe -e {jobe} -o {jobo} --wrap="{cmd}" '

    jobid_train = os.popen(batch_cmd).read().strip("\n")
    log_train[jobid_train] = batch_cmd

    # copy config into working dir
    if config_file is not None:
        shutil.copyfile(
            config_file, os.path.join(models_dir, os.path.basename(config_file))
        )

    return log_train, jobid_train, models_dir
