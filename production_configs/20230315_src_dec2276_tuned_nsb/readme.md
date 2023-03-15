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
The configuration file for lstchain included in this directory is the same used to compute the NSB, i.e. `lstchain_config_v0.9.4_from2022onwards.json`, with lstchain script `lstchain_tune_nsb`.

## Why this config is needed 

Processing of data taken from this galactic source which has a particular NSB level.
