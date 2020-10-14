#!/usr//bin/env python

# T. Vuillaume,
# Modifications by E. Garcia
# DL1 to DL2 onsite (La Palma cluster)

import os
import shutil
import argparse
from data_management import (check_and_make_dir,
                             query_continue,
                             check_and_make_dir_without_verification)

parser = argparse.ArgumentParser(description="Convert onsite files from dl1 to dl2")

parser.add_argument('input_dir', type=str,
                    help='path to the files directory to analyse',
                    )

parser.add_argument('--path_models', '-pm', action='store', type=str,
                    dest='path_models',
                    help='path to the trained models',
                    default=None,
                    )

parser.add_argument('--config_file', '-conf', action='store', type=str,
                    dest='config_file',
                    help='Path to a configuration file. If none is given, a standard configuration is applied',
                    default=None
                    )


def main(input_dir, path_models, config_file, flag_full_workflow=False, particle=None, wait_jobid_train_pipe=None,
         wait_jobids_merge=None, dictionary_with_dl1_paths=None, source_environment=None):
    """
    Convert onsite files from dl1 to dl2"

    Parameters
    ----------
    input_dir : str
        path to the files directory to analyse

    path_models : str
        path to the trained models

    config_file : str
        Path to a configuration file. If none is given, a standard configuration is applied

    flag_full_workflow : bool
        Boolean flag to indicate if this script is run as part of the workflow that converts r0 to dl2 files.

    particle : str
        Type of particle used to create the log and dictionary
            ! COMPULSORY argument when flag_full_workflow is set to True.

    wait_jobid_train_pipe : str
        a string with the batched jobid from the train stage to indicate the
        dependencies of the job to be batched
            ! COMPULSORY argument when flag_full_workflow is set to True.

    wait_jobids_merge : str
        string with merge_and_copy jobids
            ! COMPULSORY argument when flag_full_workflow is set to True.

    dictionary_with_dl1_paths : dict
        Dictionary with 'particles' as keys containing final outnames of dl1 files.
            ! COMPULSORY argument when flag_full_workflow is set to True.

    source_environment : str
        path to a .bashrc file (lstanalyzer user by default - can be configurable for custom runs) to activate a
        certain conda environment. By default : `conda activate cta`.
        ! NOTE : train_pipe AND dl1_to_dl2 MUST BE RUN WITH THE SAME ENVIRONMENT

    Returns
    -------
    log_dl1_to_dl2 : dict
        dictionary of dictionaries containing the jobid of the batched job as key and the run command (the
        lstchain_mc_dl1_to_dl2 command with all its corresponding arguments) as value.

        ****  otherwise : (if flag_full_workflow is False, by default) ****
        None is returned -- THIS IS APPLIED FOR THE ARGUMENTS SHOWN BELOW TOO

    jobid_dl1_to_dl2 : str
        jobid of the batched job to be send (for dependencies purposes) to the next stage of the
        workflow (#TODO dl2_to_dl3 )

    """

    output_dir = input_dir.replace('DL1', 'DL2')

    if flag_full_workflow:

        check_and_make_dir_without_verification(output_dir)
        print(f"\tOutput dir {particle}: {output_dir}")

        log_dl1_to_dl2 = {particle: {}}

        # path to dl1 files by particle type
        file_list = [dictionary_with_dl1_paths[particle]['training']['train_path_and_outname_dl1'],
                     dictionary_with_dl1_paths[particle]['testing']['test_path_and_outname_dl1']]

        return_jobids = []

        if wait_jobid_train_pipe == '':
            wait_jobs = wait_jobids_merge
        elif wait_jobids_merge == '':
            wait_jobs = wait_jobid_train_pipe
        elif wait_jobids_merge == '' and wait_jobid_train_pipe == '':
            wait_jobs = ''
        else:
            wait_jobs = ','.join([wait_jobid_train_pipe, wait_jobids_merge])

        job_name = {'electron': 'dl1-2_e',
                    'gamma': 'dl1-2_g',
                    'gamma-diffuse': 'dl1-2_gd',
                    'proton': 'dl1-2_p',
                    'gamma_off0.0deg': 'g0.0_merge',
                    'gamma_off0.4deg': 'g0.4_merge'
                    }

    else:
        print("\n ==== START {} ==== \n".format(os.path.basename(__file__)))

        check_and_make_dir(output_dir)
        print(f"Output dir: {output_dir}")

        file_list = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.startswith('dl1_')]

        query_continue(f"{len(file_list)} jobs,  ok?")

    for file in file_list:

        cmd = ''
        if source_environment is not None:
            cmd += source_environment
        cmd += f'lstchain_dl1_to_dl2 -f {file} -p {path_models} -o {output_dir}'

        if config_file is not None:
            cmd += f' -c {config_file}'

        if not flag_full_workflow:  # Run interactively
            print(cmd)
            os.system(cmd)

        else:  # flag_full_workflow == True !
            # 'sbatch --parsable --dependency=afterok:{wait_ids_proton_and_gammas} --wrap="{cmd}"'

            if 'training' in file:
                ftype = 'train'
            elif 'testing' in file:
                ftype = 'test'
            else:
                ftype = '-'

            jobe = os.path.join(output_dir, f"dl1_dl2_{particle}_{ftype}job.e")
            jobo = os.path.join(output_dir, f"dl1_dl2_{particle}_{ftype}job.o")

            batch_cmd = 'sbatch --parsable -p short'
            if wait_jobs != '':
                batch_cmd += ' --dependency=afterok:' + wait_jobid_train_pipe
            batch_cmd += ' -J {} -e {} -o {} --wrap="{}"'.format(job_name[particle],
                                                                 jobe, jobo,
                                                                 cmd)

            jobid_dl1_to_dl2 = os.popen(batch_cmd).read().strip('\n')

            log_dl1_to_dl2[particle][jobid_dl1_to_dl2] = batch_cmd
            return_jobids.append(jobid_dl1_to_dl2)

    # copy this script and config into working dir
    shutil.copyfile(__file__, os.path.join(output_dir, os.path.basename(__file__)))
    if config_file is not None:
        shutil.copyfile(config_file, os.path.join(output_dir, os.path.basename(config_file)))

    if not flag_full_workflow:
        print("\n ==== END {} ==== \n".format(os.path.basename(__file__)))
    else:
        return_jobids = ','.join(return_jobids)

        return log_dl1_to_dl2, return_jobids


if __name__ == '__main__':
    args = parser.parse_args()
    main(args.input_dir,
         args.path_models,
         args.config_file)
