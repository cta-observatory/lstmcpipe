#!/usr/bin/env python3
#
# DL2 to DL3 onsite (La Palma cluster)
#
# usage `sbatch --wrap="python run_onsite_mc_merge_and_dl1_to_dl2.py"`
#
#
# WORKING VERSION  @ LaPALMA. Temportal version until the the dl1 convertor is updated.


import os
import tables
import pandas as pd
import numpy as np
import copy
import astropy.units as u
from lstchain.io.io import dl1_params_lstcam_key, add_column_table
from lstchain.reco import disp
from lstchain.reco.utils import sky_to_camera

PATH_TEST = \
    '/fefs/aswg/workspace/thomas.vuillaume/mchdf5/DL1_RTA/20190415/{}/south_pointing/20191211_v.0.3.1_v00/DL1/testing'
PATH_TRAIN = \
    '/fefs/aswg/workspace/thomas.vuillaume/mchdf5/DL1_RTA/20190415/{}/south_pointing/20191211_v.0.3.1_v00/DL1/training'

PARTICLE_LIST = ['electron', 'gamma', 'gamma-diffuse', 'proton']

OUTDIRFILE = '/fefs/aswg/workspace/enrique.garcia/rta_dl1_to_dl2/merge_dl1_rta/dl1_{}_20deg_180deg___cta-prod3-demo-2147m-LaPalma-baseline-mono_{}.h5'


def add_disp_to_parameters_table(dl1_file, table_path, focal):
    """
    Reconstruct the disp parameters and source position from a DL1 parameters table and write the result in the file

    Parameters
    ----------
    dl1_file: HDF5 DL1 file containing the required field in `table_path`:
        - mc_alt
        - mc_az
        - mc_alt_tel
        - mc_az_tel

    table_path: path to the parameters table in the file
    focal: focal of the telescope
    """
    with tables.open_file(dl1_file) as hfile:
        run_array_dir = copy.copy(hfile.root.simulation.run_config.col('run_array_direction')[0])

    df = pd.read_hdf(dl1_file, key=table_path)
    source_pos_in_camera = sky_to_camera(df.mc_alt.values * u.rad,
                                         df.mc_az.values * u.rad,
                                         focal,
                                         run_array_dir[1] * u.rad,
                                         run_array_dir[0] * u.rad,
                                         )

    disp_parameters = disp.disp(df.x.values * u.m,
                                df.y.values * u.m,
                                source_pos_in_camera.x,
                                source_pos_in_camera.y)

    with tables.open_file(dl1_file, mode="a") as file:
        tab = file.root[table_path]
        add_column_table(tab, tables.Float32Col, 'disp_dx', disp_parameters[0].value)
        tab = file.root[table_path]
        add_column_table(tab, tables.Float32Col, 'disp_dy', disp_parameters[1].value)
        tab = file.root[table_path]
        add_column_table(tab, tables.Float32Col, 'disp_norm', disp_parameters[2].value)
        tab = file.root[table_path]
        add_column_table(tab, tables.Float32Col, 'disp_angle', disp_parameters[3].value)
        tab = file.root[table_path]
        add_column_table(tab, tables.Float32Col, 'disp_sign', disp_parameters[4])
        tab = file.root[table_path]
        add_column_table(tab, tables.Float32Col, 'src_x', source_pos_in_camera.x.value)
        tab = file.root[table_path]
        add_column_table(tab, tables.Float32Col, 'src_y', source_pos_in_camera.y.value)
        tab = file.root[table_path]
        add_column_table(tab, tables.Float32Col, 'mc_alt_tel', np.ones(len(df)) * run_array_dir[1])
        tab = file.root[table_path]
        add_column_table(tab, tables.Float32Col, 'mc_az_tel', np.ones(len(df)) * run_array_dir[0])
        if 'gamma' in dl1_file:
            tab = file.root[table_path]
            add_column_table(tab, tables.Float32Col, 'mc_type', np.zeros(len(df)))
        if 'electron' in dl1_file:
            tab = file.root[table_path]
            add_column_table(tab, tables.Float32Col, 'mc_type', np.ones(len(df)))
        if 'proton' in dl1_file:
            tab = file.root[table_path]
            add_column_table(tab, tables.Float32Col, 'mc_type', 101 * np.ones(len(df)))


