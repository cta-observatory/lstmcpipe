#!/usr//bin/env python

# T. Vuillaume,
# Modifications by E. Garcia
# DL1 to DL2 onsite (La Palma cluster)


import argparse
from lstchain.io.data_management import *
from data_management import check_and_make_dir_without_verification

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


def main(input_dir, path_models=None, config_file=None, flag_full_workflow=False, particle=None,
         wait_jobid_train_pipe=None, wait_jobids_merge=None, dictionary_with_dl1_paths=None):
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
        print("\n ==== START {} ==== \n".format('dl1_to_dl2_workflow'))

        check_and_make_dir_without_verification(output_dir)
        print(f"Output dir: {output_dir}")

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
                    'proton': 'dl1-2_p'
                    }

    else:
        print("\n ==== START {} ==== \n".format(sys.argv[0]))

        check_and_make_dir(output_dir)
        print(f"Output dir: {output_dir}")

        file_list = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.startswith('dl1_')]

        query_continue(f"{len(file_list)} jobs,  ok?")

    for file in file_list:
        cmd = f'lstchain_mc_dl1_to_dl2 -f {file} -p {path_models} -o {output_dir}'
        if config_file is not None:
            cmd += f' -conf {config_file}'

        if not flag_full_workflow:
            print(cmd)
            os.system(cmd)

        else:  # flag_full_workflow == True !
            # TODO missing too the job.e and job.o for this stage
            # 'sbatch --parsable --dependency=afterok:{wait_ids_proton_and_gammas} --wrap="{cmd}"'

            batch_cmd = 'sbatch --parsable'
            if wait_jobs != '':
                batch_cmd += ' --dependency=afterok:' + wait_jobid_train_pipe
            batch_cmd += ' -J {} --wrap="{}"'.format(job_name[particle], cmd)

            jobid_dl1_to_dl2 = os.popen(batch_cmd).read().strip('\n')

            log_dl1_to_dl2[particle][jobid_dl1_to_dl2] = batch_cmd
            return_jobids.append(jobid_dl1_to_dl2)

    if not flag_full_workflow:
        print("\n ==== END {} ==== \n".format(sys.argv[0]))
    else:
        print("\n ==== END {} ==== \n".format('dl1_to_dl2_workflow'))
        return_jobids = ','.join(return_jobids)

        return log_dl1_to_dl2, return_jobids


if __name__ == '__main__':
    args = parser.parse_args()
    main(args.input_dir, args.path_models, args.config_file)
