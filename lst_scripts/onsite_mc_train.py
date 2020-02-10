#!/usr//bin/env python

# T. Vuillaume,
# Modifications by E. Garcia
# Code train models from DL1 files onsite (La Palma cluster)

import argparse
from lstchain.io.data_management import *

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
source_env = 'source /local/home/lstanalyzer/.bashrc; conda activate cta;'


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
        path to the lstanalyzer .bashrc file (or an alternative .bashrc file for custom runs) to activate a
        certain conda environment. By default : `conda activate cta`
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
        None is returned

    jobid_train : str (if flag_full_workflow is True)
        jobid of the batched job to be send (for dependencies purposes) to the next stage of the
        workflow (onsite_mc_dl1_to_dl2)

        ****  otherwise : (if flag_full_workflow is False, by default) ****
        None is returned

    """

    if flag_full_workflow:
        log_train = {}
        print("\n ==== START {} ==== \n".format('mc_train_workflow'))

    else:
        print("\n ==== START {} ==== \n".format(sys.argv[0]))

    dl1_gamma_dir = os.path.dirname(os.path.abspath(gamma_dl1_train_file))
    dl1_proton_dir = os.path.dirname(os.path.abspath(proton_dl1_train_file))

    # TODO develop and add check_prod_id function --> @Thomas
    # check_prod_id(dl1_gamma_dir, dl1_proton_dir)

    models_dir = dl1_proton_dir.replace('/mc/DL1', '/models')
    models_dir = models_dir.replace('/proton/', '/')

    check_and_make_dir(models_dir)

    base_cmd = ''
    base_cmd += source_environment
    base_cmd += 'lstchain_mc_trainpipe -fg {} -fp {} -o {}'.format(os.path.abspath(gamma_dl1_train_file),
                                                                   os.path.abspath(proton_dl1_train_file),
                                                                   models_dir,
                                                                   )
    if config_file is not None:
        base_cmd = base_cmd + ' -conf {}'.format(config_file)

    jobo = os.path.join(models_dir, "train_job.o")
    jobe = os.path.join(models_dir, "train_job.e")

    if not flag_full_workflow:
        cmd = 'sbatch -e {} -o {} --wrap="{}" '.format(jobe, jobo, base_cmd)

        print(cmd)
        os.system(cmd)

    else:  # flag_full_workflow == True !
        # 'sbatch --parsable --dependency=afterok:{wait_ids_proton_and_gammas} -e {jobe} -o {jobo} --wrap="{base_cmd}"'
        cmd = 'sbatch --parsable'
        if wait_ids_proton_and_gammas != '':
            cmd += ' --dependency=afterok:' + wait_ids_proton_and_gammas
        cmd += ' -e {} -o {} --wrap="{}" '.format(jobe, jobo, base_cmd)

        jobid_train = os.popen(cmd).read().strip('\n')
        log_train[jobid_train] = cmd

        return log_train, jobid_train

    # copy this script itself into logs
    shutil.copyfile(sys.argv[0], os.path.join(models_dir, os.path.basename(sys.argv[0])))
    # copy config file into logs
    if config_file is not None:
        shutil.copy(config_file, os.path.join(models_dir, os.path.basename(config_file)))

    if not flag_full_workflow:
        print("\n ==== END {} ==== \n".format(sys.argv[0]))
    else:
        print("\n ==== END {} ==== \n".format('mc_train_workflow'))


if __name__ == '__main__':
    args = parser.parse_args()
    main(args.gamma_dl1_train, args.proton_dl1_trainm, args.config_file, source_environment=source_env)
