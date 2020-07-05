#!/usr//bin/env python3

# T. Vuillaume, 12/09/2019
# merge and copy DL1 data after production
# Modifications by E. Garcia, 21/01/2020


# 1. check job_logs
# 2. check that all files have been created in DL1 based on training and testing lists
# 3. move DL1 files in final place
# 4. merge DL1 files
# 5. move running_dir 

import os
import shutil
import argparse
from data_management import (check_job_logs,
                             read_lines_file,
                             check_files_in_dir_from_file,
                             query_continue,
                             check_and_make_dir,
                             move_dir_content)

parser = argparse.ArgumentParser(description="Merge and copy DL1 data after production. \n"
                                             " 1. check job_logs \n"
                                             " 2. check that all files have been created in DL1 based on training "
                                             "and testing lists \n"
                                             " 3. move DL1 files in final place \n"
                                             " 4. merge DL1 files \n"
                                             " 5. move running_dir ")

parser.add_argument('input_dir', type=str,
                    help='path to the DL1 files directory to merge, copy and move',
                    )


def main(input_dir, flag_full_workflow=False, particle2jobs_dict={}, particle=None, flag_merge=False,
         flag_no_image=True):
    """
    Merge and copy DL1 data after production.

        1. check job_logs
        2. check that all files have been created in DL1 based on training and testing lists
        3. move DL1 files in final place
        4. merge DL1 files
        5. move running_dir


    Parameters
    ----------
    input_dir : str
        path to the DL1 files directory to merge, copy and move.  Compulsory argument.

    flag_full_workflow : bool
        Boolean flag to indicate if this script is run as part of the workflow that converts r0 to dl2 files.

    particle2jobs_dict : dict
        Dictionary used to retrieve the r0 to dl1 jobids that were sent in the previous step of the r0-dl3 workflow.
        This script will NOT start until all the jobs sent before have finished.
        COMPULSORY argument when flag_full_workflow is set to True.

    particle : str
        Type of particle used to create the log and dictionary
        COMPULSORY argument when flag_full_workflow is set to True.

    flag_merge : bool
        Flag to indicate whether the `--smart` argument of the `lstchain_merge_hdf5_files.py` script must be set to
        True (smart merge) or False (auto merge).
        Default set to True.

    flag_no_image : bool
        Flaf to indicate whether the `--no-image` argument of the `lstchain_merge_hdf5_files.py` script must be set to
        True (--no-image True) or False (--no-image False).
        Default set to True.


    Returns
    -------

    log_merge : dict (if flag_full_workflow is True)
        dictionary of dictionaries containing the log information of this script and the jobid of the batched job,
        separated by particle

         - log_merge[particle][set_type].keys() = ['logs_script_test or logs_script_train',
                                        'train_path_and_outname_dl1 or test_path_and_outname_dl1', 'jobid']

        ****  otherwise : (if flag_full_workflow is False, by default) ****
        None is returned -- THIS IS APPLIED FOR THE ARGUMENTS SHOWN BELOW TOO

    return_jobids4train : str (if flag_full_workflow is True)
        jobid of the batched job to be send (for dependencies purposes) to the next stage of the workflow
        (train_pipe), by particle

    return_jobids_debug ; str
        jobids to store in log_reduced.txt - Mainly debug purposes.

    """

    if flag_full_workflow:
        log_merge = {particle: {'training': {}, 'testing': {}}}

        wait_r0_dl1_jobs = ','.join(particle2jobs_dict[particle])

        return_jobids4train = []
        return_jobids_debug = []

        job_name = {'electron': 'e_merge',
                    'gamma': 'g_merge',
                    'gamma-diffuse': 'gd_merge',
                    'proton': 'p_merge'
                    }

    else:
        print("\n ==== START {} ==== \n".format(os.path.basename(__file__)))

    JOB_LOGS = os.path.join(input_dir, 'job_logs')
    training_filelist = os.path.join(input_dir, 'training.list')
    testing_filelist = os.path.join(input_dir, 'testing.list')
    running_DL1_dir = os.path.join(input_dir, 'DL1')
    DL1_training_dir = os.path.join(running_DL1_dir, 'training')
    DL1_testing_dir = os.path.join(running_DL1_dir, 'testing')
    final_DL1_dir = input_dir.replace('running_analysis', 'DL1')
    logs_destination_dir = input_dir.replace('running_analysis', 'analysis_logs')

    # 1. check job logs
    check_job_logs(JOB_LOGS)

    # 2. check that all files have been created in DL1 based on training and testing lists
    # just check number of files first:
    if not len(os.listdir(DL1_training_dir)) == len(read_lines_file(training_filelist)):
        tf = check_files_in_dir_from_file(DL1_training_dir, training_filelist)
        if tf != [] and not flag_full_workflow:
            query_continue("{} files from the training list are not in the `DL1/training` directory:\n{} "
                           "Continue ?".format(len(tf), tf))

    if not len(os.listdir(DL1_testing_dir)) == len(read_lines_file(testing_filelist)):
        tf = check_files_in_dir_from_file(DL1_testing_dir, testing_filelist)
        if tf != [] and not flag_full_workflow:
            query_continue("{} files from the testing list are not in the `DL1/testing directory:\n{} "
                           "Continue ?".format(len(tf), tf))

    if not flag_full_workflow:

        print("\tmerging starts")

        # 3. merge DL1 files
        for set_type in ['testing', 'training']:
            tdir = os.path.join(running_DL1_dir, set_type)
            output_filename = 'dl1_'
            for i in [-4, -3, -2, -1]:
                output_filename += running_DL1_dir.split('/')[i]
                output_filename += '_'
            output_filename += set_type
            output_filename += '.h5'
            output_filename = os.path.join(running_DL1_dir, output_filename)
            print(f"\t\tmerge output: {output_filename}")

            # 3.1 sbatch the jobs (or send them interactively depending) if the script is(not) run as part of the
            # whole workflow
            # filelist = [os.path.join(tdir, f) for f in os.listdir(tdir)]

            cmd = f"lstchain_merge_hdf5_files -d {tdir} -o {output_filename}"
            cmd += f" --no-image {flag_no_image} --smart {flag_merge}"
            os.system(cmd)

        # 4. move DL1 files in final place
        check_and_make_dir(final_DL1_dir)
        move_dir_content(running_DL1_dir, final_DL1_dir)
        print("\tDL1 files have been moved to {}".format(final_DL1_dir))

        # copy lstchain config file there too. HiPeRTA configs are *.txt
        config_files = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.endswith(('.json', '.txt'))]
        for file in config_files:
            shutil.copyfile(file, os.path.join(final_DL1_dir, os.path.basename(file)))

        # 5. move running_dir as logs
        check_and_make_dir(logs_destination_dir)
        move_dir_content(input_dir, logs_destination_dir)
        print("\tLOGS have been moved to {}".format(logs_destination_dir))

        print("\n ==== END {} ==== \n".format(os.path.basename(__file__)))

    else:  # flag_full_workflow == True !

        print("\n\tmerging starts - {}".format(particle))

        # 3. merge DL1 files
        wait_both_merges = []
        for set_type in ['testing', 'training']:
            tdir = os.path.join(running_DL1_dir, set_type)
            output_filename = 'dl1_'
            for i in [-4, -3, -2, -1]:
                output_filename += running_DL1_dir.split('/')[i]
                output_filename += '_'
            output_filename += set_type
            output_filename += '.h5'
            base_filename = output_filename
            output_filename = os.path.join(running_DL1_dir, output_filename)
            print(f"\t\tmerge output: {output_filename}")

            # After the workflow the files will be moved, will not stay at output_filename
            if set_type == 'training':
                log_merge[particle][set_type]['train_path_and_outname_dl1'] = os.path.join(final_DL1_dir, base_filename)
            else:
                log_merge[particle][set_type]['test_path_and_outname_dl1'] = os.path.join(final_DL1_dir, base_filename)

            # TODO missing the job.o and job.e for the sbatch of the merge and copy
            cmd = 'sbatch --parsable'
            if wait_r0_dl1_jobs != '':
                cmd += ' --dependency=afterok:' + wait_r0_dl1_jobs

            cmd += ' -J {} --wrap="lstchain_merge_hdf5_files -d {} -o {} --no-image {} --smart {}"'.format(
                job_name[particle],
                tdir,
                output_filename,
                flag_no_image,
                flag_merge  ##
            )

            jobid_merge = os.popen(cmd).read().strip('\n')
            log_merge[particle][set_type][jobid_merge] = cmd

            print(f'\t\tSubmitted batch job {jobid_merge} -- {particle}, {set_type}')

            wait_both_merges.append(jobid_merge)
            return_jobids_debug.append(jobid_merge)

        # This MUST be out of the set_type loop !

        # 4. & 5. in the case of the full workflow are done in a separate sbatch to wait merge, the three steps:
        # 4 --> move DL1 files in final place
        # copy lstchain config file in final_dir too
        # 5 --> move running_dir as logs

        print("\tDL1 files will be moved to {}".format(final_DL1_dir))

        base_cmd = 'sbatch --parsable -J {} --dependency=afterok:{} ' \
                   '--wrap="python batch_dl1_utils-merge_and_copy.py -s {} -d {} --copy_conf {}"'

        wait_both_merges = ','.join(wait_both_merges)

        # 4 --> move DL1 files in final place
        jobid_move_dl1 = os.popen(base_cmd.format(job_name[particle].split('_')[0]+'_mv_dl1',
                                                  wait_both_merges,
                                                  running_DL1_dir,
                                                  final_DL1_dir, 'False'
                                                  )
                                  ).read().strip('\n')

        print(f'\t\tSubmitted batch job {jobid_move_dl1}. It will move dl1 files when {wait_both_merges} finish.')

        # copy lstchain config file in final_dir too
        jobid_copy_conf = os.popen(base_cmd.format(job_name[particle].split('_')[0] + '_cp_conf',
                                                   jobid_move_dl1,
                                                   input_dir,
                                                   final_DL1_dir, 'True'
                                                   )
                                   ).read().strip('\n')

        print(f'\t\tSubmitted batch job {jobid_copy_conf}. It will copy the used config when {jobid_move_dl1} finish.')

        # 5 --> move running_dir to final analysis_logs
        jobid_move_log = os.popen(base_cmd.format(job_name[particle].split('_')[0]+'_mv_dir',
                                                  jobid_copy_conf,
                                                  input_dir,
                                                  logs_destination_dir, 'False'
                                                  )
                                  ).read().strip('\n')

        print(f'\t\tSubmitted batch job {jobid_move_log}. It will move running_dir when {jobid_copy_conf} finish.')

        return_jobids4train.append(jobid_move_dl1)

        return_jobids_debug.append(jobid_move_dl1)
        return_jobids_debug.append(jobid_move_log)
        return_jobids_debug.append(jobid_copy_conf)

        print("\tLOGS will be moved to {}".format(logs_destination_dir))

        # Little clarification (it will not be clear in log). These keys are stored here for 2 purposes:
        # 1 - In train_pipe recover final dl1 names and path.
        # 2 - In dl1_to_dl2 recover the jobids of the merged dl1 files; (all dl1 files MUST be merged and moved
        # to dl1_dir), so instead of storing the jobid that merges all the *particle*_dl1 (jobid_merge), it will
        # be store the jobid that move the dl1 final file to dl1_dir. Until this step is not finished, the workflow
        # cannot continue.
        log_merge[particle][set_type][jobid_move_dl1] = base_cmd.format(job_name[particle].split('_')[0]+'_mv_dl1',
                                                                        wait_both_merges,
                                                                        running_DL1_dir,
                                                                        final_DL1_dir, 'False')
        log_merge[particle][set_type][jobid_copy_conf] = base_cmd.format(job_name[particle].split('_')[0] + '_cp_conf',
                                                                         jobid_move_dl1,
                                                                         input_dir,
                                                                         final_DL1_dir, 'True')
        log_merge[particle][set_type][jobid_move_log] = base_cmd.format(job_name[particle].split('_')[0]+'_mv_dir',
                                                                        jobid_copy_conf,
                                                                        input_dir,
                                                                        logs_destination_dir, 'False')

        return_jobids4train = ','.join(return_jobids4train)
        return_jobids_debug = ','.join(return_jobids_debug)

        return log_merge, return_jobids4train, return_jobids_debug


if __name__ == '__main__':
    args = parser.parse_args()
    main(args.input_dir)