def merge_all_dl1_file_by_particles():
    """

    :return:
    """
    os.makedirs('/fefs/aswg/workspace/enrique.garcia/rta_dl1_to_dl2/merge_dl1_rta', exist_ok=True)

    list_merged_part = []

    for particle_dir in PARTICLE_LIST:
        # Test path
        test_in_dir = PATH_TEST.format(particle_dir)
        os.chdir(test_in_dir)

        # Rename all *.hdf5 to *.h5 if any
        os.system(
            'if [[ "ls *.hdf5 | wc -l " > 0 ]]; then for f in *.hdf5; do mv -- "$f" "${f%.hdf5}.h5"; done; else :; fi')

        # merge all the files
        test_out_file = OUTDIRFILE.format(particle_dir, 'test')
        test_merge = 'lstchain_merge_hdf5_files -d {} -o {} --smart False'.format(test_in_dir, test_out_file)
        os.system(test_merge)
        list_merged_part.append(test_out_file)

        # Repeat for Train path
        train_in_dir = PATH_TRAIN.format(particle_dir)
        os.chdir(train_in_dir)
        os.system(
            'if [[ "ls *.hdf5 | wc -l " > 0 ]]; then for f in *.hdf5; do mv -- "$f" "${f%.hdf5}.h5"; done; else :; fi')

        train_out_file = OUTDIRFILE.format(particle_dir, 'train')
        train_merge = 'lstchain_merge_hdf5_files -d {} -o {} --smart False'.format(train_in_dir, train_out_file)
        os.system(train_merge)
        list_merged_part.append(train_out_file)

        # Give privileges to all files
        privileges = 'chmod 777 {} {}'.format(test_out_file, train_out_file)
        os.system(privileges)

    return list_merged_part


