# Source with dec 6166 at LZA and NSB tuning

## 20221025

LZA production: only nodes with zd> 52 deg are processed both for training and for test 

## Short description of the config

Config for a source src4 with dec 6166 and NSB tuning corresponding or pedestal std 1.9 pe (reference run 8649, zd=65.5, reference MC simtel_corsika_theta_65.796_az_31.344_run1.simtel.gz)


{
  "increase_nsb": true,
  "extra_noise_in_dim_pixels": 2.124,
  "extra_bias_in_dim_pixels": 0.738,
  "transition_charge": 8,
  "extra_noise_in_bright_pixels": 2.766
}


Config generated with:
```
lstmcpipe_generate_config PathConfigAllSkyFullDL1ab --dec_list dec_6166 --prod_id 20221025_src4_high_NSB_LZA --kwargs source_prod_id=20221027_v0.9.9_base_prod
```
