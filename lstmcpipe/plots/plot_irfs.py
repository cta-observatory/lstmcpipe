#!/usr/bin/env python

# T. Vuillaume & E. Garcia - 2021

from pathlib import Path
import argparse
from astropy.table import QTable
import matplotlib.pyplot as plt
import numpy as np
import astropy.units as u
from pyirf.utils import cone_solid_angle
import ctaplot
from astropy.visualization import quantity_support


def plot_summary_from_file(filename, axes=None, **kwargs):

    if axes is None:
        fig, axes = plt.subplots(2, 3, figsize=(15, 8))

    kwargs.setdefault('ls', '-')
    kwargs.setdefault('elinewidth', 0.75)
    kwargs.setdefault('label', Path(filename).stem)


    sens_table = read_sensitivity_table(filename)
    plot_sensitivity_from_table(sens_table, ax=axes.ravel()[0], **kwargs)
    kwargs.pop("label")
    axes.ravel()[0].legend()

    plot_angular_resolution_from_file(filename, ax=axes.ravel()[1], **kwargs)

    plot_energy_resolution_from_file(filename, ax=axes.ravel()[2], **kwargs)

    plot_effective_area_from_file(filename, ax=axes.ravel()[3], **kwargs)

    plot_energy_bias_from_file(filename, ax=axes.ravel()[5], **kwargs)

    plot_background_rate_from_file(filename, ax=axes.ravel()[4], **kwargs)

    axes.ravel()[0].get_figure().tight_layout()

    return axes


def read_sensitivity_table(irf_file):
    """ """
    sensitivity = QTable.read(irf_file, hdu="SENSITIVITY")[1:-1]
    return sensitivity


def plot_gh_cut_per_energy(filename, ax=None, **kwargs):
    """ """
    ax = plt.gca() if ax is None else ax

    gh_cut = QTable.read(filename, hdu="GH_CUTS")[1:-1]

    kwargs.setdefault("ls", "")
    ax.errorbar(
        0.5 * (gh_cut["low"] + gh_cut["high"]).to_value(u.TeV),
        gh_cut["cut"],
        xerr=0.5 * (gh_cut["high"] - gh_cut["low"]).to_value(u.TeV),
        **kwargs,
    )

    ax.set_ylabel("G/H-cut")
    ax.set_xlabel(r"$E_\mathrm{reco} / \mathrm{TeV}$")
    ax.set_xscale("log")
    ax.grid(True)

    return ax


def plot_sensitivity_from_table(sens_table, ax=None, **kwargs):
    """ """

    ax = plt.gca() if ax is None else ax

    sens_unit = u.Unit("erg cm-2 s-1")

    e = sens_table["reco_energy_center"]
    s = e**2 * sens_table["flux_sensitivity"]
    w = sens_table["reco_energy_high"] - sens_table["reco_energy_low"]
    energy_unit = u.TeV

    ax.errorbar(
        e.to_value(energy_unit),
        s.to_value(sens_unit),
        xerr=w.to_value(u.TeV) / 2,
        **kwargs,
    )

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.grid(True, which="both")

    # Style settings
    ax.set_title("Minimal Flux Needed for 5σ Detection in 50 hours")
    ax.set_xlabel(r'$E_{Reco}$ / TeV')
    ax.set_ylabel(rf"$(E^2 \cdot \mathrm{{Flux Sensitivity}}) /$ ({sens_unit.to_string('latex')})")

    return ax


def plot_sensitivity_from_file(irf_file, ax=None, **kwargs):

    tab = read_sensitivity_table(irf_file)
    ax = plot_sensitivity_from_table(tab, ax=ax, **kwargs)
    return ax


def plot_magic_2014(ax=None, **kwargs):
    ax = plt.gca() if ax is None else ax
    file = (
        "/fefs/home/thomas.vuillaume/software/cta-observatory/cta-lstchain/lstchain/spectra/data/magic_sensitivity.txt"
    )
    magic_2014 = np.loadtxt(file, skiprows=1)

    kwargs.setdefault("label", "MAGIC (Aleksic et al. 2014)")
    ax.loglog(
        magic_2014[:, 0] / 1e3,
        magic_2014[:, 3] * np.power(magic_2014[:, 0] / 1e3, 2),
        **kwargs,
    )

    return ax


