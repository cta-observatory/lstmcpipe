# !/usr/bin/env python3

import tables
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
                    default='./dl1_reorganized.h5'
                    )


def create_hfile_out(outf_name, sim_pointer, config_pointer, dl1_pointer, filter_pointer):

    hfile_out = tables.open_file(outf_name, 'w')
    hfile_out.create_group('/', 'simulation')
    hfile_out.create_group('/', 'dl1')

    # Simulation node V0.6
    # /simulation (Group) 'Simulation informations of the run'
    #   children := ['mc_event' (Table), 'run_config' (Table), 'thrown_event_distribution' (Table)]
    hfile_out.copy_node(sim_pointer.service.shower_distribution, newparent=hfile_out.root.simulation,
                        newname='thrown_event_distribution', recursive=True, filters=filter_pointer)
    hfile_out.copy_node(config_pointer.simulation.run, newparent=hfile_out.root.simulation,
                        newname='run_config', recursive=True, filters=filter_pointer)
    hfile_out.copy_node(sim_pointer.event.subarray.shower, newparent=hfile_out.root.simulation,
                        newname='mc_event', recursive=True, filters=filter_pointer)

    # Instrument node V0.6
    # --instrument (Group)
    #    +--telescope (Group)
    #    |  +--camera (Group)
    #           +--readout_LSTCam --> free, it was already here.
    #           +--geometry_LSTCAM --> To be renamed
    #    |  `--optics (Table)
    #    `--subarray (Group)
    #       `--layout (Table)
    instrument_node = hfile_out.copy_node(config_pointer.instrument, newparent=hfile_out.root,
                                          recursive=True, filters=filter_pointer)

    hfile_out.rename_node(instrument_node.telescope.camera.geometry_LSTCam, newname='LSTCam')

    # dl1 node V0.6
    # +--dl1 (Group)
    #    `--event (Group)
    #       `--telescope (Group)
    #          +--image (Group)
    #          `--parameters (Group)
    hfile_out.copy_node(dl1_pointer.event, newparent=hfile_out.root.dl1,
                        recursive=True, filters=filter_pointer)

    # TODO missing event/subarray/telescope/trigger (v0.8) --> event/subarray/trigger
    # TODO rename for sure
    # TODO stack tel_00X to LST_LSTCam

    hfile_out.close()


def main(input_filename, output_filename):
    """

    Parameters
    input_filename :
    output_filename :

    Returns

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
