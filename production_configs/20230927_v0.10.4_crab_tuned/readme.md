
# New Prod Config

## Prod_ID

20230927_v0.10.4_crab_tuned

## Short description of the config

full DL1ab production (with NSB tuning for Crab) with lstchain v0.10.4

NSB level was checked in the following way:

input_mc = Path("/fefs/aswg/data/mc/DL0/LSTProd2/TrainingDataset/GammaDiffuse/dec_2276/sim_telarray/node_corsika_theta_6.000_az_180.000_/output_v1.4/simtel_corsika_theta_6.000_az_180.000_run1.simtel.gz")
input_data = Path("/fefs/aswg/data/real/DL1/20221201/v0.9/tailcut84/dl1_LST-1.Run11282.0000.h5")
print("this config is commit ac7d379 on Sep 14, 2023 ")
config_file = Path("./lstchain_standard_config.json")
!lstchain_tune_nsb --input-mc $input_mc --input-data $input_data --config $config_file

The resulting values are the followings:

this config is commit ac7d379 on Sep 14, 2023 
Real data: median across camera of good pixels' pedestal std 2.633 p.e.
Number of pixels beyond 3 std dev of median: 34, (above 3.82 p.e.)
Good and not too bright pixels: 1811


{
  "increase_nsb": true,
  "extra_noise_in_dim_pixels": 2.197,
  "extra_bias_in_dim_pixels": 0.82,
  "transition_charge": 8,
  "extra_noise_in_bright_pixels": 2.88
}


These are pasted on the lstchain_config_2023-09-27.json.


contact: Hideaki Katagiri

## Why this config is needed

Reprocess the data of Crab with version of lstchain v0.10.4 and with tunning.

## Other information

### command-line:
```
prod_id = "20230927_v0.10.4_crab_tuned"
dec_list = "dec_2276"
source_prod_id = "20230901_v0.10.4_allsky_base_prod"
!lstmcpipe_generate_config PathConfigAllSkyFullDL1ab --prod_id $prod_id --kwargs source_prod_id=$source_prod_id --dec_list $dec_list --overwrite
```