def plot_effective_area_from_file(file, all_cuts=False, ax=None, **kwargs):
    """ """

    ax = plt.gca() if ax is None else ax

    if all_cuts:
        names = ["", "_NO_CUTS", "_ONLY_GH", "_ONLY_THETA"]
    else:
        names = tuple([""])

    label_basename = kwargs["label"] if "label" in kwargs else ""

    kwargs.setdefault("ls", "")

    for name in names:

        area = QTable.read(file, hdu="EFFECTIVE_AREA" + name)[0]

        kwargs["label"] = label_basename + name.replace("_", " ")

        ax.errorbar(
            0.5 * (area["ENERG_LO"] + area["ENERG_HI"]).to_value(u.TeV)[1:-1],
            area["EFFAREA"].to_value(u.m**2).T[1:-1, 0],
            xerr=0.5 * (area["ENERG_LO"] - area["ENERG_HI"]).to_value(u.TeV)[1:-1],
            **kwargs,
        )

        # Style settings
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel(r"$E_\mathrm{True}$ / TeV")
        ax.set_ylabel("Effective collection area / m²")
        ax.grid(which="both")
        ax.grid(True, which="both")

    return ax


def plot_psf_from_file(filename):

    psf_table = QTable.read(filename, hdu="PSF")[0]
    # select the only fov offset bin
    psf = psf_table["RPSF"].T[:, 0, :].to_value(1 / u.sr)

    offset_bins = np.append(psf_table["RAD_LO"], psf_table["RAD_HI"][-1])
    phi_bins = np.linspace(0, 2 * np.pi, 100)

    # Let's make a nice 2d representation of the radially symmetric PSF
    r, phi = np.meshgrid(offset_bins.to_value(u.deg), phi_bins)

    # look at a single energy bin
    # repeat values for each phi bin
    center = 0.5 * (psf_table["ENERG_LO"] + psf_table["ENERG_HI"])

    fig = plt.figure(figsize=(15, 5))
    axs = [fig.add_subplot(1, 3, i, projection="polar") for i in range(1, 4)]

    for bin_id, ax in zip([10, 20, 30], axs):
        image = np.tile(psf[bin_id], (len(phi_bins) - 1, 1))

        ax.set_title(f"PSF @ {center[bin_id]:.2f} TeV")
        ax.pcolormesh(phi, r, image)
        ax.set_ylim(0, 0.25)
        ax.set_aspect(1)

    fig.tight_layout()

    return axs


def plot_theta_cut_from_file(filename, ax=None, **kwargs):

    ax = plt.gca() if ax is None else ax

    rad_max = QTable.read(filename, hdu="RAD_MAX")[0]

    kwargs.setdefault("ls", "")
    ax.errorbar(
        0.5 * (rad_max["ENERG_LO"] + rad_max["ENERG_HI"])[1:-1].to_value(u.TeV),
        rad_max["RAD_MAX"].T[1:-1, 0].to_value(u.deg),
        xerr=0.5 * (rad_max["ENERG_HI"] - rad_max["ENERG_LO"])[1:-1].to_value(u.TeV),
        **kwargs,
    )

    ax.set_ylabel("θ-cut / deg²")
    ax.set_xlabel(r"$E_\mathrm{reco} / \mathrm{TeV}$")
    ax.set_xscale("log")

    return ax


def plot_angular_resolution_from_file(filename, ax=None, **kwargs):

    ax = plt.gca() if ax is None else ax

    ang_res = QTable.read(filename, hdu="ANGULAR_RESOLUTION")[1:-1]

    kwargs.setdefault("ls", "")
    ax.errorbar(
        0.5 * (ang_res["true_energy_low"] + ang_res["true_energy_high"]).to_value(u.TeV),
        ang_res["angular_resolution"].to_value(u.deg),
        xerr=0.5 * (ang_res["true_energy_high"] - ang_res["true_energy_low"]).to_value(u.TeV),
        **kwargs,
    )

    # Style settings
    #     ax.set_xlim(1.e-2, 2.e2)
    #     ax.set_ylim(2.e-2, 1)
    ax.set_xscale("log")
    ax.set_xlabel(r"$E_\mathrm{True}$ / TeV")
    ax.set_ylabel("Angular Resolution / deg")
    ax.grid(True, which="both")

    return ax


