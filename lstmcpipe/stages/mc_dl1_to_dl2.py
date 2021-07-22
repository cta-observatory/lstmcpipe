#!/usr/bin/env python

# T. Vuillaume,
# Modifications by E. Garcia
# lstMCpipe DL1 to DL2 onsite stage (at La Palma cluster)

import os
import shutil
from lstmcpipe.io.data_management import (
    check_and_make_dir_without_verification
)


def dl1_to_dl2(input_dir, path_models, config_file,  particle, wait_jobid_train_pipe=None,
               wait_jobids_merge=None, dictionary_with_dl1_paths=None, source_environment=None):
    """
    Convert onsite files from dl1 to dl2

    Parameters
    ----------
    input_dir : str
        DL1 base path
    path_models : str
        Path to the trained models
    config_file : str
        Path to a configuration file. If none is given, a standard configuration is applied
    particle : str
        Particle to which apply the dl1_to_dl2 stage
    wait_jobid_train_pipe : str
        Comma-separated string with the batched jobid from the train stage to indicate the
        dependencies of the current job to be batched
    wait_jobids_merge : str
        string with merge_and_copy jobids
    dictionary_with_dl1_paths : dict
        Dictionary with 'particles' as keys containing final output filenames of dl1 files.
    source_environment : str
        path to a .bashrc file to source (can be configurable for custom runs @ mc_r0_to_dl3 script) to activate
        a certain conda environment.
        ! NOTE : train_pipe AND dl1_to_dl2 MUST BE RUN WITH THE SAME ENVIRONMENT

    Returns
    -------
    log_dl1_to_dl2 : dict
        dictionary of dictionaries containing the jobid of the batched job as key and the run command (the
        lstchain_mc_dl1_to_dl2 command with all its corresponding arguments) as value.

    jobid_dl1_to_dl2 : str
        jobid of the batched job to be send (for dependencies purposes) to the next stage of the
        workflow (dl2_to_irfs)

    """

    output_dir = input_dir.replace('DL1', 'DL2')

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
                'gamma_off0.0deg': 'dl1-2_g.0',
                'gamma_off0.4deg': 'dl1-2_g.4'
                }

    for file in file_list:

        cmd = ''
        if source_environment is not None:
            cmd += source_environment
        cmd += f'lstchain_dl1_to_dl2 -f {file} -p {path_models} -o {output_dir}'

        if config_file is not None:
            cmd += f' -c {config_file}'

        # TODO dry-run option ?
        # if dry_run:
        #     print(cmd)

        if 'training' in file:
            ftype = 'train'
        elif 'testing' in file:
            ftype = 'test'
        else:
            ftype = '-'

        jobe = os.path.join(output_dir, f"dl1_dl2_{particle}_{ftype}job.e")
        jobo = os.path.join(output_dir, f"dl1_dl2_{particle}_{ftype}job.o")

        # sbatch --parsable --dependency=afterok:{wait_ids_proton_and_gammas} --wrap="{cmd}"
        batch_cmd = f'sbatch --parsable -p short --dependency=afterok:{wait_jobs} -J {job_name[particle]}' \
                    f' -e {jobe} -o {jobo} --wrap="{cmd}"'

        # Batch the job at La Palma
        jobid_dl1_to_dl2 = os.popen(batch_cmd).read().strip('\n')

        log_dl1_to_dl2[particle][jobid_dl1_to_dl2] = batch_cmd
        if 'testing' in file:  # TODO to be done to 'training' files too ? Should not be necessary
            log_dl1_to_dl2[particle]['dl2_test_path'] = file.replace('/DL1/', '/DL2/').replace('dl1_', 'dl2_')
        return_jobids.append(jobid_dl1_to_dl2)

    if config_file is not None:
        shutil.copyfile(config_file, os.path.join(output_dir, os.path.basename(config_file)))

    return_jobids = ','.join(return_jobids)

    return log_dl1_to_dl2, return_jobids
