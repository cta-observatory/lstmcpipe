import json
import subprocess
import logging


log = logging.getLogger(__name__)


def create_dl1ab_tuned_config(base_config_path, config_output_path, observed_data_path, mc_path):
    """
    Create a new lstchain config with noise parameters added.
    If there are noise parameters in the input config,
    this will fail with an Exception.

    Parameters:
    -----------
    base_config_path: str or Path-like object
        Input config. Will not be overwritten.
    config_output_path: str or Path-like object
        Where to save the new config file.
    observed_data_path: str or Path-like object
        Path to a dl1 file with observed data from which to
        calculate the parameters.
    observed_mc_path: str or Path-like object
        Path to a dl1 file with simulated data from which to
        calculate the parameters.

    Return:
    -------
    config_output_path
    """
    with open(base_config_path) as f:
        base = json.load(f)

    log.info("Running lstchain_tune_nsb to get the noise tuning parameters")
    log.info(f"Comparing mc file {mc_path} and observed file {observed_data_path}")
    cmd = [
        "lstchain_tune_nsb",
        f"--config={base_config_path}",
        f"--input-mc={mc_path}",
        f"--input-data={observed_data_path}",
    ]
    res = subprocess.run(cmd, capture_output=True)
    # Log output is directed to stderr not stdout
    log_output = res.stderr.decode()

    # The script dumps the dict as the very last output
    dict_string = "{" + log_output.rsplit("{", -1)[-1].strip()

    # This should now load into json
    parameters = json.loads(dict_string)

    modifier_settings = base.get("image_modifier", {})
    for key, value in parameters.items():
        if key in modifier_settings:
            log.warning(
                f"Overwriting image modifier parameter {key} from the base config with " f"the new value {value}."
            )
        modifier_settings[key] = value
    base["image_modifier"] = modifier_settings

    with open(config_output_path, "w") as f:
        json.dump(base, f, indent=2)

    return config_output_path