def plot_energy_dispersion_from_file(filename):

    edisp = QTable.read(filename, hdu="ENERGY_DISPERSION")[0]

    e_bins = edisp["ENERG_LO"][1:]
    migra_bins = edisp["MIGRA_LO"][1:]

    fig = plt.gca()
    plt.pcolormesh(
        e_bins.to_value(u.TeV),
        migra_bins,
        edisp["MATRIX"].T[1:-1, 1:-1, 0].T,
        cmap="inferno",
    )

    plt.xscale("log")
    plt.yscale("log")
    plt.colorbar(label="PDF Value")

    plt.xlabel(r"$E_\mathrm{True} / \mathrm{TeV}$")
    plt.ylabel(r"$E_\mathrm{Reco} / E_\mathrm{True}$")

    return fig


def plot_energy_resolution_from_file(filename, ax=None, **kwargs):

    ax = plt.gca() if ax is None else ax

    bias_resolution = QTable.read(filename, hdu="ENERGY_BIAS_RESOLUTION")[1:-1]

    kwargs.setdefault("ls", "")

    # Plot function
    ax.errorbar(
        0.5 * (bias_resolution["true_energy_low"] + bias_resolution["true_energy_high"]).to_value(u.TeV),
        bias_resolution["resolution"],
        xerr=0.5 * (bias_resolution["true_energy_high"] - bias_resolution["true_energy_low"]).to_value(u.TeV),
        **kwargs,
    )
    ax.set_xscale("log")

    # Style settings
    ax.set_xlabel(r"$E_\mathrm{True} / \mathrm{TeV}$")
    ax.set_ylabel("Energy resolution")
    ax.grid(True, which="both")

    return ax


def plot_background_rate_from_file(filename, ax=None, **kwargs):

    ax = plt.gca() if ax is None else ax

    rad_max = QTable.read(filename, hdu="RAD_MAX")[0]
    bg_rate = QTable.read(filename, hdu="BACKGROUND")[0]

    reco_bins = np.append(bg_rate["ENERG_LO"], bg_rate["ENERG_HI"][-1])

    # first fov bin, [0, 1] deg
    fov_bin = 0
    rate_bin = bg_rate["BKG"].T[:, fov_bin]

    # interpolate theta cut for given e reco bin
    e_center_bg = 0.5 * (bg_rate["ENERG_LO"] + bg_rate["ENERG_HI"])
    e_center_theta = 0.5 * (rad_max["ENERG_LO"] + rad_max["ENERG_HI"])
    theta_cut = np.interp(e_center_bg, e_center_theta, rad_max["RAD_MAX"].T[:, 0])

    # undo normalization
    rate_bin *= cone_solid_angle(theta_cut)
    rate_bin *= np.diff(reco_bins)

    if "ls" not in kwargs and "linestyle" not in kwargs:
        kwargs["ls"] = ""

    ax.errorbar(
        e_center_bg.to_value(u.TeV)[1:-1],
        rate_bin.to_value(1 / u.s)[1:-1],
        xerr=np.diff(reco_bins).to_value(u.TeV)[1:-1] / 2,
        **kwargs,
    )

    # Style settings
    ax.set_xscale("log")
    ax.set_xlabel(r"$E_\mathrm{Reco}$ / $\mathrm{TeV}$")
    ax.set_ylabel("Background rate [Hz]")
    ax.grid(True, which="both")
    ax.set_yscale("log")

    return ax


