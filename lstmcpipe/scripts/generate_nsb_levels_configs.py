import subprocess
import json
import logging
import argparse
from lstchain.io.config import get_mc_config
from pathlib import Path
from datetime import date

BASE_LSTCHAIN_MC_CONFIG = get_mc_config()

# Configure logging
logging.basicConfig(level=logging.INFO)  # Set the default log level to INFO
logger = logging.getLogger(__name__)


def build_argparser():
    """
    Build the argument parser for the script.

    Returns:
        argparse.ArgumentParser: The argument parser object.
    """
    parser = argparse.ArgumentParser(description="Generate a set of lstchain and lstmcpipe configuration files for different nsb tuning ratios.")
    parser.add_argument("--config_class", "-c",
                        type=str, default="PathConfigAllSkyFullSplitDiffuse", 
                        help="The class of the configuration to generate.")
    parser.add_argument("--nsb_ratios", "-nsb",
                        nargs="+", type=float, default=0, 
                        help="List of nsb tuning ratios. If not provided, no NSB tuning is applied.")

    parser.add_argument(
        "--dec_list",
        nargs="+",
        help="List of declination values",
        default=[
            "dec_2276",
            "dec_3476",
            "dec_4822",
            "dec_6166",
            # "dec_6166_high_density",
            "dec_6676",
            "dec_931",
            "dec_min_1802",
            "dec_min_2924",
            "dec_min_413"
        ]
    )

    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files.")

    return parser


def lstchain_config_name(nsb_tuning_ratio):
    """
    Generate the name of the lstchain configuration file based on the given nsb_tuning_ratio.

    Parameters:
        nsb_tuning_ratio (float): The nsb tuning ratio.

    Returns:
        str: The name of the lstchain configuration file.
    """
    return f"lstchain_config_nsb{nsb_tuning_ratio}.json"


def dump_lstchain_nsb_config(nsb_tuning_ratio, outdir="."):
    """
    Dump the lstchain configuration file with the given nsb_tuning_ratio.

    Parameters:
        nsb_tuning_ratio (float): The nsb tuning ratio.
    """
    new_config = BASE_LSTCHAIN_MC_CONFIG.copy()
    if nsb_tuning_ratio == 0 or nsb_tuning_ratio is None:
        new_config["waveform_nsb_tuning"]["nsb_tuning"] = False
    else:
        new_config["waveform_nsb_tuning"]["nsb_tuning"] = True
        new_config["waveform_nsb_tuning"]["nsb_tuning_ratio"] = nsb_tuning_ratio
    json_filename = Path(outdir) / lstchain_config_name(nsb_tuning_ratio)
    with open(json_filename, 'w') as f:
        json.dump(new_config, f, indent=4)
    logger.info(f"Dumped lstchain configuration file: {json_filename}")


def prod_id(nsb_tuning_ratio):
    """
    Generate the prod ID based on the given nsb_tuning_ratio.

    Parameters:
        nsb_tuning_ratio (float): The nsb tuning ratio.

    Returns:
        str: The product ID.
    """
    return f"{date.today()}_allsky_nsb_tuning_{nsb_tuning_ratio}"


def lstmcpipe_config_filename(nsb_tuning_ratio, outdir="."):
    """
    Generate the name of the lstmcpipe configuration file based on the given nsb_tuning_ratio.

    Parameters:
        nsb_tuning_ratio (float): The nsb tuning ratio.

    Returns:
        str: The name of the lstmcpipe configuration file.
    """
    return Path(outdir) / f"lstmcpipe_config_nsb{nsb_tuning_ratio}.yml"


def main():
    """
    Dump the lstchain and lstmcpipe configuration files for the given nsb_tuning_ratios.
    """
    parser = build_argparser()
    args = parser.parse_args()

    dec_list = " ".join(args.dec_list)
    nsb_tuning_ratios = args.nsb_ratios
    config_class = args.config_class
    if nsb_tuning_ratios is None:
        nsb_tuning_ratios = [None]
    for nsb_tuning_ratio in nsb_tuning_ratios:
        logger.info(f"Working on ratio {nsb_tuning_ratio}")
        outdir = Path(f"NSB-{nsb_tuning_ratio}")
        outdir.mkdir(parents=True, exist_ok=True)
        dump_lstchain_nsb_config(nsb_tuning_ratio, outdir)
        tmp_lstchain_config = "tmp_lstchain_config.json"
        command = [
            "lstmcpipe_generate_config",
            config_class,
            "--prod_id",
            prod_id(nsb_tuning_ratio),
            "-o",
            lstmcpipe_config_filename(nsb_tuning_ratio, outdir),
            "--lstchain_conf",
            tmp_lstchain_config,
            "--dec_list",
        ]
        command.extend(args.dec_list)
        if args.overwrite:
            command.append("--overwrite")
        subprocess.run(command, check=True)
        # Delete tmp_lstchain_config (the lstchain configs with nsb tuning are already dumped)
        subprocess.run(["rm", tmp_lstchain_config], check=True)
        logger.info(f"Generated lstmcpipe configuration file: {lstmcpipe_config_filename(nsb_tuning_ratio)}")


if __name__ == "__main__":
    main()