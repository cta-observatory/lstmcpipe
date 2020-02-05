#!/usr//bin/env python3

# T. Vuillaume, 12/09/2019
# merge and copy DL1 data after production
# Modifications by E. Garcia, 21/01/2020


# 1. check job_logs
# 2. check that all files have been created in DL1 based on training and testing lists
# 3. move DL1 files in final place
# 4. merge DL1 files
# 5. move running_dir 

import argparse
from .data_management import *
# from lstchain.io import smart_merge_h5files

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


def check_files_in_dir_from_file(directory, file):
    """
    Check that a list of files from a file exist in a dir

    Parameters
    ----------
    directory
    file

    Returns
    -------

    """
    with open(file) as f:
        lines = f.readlines()

    files_in_dir = os.listdir(directory)
    files_not_in_dir = []
    for line in lines:
        filename = os.path.basename(line.rstrip('\n'))
        if filename not in files_in_dir:
            files_not_in_dir.append(filename)

    return files_not_in_dir


def readlines(file):
    with open(file) as f:
        lines = [line.rstrip('\n') for line in f]
    return lines


def move_dir_content(src, dest):
    files = os.listdir(src)
    for f in files:
        shutil.move(os.path.join(src, f), dest)
    os.rmdir(src)


def main(input_dir, flag_full_workflow=False, particle2jobs_dict={}, particle=None):
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


    Returns
    -------

        log_merge : dict (if flag_full_workflow is True)
            dictionary of dictionaries containing the log information of this script and the jobid of the batched job,
            separated by particle

             - log_merge[particle].keys() = ['logs_script_test', 'logs_script_train']

            ****  otherwise : (if flag_full_workflow is False, by default) ****
            None is returned

        jobid_merge : str (if flag_full_workflow is True)
            jobid of the batched job to be send (for dependencies purposes) to the next stage of the workflow
            (train_pipe)

            ****  otherwise : (if flag_full_workflow is False, by default)
            None is returned

    """

    if flag_full_workflow:
        log_merge = {particle: {}}
        log_merge[particle]['logs_script_test'] = []
        log_merge[particle]['logs_script_train'] = []
        log_merge[particle]['test_output'] = []
        log_merge[particle]['train_output'] = []

        wait_r0_dl1_jobs = ','.join(particle2jobs_dict[particle])

    print("\n ==== START {} ==== \n".format(sys.argv[0]))

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
    if not len(os.listdir(DL1_training_dir)) == len(readlines(training_filelist)):
        tf = check_files_in_dir_from_file(DL1_training_dir, training_filelist)
        if tf != [] and not flag_full_workflow:
            query_continue("{} files from the training list are not in the `DL1/training` directory:\n{} "
                           "Continue ?".format(len(tf), tf))
        elif tf != [] and flag_full_workflow:
            to_log = "\t{} files from the training list are not in the `DL1/training` directory:\n{} " \
                     "\tCannot stop workflow. CHECK LATER !".format(len(tf), tf)
            log_merge[particle]['logs_script_train'].append(to_log)

    if not len(os.listdir(DL1_testing_dir)) == len(readlines(testing_filelist)):
        tf = check_files_in_dir_from_file(DL1_testing_dir, testing_filelist)
        if tf != [] and not flag_full_workflow:
            query_continue("{} files from the testing list are not in the `DL1/testing directory:\n{} "
                           "Continue ?".format(len(tf), tf))
        elif tf != [] and flag_full_workflow:
            to_log = "\t{} files from the testing list are not in the `DL1/testing directory:\n{} " \
                     "\tCannot stop workflow. CHECK LATER !".format(len(tf), tf)
            log_merge[particle]['logs_script_test'].append(to_log)

    # 3. merge DL1 files
    print("\tmerging starts")
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

        log_merge[particle][set_type] = output_filename

    # 3.1 sbatch the jobs (or send them interactively depending) if the script is(not) run as part of the whole workflow
        filelist = [os.path.join(tdir, f) for f in os.listdir(tdir)]
        if not flag_full_workflow:
            cmd = f"lstchain_merge_hdf5_files -d {tdir} -o {output_filename}"
            os.system(cmd)
            # smart_merge_h5files(filelist, output_filename)

        else:  # flag_full_workflow == True !
            # TODO missing the job.o and job.e for the sbatch of the merge and copy
            # cmd = f'sbatch --parsable --dependency=afterok:{wait_r0_dl1_jobs} ' \
            #       f'--wrap="lstchain_merge_hdf5_files -d {tdir} -o {output_filename}"'

            cmd = 'sbatch --parsable'
            if wait_r0_dl1_jobs != '':
                cmd += ' --dependency=afterok:' + wait_r0_dl1_jobs
            cmd += ' --wrap="lstchain_merge_hdf5_files -d {} -o {}"'.format(tdir, output_filename)

            jobid_merge = os.popen(cmd).read().strip('\n')
            log_merge[particle][jobid_merge] = cmd

            # print(f'\t\t{cmd}')
            print(f'\t\tSubmitted batch job {jobid_merge}')

    # 4. move DL1 files in final place
    check_and_make_dir(final_DL1_dir)
    move_dir_content(running_DL1_dir, final_DL1_dir)
    print("\tDL1 files have been moved to {}".format(final_DL1_dir))

    # copy lstchain config file there too
    config_files = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.endswith('.json')]
    for file in config_files:
        shutil.copyfile(file, os.path.join(final_DL1_dir, os.path.basename(file)))

    # 5. move running_dir as logs
    check_and_make_dir(logs_destination_dir)
    move_dir_content(input_dir, logs_destination_dir)
    print("\tLOGS have been moved to {}".format(logs_destination_dir))

    print("\n ==== END {} ==== \n".format(sys.argv[0]))

    if flag_full_workflow:
        return log_merge, jobid_merge


if __name__ == '__main__':
    args = parser.parse_args()
    main(args.input_dir)
