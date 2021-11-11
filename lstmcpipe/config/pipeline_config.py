import os
import yaml
import calendar
import logging
from pathlib import Path


log = logging.getLogger(__name__)


def create_path(
    parent_path, stage, obs_date, pointing_zenith, prod_id=None, particles=True
):
    p = Path(parent_path) / stage / obs_date
    if particles:
        p /= "{}"
    p /= pointing_zenith
    if prod_id:
        p /= prod_id
    return p.as_posix()  # lets play it safe for now


def load_config(config_path):
    """
    Load the pipeline config, test for invalid values and
    set paths to the data files/directories.

    Parameters:
    -----------
    config_path: str or Path-like object
        Path to the config file

    Returns:
    --------
    config: dict
        Dictionary with parameters for the r0_to_dl3 processing
    """

    # This could easily be adapted to support different formats
    with open(config_path) as f:
        loaded_config = yaml.safe_load(f)

    config_valid(loaded_config)

    config = parse_config_and_handle_global_vars(loaded_config)

    log.info(
        f'************ - Configuration for processing of {config["prod_type"]} using the {config["workflow_kind"]} pipeline:- ************'
    )
    log.info(
        "Simtel DL0 files are going to be searched at: "
        f'{config["DL0_input_dir"].format("{" + ",".join(config["all_particles"]) + "}")}'
    )
    particle_dirs = [
        "running_analysis_dir",
        "DL1_output_dir",
        "DL2_output_dir",
        "analysis_log_dir",
    ]
    log.info(
        "The following directories and all the information within them will be either created or overwritten:\n - "
        + "\n - ".join(
            [
                config[pd].format("{" + ",".join(config["all_particles"]) + "}")
                for pd in particle_dirs
            ]
        )
        + f'\n - {config["IRF_output_dir"]}'
        + f'\n - {config["model_output_dir"]}'
    )

    log.warning(
        "! Subdirectories with the same PROD_ID and analysed the same day will be overwritten !"
    )
    log.info(f'PROD_ID to be used: {config["prod_id"]}')

    log.info("Stages to be run:\n - " + "\n - ".join(config["stages_to_run"]))
    log.info("Merging options:" f"\n - No-image argument: {config['merging_no_image']}")

    return config


def config_valid(loaded_config):
    """
    Test if the given dictionary contains valid values for the
    r0_to_dl3 processing.
    TODO: The stages should be checked aswell.
    Not all combinations are sensible!

    Parameters:
    -----------
    loaded_config: dict
        Dictionary with the values in the config file

    Returns:
    --------
    True if config is valid
    """
    # Allowed options
    allowed_workflows = ["hiperta", "lstchain", "ctapipe"]
    allowed_prods = ["prod3", "prod5"]
    allowed_obs_date = ["20190415", "20200629_prod5", "20200629_prod5_trans_80"]

    # Check allowed cases
    workflow_kind = loaded_config["workflow_kind"]
    if workflow_kind not in allowed_workflows:
        raise Exception(
            f"Please select an allowed `workflow_kind`: {allowed_workflows}"
        )

    prod_type = loaded_config["prod_type"]
    if prod_type not in allowed_prods:
        raise Exception(f"Please selected an allowed production type: {allowed_prods}.")

    obs_date = loaded_config["obs_date"]

    if obs_date not in allowed_obs_date:
        raise Exception(f"Please select an allowed obs_date: {allowed_workflows}")

    # and incompatible possibilities
    if (prod_type == "prod3" and obs_date != "20190415") or (
        prod_type == "prod5" and obs_date == "20190415"
    ):
        raise Exception("This prod_type and obs_date combination is not possible.")

    base_path_dl0 = loaded_config.get("base_path_dl0")
    base_path_dl1 = loaded_config.get("base_path_dl1")
    dl1_reference_id = loaded_config.get("dl1_reference_id")
    base_path_explanation = (
        "Choose base_path_dl0 if you want to process the simtel files.\n"
        "Choose base_path_dl1 if you want to reevaluate dl1 files."
    )
    if not base_path_dl0 and not base_path_dl1:
        raise KeyError(
            "One of base_path_dl0 or base_path_dl1 needs to be specified.\n"
            + base_path_explanation
        )
    elif bool(base_path_dl0) and bool(base_path_dl1):
        raise KeyError(
            "You must only specify one of base_path_dl0 or base_path_dl1.\n"
            " We can not resolve the source files if both are defined.\n"
            + base_path_explanation
        )
    elif base_path_dl1:
        if not dl1_reference_id:
            raise KeyError(
                "If you want to reprocess dl1 files, you must give "
                "specify the input files by setting 'dl1_reference_id'"
            )

    log.debug("Configuration deemed valid")
    return True


