# !/usr/bin/env python3

import tables
from astropy.table import join, Table, vstack, Column
import numpy as np
import argparse

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


def stack_and_write_images_table(hfile_out, node_dl1, filter_pointer):
    """

    Parameters
    ----------
    hfile_out
    node_dl1
    filter_pointer

    Returns
    -------

    """
    telescope_node = node_dl1.event.telescope

    imag_per_tels = [Table(telescope_node.images.table_img.read()) for table_img in telescope_node.images]
    image_table = vstack(imag_per_tels)

    for tab in telescope_node.images:
        hfile_out.remove_node(tab)
    hfile_out.copy_node(image_table, newparent=telescope_node.images, newname='LST_LSTCam',
                        filters=filter_pointer)


def stack_and_write_parameters_table(hfile_out, node_dl1, filter_pointer):
    """

    Parameters
    hfile_out :
    node_dl1 : Output (V0.6) dl1 node pointer
    filter_pointer :
    """
    telescope_node = node_dl1.event.telescope

    param_per_tels = [Table(telescope_node.parameters.table_param.read()) for table_param in telescope_node.parameters]
    parameter_table = vstack(param_per_tels)

    for tab in telescope_node.parameters:
        hfile_out.remove_node(tab)
    hfile_out.copy_node(parameter_table, newparent=telescope_node.parameters, newname='LST_LSTCam',  # In lstchain there will only be LST wiht LSTCam
                        filters=filter_pointer)


def rename_mc_shower_colnames(dl1_node):
    """
    Rename column names of the `mc_shower` table (as in lstchian V0.6)

    Parameters
    dl1_node : Output (V0.6) dl1 node pointer
    """
    mc_shower_table = Table(dl1_node.event.subarray.mc_shower.read())
    mc_shower_table.rename_column('true_energy', 'mc_energy')
    mc_shower_table.rename_column('true_alt', 'mc_alt')
    mc_shower_table.rename_column('true_az', 'mc_alt')
    mc_shower_table.rename_column('true_core_x', 'mc_core_x')
    mc_shower_table.rename_column('true_core_y', 'mc_core_y')
    mc_shower_table.rename_column('true_h_first_int', 'mc_h_first_int')
    mc_shower_table.rename_column('true_x_max', 'mc_x_max')
    mc_shower_table.rename_column('true_shower_primary_id', 'mc_shower_primary_id')


def create_hfile_out(outf_name, sim_pointer, config_pointer, dl1_pointer, filter_pointer):
    """

    Parameters
    ----------
    outf_name
    sim_pointer
    config_pointer
    dl1_pointer
    filter_pointer
    """

    hfile_out = tables.open_file(outf_name, 'w')
    hfile_out.create_group('/', 'simulation')
    hfile_out.create_group('/', 'dl1')

    # Simulation node V0.6
    #    /simulation (Group) 'Simulation informations of the run'
    #       children := ['mc_event' (Table), 'run_config' (Table), 'thrown_event_distribution' (Table)]
    hfile_out.copy_node(sim_pointer.service.shower_distribution, newparent=hfile_out.root.simulation,
                        newname='thrown_event_distribution', recursive=True, filters=filter_pointer)
    hfile_out.copy_node(config_pointer.simulation.run, newparent=hfile_out.root.simulation,
                        newname='run_config', recursive=True, filters=filter_pointer)
    # # TODO check with pierre why this is here
    # hfile_out.copy_node(sim_pointer.event.subarray.shower, newparent=hfile_out.root.simulation,
    #                     newname='mc_event', recursive=True, filters=filter_pointer)

    # Instrument node V0.6
    #    --instrument (Group)
    #       +--telescope (Group)
    #       |  +--camera (Group)
    #              +--readout_LSTCam --> free, it was already here.
    #              +--geometry_LSTCAM --> To be renamed to LSTCam
    #       |  `--optics (Table)
    #       `--subarray (Group)
    #          `--layout (Table)
    instrument_node = hfile_out.copy_node(config_pointer.instrument, newparent=hfile_out.root,
                                          recursive=True, filters=filter_pointer)
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
    dl1_out_node = hfile_out.copy_node(dl1_pointer.event, newparent=hfile_out.root.dl1,
                                       recursive=True, filters=filter_pointer)
    hfile_out.remove_node(dl1_out_node.event.telescope.trigger)  # Table stored twice, remove to avoid problems.

    hfile_out.copy_node(sim_pointer.event.subarray.shower, newparent=hfile_out.root.dl1.event.subarray,
                        newname="mc_shower", recursive=True, filters=filter_pointer)

    rename_mc_shower_colnames(dl1_out_node)
    stack_and_write_parameters_table(hfile_out, dl1_out_node, filter_pointer)
    if 'images' in dl1_out_node.event.telescope:
        stack_and_write_images_table(hfile_out, dl1_out_node, filter_pointer)

    hfile_out.close()


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
    filter_v06 = hfile.filters

    create_hfile_out(output_filename, simulation_v08, configuration_v08, dl1_v08, filter_v06)

    hfile.close()


if __name__ == '__main__':
    args = parser.parse_args()
    main(args.infile, args.outfile)
