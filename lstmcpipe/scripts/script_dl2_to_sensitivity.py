"""
Procedure adapted from pyirf v0.4 example one (used with eventdisplay)
"""
import logging
import operator

from pathlib import Path
import numpy as np
from astropy import table
import astropy.units as u
from astropy.io import fits

from pyirf.binning import (
    create_bins_per_decade,
    add_overflow_bins,
    create_histogram_table,
)
from pyirf.cuts import calculate_percentile_cut, evaluate_binned_cut
from pyirf.sensitivity import calculate_sensitivity, estimate_background
from pyirf.utils import calculate_theta, calculate_source_fov_offset
from pyirf.benchmarks import energy_bias_resolution, angular_resolution
from pyirf.benchmarks.energy_bias_resolution import energy_resolution_absolute_68

from pyirf.spectral import (
    calculate_event_weights,
    PowerLaw,
    CRAB_HEGRA,
    IRFDOC_PROTON_SPECTRUM,
    IRFDOC_ELECTRON_SPECTRUM,
)
from pyirf.cut_optimization import optimize_gh_cut

from pyirf.irf import (
    effective_area_per_energy,
    energy_dispersion,
    psf_table,
    background_2d,
)

from pyirf.io import (
    create_aeff2d_hdu,
    create_psf_table_hdu,
    create_energy_dispersion_hdu,
    create_rad_max_hdu,
    create_background_2d_hdu,
)

from lstchain.io.io import read_mc_dl2_to_QTable
import argparse


T_OBS = 50 * u.hour

# scaling between on and off region.
# Make off region 10 times larger than on region for better
# background statistics
ALPHA = 0.1

# Radius to use for calculating bg rate
MAX_BG_RADIUS = 1 * u.deg
MAX_GH_CUT_EFFICIENCY = 0.9
GH_CUT_EFFICIENCY_STEP = 0.01

# gh cut used for first calculation of the binned theta cuts
INITIAL_GH_CUT_EFFICENCY = 0.4

MIN_THETA_CUT = 0.1 * u.deg
MAX_THETA_CUT = 0.5 * u.deg

MIN_ENERGY = 20.0 * u.GeV
MAX_ENERGY = 20.05 * u.TeV

N_BIN_PER_DECADE = 5

filters = {
    'intensity': [20, np.inf],
    # 'leakage_intensity_width_2': [0, 0.2],
}


def determine_source_position(gamma_events):
    if len(set(gamma_events['true_alt'].value)) == 1:
        source_alt = gamma_events['true_alt'][0]
    else:
        raise ValueError("The gamma source position is not unique, one should be provided with --source-alt")

    if len(set(gamma_events['true_az'].value)) == 1:
        source_az = gamma_events['true_az'][0]
    else:
        raise ValueError("The gamma source position is not unique, one should be provided with --source-alt")

    return source_alt, source_az


