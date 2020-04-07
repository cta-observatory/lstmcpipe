#!/usr/bin/env python3
#
# Reorganize the DL1 output files of the HiPeRTA and HiPeCTA r0_to_dl1 codes to reach the lstchain
# file structure for DL1 files
#
# Usage :
# $ python reorganize_dl1_file -i input.h5 [-o outname.h5]

import os
import argparse
import tables
from lstchain.io.io import dl1_params_lstcam_key, dl1_images_lstcam_key, add_column_table
from astropy.table import join, Table, vstack, Column
import astropy.units as u
import numpy as np
import pandas as pd
import copy
from lstchain.reco import disp
from lstchain.reco.utils import sky_to_camera

parser = argparse.ArgumentParser(description="Re-organize the dl1 `standard` output file from either the "
                                             "hiptecta_r1_to_dl1 or hiperta_r1_dl1 to the lstchain DL1 structure")

parser.add_argument('--infile', '-i',
                    type=str,
                    dest='infile',
                    help='dl1 output file of the `hipecta_hdf5_r1_to_dl1.py` or `hiperta_r1_dl1` script '
                         'to be re-organized',
                    default=None
                    )

parser.add_argument('--outfile', '-o',
                    type=str,
                    dest='outfile',
                    help='Output filename. dl1_reorganized.h5 by default.',
                    default='./dl1_reorganized.h5'
                    )


def create_final_h5(hfile, hfile_tmp, hfile_tmp2, output_filename):
    """
    Create the final output HDF5 file.
    It copies /instruments and /simulations nodes from the output of hipecta_hdf5_r1_to_dl1.py,
        - and /dl1/event from the created table.
        - and includes the image and pulse_time within the correct path, i.e., /dl1/event/telescope/

    TODO: Define somehow the paths globally so that it can be used .get_node()

    Parameters
    ----------
        hfile: [obj, astropy.table.table.Table] output file
        hfile_tmp: [obj, astropy.table.table.Table] hdf5 file with dl1 parameters. path:
                    `dl1/event/telescope/parameters/LST_LSTCam`
        hfile_tmp2: [obj, astropy.table.table.Table] hdf5 file with images and pulse_time. path:
                    `dl1/event/telescope/image/LST_LSTCam`
        output_filename: [str] name of output file

    Returns
    -------
        None

    """
    # The complevel MUST be set to zero, otherwise this version of libhdf5 does NOT accept the copy_node()
    filter = tables.Filters(complevel=0, complib='blosc:zstd', shuffle=False, bitshuffle=False, fletcher32=False)

    hfile_out = tables.open_file(output_filename, 'w')
    hfile_out.copy_node(hfile.root.instrument, newparent=hfile_out.root, recursive=True, filters=filter)
    hfile_out.copy_node(hfile.root.simulation, newparent=hfile_out.root, recursive=True, filters=filter)
    hfile_out.copy_node(hfile_tmp.root.dl1, newparent=hfile_out.root, recursive=True)
    hfile_out.copy_children(hfile_tmp2.root.dl1.event.telescope, hfile_out.root.dl1.event.telescope, recursive=True)

    # Move the telescope table from /instrument/subarray to /instrument (lstchain output file dl1 format)
    hfile_out.move_node('/instrument/subarray/telescope', newparent='/instrument', createparents=True)
    hfile_out.close()


