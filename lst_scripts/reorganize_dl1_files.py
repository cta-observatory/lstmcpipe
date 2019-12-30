#!/usr/bin/env python3
#
# Usage :
# $ python reorganize_dl1_file -i input.h5 [-o outname.h5]

import os
import argparse
import tables
from lstchain.io.io import dl1_params_lstcam_key, dl1_images_lstcam_key
from astropy.table import join, Table, vstack, Column
import numpy as np
#from lstchain.io import auto_merge_h5files


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
    hfile_out.close()


def modify_params_table(table, position_iterator):
    """
    Modify column names and compute missing parameters

    Parameters
    ----------
        table: [obj, astropy.table.table.Table] The table to be modified.
        position_iterator: [int] iterator to include in the modifications

    Returns
    -------
        None
    """
    # Create the column tel_id
    # TODO : it can be done more 'classly' in the case of hiperta by reading `hfile_rta.root.dl1.Tel_1.telId.read()`
    # however, hipecta does NOT have this option.
    tel_id = Column(np.full(table.columns[0].size,
                            int(position_iterator + 1)  # TODO : A bit hardcoded. Just valid for LSTs
                            ))
    table.add_column(tel_id, name='tel_id')

    # mc_energy must be computed after merging
    # log of intensity and computation of wl
    with np.errstate(divide='ignore', invalid='ignore'):
        table.add_column(np.log10(table['intensity']), name='log_intensity')
    with np.errstate(invalid='ignore'):
        table.add_column(table['width'] / table['length'], name='wl')

    if position_iterator == 0:
        print(" Runtime Warnings have been ignored to avoid repeated stdout prints.")
        print(" RuntimeWarnings due to invalid values and divide by zero in `log10(intensity)`")
        print("    operations and divide by zero in `wl` divisions.")


def stack_by_telid(dl1_pointer):
    """
    Stack :
        - LST telescopes' parameters into a table
        - Calibrated images and pulse_times into another table

    TODO : Make a walk node in the future ? --> will need to change most of the code :-/
    Parameters
    ----------
        dl1_pointer: [obj, tables.group.Group] pointer of the input hdf5 file `hfile.root.dl1`

    Returns
    -------
        Two tables [obj, astropy.table.table.Table] containing the parameters, and the images and pulse_times int their
            respective path
    """
    t1 = Table(dl1_pointer.Tel_1.parameters.read())
    t2 = Table(dl1_pointer.Tel_2.parameters.read())
    t3 = Table(dl1_pointer.Tel_3.parameters.read())
    t4 = Table(dl1_pointer.Tel_4.parameters.read())
    tabs = [t1, t2, t3, t4]

    for i, tab in enumerate(tabs):
        modify_params_table(tab, i)

        if i == 0:
            stacked_param = tab
        else:
            stacked_param = vstack((stacked_param, tab))

    # Image
    imag1 = Table(dl1_pointer.Tel_1.calib_pic.read())
    imag2 = Table(dl1_pointer.Tel_2.calib_pic.read())
    imag3 = Table(dl1_pointer.Tel_3.calib_pic.read())
    imag4 = Table(dl1_pointer.Tel_4.calib_pic.read())
    imags = [imag1, imag2, imag3, imag4]

    for i, imag in enumerate(imags):
        try:
            imag.rename_column('eventId', 'event_id')
        except KeyError:
            #print("RTA case")
            pass

        if i == 0:
            stack_imag = imag
        else:
            stack_imag = vstack((stack_imag, imag))

    return stacked_param, stack_imag


def reorganize_dl1(input_filename, output_filename):
    """

    Parameters
    ----------
        input_filename: [str] Input filename
        output_filename: [str] Output filename
    Returns
    -------
        None. It dumps the final hdf5 file with the correct structure.

    """
    hfile = tables.open_file(input_filename, 'r')

    # Pointers
    dl1 = hfile.root.dl1
    mc_event = Table(hfile.root.simulation.mc_event.read())

    # Temporal names for temporal files, later erased
    _param = str(os.path.abspath(output_filename).rsplit('/', 1)[0]) + '/dl1_prams_tmp_' + str(os.path.basename(input_filename))
    _images = str(os.path.abspath(output_filename).rsplit('/', 1)[0]) + '/dl1_imags_tmp_' + str(os.path.basename(input_filename))

    table_dl1, table_imags = stack_by_telid(dl1)

    # Join together with the mc_events, compute log of mc_energy and dump it
    table_dl1 = join(table_dl1, mc_event, keys='event_id')
    table_dl1.add_column(np.log10(table_dl1['mc_energy']), name='log_mc_energy')

    table_dl1.write(_param, format='hdf5', path=dl1_params_lstcam_key, overwrite=True)
    table_imags.write(_images, format='hdf5', path=dl1_images_lstcam_key, overwrite=True)

    _hfile_param = tables.open_file(_param, 'r')
    _hfile_imgas = tables.open_file(_images, 'r')

    create_final_h5(hfile, _hfile_param, _hfile_imgas, output_filename)

    # Close and erase
    _hfile_param.close()
    _hfile_imgas.close()
    os.remove(_param)
    os.remove(_images)

    hfile.close()


def main():
    parser = argparse.ArgumentParser(description="Re-organize the dl1 `standar` output file from either the "
                                                 "hiptecta_r1_to_dl1 or hiperta_r1_dl1 to the agreed DL1 structure")

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
    args = parser.parse_args()

    reorganize_dl1(args.infile, args.outfile)


if __name__ == '__main__':
    main()
