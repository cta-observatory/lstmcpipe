# !/usr/bin/env python3

# Everything is hardcoded to LST telescopes - because this is just a temporal work that will no longer be used
# in the moment lstchain upgrades to V0.8

import os
import tables
import argparse
from astropy.table import Table, vstack, join
from astropy.io.misc.hdf5 import write_table_hdf5
from lst_scripts.reorganize_dl1hiperta_to_dl1lstchain import add_disp_and_mc_type_to_parameters_table

parser = argparse.ArgumentParser(description="Re-organize the dl1 `standard` output file from either the "
                                             "hiptecta_r1_to_dl1 or hiperta_r1_dl1 to the lstchain DL1 structure")

parser.add_argument('--infile', '-i',
                    type=str,
                    dest='infile',
                    help='dl1 output file of `hiperta_r0_dl1` to be converted to dl1lstchain_v060',
                    default=None
                    )

parser.add_argument('--outfile', '-o',
                    type=str,
                    dest='outfile',
                    help='Output filename. dl1_reorganized.h5 by default.',
                    default='./dl1v0.6_reorganized.h5'
                    )


def stack_images_table(output_filename):
    """
    Stack all the `tel_00X` image tables (in case they exit) and write in the v0.6 file

    Parameters
    output_filename : [str] output file name

    Returns
    image_table : single table with all the tel_00X image tables stacked
    """

    with tables.open_file(output_filename, 'a') as hfile_out:

        image_node = hfile_out.root.dl1.event.telescope.images
        images_table = [Table(img_table.read()) for img_table in image_node]
        images_table = vstack(images_table)

        for tab in image_node:
            hfile_out.remove_node(tab)

    # Todo ?? change names of column `image_mask` to `` ??

    return images_table


def stack_and_modify_parameters_table(output_filename, mc_shower_table):
    """
    Stack all the `tel_00X` parameters tables (of v0.8), change names of the columns and write the table in the
    V0.6 (lstchain like) format

    Parameters
    output_filename : [str] output file name
    param_tables_per_tel_path : [list] containing all the tel_00X in output.root.dl1.event.telescope.parameters
    mc_shower_table : astropy table with mc_shower cols renamed

    Returns
    parameters_table : astropy table with all tel_00x parameters table stacked and renamed
    """
    with tables.open_file(output_filename, 'a') as hfile_out:

        param_node = hfile_out.root.dl1.event.telescope.parameters
        parameters_table = [Table(param_table.read()) for param_table in param_node]
        parameters_table = vstack(parameters_table)

        for tab in param_node:
            hfile_out.remove_node(tab)

    parameters_table.rename_column('hillas_intensity', 'intensity')
    parameters_table.rename_column('hillas_x', 'x')
    parameters_table.rename_column('hillas_y', 'y')
    parameters_table.rename_column('hillas_r', 'r')
    parameters_table.rename_column('hillas_phi', 'phi')
    parameters_table.rename_column('hillas_length', 'length')
    parameters_table.rename_column('hillas_width', 'width')
    parameters_table.rename_column('hillas_psi', 'psi')
    parameters_table.rename_column('hillas_skewness', 'skewness')
    parameters_table.rename_column('hillas_kurtosis', 'kurtosis')
    parameters_table.rename_column('timing_slope', 'time_gradient')
    parameters_table.rename_column('timing_intercept', 'intercept')
    parameters_table.rename_column('morphology_num_pixels', 'n_pixels')
    parameters_table.rename_column('morphology_num_islands', 'n_islands')

    # Param table is indeed huge - it contains all the mc_events parameters (from v0.6 !!) too
    parameters_table = join(parameters_table, mc_shower_table, keys='event_id')

    return parameters_table


def rename_mc_shower_colnames(mc_shower_table):
    """
    Rename column names of the `mc_shower` table and dump the table to the v0.6 output hfile.

    Parameters
    mc_shower_table : [astropy.Table] tables with mc_shower read
    """
    mc_shower_table.rename_column('true_energy', 'mc_energy')
    mc_shower_table.rename_column('true_alt', 'mc_alt')
    mc_shower_table.rename_column('true_az', 'mc_az')
    mc_shower_table.rename_column('true_core_x', 'mc_core_x')
    mc_shower_table.rename_column('true_core_y', 'mc_core_y')
    mc_shower_table.rename_column('true_h_first_int', 'mc_h_first_int')
    mc_shower_table.rename_column('true_x_max', 'mc_x_max')
    mc_shower_table.rename_column('true_shower_primary_id', 'mc_shower_primary_id')

    return mc_shower_table


