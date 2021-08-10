#!/usr/bin/env python

import os




def batch_dl2_to_sensitivity(dl2_directory, offset_gammas, job_ids_from_dl1_dl2, log_from_dl1_dl2, source_env, prod_id):
    """
    Batches the dl2_to_sensitivity stage (`stages.script_dl2_to_sensitivity` based in the pyIRF iib) once the
    dl1_to_dl2 stage had finished.

    Parameters
    ----------
    dl2_directory: str
        Base path to DL2 directory to be formatted with particle type
    offset_gammas: list
        list off gamma offsets
    job_ids_from_dl1_dl2: str
        Comma-separated string with the job ids from the dl1_to_dl2 stage to be used as a slurm dependency
        to schedule the current stage
    log_from_dl1_dl2: dict
        Dictionary from dl1_to_dl2 stage with particle path information
    source_env: str
        source environment to select the desired conda environment (source .bashrc + conda activate $ENV)
    prod_id: str
        String with prod_id prefix to complete 'file-naming'

    Returns
    -------
    log_dl2_to_sensitivity: dict
        Dictionary with job_id-slurm command key-value pair used for logging
    jobid_for_check: str
        Comma-separated jobids batched in the current stage
    debug_log: dict
        Dictionary with the job-id and stage explanation to be stored in the debug file

    """
    print("\n ==== START {} ==== \n".format('batch mc_dl2_to_sensitivity'))

    debug_log = {}
    jobid_for_check = []
    log_dl2_to_sensitivity = {}

    for off in offset_gammas:

        log, jobid = dl2_to_sensitivity(dl2_directory,
                                        log_from_dl1_dl2,
                                        gamma_offset=off,
                                        prod_id=prod_id,
                                        source_env=source_env,
                                        wait_jobs_dl1_dl2=job_ids_from_dl1_dl2
                                        )

        jobid_for_check.append(jobid)
        log_dl2_to_sensitivity[f'gamma_{off}'] = log
        debug_log[jobid] = f'Gamma_{off} job_ids from the dl2_to_sensitivity stage and the plot_irfs script that ' \
                           f'depends on the dl1_to_dl2 stage job_ids; {job_ids_from_dl1_dl2}'

    jobid_for_check = ','.join(jobid_for_check)

    print("\n ==== END {} ==== \n".format('batch mc_dl2_to_sensitivity'))

    return log_dl2_to_sensitivity, jobid_for_check, debug_log




def batch_plot_sensitivity(sensitivity_filename, wait_jobid_dl2_to_sens, gamma_offset, source_env):
    """
    Batches the the `plot_irfs` entry point after the computation of the `dl2_to_sensitivity` script

    Parameters
    ----------
    sensitivity_filename: str
        Path to sensitivity.fits.gz file
    wait_jobid_dl2_to_sens: str
        Jobid from dl2_to_sensitivity stage to be used as a slurm dependency
    gamma_offset: str
        String to indicate the gamma offset. Either 'off0.0deg' or 'off0.4deg'
    source_env: str
        Source environment (source .bashrc + conda activate env) to be used in the slurm cmd

    Returns
    -------
    log: dict
        Dictionary with job_id-slurm command key-value pair used for logging
    job_id: str
        String with single job_id batched by the lstmcpipe_plot_irfs entry point

    """
    cmd = f'lstmcpipe_plot_irfs -f {sensitivity_filename} -o {sensitivity_filename.replace(".fits.gz", ".png")}'

    jobe = os.path.join(os.path.abspath(os.path.dirname(sensitivity_filename)),
                        f'job_plot_sensitivity_gamma_{gamma_offset}.e')
    jobo = os.path.join(os.path.abspath(os.path.dirname(sensitivity_filename)),
                        f'job_plot_sensitivity_gamma_{gamma_offset}.o')

    job_name = gamma_offset.replace(".", "").replace("off", "").replace("deg", "")
    base_cmd = f'sbatch --parsable -p short --dependency=afterok:{wait_jobid_dl2_to_sens} -e {jobe} -o {jobo}' \
               f' -J {job_name}_sens_plot --wrap="export MPLBACKEND=Agg; {source_env} {cmd}"'

    job_id = os.popen(base_cmd).read().strip('\n')
    log = {job_id: base_cmd}

    return log, job_id


