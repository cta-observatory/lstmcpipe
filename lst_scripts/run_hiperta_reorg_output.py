#!/usr/bin/env python3
#
# usage

import os
import argparse
from distutils.util import strtobool
from hipecta.programs.reorganize_dl1_files import reorganize_dl1


def main():
    parser = argparse.ArgumentParser(description="Run hiperta_r0_dl1 and reorganize_dl1_files")

    parser.add_argument('--infile', '-i',
                        type=str,
                        dest='infile',
                        help='mc r0 file to be run with hiperta_r0_dl1',
                        default=None
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

    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    output_hiperta_filename = os.path.join(args.outdir + "dl1_" + os.path.basename(args.infile))
    cmd_hiperta = f'hiperta_r1_dl1 -i {args.infile} -c {args.config} -o {args.outdir} -k {args.keep_file}'
    os.system(cmd_hiperta)

    output_reorganized_filename = os.path.join(args.outdir + "dl1_reorganized_" + os.path.basename(args.infile))
    reorganize_dl1(output_hiperta_filename, output_reorganized_filename)

    # Erase the hiperta dl1 file created ?
    if not args.keep_files:
        os.remove(output_hiperta_filename)

    print("\nDone.")


if __name__ == '__main__':
    main()
