#!/usr/bin/bash

# script to reduce all MC production to DL1 at once.
# To be edited to change parameters.

config_file="lstchain_standard_config.json"
train_test_ratio="0.5"


proton_dl0_dir="/fefs/aswg/data/mc/DL0/20190415/proton/south_pointing/"
gamma_dl0_dir="/fefs/aswg/data/mc/DL0/20190415/gamma/south_pointing/"
gamma_diffuse_dl0_dir="/fefs/aswg/data/mc/DL0/20190415/gamma-diffuse/south_pointing/"
electron_dl0_dir="/fefs/aswg/data/mc/DL0/20190415/electron/south_pointing/"


python onsite_mc_r0_to_dl1.py $proton_dl0_dir -conf $config_file -ratio $train_test_ratio
python onsite_mc_r0_to_dl1.py $gamma_dl0_dir -conf $config_file -ratio $train_test_ratio
python onsite_mc_r0_to_dl1.py $gamma_diffuse_dl0_dir -conf $config_file -ratio $train_test_ratio
python onsite_mc_r0_to_dl1.py $electron_dl0_dir -conf $config_file -ratio $train_test_ratio