def batch_dl2_to_sensitivity(gamma_file, proton_file, electron_file, gamma_offset, output_directory, output_filename,
                             source_env, wait_jobs_dl1dl2):
    """
    Batches the dl2_to_sensitivity slurm script with all the needed args

    Parameters
    ----------
    gamma_file: str
        Path to DL2 gamma test file
    proton_file: str
        Path to DL2 proton test file
    electron_file: str
        Path to DL2 electron test file
    gamma_offset: str
        String to indicate the gamma offset. Either 'off0.0deg' or 'off0.4deg'
    output_directory: str
        Absolute path with output directory
    output_filename: str
        Output filename
    source_env: str
        Source environment (source .bashrc + conda activate env) to be used in the slurm cmd
    wait_jobs_dl1dl2: str
        Comma-separated string with the jobs (dependency) to wait for before launching the cmd

    Returns
    -------
    log: dict
        Dictionary with job_id-slurm command key-value pair used for logging
    job_id: str
        String with single job_id batched by the dl2_to_sensitivity script

    """

    cmd = f'lstmcpipe_dl2_to_sensitivity -g {gamma_file} -p {proton_file} -e {electron_file} ' \
          f' -o {output_filename}'

    jobo = os.path.join(output_directory, f'job_dl2_to_sensitivity_gamma_{gamma_offset}.o')
    jobe = os.path.join(output_directory, f'job_dl2_to_sensitivity_gamma_{gamma_offset}.e')

    job_name = gamma_offset.replace(".", "").replace("off", "")
    base_cmd = f'sbatch --parsable -p short --dependency=afterok:{wait_jobs_dl1dl2} -e {jobe} -o {jobo} ' \
               f' -J {job_name}_sensitivity --wrap="{source_env} {cmd}"'

    job_id = os.popen(base_cmd).read().strip('\n')

    log = {job_id: base_cmd}

    return log, job_id


def compose_sensitivity_outdir(dl2_dir, gamma_offset):
    """
    Compute the sensitivity output directory depending on the type of gamma file

    Parameters
    ----------
    dl2_dir: str
        Base path to DL2 directory
    gamma_offset: str
        String to indicate the gamma offset. Either 'off0.0deg' or 'off0.4deg'

    Returns
    -------
    output_sensitivity_dir: str
        Absolute path in where to store the sensitivity.fits.fz files

    """

    allowed_gamma_off = ['off0.0deg', 'off0.4deg']
    if gamma_offset not in allowed_gamma_off:
        print(f'Please select a valid gamma_offset to compute the IRFS: {" or ".join(allowed_gamma_off)}')
        exit(-1)

    output_sensitivity_dir = os.path.join(dl2_dir.replace('/DL2/', '/IRF/').replace('/{}/', '/'),
                                          gamma_offset)

    os.makedirs(output_sensitivity_dir, exist_ok=True)

    return output_sensitivity_dir


