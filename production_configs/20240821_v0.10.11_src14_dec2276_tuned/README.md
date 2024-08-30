
# New Prod Config

## Prod_ID

20240821_v0.10.11_src14_tuned

## Description

full DL1ab production (with NSB tuning for src14) with lstchain v0.10.11

NSB level was checked in the following way:

```
input_mc = /fefs/aswg/data/mc/DL0/LSTProd2/TrainingDataset/Protons/dec_2276/sim_telarray/node_theta_6.000_az_180.000_/output_v1.4/simtel_corsika_theta_6.000_az_180.000_run10.simtel.gz

input_data = /fefs/aswg/data/real/DL1/20240613/v0.10/tailcut84/dl1_LST-1.Run17799.0016.h5

print("this config was downloaded (and modified) on %s" % download_config_modified_time)
config_file = Path("./lstchain_standard_config.json")

lstchain_tune_nsb --config standard_lstchain_config.json --input-mc /fefs/aswg/data/mc/DL0/LSTProd2/TrainingDataset/Protons/dec_2276/sim_telarray/node_theta_6.000_az_180.000_/output_v1.4/simtel_corsika_theta_6.000_az_180.000_run10.simtel.gz --input-data /fefs/aswg/data/real/DL1/20240613/v0.10/tailcut84/dl1_LST-1.Run17799.0016.h5 -o tuned_lstchain_config.json

## Why this config is needed

Analysis of future data taken on src14

## Config file creation

The config file was initially cretaed by using lstmcpipe_generate_config:
'''
lstmcpipe_generate_config PathConfigAllSkyFullDL1ab --dec_list dec_2276 --prod_id 20240821_v0.10.11_src14_dec2276_tuned --kwargs source_prod_id=20240131_allsky_v0.10.5_all_dec_base
