#!/usr/bin/env python

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
# > python onsite_mc_r0_to_dl3.py -c config_MC_prod.yml -conf_lst LSTCHAIN_CONFIG_FILE [-conf_rta RTA_CONFIG_FILE]
#

import sys
import argparse
from os.path import abspath
from distutils.util import strtobool
from lstmcpipe.workflow_management import (
    batch_r0_to_dl1,
    batch_r0_to_dl1_rta,
    batch_merge_and_copy_dl1,
    batch_train_pipe,
    batch_dl1_to_dl2,
    batch_dl2_to_irfs,
    batch_dl2_to_sensitivity,
    save_log_to_file,
    create_dict_with_dl1_filenames,
    batch_mc_production_check,
    parse_config_and_handle_global_vars,
    create_log_files,
    update_scancel_file,
    batch_plot_rf_features
)


parser = argparse.ArgumentParser(description="MC R0 to DL3 full pipeline")

parser.add_argument('--config_mc_prod', '-c',
                    action='store',
                    type=str,
                    dest='config_mc_prod',
                    help='Path to the MC_production configuration file. ',
                    default='./config_MC_prod.yml',
                    required=True
                    )

parser.add_argument('--config_file_lst', '-conf_lst',
                    action='store',
                    type=str,
                    dest='config_file_lst',
                    help='Path to a lstchain-like configuration file. '
                         'RF classifier and regressor arguments must be declared here !',
                    default=None,
                    required=True
                    )

parser.add_argument('--config_file_rta', '-conf_rta',
                    action='store',
                    type=str,
                    dest='config_file_rta',
                    help='Path to a HiPeRTA-like configuration file.'
                         'Only to be declared if WORKFLOW_KIND = "hiperta". ',
                    default=None
                    )

# OPTIONAL / ADVANCED ARGUMENTS

parser.add_argument('--no-image',
                    action='store',
                    type=lambda x: bool(strtobool(x)),
                    dest='flag_no_image',
                    help='--no-image argument for the merging stage.'
                         'True will merge dl1 files without image. False will do the opposite',
                    default=True
                    )

args = parser.parse_args()

#######################################################################################################################