def parse_config_and_handle_global_vars(loaded_config):
    """
    Generates the config, that is used in the pipeline.
    Sets file paths for the la palma cluster
    and handles differences between prod3 and prod5.

    Parameters
    ----------
    loaded_config: dict
        Dictionary with the values read from the config file.
        No checks on the correctness of the data is applied,
        so this has to be done before.

    Returns
    -------
    config : dict
        Dictionary with all the variables needed along the r0_to_dl3 workflow

    """
    config = {}

    prod_id = loaded_config.get("prod_id", "v00")
    stages_to_be_run = loaded_config["stages_to_be_run"]
    merging_options = loaded_config["merging_options"]["no_image"]
    # dl0 for processing simtels, dl1 to reprocess older productions (dl1ab)
    base_path_dl0 = loaded_config.get("base_path_dl0")
    base_path_dl1 = loaded_config.get("base_path_dl1")
    dl1_reference_id = loaded_config.get("dl1_reference_id")

    pointing = loaded_config["pointing"]
    zenith = loaded_config["zenith"]
    particles = loaded_config["particles"]
    offset_gammas = loaded_config["offset_gammas"]
    obs_date = loaded_config["obs_date"]
    prod_type = loaded_config["prod_type"]
    workflow_kind = loaded_config["workflow_kind"]

    # Prod_id syntax
    t = calendar.datetime.date.today()
    year, month, day = f"{t.year:04d}", f"{t.month:02d}", f"{t.day:02d}"
    if workflow_kind == "lstchain":
        import lstchain

        base_prod_id = f"{year}{month}{day}_v{lstchain.__version__}"
    elif workflow_kind == "ctapipe":
        import ctapipe

        base_prod_id = f"{year}{month}{day}_vctapipe{ctapipe.__version__}"
    elif workflow_kind == "hiperta":  # RTA
        # TODO parse version from hiPeRTA module
        import lstchain

        base_prod_id = f"{year}{month}{day}_vRTA300_v{lstchain.__version__}"

    # Create the final config structure to be passed to the pipeline
    # 1 - Prod_id
    if "trans_80" in obs_date:
        suffix_id = "_{}_trans_80_{}".format(prod_type, prod_id)
    else:
        suffix_id = "_{}_{}".format(prod_type, prod_id)
    config["prod_id"] = base_prod_id + suffix_id

    # 2 - Parse source environment correctly
    src_env = (
        f"source {loaded_config['source_environment']['source_file']}; "
        f"conda activate {loaded_config['source_environment']['conda_env']}; "
    )
    config["source_environment"] = src_env

    # 3 - particles loop
    config["source_environment"] = src_env
    config["all_particles"] = particles

    # 3.1 - Gammas' offsets

    # 4 - Stages to be run
    config["stages_to_run"] = stages_to_be_run
    config["merging_no_image"] = merging_options

    # 5 - production workflow and type
    config["workflow_kind"] = workflow_kind
    config["prod_type"] = prod_type

    # 6 - Global paths
    if prod_type == "prod3":
        pointing_zenith = pointing
        config["gamma_offs"] = None

    else:  # Prod5
        # TODO correct the path for all the prod5_* at the LP_cluster
        #  as they were run as $ZENITH/$POINTING instead of $POINTING/$ZENITH/
        pointing_zenith = os.path.join(zenith, pointing)
        config["gamma_offs"] = offset_gammas

    if base_path_dl0:
        if workflow_kind == "lstchain" or workflow_kind == "ctapipe":
            config["DL0_input_dir"] = create_path(
                base_path_dl0, "DL0", obs_date, pointing_zenith
            )
        else:  # RTA
            config["DL0_input_dir"] = create_path(
                base_path_dl0, "R0", obs_date, pointing_zenith
            )
    elif base_path_dl1:
        config["DL1_input_dir"] = create_path(
            base_path_dl1, "DL1", obs_date, pointing_zenith, dl1_reference_id
        )

    directories = {
        "running_analysis_dir": "running_analysis",
        "analysis_log_dir": "analysis_logs",
        "DL1_output_dir": "DL1",
        "DL2_output_dir": "DL2",
    }
    for key, value in directories.items():
        config[key] = create_path(
            base_path_dl0, value, obs_date, pointing_zenith, config["prod_id"]
        )

    config["IRF_output_dir"] = create_path(
        base_path_dl0,
        "IRF",
        obs_date,
        pointing_zenith,
        config["prod_id"],
        particles=False,
    )
    # small difference if the user is the lstanalyzer
    config["model_output_dir"] = create_path(
        "fefs/aswg/data" if base_path_dl0 == "/fefs/aswg/data/mc" else base_path_dl0,
        "models",
        obs_date,
        pointing_zenith,
        config["prod_id"],
        particles=False,
    )
    return config
