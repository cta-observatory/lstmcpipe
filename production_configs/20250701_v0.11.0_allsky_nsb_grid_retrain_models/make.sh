#!/bin/bash

# Define the base production ID prefix
BASE_PROD_ID_PREFIX="20240918_v0.10.12_allsky_nsb_tuning_"

# List of NSB levels (the last 4 characters of the prod_id)
NSB_LEVELS=(
    "0.00"
    "0.07"
    "0.14"
    "0.22"
    "0.38"
    "0.50"
    "0.81"
    "1.25"
    "1.76"
    "2.34"
)


# Define the common lstmcpipe_generate_config command parts
DEC_LIST="dec_2276 dec_3476 dec_4822 dec_6166 dec_6676 dec_931 dec_min_1802 dec_min_2924 dec_min_413"
LSTMCPIPE_COMMAND_BASE="lstmcpipe_generate_config PathConfigAllTrainTestDL1b --dec_list $DEC_LIST --prod_id 20250701_v0.11.0_allsky_models_nsb_X.XX --kwargs source_prod_id=PROD_ID --overwrite"

# Loop through each NSB level
for nsb_level in "${NSB_LEVELS[@]}"; do
    # Construct the full prod_id for the current NSB level
    current_prod_id="${BASE_PROD_ID_PREFIX}${nsb_level}"

    # Construct the directory name
    dir_name="NSB-${nsb_level}"

    echo "Processing prod_id: ${current_prod_id}"
    echo "Creating directory: ${dir_name}"

    # Create the directory
    mkdir -p "${dir_name}"

    # Check if the directory was created successfully
    if [ $? -ne 0 ]; then
        echo "Error: Could not create directory ${dir_name}. Skipping this NSB level."
        continue
    fi

    # Go inside the directory
    pushd "${dir_name}" || { echo "Error: Could not enter directory ${dir_name}. Skipping this NSB level."; continue; }

    # Replace placeholders in the lstmcpipe command
    # Replace X.XX with the current nsb_level for the output prod_id
    # Replace PROD_ID with the source prod_id
    executed_command=$(echo "${LSTMCPIPE_COMMAND_BASE}" | sed "s/X.XX/${nsb_level}/g" | sed "s/PROD_ID/${current_prod_id}/g")

    echo "Running command: ${executed_command}"

    # Execute the lstmcpipe command
    eval "${executed_command}"

    # Check if the command ran successfully
    if [ $? -ne 0 ]; then
        echo "Warning: lstmcpipe command failed for prod_id ${current_prod_id}."
    fi

    # Go back to the original directory
    popd

    echo "----------------------------------------"
done

echo "Script finished."
