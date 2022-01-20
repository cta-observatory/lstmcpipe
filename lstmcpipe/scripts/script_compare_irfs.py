# #!/usr/bin/env python
import os
import logging
import argparse
import ctaplot
import matplotlib.pyplot as plt
from lstmcpipe.plots.plot_irfs import plot_summary_from_file
from distutils.util import strtobool


def plot_comparison(filelist, outfile, cta_north=False, save_figure=True):
    """
    Create a 2x2 plot comparing different sensitivity curves

    Parameters
    ----------
    filelist: list
        File list with sensitivity curves to be compared.
    outfile: str or Path
        for the output file to be savec
    cta_north: Bool
        Flag to superpose/add (True) or not (False - Default) the CTA North.
        Imported from ctaplot
    save_figure: Bool
        Flag to indicate if to save the final plot or not
    """
    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger("lstchain MC DL2 to IRF - sensitivity curves")

    log.info("Starting lstmcpipe compare irfs script")

    fig, axes = plt.subplots(2, 2, figsize=(15, 10))

    for file in filelist:
        log.info(f"Plotting IRFs from file {file}")
        label = os.path.basename(file)
        plot_summary_from_file(file, axes=axes, label=label)

    if cta_north:
        ctaplot.plot_sensitivity_cta_performance('north', ax=axes.ravel()[0])
        ctaplot.plot_angular_resolution_cta_performance('north', ax=axes.ravel()[1])
        ctaplot.plot_energy_resolution_cta_performance('north', ax=axes.ravel()[2])
        ctaplot.plot_effective_area_cta_performance('north', ax=axes.ravel()[3])

    if save_figure:
        plt.savefig(outfile, dpi=300, bbox_inches='tight')


def main():
    parser = argparse.ArgumentParser(description="Produce IRFs comparative plots")

    # Required arguments
    parser.add_argument('--filelist', '-f',
                        type=str,
                        nargs='*',
                        dest='filelist',
                        help='List of IRF files',
                        required=True
                        )

    # optional
    parser.add_argument('--outfile', '-o', action='store', type=str,
                        dest='outfile',
                        help='Path of the outfile',
                        default='compare_irfs.png',
                        )

    parser.add_argument('--add-cta-north',
                        action='store_true',
                        dest='cta_north',
                        help='add CTA north performances curves'
                        )

    parser.add_argument('--save-figure', '-s',
                        action='store',
                        type=lambda x: bool(strtobool(x)),
                        dest='save_figure',
                        help='Save resulting figure',
                        default=True
                        )

    args = parser.parse_args()
    plot_comparison(args.filelist, args.outfile,  args.cta_north, args.save_figure)


if __name__ == '__main__':
    main()
