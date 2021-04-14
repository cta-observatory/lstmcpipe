#!/usr//bin/env python

# T. Vuillaume,
# Modifications by E. Garcia
# Code train models from DL1 files onsite (La Palma cluster)

import os
import shutil
import argparse
from data_management import (check_and_make_dir,
                             check_and_make_dir_without_verification)

parser = argparse.ArgumentParser(description="Train models onsite")

parser.add_argument('--gamma_dl1_training_file', '-fg', type=str,
                    dest='gamma_dl1_train',
                    help='path to the gamma file',
                    )

parser.add_argument('--proton_dl1_training_file', '-fp', type=str,
                    dest='proton_dl1_train',
                    help='path to the proton file',
                    )

parser.add_argument('--config_file', '-conf', action='store', type=str,
                    dest='config_file',
                    help='Path to a configuration file. If none is given, a standard configuration is applied',
                    default=None
                    )

# source env onsite - can be changed for custom install
source_env = 'source /fefs/aswg/software/virtual_env/.bashrc; conda activate cta;'


def main(gamma_dl1_train_file, proton_dl1_train_file, config_file=None, source_environment=source_env,
         flag_full_workflow=False, wait_ids_proton_and_gammas=None):
    """
    Train RF from dl1 data  (onsite LaPalma cluster)

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
    flag_full_workflow :  bool
        Boolean flag to indicate if this script is run as part of the workflow that converts r0 to dl2 files.
    wait_ids_proton_and_gammas : str
        a string (of chained jobids separated by ',' and without spaces between each element), to indicate the
        dependencies of the job to be batched
        COMPULSORY argument when flag_full_workflow is set to True.


    Returns
    -------
    log_train : dict (if flag_full_workflow is True)
        dictionary containing the jobid of the batched job as key and the run command (the lstchain_mc_train
        command with all its corresponding arguments) as value.

        ****  otherwise : (if flag_full_workflow is False, by default) ****
        None is returned -- THIS IS APPLIED FOR THE ARGUMENTS SHOWN BELOW TOO

    jobid_train : str (if flag_full_workflow is True)
        jobid of the batched job to be send (for dependencies purposes) to the next stage of the
        workflow (onsite_mc_dl1_to_dl2)

    models_dir : str
        Path with the directory where the models are stored

    """

    if flag_full_workflow:
        log_train = {}

    else:
        print(f"\n ==== START {os.path.basename(__file__)} ==== \n")

    # dl1_gamma_dir = os.path.dirname(os.path.abspath(gamma_dl1_train_file))
    dl1_proton_dir = os.path.dirname(os.path.abspath(proton_dl1_train_file))

    # check if it path follows the established paths (lstchain-like) or not (rta-like) ##
    if dl1_proton_dir.find('/mc/DL1/') > 0:
        models_dir = dl1_proton_dir.replace('/mc/DL1', '/models')
    else:
        models_dir = dl1_proton_dir.replace('/DL1', '/models')
    models_dir = models_dir.replace('/proton/', '/')

    print(f"\tModels will be placed in {models_dir}")
    if flag_full_workflow:
        check_and_make_dir_without_verification(models_dir)
    else:
        check_and_make_dir(models_dir)

    base_cmd = ''
    base_cmd += source_environment
    base_cmd += f'lstchain_mc_trainpipe --fg {os.path.abspath(gamma_dl1_train_file)}' \
                f' --fp {os.path.abspath(proton_dl1_train_file)} -o {models_dir}'

    if config_file is not None:
        base_cmd = base_cmd + ' -c {}'.format(config_file)

    jobo = os.path.join(models_dir, "train_job.o")
    jobe = os.path.join(models_dir, "train_job.e")

    if not flag_full_workflow:
        cmd = f'sbatch -p long -e {jobe} -o {jobo} --wrap="{base_cmd}" '

        print(cmd)
        os.system(cmd)

    else:  # flag_full_workflow == True !
        # 'sbatch --parsable --dependency=afterok:{wait_ids_proton_and_gammas} -e {jobe} -o {jobo} --wrap="{base_cmd}"'
        cmd = 'sbatch --parsable -p long'
        if wait_ids_proton_and_gammas != '':
            cmd += ' --dependency=afterok:' + wait_ids_proton_and_gammas
        cmd += f' -J train_pipe -e {jobe} -o {jobo} --wrap="{base_cmd}" '

        jobid_train = os.popen(cmd).read().strip('\n')
        log_train[jobid_train] = cmd

    # copy this script and config into working dir
    shutil.copyfile(__file__, os.path.join(models_dir, os.path.basename(__file__)))
    if config_file is not None:
        shutil.copyfile(config_file, os.path.join(models_dir, os.path.basename(config_file)))

    if not flag_full_workflow:
        print(f"\n ==== END {os.path.basename(__file__)} ==== \n")
    else:
        return log_train, jobid_train, models_dir


if __name__ == '__main__':
    args = parser.parse_args()
    main(args.gamma_dl1_train,
         args.proton_dl1_train,
         args.config_file,
         source_environment=source_env)
