#!/usr/bin/env python

import os


def batch_plot_senstitivity(sensitivity_filename, wait_jobid_dl2_to_sens, job_name):
    """
    Batches the the `plot_irfs` entry point after the computation of the `dl2_to_sensitivity` script

    Parameters
    ----------
    sensitivity_filename: str
        Path to sensitivity.fits.gz file
    wait_jobid_dl2_to_sens: str
        Jobid from dl2_to_sensitivity stage to be used as a slurm dependency
    job_name: str
        Gamma type string for file-naming

    Returns
    -------
    log: dict
        Dictionary with job_id-slurm command key-value pair used for logging
    job_id: str
        String with single job_id batched by the lstmcpipe_plot_irfs entry point

    """
    cmd = f'lstmcpipe_plot_irfs -f {sensitivity_filename} -o {sensitivity_filename.replace(".fits.gz", ".png")}'

    jobe = os.path.join(os.path.abspath(os.path.dirname(sensitivity_filename)),
                        f'job_plot_sensitivity_g_{job_name}.e')
    jobo = os.path.join(os.path.abspath(os.path.dirname(sensitivity_filename)),
                        f'job_plot_sensitivity_g_{job_name}.o')

    base_cmd = f'sbatch --parsable -p short --dependency=afterok:{wait_jobid_dl2_to_sens} -e {jobe} -o {jobo}' \
               f' - J {job_name}_sens_plot --wrap="{cmd}"'

    job_id = os.popen(base_cmd).read().strip('\n')
    log = {job_id: base_cmd}

    return log, job_id


def batch_dl2_to_sensitivity(gamma_file, proton_file, electron_file, job_name, output_directory, output_filename,
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
    job_name: str
        Prefix (with the particle type) to be added in the name of the slurm job to be batched
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

    jobo = os.path.join(output_directory, f'job_dl2_to_sensitivity_gamma_{job_name}.o')
    jobe = os.path.join(output_directory, f'job_dl2_to_sensitivity_gamma_{job_name}.e')

    base_cmd = f'sbatch --parsable -p short --dependency=afterok:{wait_jobs_dl1dl2} -e {jobe} -o {jobo} ' \
               f' -J {job_name}_sensitivity --wrap="{source_env} {cmd}"'

    job_id = os.popen(base_cmd).read().strip('\n')

    log = {job_id: base_cmd}

    return log, job_id


def compose_sensitivity_outdir(dl2_dir, gamma_point_like, gamma_offset):
    """
    Compute the sensitivity output directory depending on the type of gamma file

    Parameters
    ----------
    dl2_dir: str
        Base path to DL2 directory
    gamma_point_like: bool
        Boolean flag to indicate if particle is `gamma` or `gamma-diffuse`
    gamma_offset: str
        String to indicate the gamma offset if gamma_point_like == True. Either 'off0.0deg' or 'off0.4deg'

    Returns
    -------
    output_sensitivity_dir: str
        Absolute path in where to store the sensitivity.fits.fz files

    """

    allowed_gamma_off = ['off0.0deg', 'off0.4deg']
    if gamma_offset not in allowed_gamma_off:
        print(f'Please select a valid gamma_offset to compute the IRFS: {" or ".join(allowed_gamma_off)}')
        exit(-1)

    if gamma_point_like:
        output_sensitivity_dir = os.path.join(dl2_dir.replace('/DL2/', '/IRF/').replace('/{}/', '/'),
                                              gamma_offset)
    else:
        output_sensitivity_dir = os.path.join(dl2_dir.replace('/DL2/', '/IRF/').replace('/{}/', '/'),
                                              'diffuse')

    os.makedirs(output_sensitivity_dir, exist_ok=True)

    return output_sensitivity_dir


def sensitivity_io(dl2_directory, log_from_dl1_dl2, gamma_point_like=True, gamma_offset='off0.0deg', prod_id=None):
    """
    Manages the i/o arguments and parameters to be passed to the batch_dl2_to_sensitivity function.

    Parameters
    ----------
    dl2_directory: str
        Base path to DL2 directory
    log_from_dl1_dl2: dict
        Dictionary with particle abs path created in previous stages #TODO to be changed by a glob.glob ?
    gamma_point_like: bool
        Boolean flag to indicate if particle is `gamma` or `gamma-diffuse`
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
    job_name: str
        Prefix (with the particle type) to be added in the name of the slurm job to be batched
    output_directory: str
        Absolute path with output directory
    output_sensitivity_filename: str
        Output filename

    """
    output_directory = compose_sensitivity_outdir(dl2_directory, gamma_point_like, gamma_offset)

    # Find paths to DL2 files
    proton_file = log_from_dl1_dl2['proton']['dl2_test_path']
    electron_file = log_from_dl1_dl2['electron']['dl2_test_path']

    if gamma_point_like and gamma_offset == 'off0.0deg':
        gamma_file = log_from_dl1_dl2['gamma_off0.0deg']['dl2_test_path']
        job_name = '00deg'
    elif gamma_point_like and gamma_offset == 'off0.4deg':
        gamma_file = log_from_dl1_dl2['gamma_off0.4deg']['dl2_test_path']
        job_name = '04deg'
    else:
        gamma_file = log_from_dl1_dl2['gamma-diffuse']['dl2_test_path']
        job_name = 'diff'

    # Create output filenames
    if prod_id is None:
        output_sensitivity_filename = os.path.join(output_directory, 'sensitivity.fits.gz')
    else:
        if gamma_point_like:
            output_sensitivity_filename = os.path.join(
                output_directory,
                f'{prod_id.replace(".", "")}_gamma_{gamma_offset.replace(".", "")}_sensitivity.fits.gz')
        else:
            output_sensitivity_filename = os.path.join(
                output_directory,
                f'{prod_id.replace(".", "")}_gamma_diffuse_sensitivity.fits.gz')

    return gamma_file, proton_file, electron_file, job_name, output_directory, output_sensitivity_filename


def dl2_to_sensitivity(dl2_dir, log_from_dl1_dl2, gamma_point_like=True, gamma_offset='off0.0deg', prod_id=None,
                       source_env='', wait_jobs_dl1_dl2=''):
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
    gamma_point_like: bool
        Boolean flag to indicate if particle is `gamma` or `gamma-diffuse`
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
        String with single job_id batched by the dl2_to_sensitivity script

    """
    log_dl2_to_sensitivity = {}
    jobids_dl2_to_sensitivity = []

    g_file, p_file, e_file, job_name, out_dir, out_file = \
        sensitivity_io(dl2_dir,
                       log_from_dl1_dl2,
                       gamma_point_like,
                       gamma_offset,
                       prod_id)

    # create sensitivity files
    log_dl2_sens, job_id_dl2_sens = \
        batch_dl2_to_sensitivity(g_file,
                                 p_file,
                                 e_file,
                                 job_name,
                                 out_dir,
                                 out_file,
                                 source_env,
                                 wait_jobs_dl1_dl2)

    log_dl2_to_sensitivity.update(log_dl2_sens)
    jobids_dl2_to_sensitivity.append(job_id_dl2_sens)

    # Create plot from sensitivity files
    log_plot_sens, job_id_plot_sens = \
        batch_plot_senstitivity(out_file, job_id_dl2_sens, job_name)

    log_dl2_to_sensitivity.update(log_plot_sens)
    jobids_dl2_to_sensitivity.append(job_id_plot_sens)
    jobids_dl2_to_sensitivity = ','.join(jobids_dl2_to_sensitivity)

    return log_dl2_to_sensitivity, jobids_dl2_to_sensitivity
