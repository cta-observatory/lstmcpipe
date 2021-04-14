#!/usr/bin/env python

# E. Garcia, Avr '21
#
# DL2 to IRFs stage for the R0 to IRFs full MC production workflow.
#
#
# As all the previous stages, this script make use of the lstchain entry points to batch each workflow stage.
# Also, it can be run interactively or within the full workflow, launched by the onsite_mc_r0_to_dl3.py script.
#
# usage:
#  python onsite_mc_dl2_to_irfs [--point-like] -g DL2_gamma_path -p DL2_proton_path -e DL2_electron_path
#   -c lstchain_config -o output_directory
#

import os
import glob
import shutil
import argparse
from distutils.util import strtobool
from data_management import (check_and_make_dir,
                             check_and_make_dir_without_verification
                             )

parser = argparse.ArgumentParser(description="Convert onsite files from dl1 to dl2")

parser.add_argument('input_dir', type=str,
                    help='path to the DL2 directory to analyse',
                    )

parser.add_argument('--config_file', '-c', action='store', type=str,
                    dest='config_file',
                    help='Path to a configuration file. If none is given, a standard configuration is applied',
                    default=None
                    )

parser.add_argument('--point_like', '-p', action='store',
                    type=lambda x: bool(strtobool(x)),
                    dest='point_like',
                    help='Point like IRFs will be produced, otherwise Full Enclosure.\n'
                         'If True; a gamma point-like file will be selected, otherwise (False) gamma-diffuse files '
                         'will be chosen.\n'
                         'Default=True',
                    default=True,
                    )

parser.add_argument('--gamma_offset', '-offset', action='store', type=str,
                    dest='gamma_offset',
                    help='If point-like IRF argument selected, gamma offset can be configure:\n'
                         ' - "0.0deg" for ON/OFF observation, \n'
                         ' - "0.4deg" for wobble observations. \n'
                         'Default="0.0deg"',
                    default='0.0deg',
                    )


def check_dl2_files(dl2_dir, pointlike, gamma_off):
    """
    Search DL2 testing files for each of the desired particles depending on the IRF configuration (point-like
    and gamma-offset).

    Parameters
    ----------
    dl2_dir: str
        General path to DL2 directory, not formatted with the particle.
    pointlike: bool
        IRF configuration parameter to indicate point-like or diffuse gammas.
    gamma_off:
        IRF configuration parameter with the gamma-offset.

    Returns
    -------
    dl2_particle_paths: dict
        Dictionary containing the path to the DL2 testing files depending on the desired IRF configuration

    """
    # Make particle loop depending on gamma point like
    particles_irfs = ['electron', 'proton']
    if pointlike:
        particles_irfs.append('gamma')
    else:
        particles_irfs.append('gamma-diffuse')

    dl2_particle_paths = {}
    for particle in particles_irfs:
        dl2_particle_paths[particle] = {}

        if particle == 'gamma':
            particle_dir_dl2 = os.path.join(dl2_dir.format(particle), f'off{gamma_off}')
        else:
            particle_dir_dl2 = dl2_dir.format(particle)

        if os.path.isdir(particle_dir_dl2):
            dl2_particle_paths[particle] = \
                glob.glob(os.path.join(particle_dir_dl2,
                                       '*testing.h5')
                          )[0]
        else:
            print(f'DL2 {particle} directory cannot be found or does not exists:\n {particle_dir_dl2}')
            exit(-1)

    return dl2_particle_paths


