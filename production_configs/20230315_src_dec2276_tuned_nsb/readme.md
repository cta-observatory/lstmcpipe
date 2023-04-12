# New Prod Config 

## 20230315

## Short description of the config

Config for a galactic source with dec 22.47 and NSB tuning:

"image_modifier": {
        "increase_nsb": true,
        "extra_noise_in_dim_pixels": 1.309,
        "extra_bias_in_dim_pixels": 0.54,
        "transition_charge": 8,
        "extra_noise_in_bright_pixels": 1.79
    }
The NSB parameters have been computed by using lstchain script `lstchain_tune_nsb` with configuration file `lstchain_config_v0.9.4_from2022onwards.json`.

The configuration file for lstchain and lstmcpipe included in this directory have been produced by running
```
source /fefs/aswg/software/conda/etc/profile.d/conda.sh

conda activate lstchain-v0.9.13

lstmcpipe_generate_config PathConfigAllSkyFullDL1ab --dec_list dec_2276 --prod_id 20230315_src_dec2276_tuned_nsb --kwargs source_prod_id=20230315_src_dec2276_tuned_nsb
```

## Why this config is needed 

Processing of data taken from this galactic source which has a particular NSB level.