def main():
    list_merged_particles = merge_all_dl1_file_by_particles()

    #     # VERY VERY HARDCODED...
    #     electron_test = list_merged_particles[0]
    #     electron_train = list_merged_particles[1]
    #     gamma_test = list_merged_particles[2]
    #     gamma_train = list_merged_particles[3]
    #     gamma_diff_test = list_merged_particles[4]
    #     gamma_diff_train = list_merged_particles[5]
    #     proton_test = list_merged_particles[6]
    #     proton_train = list_merged_particles[7]

    PATH_FILES = '/fefs/aswg/workspace/enrique.garcia/rta_dl1_to_dl2/merge_dl1_rta/dl1_{}_20deg_180deg___cta-prod3-demo-2147m-LaPalma-baseline-mono_{}.h5'
    electron_test = PATH_FILES.format(PARTICLE_LIST[0], 'test')
    electron_train = PATH_FILES.format(PARTICLE_LIST[0], 'train')
    gamma_test = PATH_FILES.format(PARTICLE_LIST[1], 'test')
    gamma_train = PATH_FILES.format(PARTICLE_LIST[1], 'train')
    gamma_diff_test = PATH_FILES.format(PARTICLE_LIST[2], 'test')
    gamma_diff_train = PATH_FILES.format(PARTICLE_LIST[2], 'train')
    proton_test = PATH_FILES.format(PARTICLE_LIST[3], 'test')
    proton_train = PATH_FILES.format(PARTICLE_LIST[3], 'train')

    #     # add disp_* and mc_type parameters to table
    focal = 28 * u.m
    add_disp_to_parameters_table(electron_test, dl1_params_lstcam_key, focal)
    add_disp_to_parameters_table(electron_train, dl1_params_lstcam_key, focal)
    add_disp_to_parameters_table(gamma_test, dl1_params_lstcam_key, focal)
    add_disp_to_parameters_table(gamma_train, dl1_params_lstcam_key, focal)
    add_disp_to_parameters_table(gamma_diff_test, dl1_params_lstcam_key, focal)
    add_disp_to_parameters_table(gamma_diff_train, dl1_params_lstcam_key, focal)
    add_disp_to_parameters_table(proton_test, dl1_params_lstcam_key, focal)
    add_disp_to_parameters_table(proton_train, dl1_params_lstcam_key, focal)

    print(electron_test, '\n', electron_train, '\n', gamma_test, '\n', gamma_train, '\n', gamma_diff_test, '\n',
          gamma_diff_train, '\n', proton_test, '\n', proton_train)
    print("Print just for debbuging. ")
    print("")

    # Path for correct script
    PATH_LSTCHAIN = '/home/enrique.garcia/software/cta-lstchain/lstchain/scripts/'
    CONFIG_RTA = '/fefs/aswg/workspace/enrique.garcia/rta_dl1_to_dl2/lstchain_rta_prod_config.json'

    print("\n -- lstchain_trainpipe\n")
    # lstchain_trainpipe
    dir_dl1_dl2 = '/fefs/aswg/workspace/enrique.garcia/rta_dl1_to_dl2'
    dir_trained_models = os.path.join(dir_dl1_dl2, 'trained_models')
    os.makedirs(dir_trained_models, exist_ok=True)
    lstchain_trainpipe = 'python {}lstchain_mc_trainpipe.py -fg {} -fp {} -s True -o {} -conf {}'.format(PATH_LSTCHAIN,
                                                                                                         gamma_diff_train,
                                                                                                         proton_train,
                                                                                                         dir_trained_models,
                                                                                                         CONFIG_RTA
                                                                                                         )
    os.system(lstchain_trainpipe)

    # lstchain_dl1_to_dl2 for point gamma
    dir_dl2_data = os.path.join(dir_dl1_dl2, 'dl2_data')
    os.makedirs(dir_dl2_data, exist_ok=True)
    lstchain_dl1_dl2_gamma_point_test = 'python {}lstchain_mc_dl1_to_dl2.py -f {} -p {} -o {} -conf {}'.format(
        PATH_LSTCHAIN,
        gamma_test,
        dir_trained_models,
        dir_dl2_data,
        CONFIG_RTA
    )

    # dl1_to_dl2 for proton
    lstchain_dl1_dl2_proton_test = 'python {}lstchain_mc_dl1_to_dl2.py -f {} -p {} -o {} -conf {}'.format(PATH_LSTCHAIN,
                                                                                                          proton_test,
                                                                                                          dir_trained_models,
                                                                                                          dir_dl2_data,
                                                                                                          CONFIG_RTA
                                                                                                          )

    # dl1_to_dl2 for electrons
    lstchain_dl1_dl2_electron_test = 'python {}lstchain_mc_dl1_to_dl2.py -f {} -p {} -o {} -conf {}'.format(
        PATH_LSTCHAIN,
        electron_test,
        dir_trained_models,
        dir_dl2_data,
        CONFIG_RTA
        )
    print("\n -- lstchain_dl1_to_dl2 for gamma test\n")
    print(lstchain_dl1_dl2_gamma_point_test)
    os.system(lstchain_dl1_dl2_gamma_point_test)
    print("\n -- lstchain_dl1_to_dl2 for protons test\n")
    print(lstchain_dl1_dl2_proton_test)
    os.system(lstchain_dl1_dl2_proton_test)
    print("\n -- lstchain_dl1_to_dl2 for electron test\n")
    print(lstchain_dl1_dl2_electron_test)
    os.system(lstchain_dl1_dl2_electron_test)

    os.system('chmod -R 777 /fefs/aswg/workspace/enrique.garcia/rta_dl1_to_dl2/')


if __name__ == '__main__':
    main()
