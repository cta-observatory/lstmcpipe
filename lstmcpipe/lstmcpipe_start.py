# #!/usr/bin/env python

# E. Garcia, Jan '20
#
# Full workflow from r0 to dl3.
#  wraps together the individual scripts of
#   - onsite_mc_r0_to_dl1
#   - onsite_mc_merge_and_copy_dl1
#   - onsite_mc_train
#   - onsite_mc_dl1_to_dl2
#   - onsite_mc_dl2_to_irfs
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
from lstmcpipe.workflow_management import (
    create_dl1_filenames_dict,
    batch_mc_production_check,
)
from lstmcpipe.stages import (
    batch_process_dl1,
    batch_merge_and_copy_dl1,
    batch_train_pipe,
    batch_dl1_to_dl2,
    batch_dl2_to_irfs,
    batch_dl2_to_sensitivity,
    batch_plot_rf_features,
)


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
    default=None,
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

parser.add_argument(
    "--debug", action="store_true", help="print debug messages to stderr"
)
parser.add_argument(
    "--log-file",
    action="store",
    type=str,
    dest="log_file",
    help="Optional log file. This is independent of the slurm job logs and only handles lstmcpipe logging",
    default=None,
)

args = parser.parse_args()

#######################################################################################################################


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
    log = setup_logging(verbose=args.debug, logfile=args.log_file)
    log.info("Starting lstmcpipe processing script")
    # Read MC production configuration file
    config = load_config(args.config_mc_prod)
    query_continue("Are you sure ?")

    # Load variables
    prod_id = config["prod_id"]
    workflow_kind = config["workflow_kind"]
    batch_config = config["batch_config"]
    stages_to_run = config["stages_to_run"]
    all_particles = config["all_particles"]
    input_dir = config["input_dir"]
    dl1_output_dir = config["DL1_output_dir"]
    dl2_output_dir = config["DL2_output_dir"]
    running_analysis_dir = config["running_analysis_dir"]
    gamma_offs = config.get("gamma_offs")
    no_image_merging = config.get("merging_no_image")

    # Create log files and log directory
    logs_files, scancel_file, logs_dir = create_log_files(prod_id)

    # Make sure the lstchain config is defined if needed
    # It is not exactly required if you process only up to dl1
    if any(
        [
            step not in ("r0_to_dl1", "dl1ab", "merge_and_copy_dl1")
            for step in stages_to_run
        ]
    ):
        if args.config_file_lst is None:
            raise Exception(
                "The lstchain config needs to be defined for all steps following dl1 processing"
            )

    if "r0_to_dl1" in stages_to_run and "reprocess_dl1" in stages_to_run:
        raise Exception("There can only be one stage producing dl1 files")

    # 1 STAGE --> R0/1 to DL1 or reprocessing of existing dl1a files
    r0_to_dl1 = "r0_to_dl1" in stages_to_run
    dl1ab = "dl1ab" in stages_to_run

    if r0_to_dl1 or dl1ab:
        stage_input_dir = Path(input_dir)
        if workflow_kind == "lstchain":
            dl1_config = Path(args.config_file_lst).resolve().as_posix()
            if config.get("dl1_noise_tune_data_run"):
                # lstchain uses json, but just in case
                assert ".json" in dl1_config
                dl1_config = create_dl1ab_tuned_config(
                    dl1_config,
                    dl1_config.replace(".json", "_tuning.json"),
                    config.get("dl1_noise_tune_data_run"),
                    config.get("dl1_noise_tune_mc_run"),
                )
        elif workflow_kind == "hiperta":
            dl1_config = Path(args.config_file_rta).resolve()
        else:  # if this wasnt ctapipe, the config parsing would have failed
            dl1_config = Path(args.config_file_ctapipe).resolve()
        if dl1ab:
            stage_input_dir /= config["dl1_reference_id"]

        particle2jobid_process_dl1_dict, jobs_all_dl1 = batch_process_dl1(
            input_dir=stage_input_dir.as_posix(),
            conf_file=dl1_config,
            prod_id=prod_id,
            particles_loop=all_particles,
            batch_config=batch_config,
            gamma_offsets=gamma_offs,
            workflow_kind=workflow_kind,
            new_production=r0_to_dl1,
            logs=logs_files,
        )

        update_scancel_file(scancel_file, jobs_all_dl1)

    else:
        jobs_all_dl1 = ""
        particle2jobid_process_dl1_dict = {}
        for particle in all_particles:
            particle2jobid_process_dl1_dict[particle] = ""

    # 2 STAGE --> Merge,copy and move DL1 files
    if "merge_and_copy_dl1" in stages_to_run:
        (
            merged_dl1_paths_dict,
            jobs_to_train,
            jobs_all_dl1_finished,
        ) = batch_merge_and_copy_dl1(
            running_analysis_dir,
            particle2jobid_process_dl1_dict,
            all_particles,
            smart_merge=False,  # smart_merge=WORKFLOW_KIND
            no_image_flag=no_image_merging,
            gamma_offsets=gamma_offs,
            prod_id=prod_id,
            batch_config=batch_config,
            workflow_kind=workflow_kind,
            logs=logs_files,
        )

        update_scancel_file(scancel_file, jobs_all_dl1_finished)

    else:
        # Create just the needed dictionary inputs (dl1 files must exist !)
        merged_dl1_paths_dict = create_dl1_filenames_dict(
            dl1_output_dir, all_particles, gamma_offs
        )
        jobs_to_train = ""
        jobs_all_dl1_finished = ""

    # 3 STAGE --> Train pipe
    if "train_pipe" in stages_to_run:
        train_config = Path(args.config_file_lst)

        job_from_train_pipe, model_dir = batch_train_pipe(
            merged_dl1_paths_dict,
            train_config,
            jobs_to_train,
            batch_config=batch_config,
            logs=logs_files,
        )

        update_scancel_file(scancel_file, job_from_train_pipe)

        # Plot the RF feature's importance
        batch_plot_rf_features(
            model_dir,
            args.config_file_lst,
            batch_config,
            job_from_train_pipe,
            logs=logs_files,
        )

    else:
        job_from_train_pipe = ""
        model_dir = config["model_output_dir"]

    # 4 STAGE --> DL1 to DL2 stage
    if "dl1_to_dl2" in stages_to_run:
        dl1_to_dl2_config = Path(args.config_file_lst)

        dl2_files_path_dict, jobs_from_dl1_dl2 = batch_dl1_to_dl2(
            dl1_output_dir,
            model_dir,
            dl1_to_dl2_config,
            job_from_train_pipe,  # Single jobid from train
            jobs_all_dl1_finished,  # jobids from merge
            merged_dl1_paths_dict,  # final dl1 names
            all_particles,
            batch_config=batch_config,
            gamma_offsets=gamma_offs,
            logs=logs_files,
        )

        update_scancel_file(scancel_file, jobs_from_dl1_dl2)

    else:
        jobs_from_dl1_dl2 = ""
        dl2_files_path_dict = {}  # Empty log will be manage inside onsite_dl2_irfs

    # 5 STAGE --> DL2 to IRFs stage
    if "dl2_to_irfs" in stages_to_run:
        jobs_from_dl2_irf = batch_dl2_to_irfs(
            dl2_output_dir,
            all_particles,
            gamma_offs,
            Path(args.config_file_lst),
            jobs_from_dl1_dl2,  # Final dl2 names
            log_from_dl1_dl2=dl2_files_path_dict,
            batch_config=batch_config,
            prod_id=prod_id,
            logs=logs_files,
        )

        update_scancel_file(scancel_file, jobs_from_dl2_irf)

    else:
        jobs_from_dl2_irf = ""

    # 6 STAGE --> DL2 to sensitivity curves
    if "dl2_to_sensitivity" in stages_to_run:
        jobs_from_dl2_sensitivity = batch_dl2_to_sensitivity(
            dl2_output_dir,
            gamma_offs,
            jobs_from_dl1_dl2,
            dl2_files_path_dict,  # Final dl2 names
            batch_config=batch_config,
            prod_id=prod_id,
            logs=logs_files,
        )

        update_scancel_file(scancel_file, jobs_from_dl2_sensitivity)

    else:
        jobs_from_dl2_sensitivity = ""

    # Check DL2 jobs and the full workflow if it has finished correctly
    jobid_check = batch_mc_production_check(
        jobs_all_dl1,
        jobs_all_dl1_finished,
        job_from_train_pipe,
        jobs_from_dl1_dl2,
        jobs_from_dl2_irf,
        jobs_from_dl2_sensitivity,
        prod_id,
        log_directory=logs_dir,
        prod_config_file=args.config_mc_prod,
        last_stage=stages_to_run[-1],
        batch_config=batch_config,
        logs_files=logs_files,
    )

    update_scancel_file(scancel_file, jobid_check)
    log.info("Finished lstmcpipe processing script. All jobs have been submitted")


if __name__ == "__main__":
    main()
