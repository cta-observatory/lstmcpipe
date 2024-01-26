# #!/usr/bin/env python

# E. Garcia, T. VUILLAUME, LAPP, CNRS
#
# Full workflow from r0 to dl3.
#  wraps together the individual scripts of
#   - mc_process_dl1
#   - mc_train_test_split
#   - mc_merge_dl1
#   - mc_train
#   - mc_dl1_to_dl2
#   - mc_dl2_to_irfs
#   - mc_dl2_to_sensitivity
#
# usage:
# > lstmcpipe -c config_MC_prod.yml -conf_lst LSTCHAIN_CONFIG_FILE [-conf_rta RTA_CONFIG_FILE]
#   [-conf_cta CTA_CONFIG_FILE]
#

import argparse
from pathlib import Path
from lstmcpipe.logging import setup_logging
from lstmcpipe.io.data_management import query_continue
from lstmcpipe.config import load_config, create_dl1ab_tuned_config
from lstmcpipe.io.lstmcpipe_tree_path import (
    create_log_files,
    update_scancel_file,
)
from lstmcpipe.utils import (
    batch_mc_production_check,
)
from lstmcpipe.stages import (
    batch_process_dl1,
    batch_train_test_splitting,
    batch_merge_dl1,
    batch_train_pipe,
    batch_dl1_to_dl2,
    batch_dl2_to_irfs,
    batch_dl2_to_sensitivity,
    batch_plot_rf_features,
)


def build_argparser():
    """
    Build argument parser and return it
    """
    parser = argparse.ArgumentParser(description="MC R0 to DL3 full pipeline")

    parser.add_argument(
        "--config_mc_prod",
        "-c",
        action="store",
        type=str,
        dest="config_mc_prod",
        help="Path to the MC_production configuration file. ",
        default="./config_MC_prod.yml",
        required=True,
    )

    parser.add_argument(
        "--config_file_lst",
        "-conf_lst",
        action="store",
        type=str,
        dest="config_file_lst",
        help="Path to a lstchain-like configuration file. "
        "RF classifier and regressor arguments must be declared here !",
        required=True,
    )

    parser.add_argument(
        "--config_file_ctapipe",
        "-conf_cta",
        action="store",
        type=str,
        dest="config_file_ctapipe",
        help="Path to a ctapipe-like configuration file."
        'Only to be declared if WORKFLOW_KIND = "ctapipe" and only used up to dl1.',
        default=None,
    )

    parser.add_argument(
        "--config_file_rta",
        "-conf_rta",
        action="store",
        type=str,
        dest="config_file_rta",
        help="Path to a HiPeRTA-like configuration file."
        'Only to be declared if WORKFLOW_KIND = "hiperta" and only used up to dl1.',
        default=None,
    )

    parser.add_argument("--debug", action="store_true", help="print debug messages to stderr")
    parser.add_argument(
        "--log-file",
        action="store",
        type=str,
        dest="log_file",
        help="Optional log file. This is independent of the slurm job logs and only handles lstmcpipe logging",
        default=None,
    )

    return parser


