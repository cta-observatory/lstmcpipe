import numpy as np
import astropy.units as u
import matplotlib.pyplot as plt

from pyirf.utils import calculate_theta, calculate_source_fov_offset
from lstchain.io.io import read_mc_dl2_to_QTable
from lstchain.reco.utils import filter_events
from astropy.table import QTable


from ..scripts.script_dl2_to_sensitivity import determine_source_position, filters


def read_gh_cut_table(filename):
    return QTable.read(filename, hdu="GH_CUTS")


def read_theta_cut_table(filename):
    return QTable.read(filename, hdu="RAD_MAX")[0]


def theta2_hist_per_energy_bin(irf_file, dl2_gamma_file):
    """
    plot a theta2 histogram per energy bin of gammas selected event (passing gh_score cut)
    and displaying the theta2 cut applied for IRFs
    """

    gammas, sim_info = read_mc_dl2_to_QTable(dl2_gamma_file)
    gammas = filter_events(gammas, filters)
    for prefix in ("true", "reco"):
        k = f"{prefix}_source_fov_offset"
        gammas[k] = calculate_source_fov_offset(gammas, prefix=prefix)

    source_alt, source_az = determine_source_position(gammas)
    gammas['theta'] = calculate_theta(gammas, assumed_source_az=source_az, assumed_source_alt=source_alt)

    gh_cuts = read_gh_cut_table(irf_file)
    theta_cuts = read_theta_cut_table(irf_file)

    tc = theta_cuts["RAD_MAX"].T[:, 0]
    energy_min = theta_cuts['ENERG_LO']
    energy_max = theta_cuts['ENERG_HI']

    np.testing.assert_allclose(energy_min, gh_cuts['low'])
    np.testing.assert_allclose(energy_max, gh_cuts['high'])

    ncols = 5
    nrows = len(energy_min) // ncols + int((len(energy_min) % ncols) > 0)

    fig, axes = plt.subplots(ncols=ncols, nrows=nrows, figsize=(ncols * 5, nrows * 5))
    xrange = (0, 0.4)
    for ii, emin in enumerate(energy_min):
        ax = axes.ravel()[ii]
        emax = energy_max[ii]
        mask = (
            (gammas['gh_score'] < gh_cuts['cut'][ii]) & (emin <= gammas['true_energy']) & (gammas['true_energy'] < emax)
        )

        t2unit = u.deg**2
        n, bins, _ = ax.hist(
            (gammas[mask]['theta'] ** 2).to_value(t2unit),
            label=f'{emin:0.2f}-{emax:0.2f}',
            histtype='step',
            lw=2,
            bins=np.linspace(*xrange),
            range=xrange,
            density=False,
        )
        ax.vlines((tc[ii] ** 2).to_value(t2unit), 0, np.max(n), color='orange')
        ax.legend()
        ax.set_xlim(*xrange)
        ax.set_xlabel(f'theta2 / {t2unit}')
        ax.set_title(f"gh cut: {gh_cuts['cut'][ii]:0.3f}")
        plt.tight_layout()

    return axes
