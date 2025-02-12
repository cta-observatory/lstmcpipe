import yaml
import os
import glob

# Define the directories to process
directories = glob.glob("NSB-*")

for dir_name in directories:
    yaml_files = glob.glob(os.path.join(dir_name, "lstmcpipe_*.yml"))

    for yaml_file in yaml_files:
        with open(yaml_file, "r") as f:
            data = yaml.safe_load(f)

        # Keep only the required stages
        if "stages" in data:
            data["stages"] = {
                key: value for key, value in data["stages"].items()
                if key in ["dl1_to_dl2", "dl2_to_irfs"]
            }

        # Keep only required stages in stages_to_run
        if "stages_to_run" in data and isinstance(data["stages_to_run"], list):
            data["stages_to_run"] = [
                stage for stage in data["stages_to_run"]
                if stage in ["dl1_to_dl2", "dl2_to_irfs"]
            ]

        # Update specific key-value pairs
        if "prod_id" in data and isinstance(data["prod_id"], str):
            data["prod_id"] = data["prod_id"].replace(
                "20240918_v0.10.12_allsky_nsb_tuning_", 
                "20250212_v0.10.17_allsky_interp_dl2_irfs_nsb_"
            )

        if "lstmcpipe_version" in data and isinstance(data["lstmcpipe_version"], str):
            data["lstmcpipe_version"] = "0.11.3"

        if "source_environment" in data and isinstance(data["source_environment"], dict):
            if "source_file" in data["source_environment"]:
                data["source_environment"]["source_file"] = "/fefs/aswg/software/conda/etc/profile.d/conda.sh"
            if "conda_env" in data["source_environment"]:
                data["source_environment"]["conda_env"] = "lstchain-v0.10.17"

        # Function to replace paths recursively
        def replace_paths(value):
            if isinstance(value, str):
                value = value.replace(
                    "/fefs/aswg/data/mc/DL2/AllSky/20240918_v0.10.12_allsky_nsb_tuning_",
                    "/fefs/aswg/data/mc/DL2/AllSky/20250212_v0.10.17_allsky_interp_dl2_irfs_nsb_"
                )
                value = value.replace(
                    "/fefs/aswg/data/mc/IRF/AllSky/20240918_v0.10.12_allsky_nsb_tuning_",
                    "/fefs/aswg/data/mc/IRF/AllSky/20250212_v0.10.17_allsky_interp_dl2_irfs_nsb_"
                )
                return value
            elif isinstance(value, list):
                return [replace_paths(v) for v in value]
            elif isinstance(value, dict):
                return {k: replace_paths(v) for k, v in value.items()}
            return value

        # Apply path replacements recursively
        data = replace_paths(data)

        # Write the modified YAML back to the file
        with open(yaml_file, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        print(f"Processed {yaml_file} ✅")