if __name__ == '__main__':

    # Read MC production configuration file
    config = parse_config_and_handle_global_vars(args.config_mc_prod)

    # Load variables
    prod_id = config['prod_id']
    prod_type = config['prod_type']
    workflow_kind = config['workflow_kind']
    source_env = config['source_environment']
    stages_to_run = config['stages_to_run']
    all_particles = config['all_particles']
    dl0_data_dir = config['DL0_data_dir']
    dl1_data_dir = config['DL1_data_dir']
    dl2_data_dir = config['DL2_data_dir']
    running_analysis_dir = config['running_analysis_dir']
    gamma_offs = config['gamma_offs']

    # Create log files
    log_file, debug_file, scancel_file = create_log_files(prod_id)

    # 1 STAGE --> R0/1 to DL1
    if 'r0_to_dl1' in stages_to_run:

        if workflow_kind == 'lstchain':

            log_batch_r0_dl1, debug_r0dl1, jobs_all_r0_dl1 = batch_r0_to_dl1(
                dl0_data_dir,
                abspath(args.config_file_lst),
                prod_id,
                all_particles,
                source_env=source_env,
                gamma_offsets=gamma_offs
            )

        elif workflow_kind == 'hiperta':

            log_batch_r0_dl1, debug_r0dl1, jobs_all_r0_dl1 = batch_r0_to_dl1_rta(
                dl0_data_dir,
                abspath(args.config_file_rta),
                prod_id,
                all_particles,
                abspath(args.config_file_lst),
                gamma_offsets=gamma_offs
            )

        else:
            sys.exit("Choose a valid `workflow_kind` : 'lst' OR 'rta' in the config_MC_prod.yml file ")

        save_log_to_file(log_batch_r0_dl1, log_file, log_format='yml', workflow_step='r0_to_dl1')
        save_log_to_file(debug_r0dl1, debug_file, log_format='yml', workflow_step='r0_to_dl1')
        update_scancel_file(scancel_file, jobs_all_r0_dl1)

    else:
        jobs_all_r0_dl1 = ''
        log_batch_r0_dl1 = {}
        for particle in all_particles:
            log_batch_r0_dl1[particle] = ''

    # 2 STAGE --> Merge,copy and move DL1 files
    if 'merge_and_copy_dl1' in stages_to_run:

        log_batch_merge_and_copy, jobs_to_train, jobs_all_dl1_finished, debug_merge = batch_merge_and_copy_dl1(
            running_analysis_dir,
            log_batch_r0_dl1,
            all_particles,
            smart_merge=False,  # smart_merge=WORKFLOW_KIND
            no_image_flag=args.flag_no_image,
            gamma_offsets=gamma_offs,
            prod_id=prod_id,
            source_env=source_env
        )

        save_log_to_file(log_batch_merge_and_copy, log_file, log_format='yml', workflow_step='merge_and_copy_dl1')
        save_log_to_file(debug_merge, debug_file, log_format='yml', workflow_step='merge_and_copy_dl1')
        update_scancel_file(scancel_file, jobs_all_dl1_finished)

    else:
        # Create just the needed dictionary inputs (dl1 files must exist !)
        log_batch_merge_and_copy = create_dict_with_dl1_filenames(dl1_data_dir, all_particles, gamma_offs)
        jobs_to_train = ''
        jobs_all_dl1_finished = ''

    # 3 STAGE --> Train pipe
    if 'train_pipe' in stages_to_run:

        log_batch_train_pipe, job_from_train_pipe, model_dir, debug_train = batch_train_pipe(
            log_batch_merge_and_copy,
            abspath(args.config_file_lst),
            jobs_to_train,
            source_env=source_env
        )

        save_log_to_file(log_batch_train_pipe, log_file, log_format='yml', workflow_step='train_pipe')
        save_log_to_file(debug_train, debug_file, log_format='yml', workflow_step='train_pipe')
        update_scancel_file(scancel_file, job_from_train_pipe)

        # Plot the RF feature's importance
        log_plot_rf_features = batch_plot_rf_features(model_dir, args.config_file_lst, source_env, job_from_train_pipe)
        save_log_to_file(log_plot_rf_features, debug_file, log_format='yml',
                         workflow_step='plot_RF_features_importance')

    else:
        job_from_train_pipe = ''
        model_dir = config['model_dir']

    # 4 STAGE --> DL1 to DL2 stage
    if 'dl1_to_dl2' in stages_to_run:

        log_batch_dl1_to_dl2, jobs_from_dl1_dl2, debug_dl1dl2 = batch_dl1_to_dl2(
            dl1_data_dir,
            model_dir,
            abspath(args.config_file_lst),
            job_from_train_pipe,       # Single jobid from train
            jobs_all_dl1_finished,     # jobids from merge
            log_batch_merge_and_copy,  # final dl1 names
            all_particles,
            source_env=source_env,
            gamma_offsets=gamma_offs
        )

        save_log_to_file(log_batch_dl1_to_dl2, log_file, log_format='yml', workflow_step='dl1_to_dl2')
        save_log_to_file(debug_dl1dl2, debug_file, log_format='yml', workflow_step='dl1_to_dl2')
        update_scancel_file(scancel_file, jobs_from_dl1_dl2)

    else:
        jobs_from_dl1_dl2 = ''
        log_batch_dl1_to_dl2 = {}  # Empty log will be manage inside onsite_dl2_irfs

    # 5 STAGE --> DL2 to IRFs stage
    if 'dl2_to_irfs' in stages_to_run:
        log_batch_dl2_to_irfs, jobs_from_dl2_irf, debug_dl2_to_irfs = batch_dl2_to_irfs(
            dl2_data_dir,
            all_particles,
            gamma_offs,
            abspath(args.config_file_lst),
            jobs_from_dl1_dl2,           # Final dl2 names
            log_from_dl1_dl2=log_batch_dl1_to_dl2,
            source_env=source_env,
            prod_id=prod_id
        )

        save_log_to_file(log_batch_dl2_to_irfs, log_file, log_format='yml', workflow_step='dl2_to_irfs')
        save_log_to_file(debug_dl2_to_irfs, debug_file, log_format='yml', workflow_step='dl2_to_irfs')
        update_scancel_file(scancel_file, jobs_from_dl2_irf)

    else:
        jobs_from_dl2_irf = ''

    # 6 STAGE --> DL2 to sensitivity curves
    if 'dl2_to_sensitivity' in stages_to_run:
        log_batch_dl2_sensitivity, jobs_from_dl2_sensitivity, debug_dl2_to_sensitivity = \
            batch_dl2_to_sensitivity(
                dl2_data_dir,
                all_particles,
                gamma_offs,
                jobs_from_dl1_dl2,
                log_batch_dl1_to_dl2,       # Final dl2 names
                source_env=source_env,
                prod_id=prod_id
            )

        save_log_to_file(log_batch_dl2_sensitivity, log_file, log_format='yml', workflow_step='dl2_to_sensitivity')
        save_log_to_file(debug_dl2_to_sensitivity, debug_file, log_format='yml', workflow_step='dl2_to_sensitivity')
        update_scancel_file(scancel_file, jobs_from_dl2_sensitivity)

    else:
        jobs_from_dl2_sensitivity = ''

    # Check DL2 jobs and the full workflow if it has finished correctly
    jobid_check, debug_mc_check = batch_mc_production_check(
        jobs_all_r0_dl1,
        jobs_all_dl1_finished,
        job_from_train_pipe,
        jobs_from_dl1_dl2,
        jobs_from_dl2_irf,
        jobs_from_dl2_sensitivity,
        prod_id,
        log_file,
        debug_file,
        scancel_file
    )

    save_log_to_file(debug_mc_check, debug_file, log_format='yml', workflow_step='check_full_workflow')
    update_scancel_file(scancel_file, jobid_check)
