
# New Prod Config

## Prod_ID

20240727_v0.10.11_src12_tuned

## Short description of the config

full DL1ab production (with NSB tuning for src12) with lstchain v0.10.11

NSB level was checked in the following way:

```
input_mc_base = Path("/fefs/aswg/data/mc/DL0/LSTProd2/TrainingDataset/GammaDiffuse/")
input_mc = input_mc_base / "dec_min_413/sim_telarray/node_corsika_theta_33.058_az_173.79_/output_v1.4/simtel_corsika_theta_33.058_az_173.79_run1.simtel.gz"

input_data_base = Path("/fefs/aswg/data/real/DL1/")
input_data = input_data_base / "20240701/v0.10/tailcut84/dl1_LST-1.Run17967.0000.h5"

print("this config was downloaded (and modified) on %s" % download_config_modified_time)
config_file = Path("./lstchain_standard_config.json")

!lstchain_tune_nsb --input-mc $input_mc --input-data $input_data --config $config_file
```


The resulting values are the followings:

```
this config was downloaded (and modified) on 2024-07-27 10:21:03

Real data:
   Number of bad pixels (from calibration): 13
   Median of FF pixel charge: 75.561 p.e.
   Median across camera of good pixels' pedestal std 2.217 p.e.
   Number of pixels beyond 3 std dev of median:    34, (above 2.73 p.e.)
Good and not too bright pixels: 1812


{
  "increase_nsb": true,
  "extra_noise_in_dim_pixels": 1.297,
  "extra_bias_in_dim_pixels": 0.385,
  "transition_charge": 8,
  "extra_noise_in_bright_pixels": 1.536
}
```

These are pasted on the lstchain_config_2024-07-27.json.

contact: Hideaki Katagiri

## Why this config is needed

Reprocess the data of src12 with version of lstchain v0.10.11 and with NSB tunning.

## Other information

### command-line:
```
prod_id = "20240727_v0.10.11_src12_tuned"
dec_list = "dec_min_413" # declination=-4.13, Decl. of G17.8+16.8 = -5.145
source_prod_id = "20240131_allsky_v0.10.5_all_dec_base"
!lstmcpipe_generate_config PathConfigAllSkyFullDL1ab --overwrite --prod_id $prod_id --kwargs source_prod_id=$source_prod_id --dec_list $dec_list
```
