#!/usr/bin/env python3
#
# DL2 to DL3 onsite (La Palma cluster)
#
# usage

import os

PATH_TEST = \
    '/fefs/aswg/workspace/thomas.vuillaume/mchdf5/DL1_RTA/20190415/{}/south_pointing/20191211_v.0.3.1_v00/DL1/testing'
PATH_TRAIN = \
    '/fefs/aswg/workspace/thomas.vuillaume/mchdf5/DL1_RTA/20190415/{}/south_pointing/20191211_v.0.3.1_v00/DL1/training'

PARTICLE_LIST = ['electron', 'gamma', 'gamma-diffuse', 'proton']

OUTDIRFILE = '/fefs/aswg/workspace/enrique.garcia/rta_dl1_to_dl2/merge_dl1_rta/dl1_{}_20deg_180deg___cta-prod3-demo-2147m-LaPalma-baseline-mono_{}.h5'


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

    # VERY VERY HARDCODED...
    electron_test = list_merged_particles[0]
    electron_train = list_merged_particles[1]
    gamma_test = list_merged_particles[2]
    gamma_train = list_merged_particles[3]
    gamma_diff_test = list_merged_particles[4]
    gamma_diff_train = list_merged_particles[5]
    proton_test = list_merged_particles[6]
    proton_train = list_merged_particles[7]

    # lstchain_trainpipe
    dir_dl1_dl2 = '/fefs/aswg/workspace/enrique.garcia/rta_dl1_to_dl2'
    dir_trained_models = os.path.join(dir_dl1_dl2, 'trained_models/')
    os.makedirs(dir_trained_models, exist_ok=True)
    lstchain_trainpipe = 'lstchain_mc_trainpipe.py -fg {} -fp {} -s True -o {}'.format(gamma_diff_train,
                                                                                       proton_train,
                                                                                       dir_trained_models
                                                                                       )
    os.system(lstchain_trainpipe)

    # lstchain_dl1_to_dl2 for point gamma
    dir_dl2_data = os.path.join(dir_dl1_dl2, '/dl2_data')
    os.makedirs(dir_dl2_data, exist_ok=True)
    lstchain_dl1_dl2_gamma_point_test = 'lstchain_mc_dl1_to_dl2.py -f {} -p {} -o {}'.format(gamma_test,
                                                                                             dir_trained_models,
                                                                                             dir_dl2_data
                                                                                             )
    # dl1_to_dl2 for proton
    lstchain_dl1_dl2_proton_test = 'lstchain_mc_dl1_to_dl2.py -f {} -p {} -o {}'.format(proton_test,
                                                                                        dir_trained_models,
                                                                                        dir_dl2_data
                                                                                        )
    # dl1_to_dl2 for proton
    lstchain_dl1_dl2_electron_test = 'lstchain_mc_dl1_to_dl2.py -f {} -p {} -o {}'.format(electron_test,
                                                                                          dir_trained_models,
                                                                                          dir_dl2_data
                                                                                          )

    os.system(lstchain_dl1_dl2_gamma_point_test)
    os.system(lstchain_dl1_dl2_proton_test)
    os.system(lstchain_dl1_dl2_electron_test)

    os.system('chmod -R 777 /fefs/aswg/workspace/enrique.garcia/rta_dl1_to_dl2/')


if __name__ == '__main__':
    main()