def add_disp_and_mc_type_to_parameters_table(dl1_file, table_path):
    """
    HARDCODED function obtained from `lstchain.reco.dl0_to_dl1` because `mc_alt_tel` and `mc_az_tel` are zipped within
    `run_array_direction`.
    1. Reconstruct the disp parameters and source position from a DL1 parameters table and write the result in the file.
    2. Computes mc_type from the name of the file.


    Parameters
    ----------
    dl1_file: HDF5 DL1 file containing the required field in `table_path`:
        - mc_alt
        - mc_az
        - mc_alt_tel
        - mc_az_tel

    table_path: path to the parameters table in the file

    Returns
    -------
        None
    """
    with tables.open_file(dl1_file) as hfile:
        run_array_dir = copy.copy(hfile.root.simulation.run_config.col('run_array_direction')[0])
        # Remember that /telescope has been moved previously
        focal = copy.copy(hfile.root.instrument.telescope.optics.col('equivalent_focal_length')[0])

    df = pd.read_hdf(dl1_file, key=table_path)
    source_pos_in_camera = sky_to_camera(df.mc_alt.values * u.rad,
                                         df.mc_az.values * u.rad,
                                         focal * u.m,
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
            add_column_table(tab, tables.Float32Col, 'mc_type', 101*np.ones(len(df)))


def modify_params_table(table, tel_id, focal=28):
    """
    Modify column names and compute missing parameters

    Parameters
    ----------
        table: [obj, astropy.table.table.Table] The table to be modified.
        position_iterator: [int] iterator to include in the modifications
        focal: [float] focal length in meters

    Returns
    -------
        None
    """
    # Create the column tel_id

    table.add_column(Column(tel_id * np.ones(len(table)), dtype=int), name='tel_id')

    # Rename `leakage_intensity2` --> `leakage`
    table.rename_column('leakage_intensity2', 'leakage')

    # X and Y in meters
    table['x'] *= focal
    tables['y'] *= focal

    # mc_energy must be computed after merging
    # log of intensity and computation of wl
    table.add_column(np.log10(table['intensity']), name='log_intensity')
    table.add_column(table['width'] / table['length'], name='wl')


def stack_by_telid(dl1_pointer, focal=28):
    """
    Stack :
        - LST telescopes' parameters into a table
        - Calibrated images and pulse_times into another table

    Parameters
    ----------
        dl1_pointer: [obj, tables.group.Group] pointer of the input hdf5 file `hfile.root.dl1`
        focal: [int] focal of the telescope.

    Returns
    -------
        Two tables [obj, astropy.table.table.Table] containing the parameters, and the images and pulse_times int their
            respective path
    """

    tels_params = [Table(tel.parameters.read()) for tel in dl1_pointer]
    try:
        tel_ids = [tel['telId'][0] for tel in dl1_pointer]
    except:
        # if the tel_id column does not exist, we assign tel ids by simple iteration
        tel_ids = [i+1 for i in range(len(tels_params))]

    for tab, tel_id in zip(tels_params, tel_ids):
        modify_params_table(tab, tel_id, focal=focal)

    # tabs = [Table(tel) for tel in tels_params]

    stacked_param = vstack(tels_params)

    images = [Table(tel.calib_pic.read()) for tel in dl1_pointer]

    # adding stupid tel_id to the image table as well
    for image_tab, tel_id in zip(images, tel_ids):
        image_tab.add_column(Column(tel_id * np.ones(len(image_tab)), dtype=int), name='tel_id')

    stacked_images = vstack(images)
    if 'event_id' not in stacked_images.columns:
        stacked_images.add_column(stacked_param['event_id'])

    try:
        #  HiPeCTA case
        stacked_images.rename_column('eventId', 'event_id')
    except KeyError:
        #  HiPeRTA case
        pass

    return stacked_param, stacked_images


def reorganize_dl1(input_filename, output_filename):
    """
    Reorganize the output dl1 files of hiperta/hipecta codes to reach the same structure found in lstchain dl1 files.

    Parameters
    ----------
        input_filename: str
            Input filename
        output_filename: str
            Output filename
    Returns
    -------
        None. It dumps the final hdf5 file with the correct structure.

    """
    hfile = tables.open_file(input_filename, 'r')

    # Pointers
    dl1 = hfile.root.dl1
    mc_event = Table(hfile.root.simulation.mc_event.read())

    # Temporal names for temporal files, later erased
    _param = str(os.path.abspath(output_filename).rsplit('/', 1)[0]) + '/dl1_prams_tmp_' + str(
        os.path.basename(input_filename))
    _images = str(os.path.abspath(output_filename).rsplit('/', 1)[0]) + '/dl1_imags_tmp_' + str(
        os.path.basename(input_filename))

    focal = hfile.root.instrument.telescope.optics.col('equivalent_focal_length')[0]
    table_dl1, table_imags = stack_by_telid(dl1, focal=focal)

    # Join together with the mc_events, compute log of mc_energy and dump it
    table_dl1 = join(table_dl1, mc_event, keys='event_id')
    table_dl1.add_column(np.log10(table_dl1['mc_energy']), name='log_mc_energy')

    # write tmp files
    table_dl1.write(_param, format='hdf5', path=dl1_params_lstcam_key, overwrite=True)
    table_imags.write(_images, format='hdf5', path=dl1_images_lstcam_key, overwrite=True)

    # open tmp files
    _hfile_param = tables.open_file(_param, 'r')
    _hfile_imags = tables.open_file(_images, 'r')

    create_final_h5(hfile, _hfile_param, _hfile_imags, output_filename)

    # Add disp_* and mc_type to the parameters table
    add_disp_and_mc_type_to_parameters_table(output_filename, dl1_params_lstcam_key)

    # Close and erase
    _hfile_param.close()
    _hfile_imags.close()
    os.remove(_param)
    os.remove(_images)

    hfile.close()


if __name__ == '__main__':
    args = parser.parse_args()
    reorganize_dl1(args.infile,
                   args.outfile)
