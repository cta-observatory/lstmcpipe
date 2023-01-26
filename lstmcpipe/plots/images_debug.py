# to run this script you need a DL1 debug files of hipeRTA and a DL1 file from lstchain from the same run


import numpy as np
import matplotlib.pyplot as plt
from ctapipe.visualization import CameraDisplay
from ctapipe.image import tailcuts_clean
from ctapipe.instrument import SubarrayDescription
from lstchain.io.io import (
    dl1_images_lstcam_key,
    dl1_params_lstcam_key,
)
from astropy.table import Table, join
from ctapipe.containers import HillasParametersContainer
from matplotlib.backends.backend_pdf import PdfPages
import astropy.units as u
from astropy.coordinates import Angle
from lstchain.io.config import get_standard_config
from lstchain.io.config import read_configuration_file


def get_hillas_container(row):
    h = HillasParametersContainer()
    h.x = row["x"] * 28 * u.m
    h.y = row["y"] * 28 * u.m
    h.r = row["r"] * 28 * u.m
    h.phi = Angle(row["phi"] * u.rad)
    h.width = row["width"] * u.m
    h.length = row["length"] * u.m
    h.psi = Angle(row["psi"] * u.rad)
    h.skewness = row["skewness"]
    h.kurtosis = row["kurtosis"]
    h.length_uncertainty = 0 * u.m
    h.width_uncertainty = 0 * u.m
    return h


def get_cleaning_config(config_file=None):
    if config_file is None:
        config = get_standard_config()
    else:
        config = read_configuration_file(config_file)
    cleaning_parameters = config["tailcut"]
    cleaning_parameters.pop("use_only_main_island", True)
    cleaning_parameters.pop("delta_time", None)
    return cleaning_parameters


def main(filename, config_file=None):

    sub = SubarrayDescription.from_hdf(filename)
    geom = sub.tel[1].camera.geometry

    dl1_parameters_table = Table.read(filename, path=dl1_params_lstcam_key)
    images_table = Table.read(filename, path=dl1_images_lstcam_key)

    dl1_table = join(dl1_parameters_table, images_table, keys=["event_id", "tel_id", "obs_id"])

    params_cleaning = get_cleaning_config(config_file)

    selected_table = dl1_table[(dl1_table["intensity"] > 500) & np.isfinite(dl1_table["intensity"])]

    with PdfPages("images_examples.pdf") as pp:

        for ii, row in enumerate(selected_table[:10]):
            h = get_hillas_container(row)

            image = row["image"]
            peak_time = row["peak_time"]

            clean_mask = tailcuts_clean(geom, image, **params_cleaning)

            fig, axes = plt.subplots(1, 2, figsize=(12, 6))
            fig.suptitle(f"event id : {row['event_id']}")

            ax = axes[0]
            display = CameraDisplay(geom, image, ax=ax)
            display.add_colorbar(ax=ax)
            ax.set_title("charges")
            display.highlight_pixels(clean_mask, color="red", alpha=0.33)
            display.overlay_moments(h)

            ax = axes[1]
            display = CameraDisplay(geom, peak_time, ax=ax)
            display.highlight_pixels(clean_mask, color="red", alpha=0.2)
            display.add_colorbar(ax=ax)
            ax.set_title("peak time")

            pp.savefig(dpi=100)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Images debug")
    parser.add_argument("filename", type=str, help="path to the lstchain DL1 file")

    args = parser.parse_args()

    main(args.filename)
