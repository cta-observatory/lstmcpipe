import argparse
import os
import pandas as pd
from lstchain.io.io import dl2_params_lstcam_key
import matplotlib.pyplot as plt
import ctaplot
from ctaplot.plots import plot_binned_stat


parser = argparse.ArgumentParser(description="Reconstruct events")

# Required arguments
parser.add_argument(
    "--gamma_file", "-fg", type=str, dest="gamma_file", help="path to a DL1 HDF5 file"
)

# Required arguments
# parser.add_argument('--datafile', '-fp', type=str,
#                     dest='proton_file',
#                     help='path to a DL1 HDF5 file',
#                     )

parser.add_argument(
    "--pathmodels",
    "-p",
    action="store",
    type=str,
    dest="path_models",
    help="Path where to find the trained RF",
    default="./trained_models",
)

# Optional argument
parser.add_argument(
    "--outdir",
    "-o",
    action="store",
    type=str,
    dest="outdir",
    help="Path where to store the reco dl2 events",
    default="./plots",
)


parser.add_argument(
    "--config_file",
    "-conf",
    action="store",
    type=str,
    dest="config_file",
    help="Path to a configuration file. If none is given, a standard configuration is applied",
    default=None,
)

args = parser.parse_args()


def plot_histograms(data, save_dir=None, **kwargs):
    """
    Plot the histogram of every data column in a dataframe

    Parameters
    ----------
    data: `pandas.DataFrame`
    save_dir: path. if None the figures are not saved but showed.
    kwargs: args for hist

    """

    if save_dir is not None:
        os.makedirs(save_dir, exist_ok=True)

    for k in data.columns:
        fig, ax = plt.subplots(figsize=(15, 10))
        data[k].hist(ax=ax, **kwargs)
        ax.set_title(f"{k} hist")
        ax.set_xlabel(k)

        if save_dir is not None:
            fig_name = os.path.join(save_dir, f"hist_{k}.png")
            fig.savefig(fig_name, fmt="png", dpi=200)

        else:
            fig.show()


def plot_binned_stat_grid(data, x_col, **binned_stat_args):
    """
    Make a figure with a grid of binned stat plots

    Parameters
    ----------
    data: `pandas.dataframe`
    x_col: str
    binned_stat_args: args for `ctaplot.plot.plot_binned_stat`

    Returns
    -------
    `matplotlib.figure.Figure`
    """

    n = len(data.columns)
    ncol = 4
    nrows = n // ncol + 1 * (n % ncol > 0)

    fig, axes = plt.subplots(
        nrows=nrows, ncols=ncol, figsize=(20, 20 * 0.66 * (nrows / ncol)), sharex=False
    )

    raxes = axes.ravel()
    cols = list(data.columns)
    cols.remove(x_col)  # no need to plot x_col versus itself

    if "statistic" not in binned_stat_args:
        binned_stat_args["statistic"] = "mean"

    for ii, k in enumerate(cols):
        ax = raxes[ii]

        plot_binned_stat(data[x_col], data[k], ax=ax, **binned_stat_args)

        ax.set_title(f"{k}", fontsize=15)
        ax.grid("on")

    for ii in range(len(cols), len(axes.ravel())):
        raxes[ii].remove()

    fig.suptitle(
        rf"{binned_stat_args['statistic']} as a function of {x_col}",
        fontsize=20,
        y=1.02,
    )
    fig.tight_layout()

    return fig


# plot histograms


if __name__ == "__main__":

    gamma = pd.read_hdf(args.gamma_file, key=dl2_params_lstcam_key)
    selection = (
        (gamma.intensity > 200) & (gamma.leakage < 0.2) & (gamma.gammaness > 0.5)
    )
    selected_gamma = gamma[selection]

    plot_histograms(gamma, save_dir=os.path.join(args.outdir, "hist"), bins=100)

    fig = plot_binned_stat_grid(gamma, "log_mc_energy", errorbar=True)
    fig.savefig(os.path.join(args.outdir, "means_per_energy.png"))

    fig, ax = plt.subplots(figsize=(10, 7))
    ax = ctaplot.plot_angular_resolution_cta_performance("north", color="black", ax=ax)
    ax = ctaplot.plot_angular_resolution_per_energy(
        gamma.reco_alt,
        gamma.reco_az,
        gamma.mc_alt,
        gamma.mc_az,
        gamma.reco_energy,
        ax=ax,
        label="all gammas",
    )
    ax = ctaplot.plot_angular_resolution_per_energy(
        selected_gamma.reco_alt,
        selected_gamma.reco_az,
        selected_gamma.mc_alt,
        selected_gamma.mc_az,
        selected_gamma.reco_energy,
        ax=ax,
        label="selected gammas",
    )
    ax.legend()
    ax.set_ylim(0, 0.5)
    ax.grid(which="both")
    fig.savefig(os.path.join(args.outdir, "angular_resolution.png"), fmt="png", dpi=200)

    fig, ax = plt.subplots(figsize=(10, 7))
    ax = ctaplot.plot_energy_resolution_cta_performance("north", color="black", ax=ax)
    ax = ctaplot.plot_energy_resolution(
        gamma.mc_energy, gamma.reco_energy, label="all gammas", ax=ax
    )
    ax = ctaplot.plot_energy_resolution(
        selected_gamma.mc_energy,
        selected_gamma.reco_energy,
        label="selected gammas",
        ax=ax,
    )
    ax.legend()
    ax.set_ylim(0, 0.5)
    ax.grid(which="both")
    fig.savefig(os.path.join(args.outdir, "energy_resolution.png"), fmt="png", dpi=200)

    ## add:
    # effective area
    # ROC per energy