def create_hfile_out(outfile_name, sim_pointer08, config_pointer08, dl1_pointer, filter_pointer):
    """
    Create output hfile (lstchainv0.6 like hdf5 file)

    Parameters
    outfile_name : [str] output hfile name
    sim_pointer08 : dl1-file_v0.8_simulation pointer
    config_pointer08 : dl1-file_v.08_configuration pointer
    dl1_pointer :  dl1-file_v0.8_dl1 pointer
    filter_pointer : dl1-file_v0.8 filters pointer
    """
    subarray_path = 'dl1/event/subarray'
    mc_shower_table_path = os.path.join(subarray_path, 'mc_shower')

    telescope_path = 'dl1/event/telescope'
    param_table_path = os.path.join(telescope_path, 'parameters/LST_LSTCam')
    imag_table_path = os.path.join(telescope_path, 'parameters/LST_LSTCam')

    with tables.open_file(outfile_name, 'w') as hfile_out:
        hfile_out.create_group('/', 'simulation')
        hfile_out.create_group('/', 'dl1')

        # Simulation node V0.6
        #    /simulation (Group) 'Simulation information of the run'
        #       children := ['mc_event' (Table), 'run_config' (Table), 'thrown_event_distribution' (Table)]
        hfile_out.copy_node(sim_pointer08.service.shower_distribution,
                            newparent=hfile_out.root.simulation,
                            newname='thrown_event_distribution',
                            recursive=True,
                            filters=filter_pointer)
        hfile_out.copy_node(config_pointer08.simulation.run,
                            newparent=hfile_out.root.simulation,
                            newname='run_config',
                            recursive=True,
                            filters=filter_pointer)

        # Instrument node V0.6
        #    --instrument (Group)
        #       +--telescope (Group)
        #       |  +--camera (Group)
        #              +--readout_LSTCam --> copied free, it can be erase.
        #              +--geometry_LSTCAM --> To be renamed to LSTCam
        #       |  `--optics (Table)
        #       `--subarray (Group)
        #          `--layout (Table)
        instrument_node = hfile_out.copy_node(config_pointer08.instrument,
                                              newparent=hfile_out.root,
                                              recursive=True,
                                              filters=filter_pointer)
        hfile_out.rename_node(instrument_node.telescope.camera.geometry_LSTCam, newname='LSTCam')

        # dl1 node V0.6
        #    +--dl1 (Group)
        #       `--event (Group)
        #          +--telescope (Group)
        #             +--image (Group)
        #             `--parameters (Group)
        #          `--subarray (Group)
        #             +--mc_shower (Table)
        #             `--trigger (Table)
        dl1_event_node06 = hfile_out.copy_node(dl1_pointer.event,
                                               newparent=hfile_out.root.dl1,
                                               recursive=True,
                                               filters=filter_pointer)
        # This will only happen on ctapipe, not RTA
        # hfile_out.remove_node(dl1_event_node06.telescope.trigger)  # Table stored twice, remove to avoid problems.

        subarray_pointer = hfile_out.root[subarray_path]
        hfile_out.copy_node(sim_pointer08.event.subarray.shower,
                            newparent=subarray_pointer,
                            newname="mc_shower",
                            recursive=True,
                            filters=filter_pointer)

    # Rename mc_shower table
    mc_shower_table = Table.read(outfile_name, path=mc_shower_table_path)
    mc_shower_table = rename_mc_shower_colnames(mc_shower_table)
    write_table_hdf5(mc_shower_table, outfile_name, path=mc_shower_table_path, overwrite=True, append=True)

    # Stack and modify parameter table
    param_table = stack_and_modify_parameters_table(outfile_name, mc_shower_table)
    write_table_hdf5(param_table, outfile_name, path=param_table_path, overwrite=True, append=True)

    # Stack and modify images table if exist
    if 'images' in dl1_event_node06.telescope:
        imag_table = stack_images_table(outfile_name)
        write_table_hdf5(imag_table, outfile_name, path=imag_table_path, overwrite=True, append=True)


def main(input_filename, output_filename):
    """
    Conversion from dl1 data model (ctapipe and hiper(CTA)RTA) data model, and convert it to lstchain_v0.6 data mode.

    Parameters
    input_filename : [str] Input filename
    output_filename : [str] Output filename
    """
    hfile = tables.open_file(input_filename, 'r')

    # dl1 v0.8 Pointers
    simulation_v08 = hfile.root.simulation
    configuration_v08 = hfile.root.configuration
    dl1_v08 = hfile.root.dl1
    filter_v08 = hfile.filters

    create_hfile_out(output_filename, simulation_v08, configuration_v08, dl1_v08, filter_v08)

    # Add disp_* and mc_type to the parameters table.
    add_disp_and_mc_type_to_parameters_table(output_filename, 'dl1/event/telescope/parameters/LST_LSTCam')

    hfile.close()


if __name__ == '__main__':
    args = parser.parse_args()
    main(args.infile, args.outfile)
