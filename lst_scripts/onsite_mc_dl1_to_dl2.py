#!/usr//bin/env python

# T. Vuillaume,
# Modifications by E. Garcia
# DL1 to DL2 onsite (La Palma cluster)


import argparse
from lstchain.io.data_management import *

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


def main(input_dir, path_models=None, config_file=None, flag_full_workflow=False,
         wait_ids_proton_and_gammas=None, particle=None):
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
    wait_ids_proton_and_gammas : str
        a string (of chained jobids separated by ',' and without spaces between each element), to indicate the
        dependencies of the job to be batched
        COMPULSORY argument when flag_full_workflow is set to True.
    particle : str
        Type of particle used to create the log and dictionary
        COMPULSORY argument when flag_full_workflow is set to True.

    Returns
    -------
        log_dl1_to_dl2 : dict
            dictionary of dictionaries containing the jobid of the batched job as key and the run command (the
            lstchain_mc_dl1_to_dl2 command with all its corresponding arguments) as value.

            ****  otherwise : (if flag_full_workflow is False, by default) ****
            None is returned

        jobid_dl1_to_dl2 : str
            jobid of the batched job to be send (for dependencies purposes) to the next stage of the
            workflow (#TODO dl2_to_dl3 ??)

            ****  otherwise : (if flag_full_workflow is False, by default) ****
            None is returned

    """

    if flag_full_workflow:
        log_dl1_to_dl2 = {particle: {}}

    output_dir = input_dir.replace('DL1', 'DL2')

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

            batch_cmd = f'sbatch --parsable --dependency=afterok:{wait_ids_proton_and_gammas} --wrap="{cmd}"'
            jobid_dl1_to_dl2 = os.popen(batch_cmd).read().split('\n')

            log_dl1_to_dl2[particle][jobid_dl1_to_dl2] = batch_cmd

            return log_dl1_to_dl2, jobid_dl1_to_dl2


if __name__ == '__main__':
    args = parser.parse_args()
    main(args.input_dir, args.path_models, args.config_file)