def plot_magic_bkg_rate(ax=None, **kwargs):

    ax = plt.gca() if ax is None else ax

    table = ctaplot.ana.get_magic_sensitivity()

    emin = table["e_min"].to_value(u.TeV)
    emax = table["e_max"].to_value(u.TeV)
    ecenter = table["e_center"].to_value(u.TeV)
    bkg_rate = table["background_rate"].to_value(1 / u.s)
    bkg_rate_err = table["background_rate_err"].to_value(1 / u.s)

    kwargs.setdefault("label", "MAGIC (Aleksić et al, 2016)")

    ax.errorbar(
        ecenter,
        bkg_rate,
        xerr=[ecenter - emin, emax - ecenter],
        yerr=bkg_rate_err,
        **kwargs,
    )

    ax.set_xlabel(r"$E_\mathrm{Reco} [\mathrm{TeV}]$")
    ax.set_ylabel("Background rate [Hz]")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.grid(True, which="both")

    return ax


def plot_energy_bias_from_file(filename, ax=None, **kwargs):

    ax = plt.gca() if ax is None else ax

    bias_resolution = QTable.read(filename, hdu="ENERGY_BIAS_RESOLUTION")[1:-1]

    kwargs.setdefault("ls", "")

    # Plot function
    ax.errorbar(
        0.5 * (bias_resolution["true_energy_low"] + bias_resolution["true_energy_high"]).to_value(u.TeV),
        bias_resolution["bias"],
        xerr=0.5 * (bias_resolution["true_energy_high"] - bias_resolution["true_energy_low"]).to_value(u.TeV),
        **kwargs,
    )
    ax.set_xscale("log")

    # Style settings
    ax.set_xlabel(r"$E_\mathrm{True}$ / $\mathrm{TeV}$")
    ax.set_ylabel("Energy bias")
    ax.grid(True, which="both")

    return ax


def plot_sensitivity_ratio(sensitivity_tables, baseline_index=0, ax=None, labels=None, **kwargs):
    """
    Plot the ratio of sensitivities as a function of the energy

    Parameters
    ----------
    sensitivity_tables: list
        list of sensitivity tables
    baseline_index: int
        index of the baseline to use in the list
    ax: pyplot.axis
    labels: list
        list of labels to use
    kwargs: kwargs for the plot

    Returns
    -------
    ax: pyplot.axis
    """

    ax = plt.gca() if ax is None else ax

    sens_table_baseline = sensitivity_tables[baseline_index]
    e = sens_table_baseline["reco_energy_center"]
    w = sens_table_baseline["reco_energy_high"] - sens_table_baseline["reco_energy_low"]
    s_baseline = e**2 * sens_table_baseline["flux_sensitivity"]

    for ii, sens_table in enumerate(sensitivity_tables):
        s = e**2 * sens_table["flux_sensitivity"]
        if labels is not None:
            kwargs['label'] = labels[ii]
        with quantity_support():
            ax.errorbar(
                e,
                s / s_baseline,
                xerr=w / 2,
                **kwargs,
            )
    ax.set_title('Sensitivity ratio (lower is better)')
    ax.set_xscale('log')
    ax.grid(True, which='both')
    ax.set_xlabel(f'Energy / {e.unit}')

    return ax


def plot_sensitivity_ratio_from_files(filelist, baseline_index=0, ax=None, **kwargs):
    """
    Plot the ratio of sensitivities as a function of the energy

    Parameters
    ----------
    sensitivity_tables: list
        list of sensitivity tables
    baseline_index: int
        index of the baseline to use in the list
    ax: pyplot.axis
    kwargs: kwargs for the plot

    Returns
    -------
    ax: pyplot.axis
    """

    sens_tables = [read_sensitivity_table(file) for file in filelist]
    labels = [Path(file).name for file in filelist]
    ax = plot_sensitivity_ratio(sens_tables, baseline_index=baseline_index, ax=ax, labels=labels, **kwargs)
    return ax


def main():

    parser = argparse.ArgumentParser(description="Produce lstMCpipe IRFs plot from a sensitivity.fits.gz file")

    # Required arguments
    parser.add_argument("--filename", "-f", type=str, dest="filename", help="Input filename")
    parser.add_argument("--outfile", "-o", type=Path, dest="outfile", help="Output filename")

    args = parser.parse_args()

    plot_summary_from_file(args.filename)

    args.outfile.parent.mkdir(exist_ok=True)
    plt.savefig(args.outfile)


if __name__ == "__main__":
    main()