def main(dl2_directory, config_file, irf_point_like=True, irf_gamma_offset='0.0deg', source_env=None,
         flag_full_workflow=False, log_from_dl1_dl2={}, wait_jobs_dl1dl2=None, prod_id=None):
    """
    Batches/runs interactively the lstchain `lstchain_create_irf_files` entry point.
    Last stage of the MC prod workflow.

    Parameters
    ----------
    dl2_directory: str
        General path to DL2 directory, not formatted with the particle.
    config_file: str
        Path to a configuration file. If none is given, a standard configuration is applied
    irf_point_like: bool
        MC prod configuration argument to create IRFs: {True: gamma, False: gamma-diffuse}.
    irf_gamma_offset: str
        MC prod configuration argument to create IRFs: 0.0deg (for ON/OFF obs) or 0.4deg (for wobble obs).
    source_env: str
        path to a .bashrc file to source (can be configurable for custom runs @ mc_r0_to_dl3 script) to activate
        a certain conda environment.
    flag_full_workflow: bool
        Boolean flag to indicate if this script is run as part of the workflow that converts r0 to dl2 files.
    log_from_dl1_dl2: dict
        Dictionary with dl2 output path. Files are not yet here, but path and full name are needed to batch the job.
    wait_jobs_dl1dl2: str
        Comma separated string with the job ids of previous stages (dl1_to_dl2 stage) to be passed as dependencies to
        the create_irfs_files job to be batched.
    prod_id: str
        prod_id defined within config_MC_prod.yml file

    Returns
    -------
    log_dl2_to_irfs: dict
        Dictionary-wise log containing {'job_id': 'batched_cmd'}
    list_job_id_dl2_irfs: list
        Job-ids of the batched job to be passed to the last (MC prod check) stage of the workflow.
    """
    allowed_gamma_off = ['0.0deg', '0.4deg']
    if irf_gamma_offset not in allowed_gamma_off:
        print(f'Please select a valid gamma_offset to compute the IRFS: {" or ".join(allowed_gamma_off)}')
        exit(-1)

    output_irfs_dir = dl2_directory.replace('/DL2/', '/IRF/').replace('/{}/', '/')
    if prod_id is None:
        output_filename_irf = os.path.join(output_irfs_dir, 'irf.fits.gz')
    else:
        output_filename_irf = os.path.join(output_irfs_dir, prod_id.replace('.', '') + '.fits.gz')

    log_dl2_to_irfs = {}
    list_job_id_dl2_irfs = []

    if not flag_full_workflow or log_from_dl1_dl2 == {}:
        dl2_particle_paths = check_dl2_files(
            dl2_directory,
            irf_point_like,
            irf_gamma_offset)

        # Comprehension list to find gamma or gamma-diffuse
        gamma_kind = [g for g in dl2_particle_paths.keys() if g.startswith('gamma')][0]

        gamma_file = dl2_particle_paths[gamma_kind]
        proton_file = dl2_particle_paths['proton']
        electron_file = dl2_particle_paths['electron']

    else:
        proton_file = log_from_dl1_dl2['proton']['dl2_test_path']
        electron_file = log_from_dl1_dl2['electron']['dl2_test_path']

        if irf_point_like and irf_gamma_offset == '0.0deg':
            gamma_file = log_from_dl1_dl2['gamma_off0.0deg']['dl2_test_path']
        elif irf_point_like and irf_gamma_offset == '0.4deg':
            gamma_file = log_from_dl1_dl2['gamma_off0.4deg']['dl2_test_path']
        else:
            gamma_file = log_from_dl1_dl2['gamma-diffuse']['dl2_test_path']

    if irf_point_like:
        point_like = '--point-like'
    else:
        point_like = ''

    cmd = f'lstchain_create_irf_files {point_like} -g {gamma_file} -p {proton_file} -e {electron_file}' \
          f' -o {output_filename_irf}'
    if config_file is not None:
        cmd += f' --config={config_file}'

    if not flag_full_workflow:
        print(f"\n ==== START {os.path.basename(__file__)} ==== \n")

        check_and_make_dir(output_irfs_dir)
        # print (cmd)
        os.system(cmd)

        print(f"\n ==== END {os.path.basename(__file__)} ==== \n")

    else:  # flag_full_workflow == True !
        print(f'\tOutput dir IRFs: {output_irfs_dir}')

        check_and_make_dir_without_verification(output_irfs_dir)

        jobe = os.path.join(output_irfs_dir, f"job_dl2_to_irfs.e")
        jobo = os.path.join(output_irfs_dir, f"job_dl2_to_irfs.o")

        batch_cmd = f'sbatch --parsable -p short --dependency=afterok:{wait_jobs_dl1dl2} -J MC_IRFs' \
                    f' -e {jobe} -o {jobo} --wrap="{source_env} {cmd}"'

        job_id_dl2_irfs = os.popen(batch_cmd).read().strip('\n')

        log_dl2_to_irfs[job_id_dl2_irfs] = batch_cmd
        list_job_id_dl2_irfs.append(job_id_dl2_irfs)

    # Copy Script and config into working dir
    shutil.copyfile(__file__, os.path.join(output_irfs_dir, os.path.basename(__file__)))
    if config_file is not None or config_file is not '':
        shutil.copyfile(config_file, os.path.join(output_irfs_dir, os.path.basename(config_file)))

    if flag_full_workflow:
        return log_dl2_to_irfs, list_job_id_dl2_irfs


if __name__ == '__main__':
    args = parser.parse_args()
    main(args.input_dir,
         args.config_file,
         args.point_like,
         args.gamma_offset
         )