def main():
    log = logging.getLogger("lstchain MC DL2 to IRF - sensitivity curves")

    parser = argparse.ArgumentParser(description="MC DL2 to IRF")

    # Required arguments
    parser.add_argument("--gamma-dl2", "-g", type=str, dest="gamma_file", help="Path to the dl2 gamma file")

    parser.add_argument(
        "--proton-dl2",
        "-p",
        type=str,
        dest="proton_file",
        help="Path to the dl2 proton file",
    )

    parser.add_argument(
        "--electron-dl2",
        "-e",
        type=str,
        dest="electron_file",
        help="Path to the dl2 electron file",
    )

    parser.add_argument(
        "--outfile",
        "-o",
        action="store",
        type=str,
        dest="outfile",
        help="Path where to save IRF FITS file",
        default="sensitivity.fits.gz",
    )

    parser.add_argument(
        "--source_alt",
        action="store",
        type=float,
        dest="source_alt",
        help="Source altitude (optional). If not provided, it will be guessed from the gammas true altitude",
        default=None,
    )

    parser.add_argument(
        "--source_az",
        action="store",
        type=float,
        dest="source_az",
        help="Source azimuth (optional). If not provided, it will be guessed from the gammas true altitude",
        default=None,
    )

    # Optional arguments
    # parser.add_argument('--config', '-c', action='store', type=Path,
    #                     dest='config_file',
    #                     help='Path to a configuration file. If none is given, a standard configuration is applied',
    #                     default=None
    #                     )

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    logging.getLogger("pyirf").setLevel(logging.DEBUG)

    particles = {
        "gamma": {"file": args.gamma_file, "target_spectrum": CRAB_HEGRA},
        "proton": {"file": args.proton_file, "target_spectrum": IRFDOC_PROTON_SPECTRUM},
        "electron": {
            "file": args.electron_file,
            "target_spectrum": IRFDOC_ELECTRON_SPECTRUM,
        },
    }

    for particle_type, p in particles.items():
        log.info("Simulated Events: {}".format(particle_type.title()))
        p["events"], p["simulation_info"] = read_mc_dl2_to_QTable(p["file"])
        # p['events'] = filter_events(p['events'], filters)

        print("=====", particle_type, "=====")
        # p["events"]["particle_type"] = particle_type

        p["simulated_spectrum"] = PowerLaw.from_simulation(p["simulation_info"], T_OBS)
        p["events"]["weight"] = calculate_event_weights(
            p["events"]["true_energy"], p["target_spectrum"], p["simulated_spectrum"]
        )
        for prefix in ("true", "reco"):
            k = f"{prefix}_source_fov_offset"
            p["events"][k] = calculate_source_fov_offset(p["events"], prefix=prefix)

    gammas = particles["gamma"]["events"]
    # background table composed of both electrons and protons
    background = table.vstack([particles["proton"]["events"], particles["electron"]["events"]])

    if args.source_alt is None or args.source_az is None:
        source_alt, source_az = determine_source_position(gammas)
    else:
        source_alt, source_az = args.source_alt, args.source_az

    for particle_type, p in particles.items():
        # calculate theta / distance between reco and assumed source position
        # we handle only ON observations here, so the assumed source pos is the pointing position
        p["events"]["theta"] = calculate_theta(p["events"], assumed_source_az=source_az, assumed_source_alt=source_alt)
        log.info(p["simulation_info"])
        log.info("")

    INITIAL_GH_CUT = np.quantile(gammas["gh_score"], (1 - INITIAL_GH_CUT_EFFICENCY))
    log.info("Using fixed G/H cut of {} to calculate theta cuts".format(INITIAL_GH_CUT))

    # event display uses much finer bins for the theta cut than
    # for the sensitivity
    theta_bins = add_overflow_bins(create_bins_per_decade(MIN_ENERGY, MAX_ENERGY, N_BIN_PER_DECADE))

    # theta cut is 68 percent containment of the gammas
    # for now with a fixed global, unoptimized score cut
    mask_theta_cuts = gammas["gh_score"] >= INITIAL_GH_CUT
    theta_cuts = calculate_percentile_cut(
        gammas["theta"][mask_theta_cuts],
        gammas["reco_energy"][mask_theta_cuts],
        bins=theta_bins,
        min_value=MIN_THETA_CUT,
        fill_value=MAX_THETA_CUT,
        max_value=MAX_THETA_CUT,
        percentile=68,
    )

    # same number of bins per decade than official CTA IRFs
    sensitivity_bins = add_overflow_bins(
        create_bins_per_decade(MIN_ENERGY, MAX_ENERGY, bins_per_decade=N_BIN_PER_DECADE)
    )

    log.info("Optimizing G/H separation cut for best sensitivity")
    gh_cut_efficiencies = np.arange(
        GH_CUT_EFFICIENCY_STEP,
        MAX_GH_CUT_EFFICIENCY + GH_CUT_EFFICIENCY_STEP / 2,
        GH_CUT_EFFICIENCY_STEP,
    )
    sensitivity_step_2, gh_cuts = optimize_gh_cut(
        gammas,
        background,
        reco_energy_bins=sensitivity_bins,
        gh_cut_efficiencies=gh_cut_efficiencies,
        op=operator.ge,
        theta_cuts=theta_cuts,
        alpha=ALPHA,
        background_radius=MAX_BG_RADIUS,
    )

    # now that we have the optimized gh cuts, we recalculate the theta
    # cut as 68 percent containment on the events surviving these cuts.
    log.info("Recalculating theta cut for optimized GH Cuts")
    for tab in (gammas, background):
        tab["selected_gh"] = evaluate_binned_cut(tab["gh_score"], tab["reco_energy"], gh_cuts, operator.ge)

    theta_cuts_opt = calculate_percentile_cut(
        gammas[gammas["selected_gh"]]["theta"],
        gammas[gammas["selected_gh"]]["reco_energy"],
        theta_bins,
        percentile=68,
        fill_value=MAX_THETA_CUT,
        max_value=MAX_THETA_CUT,
        min_value=MIN_THETA_CUT,
    )

    gammas["selected_theta"] = evaluate_binned_cut(gammas["theta"], gammas["reco_energy"], theta_cuts_opt, operator.le)
    gammas["selected"] = gammas["selected_theta"] & gammas["selected_gh"]

    # calculate sensitivity
    signal_hist = create_histogram_table(gammas[gammas["selected"]], bins=sensitivity_bins)
    background_hist = estimate_background(
        background[background["selected_gh"]],
        reco_energy_bins=sensitivity_bins,
        theta_cuts=theta_cuts_opt,
        alpha=ALPHA,
        background_radius=MAX_BG_RADIUS,
    )
    sensitivity = calculate_sensitivity(signal_hist, background_hist, alpha=ALPHA)

    # scale relative sensitivity by Crab flux to get the flux sensitivity
    spectrum = particles["gamma"]["target_spectrum"]
    for s in (sensitivity_step_2, sensitivity):
        s["flux_sensitivity"] = s["relative_sensitivity"] * spectrum(s["reco_energy_center"])

    log.info("Calculating IRFs")
    hdus = [
        fits.PrimaryHDU(),
        fits.BinTableHDU(sensitivity, name="SENSITIVITY"),
        fits.BinTableHDU(sensitivity_step_2, name="SENSITIVITY_STEP_2"),
        fits.BinTableHDU(theta_cuts, name="THETA_CUTS"),
        fits.BinTableHDU(theta_cuts_opt, name="THETA_CUTS_OPT"),
        fits.BinTableHDU(gh_cuts, name="GH_CUTS"),
    ]

    masks = {
        "": gammas["selected"],
        "_NO_CUTS": slice(None),
        "_ONLY_GH": gammas["selected_gh"],
        "_ONLY_THETA": gammas["selected_theta"],
    }

    # binnings for the irfs
    true_energy_bins = add_overflow_bins(create_bins_per_decade(MIN_ENERGY, MAX_ENERGY, N_BIN_PER_DECADE))
    reco_energy_bins = add_overflow_bins(create_bins_per_decade(MIN_ENERGY, MAX_ENERGY, N_BIN_PER_DECADE))

    fov_offset_bins = [0, 0.6] * u.deg
    source_offset_bins = np.arange(0, 1 + 1e-4, 1e-3) * u.deg
    energy_migration_bins = np.geomspace(0.2, 5, 200)

    for label, mask in masks.items():
        effective_area = effective_area_per_energy(
            gammas[mask],
            particles["gamma"]["simulation_info"],
            true_energy_bins=true_energy_bins,
        )
        hdus.append(
            create_aeff2d_hdu(
                effective_area[..., np.newaxis],  # add one dimension for FOV offset
                true_energy_bins,
                fov_offset_bins,
                extname="EFFECTIVE_AREA" + label,
            )
        )
        edisp = energy_dispersion(
            gammas[mask],
            true_energy_bins=true_energy_bins,
            fov_offset_bins=fov_offset_bins,
            migration_bins=energy_migration_bins,
        )
        hdus.append(
            create_energy_dispersion_hdu(
                edisp,
                true_energy_bins=true_energy_bins,
                migration_bins=energy_migration_bins,
                fov_offset_bins=fov_offset_bins,
                extname="ENERGY_DISPERSION" + label,
            )
        )

    bias_resolution = energy_bias_resolution(
        gammas[gammas["selected"]],
        true_energy_bins,
        resolution_function=energy_resolution_absolute_68,
    )
    ang_res = angular_resolution(gammas[gammas["selected_gh"]], true_energy_bins)
    psf = psf_table(
        gammas[gammas["selected_gh"]],
        true_energy_bins,
        fov_offset_bins=fov_offset_bins,
        source_offset_bins=source_offset_bins,
    )

    background_rate = background_2d(
        background[background["selected_gh"]],
        reco_energy_bins,
        fov_offset_bins=np.arange(0, 11) * u.deg,
        t_obs=T_OBS,
    )

    hdus.append(create_background_2d_hdu(background_rate, reco_energy_bins, fov_offset_bins=np.arange(0, 11) * u.deg))
    hdus.append(create_psf_table_hdu(psf, true_energy_bins, source_offset_bins, fov_offset_bins))
    hdus.append(create_rad_max_hdu(theta_cuts_opt["cut"][:, np.newaxis], theta_bins, fov_offset_bins))
    hdus.append(fits.BinTableHDU(ang_res, name="ANGULAR_RESOLUTION"))
    hdus.append(fits.BinTableHDU(bias_resolution, name="ENERGY_BIAS_RESOLUTION"))

    log.info("Writing output file")
    Path(args.outfile).parent.mkdir(exist_ok=True)
    fits.HDUList(hdus).writeto(args.outfile, overwrite=True)


if __name__ == "__main__":
    main()
