#!/usr//bin/env python

# T. Vuillaume,
# Modifications by E. Garcia
# Code train models from DL1 files onsite (La Palma cluster)

import os
import shutil
from lstmcpipe.io.data_management import check_and_make_dir_without_verification


def train_pipe(gamma_dl1_train_file, proton_dl1_train_file, config_file=None, source_environment=None,
               wait_ids_proton_and_gammas=None):
    """
    Train RF from MC DL1 data (onsite LaPalma cluster)

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
    wait_ids_proton_and_gammas : str
        a string (of chained jobids separated by ',' and without spaces between each element), to indicate the
        dependencies of the job to be batched

    Returns
    -------
    log_train : dict
        dictionary containing the jobid of the batched job as key and the run command (the lstchain_mc_train
        command with all its corresponding arguments) as value.

    jobid_train : str
        jobid of the batched job to be send (for dependencies purposes) to the next stage of the
        workflow (onsite_mc_dl1_to_dl2)

    models_dir : str
        Path with the directory where the models are stored

    """
    log_train = {}

    dl1_proton_dir = os.path.dirname(os.path.abspath(proton_dl1_train_file))

    # check if it path follows the established paths (lstchain-like) or not (rta-like) ##
    if dl1_proton_dir.find('/mc/DL1/') > 0:
        models_dir = dl1_proton_dir.replace('/mc/DL1', '/models')
    else:
        models_dir = dl1_proton_dir.replace('/DL1', '/models')
    models_dir = models_dir.replace('/proton/', '/')

    print(f"\tModels will be placed in {models_dir}")
    check_and_make_dir_without_verification(models_dir)

    cmd = ''
    if source_environment is not None:
        cmd += source_environment

    cmd += f' lstchain_mc_trainpipe --fg {os.path.abspath(gamma_dl1_train_file)}' \
           f' --fp {os.path.abspath(proton_dl1_train_file)} -o {models_dir}'

    if config_file is not None:
        cmd = cmd + ' -c {}'.format(config_file)

    jobo = os.path.join(models_dir, "train_job.o")
    jobe = os.path.join(models_dir, "train_job.e")

    # TODO dry-run option ?
    # if dry_run:
    #     print(cmd)

    # 'sbatch --parsable --dependency=afterok:{wait_ids_proton_and_gammas} -e {jobe} -o {jobo} --wrap="{base_cmd}"'
    batch_cmd = 'sbatch --parsable -p long'
    if wait_ids_proton_and_gammas != '':
        batch_cmd += ' --dependency=afterok:' + wait_ids_proton_and_gammas
    batch_cmd += f' -J train_pipe -e {jobe} -o {jobo} --wrap="{cmd}" '

    jobid_train = os.popen(cmd).read().strip('\n')
    log_train[jobid_train] = cmd

    # copy config into working dir
    if config_file is not None:
        shutil.copyfile(config_file, os.path.join(models_dir, os.path.basename(config_file)))

    return log_train, jobid_train, models_dir