def main():
    """
    Main lstmcpipe script. This will launch the selected stages and start the processing.
    The jobs are submitted, but not awaited meaning that the analysis will be going on after
    the script has exited. To look at the submitted jobs, you can use e.g. `squeue -u $USER`.

    Arguments, that can be passed via the command line:
    ---------------------------------------------------
    --config_mc_prod / -c
        path to a yaml configuration file containing lstmcpipe settings
        This defines the stages run, the files processed, ...
    --config_file_lst / -conf_lst
        path to a yaml configuration file containing lstchain settings
        This defines the processing parameters like cleaning, models...
    --config_file_ctapipe / -conf_cta
        same for ctapipe
    --config_file_rat / -conf_rta
        same for HIPERTA
    --log-file
        Optional: path to a file where lstmcpipe logging will be written to.
    --debug
        Toggle to enable debug print messages.
    """
    parser = build_argparser()
    args = parser.parse_args()

    log = setup_logging(verbose=args.debug, logfile=args.log_file)
    log.info("Starting lstmcpipe processing script")
    # Read MC production configuration file
    lstmcpipe_config = load_config(args.config_mc_prod)
    query_continue("Are you sure ?")

    # Load variables
    prod_id = lstmcpipe_config["prod_id"]
    workflow_kind = lstmcpipe_config["workflow_kind"]
    batch_config = lstmcpipe_config["batch_config"]
    stages_to_run = lstmcpipe_config["stages_to_run"]

    # Create log files and log directory
    logs_files, scancel_file, logs_dir = create_log_files(prod_id)
    all_job_ids = {}

    # 1 STAGE --> R0/1 to DL1 or reprocessing of existing dl1a files
    r0_to_dl1 = "r0_to_dl1" in stages_to_run
    dl1ab = "dl1ab" in stages_to_run

    if r0_to_dl1 or dl1ab:
        if workflow_kind == "lstchain":
            dl1_config = Path(args.config_file_lst).resolve().as_posix()
            if lstmcpipe_config.get("dl1_noise_tune_data_run"):
                dl1_config = create_dl1ab_tuned_config(
                    dl1_config,
                    dl1_config.replace(".json", "_tuning.json"),
                    lstmcpipe_config.get("dl1_noise_tune_data_run"),
                    lstmcpipe_config.get("dl1_noise_tune_mc_run"),
                )
        elif workflow_kind == "hiperta":
            dl1_config = Path(args.config_file_rta).resolve().as_posix()
        else:  # if this was not ctapipe, the config parsing would have failed
            dl1_config = Path(args.config_file_ctapipe).resolve().as_posix()

        jobs_from_dl1_processing = batch_process_dl1(
            lstmcpipe_config["stages"],
            conf_file=dl1_config,
            batch_config=batch_config,
            workflow_kind=workflow_kind,
            new_production=r0_to_dl1,
            logs=logs_files,
        )

        update_scancel_file(scancel_file, jobs_from_dl1_processing)
        if r0_to_dl1:
            all_job_ids.update({"r0_dl1": jobs_from_dl1_processing})
        else:
            all_job_ids.update({"dl1ab": jobs_from_dl1_processing})
    else:
        jobs_from_dl1_processing = None

    # 2.1 STAGE --> Train, test splitting
    if "train_test_split" in stages_to_run:
        jobs_from_splitting = batch_train_test_splitting(
            lstmcpipe_config["stages"]["train_test_split"],
            jobids_from_r0dl1=jobs_from_dl1_processing,
            batch_config=batch_config,
            logs=logs_files,
        )

        update_scancel_file(scancel_file, jobs_from_splitting)
        all_job_ids.update({"train_test_split": jobs_from_splitting})
    else:
        jobs_from_splitting = ""

    # 2.2 STAGE --> Merge DL1 files
    if jobs_from_splitting != "":
        merge_wait_jobs = ",".join([jobs_from_dl1_processing, jobs_from_splitting])
    else:
        merge_wait_jobs = jobs_from_dl1_processing

    if "merge_dl1" in stages_to_run:
        jobs_from_merge = batch_merge_dl1(
            lstmcpipe_config["stages"]["merge_dl1"],
            jobid_from_splitting=merge_wait_jobs,
            batch_config=batch_config,
            workflow_kind=workflow_kind,
            logs=logs_files,
        )

        update_scancel_file(scancel_file, jobs_from_merge)
        all_job_ids.update({"merge_and_copy_dl1": jobs_from_merge})
    else:
        jobs_from_merge = None

    # 3 STAGE --> Train pipe
    if "train_pipe" in stages_to_run:
        job_from_train_pipe = batch_train_pipe(
            lstmcpipe_config["stages"]["train_pipe"],
            jobs_from_merge,
            config_file=Path(args.config_file_lst).resolve().as_posix(),
            batch_config=batch_config,
            logs=logs_files,
        )

        update_scancel_file(scancel_file, job_from_train_pipe)
        all_job_ids.update({"train_pipe": job_from_train_pipe})

        # Plot the RF feature's importance
        job_from_plot_rf_feat = batch_plot_rf_features(
            lstmcpipe_config["stages"]["train_pipe"],
            Path(args.config_file_lst).resolve().as_posix(),
            batch_config,
            job_from_train_pipe,
            logs=logs_files,
        )
        update_scancel_file(scancel_file, job_from_plot_rf_feat)
        all_job_ids.update({"plot_rf_feat": job_from_plot_rf_feat})

    else:
        job_from_train_pipe = None

    # 4 STAGE --> DL1 to DL2 stage
    if "dl1_to_dl2" in stages_to_run:
        jobs_dependency_for_dl1_dl2 = jobs_from_merge
        if job_from_train_pipe is not None:
            jobs_dependency_for_dl1_dl2 = (
                ",".join([jobs_dependency_for_dl1_dl2, job_from_train_pipe])
                if jobs_dependency_for_dl1_dl2 is not None
                else job_from_train_pipe
            )

        jobs_from_dl1_dl2 = batch_dl1_to_dl2(
            lstmcpipe_config["stages"]["dl1_to_dl2"],
            Path(args.config_file_lst).resolve().as_posix(),
            jobs_dependency_for_dl1_dl2,
            batch_config=batch_config,
            logs=logs_files,
        )

        update_scancel_file(scancel_file, jobs_from_dl1_dl2)
        all_job_ids.update({"dl1_to_dl2": jobs_from_dl1_dl2})
    else:
        jobs_from_dl1_dl2 = None

    # 5 STAGE --> DL2 to IRFs stage
    if "dl2_to_irfs" in stages_to_run:
        jobs_from_dl2_irf = batch_dl2_to_irfs(
            lstmcpipe_config["stages"]["dl2_to_irfs"],
            Path(args.config_file_lst).resolve().as_posix(),
            jobs_from_dl1_dl2,
            batch_config=batch_config,
            logs=logs_files,
        )

        update_scancel_file(scancel_file, jobs_from_dl2_irf)
        all_job_ids.update({"dl2_to_irfs": jobs_from_dl2_irf})

    # 6 STAGE --> DL2 to sensitivity curves
    if "dl2_to_sensitivity" in stages_to_run:
        jobs_from_dl2_sensitivity = batch_dl2_to_sensitivity(
            lstmcpipe_config["stages"]["dl2_to_sensitivity"],
            jobs_from_dl1_dl2,
            batch_config=batch_config,
            logs=logs_files,
        )

        update_scancel_file(scancel_file, jobs_from_dl2_sensitivity)
        all_job_ids.update({"dl2_to_sensitivity": jobs_from_dl2_sensitivity})

    # Check DL2 jobs and the full workflow if it has finished correctly
    jobid_check = batch_mc_production_check(
        all_job_ids,
        log_directory=logs_dir,
        prod_id=prod_id,
        prod_config_file=args.config_mc_prod,
        batch_config=batch_config,
        logs_files=logs_files,
    )

    update_scancel_file(scancel_file, jobid_check)
    log.info("Finished lstmcpipe processing script. All jobs have been submitted")


if __name__ == "__main__":
    main()
