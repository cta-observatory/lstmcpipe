# #!/usr/bin/env python
import logging
import argparse
from pathlib import Path

import ctaplot
import matplotlib.pyplot as plt
from lstmcpipe.plots.plot_irfs import plot_summary_from_file


def plot_comparison(filelist, outfile=None, cta_north=False):
    """
    Create a 2x2 plot comparing different sensitivity curves

    Parameters
    ----------
    filelist: list
        File list with sensitivity curves to be compared.
    outfile: str or Path or None
        path to the output file to be saved.
        if None, the figure is not saved
    cta_north: Bool
        Flag to superpose/add (True) or not (False - Default) the CTA North.
        Imported from ctaplot
    """
    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger("lstchain MC DL2 to IRF - sensitivity curves")

    log.info("Starting lstmcpipe compare irfs script")

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))

    for file in filelist:
        log.info(f"Plotting IRFs from file {file}")
        label = Path(file).stem
        plot_summary_from_file(file, axes=axes, label=label)

    if cta_north:
        ctaplot.plot_sensitivity_cta_performance('north', ax=axes.ravel()[0])
        ctaplot.plot_angular_resolution_cta_performance('north', ax=axes.ravel()[1])
        ctaplot.plot_energy_resolution_cta_performance('north', ax=axes.ravel()[2])
        ctaplot.plot_effective_area_cta_performance('north', ax=axes.ravel()[3])

    fig.tight_layout()
    if outfile is not None:
        fig.savefig(outfile, dpi=200, bbox_inches='tight')
    else:
        fig.show()

    return axes


def main():
    parser = argparse.ArgumentParser(description="Produce IRFs comparative plots")

    # Required arguments
    parser.add_argument(
        '--filelist', '-f', type=str, nargs='*', dest='filelist', help='List of IRF files', required=True
    )

    # optional
    parser.add_argument(
        '--outfile',
        '-o',
        action='store',
        type=Path,
        dest='outfile',
        help='Path of the outfile',
        default='compare_irfs.png',
    )

    parser.add_argument(
        '--add-cta-north', action='store_true', dest='cta_north', help='add CTA north performances curves'
    )

    args = parser.parse_args()
    plot_comparison(args.filelist, args.outfile, args.cta_north)


if __name__ == '__main__':
    main()