def sensitivity_io(dl2_directory, log_from_dl1_dl2, gamma_offset='off0.0deg', prod_id=None):
    """
    Manages the i/o arguments and parameters to be passed to the batch_dl2_to_sensitivity function.

    Parameters
    ----------
    dl2_directory: str
        Base path to DL2 directory
    log_from_dl1_dl2: dict
        Dictionary with particle abs path created in previous stages #TODO to be changed by a glob.glob ?
    gamma_offset: str
        String to indicate the gamma offset if gamma_point_like == True. Either 'off0.0deg' or 'off0.4deg'
    prod_id: str
        String with prod_id prefix to complete 'file-naming'

    Returns
    -------
    gamma_file: str
        Absolute path to DL2 gamma test file
    proton_file: str
        Absolute path to DL2 proton test file
    electron_file: str
        Absolute path to DL2 electron test file
    output_directory: str
        Absolute path with output directory
    output_sensitivity_filename: str
        Output filename

    """
    output_directory = compose_sensitivity_outdir(dl2_directory, gamma_offset)

    # Find paths to DL2 files
    proton_file = log_from_dl1_dl2['proton']['dl2_test_path']
    electron_file = log_from_dl1_dl2['electron']['dl2_test_path']

    if gamma_offset == 'off0.0deg':
        gamma_file = log_from_dl1_dl2['gamma_off0.0deg']['dl2_test_path']
    else:
        # gamma_offset == 'off0.4deg'. No other case possible, it has been checked in 'compose_sensitivity_outdir'
        gamma_file = log_from_dl1_dl2['gamma_off0.4deg']['dl2_test_path']

    # Create output filenames
    if prod_id is None:
        output_sensitivity_filename = os.path.join(output_directory, 'sensitivity.fits.gz')
    else:
        output_sensitivity_filename = os.path.join(
            output_directory,
            f'{prod_id.replace(".", "")}_gamma_{gamma_offset.replace(".", "")}_sensitivity.fits.gz')

    return gamma_file, proton_file, electron_file, output_directory, output_sensitivity_filename


def dl2_to_sensitivity(dl2_dir, log_from_dl1_dl2, gamma_offset='off0.0deg', prod_id=None, source_env='',
                       wait_jobs_dl1_dl2=''):
    """
    Function to run the `script_dl2_to_sensitivity` for the gamma (and the different gamma offsets) and gamma-diffuse
    particles.
    Creates the sensitivity *.fits.gz files and the corresponding sensitivity curve plot.

    Parameters
    ----------
    dl2_dir: str
        Base path to DL2 directory
    log_from_dl1_dl2: dict
        Dictionary with particle abs path created in previous stages #TODO to be changed by a glob.glob ?
    gamma_offset: str
        String to indicate the gamma offset if gamma_point_like == True. Either 'off0.0deg' or 'off0.4deg'
    prod_id: str
        String with prod_id prefix to complete 'filenaming'
    source_env: str
        Source environment (source .bashrc + conda activate env) to be used in the slurm cmd
    wait_jobs_dl1_dl2: str
        Comma-separated string with the jobs (dependency) to wait for before launching the cmd

    Returns
    -------
    log_dl2_to_sensitivity: dict
        Dictionary with job_id-slurm command key-value pair used for logging
    job_id: str
        String with job_ids batched by the dl2_to_sensitivity script

    """
    log_dl2_to_sensitivity = {}
    jobids_dl2_to_sensitivity = []

    g_file, p_file, e_file, out_dir, out_file = \
        sensitivity_io(dl2_dir,
                       log_from_dl1_dl2,
                       gamma_offset,
                       prod_id)

    # create sensitivity files
    log_dl2_sens, job_id_dl2_sens = \
        batch_dl2_to_sensitivity(g_file,
                                 p_file,
                                 e_file,
                                 gamma_offset,
                                 out_dir,
                                 out_file,
                                 source_env,
                                 wait_jobs_dl1_dl2)

    log_dl2_to_sensitivity.update(log_dl2_sens)
    jobids_dl2_to_sensitivity.append(job_id_dl2_sens)

    # Create plot from sensitivity files
    log_plot_sens, job_id_plot_sens = \
        batch_plot_sensitivity(out_file,
                               job_id_dl2_sens,
                               gamma_offset,
                               source_env)

    log_dl2_to_sensitivity.update(log_plot_sens)
    jobids_dl2_to_sensitivity.append(job_id_plot_sens)
    jobids_dl2_to_sensitivity = ','.join(jobids_dl2_to_sensitivity)

    return log_dl2_to_sensitivity, jobids_dl2_to_sensitivity
