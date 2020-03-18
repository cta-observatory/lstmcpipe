#!/usr/bin/env python3
#
# usage:  # If repository installed, i.e., entry point working correctly
# hiperta_r0_to_dl1lstchain -i INFILE [-o OUTDIR] [-c CONFIG_FILE] [-k KEEP_FILE]
# python hiperta_r0_to_dl1lstchain.py -i INFILE [-o OUTDIR] [-c CONFIG_FILE] [-k KEEP_FILE]

import os
import argparse
from distutils.util import strtobool
from hipecta.programs.reorganize_dl1_files import reorganize_dl1


parser = argparse.ArgumentParser(description="Run hiperta_r0_dl1 and reorganize_dl1_files")

parser.add_argument('--infile', '-i',
                    type=str,
                    dest='infile',
                    help='mc r0 file to be run with hiperta_r0_dl1',
                    )

parser.add_argument('--outdir', '-o',
                    type=str,
                    dest='outdir',
                    help='Path where to store the dl1 files.',
                    default='./dl1_data/'
                    )

parser.add_argument('--config', '-c',
                    type=str,
                    dest='config',
                    help='Configuration file for hiperta_r1_dl1',
                    default='./default_PConfigCut.txt'
                    )

parser.add_argument('--keep_file', '-k',
                    type=lambda x: bool(strtobool(x)),
                    help='Keep output of hiperta. Set by default to False',
                    default=False
                    )


def main(infile, outdir='./dl1_data/', config='./default_PConfigCut.txt', keep_file=False, flag_full_workflow=False):
    """
    Run hiperta_r0_dl1 and reorganize_dl1_files either independently (for a single INFILE), either as part of a
    pipeline/workflow (flag_full_workflow will need to be set as True)

    Parameters
    ----------
    infile: str
        Path to the file to analyse
    outdir: str
        Path to the OUTPUT DIRECTORY to store the outfile. Default = './dl1_data/'
    config: str
        path to a configuration file. If none, the default './default_PConfigCut.txt' config is applied.
        # TODO : set a way of launching / finding the default config
    keep_file: bool
        Boolean flag to indicate if the output of the hiperta_r1_to_dl1 code should be kept or not. The
        dl1_reorganized_*.h5 will be always created.
    flag_full_workflow: bool
        Boolean flag to indicate if this script is run as part of a workflow/pipeline.

    Returns
    -------
    none
        * If flag_full_workflow is False: It will create a dl1_reorganized_INFILE_NAME.h5 file. A dl1 file created with
            the hiperta_r0_dl1 code.
        * If flag_full_workflow is True: It will sbatch bothh the hiperta_r0_dl1 and the reorganize_dl1 jobs.

    """
    if not flag_full_workflow:  # Run the code independently, for a single input INFILE

        os.makedirs(outdir, exist_ok=True)

        output_hiperta_filename = os.path.join(outdir, "dl1_" + os.path.basename(infile))
        cmd_hiperta = f'hiperta_r1_dl1 -i {infile} -c {config} -o {outdir} -k {keep_file}'
        os.system(cmd_hiperta)

        output_reorganized_filename = os.path.join(outdir, "dl1_reorganized_" + os.path.basename(infile))
        reorganize_dl1(output_hiperta_filename, output_reorganized_filename)

        # Erase the hiperta dl1 file created ?
        if not keep_file:
            os.remove(output_hiperta_filename)

        print("\nDone.")

    else:  # Run the code as part of a workflow/pipeline
        pass  # TODO


if __name__ == '__main__':
    args = parser.parse_args()
    main(args.infile,
         args.outdir,
         args.config,
         args.keep_file
         )
