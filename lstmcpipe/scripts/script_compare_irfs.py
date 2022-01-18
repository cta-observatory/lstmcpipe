import os
import logging
import argparse

import ctaplot
import matplotlib.pyplot as plt
from lstmcpipe.plots.plot_irfs import plot_summary_from_file

def plot_comparison(filelist, outfile, cta_north=False):
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


    plt.savefig(outfile, dpi=300, bbox_inches='tight')


def main():
    parser = argparse.ArgumentParser(description="Produce IRFs comparative plots")

    # Required arguments
    parser.add_argument('--filelist', '-f',
                        type=str,
                        nargs='*',
                        dest='filelist',
                        help='List of IRF files',
                        )

    parser.add_argument('--outfile', '-o', action='store', type=str,
                        dest='outfile',
                        help='Path of the outfile',
                        default='compare_irfs.png',
                        )

    # optional
    parser.add_argument('--add-cta-north',
                        action='store_true',
                        dest='cta_north',
                        help='add CTA north performances curves'
                        )

    args = parser.parse_args()
    plot_comparison(args.filelist, args.outfile,  args.cta_north)

if __name__ == '__main__':
    main()

