#!/usr/bin/env python3
#
# usage:
# python hiperta_r0_to_dl1lstchain.py -i INFILE [-o OUTDIR] [-c CONFIG_FILE] [-k KEEP_FILE]

import os
import argparse
from lstmcpipe.hiperta.reorganize_dl1hiperta300_to_dl1lstchain060 import (
    main as reorganize_dl1,
)


def main():
    """Run hiperta_r0_dl1 and reorganize_dl1hipertaV300_to_dl1lstchain060"""
    parser = argparse.ArgumentParser(
        description="Run hiperta_r0_dl1 and reorganize_dl1hiperta_v300_to_dl1lstchain_v060"
    )

    parser.add_argument(
        "--infile", "-i", type=str, dest="infile", help="mc r0 file to be run with hiperta_r0_dl1", required=True
    )

    parser.add_argument(
        "--outdir",
        "-o",
        type=str,
        dest="outdir",
        help="Path where to store the dl1 files.",
        default="./dl1_data/",
    )

    parser.add_argument(
        "--config",
        "-c",
        type=str,
        dest="config",
        help="Configuration file for hiperta_r1_dl1",
        default="./default_PConfigCut.txt",
        # TODO : set a way of creating the small config file that it is needed
    )

    parser.add_argument(
        "--keep_file",
        "-k",
        action='store_true',
        dest="keep_file",
        help="Keep output of hiperta. Set by default to False",
    )

    parser.add_argument(
        "--debug_mode",
        "-d",
        action='store_true',
        dest="debug_mode",
        help="Activate debug mode (add cleaned mask in the output hdf5). Set by default to False",
    )
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    # TODO. Hardcoded. Change `--selectedtel 1` when various tels available
    cmd_hiperta = f"hiperta_r0_dl1 -i {args.infile} -c {args.config} -o {args.outdir} --selectedtel 1"
    if args.debug_mode:  # in HiPeRTA
        cmd_hiperta += " -g"
    os.system(cmd_hiperta)

    # We know in advance the name of the output
    output_hiperta_filename = os.path.join(args.outdir, "dl1_" + os.path.basename(args.infile))
    output_reorganized_filename = os.path.join(args.outdir, "dl1v06_reorganized_" + os.path.basename(args.infile))
    reorganize_dl1(output_hiperta_filename, output_reorganized_filename)

    # Erase the hiperta dl1 file created ?
    if not args.keep_file:
        os.remove(output_hiperta_filename)

    print("\nDone.")


if __name__ == "__main__":
    main()
