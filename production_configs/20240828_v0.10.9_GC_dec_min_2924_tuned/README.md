# Prod 20240828_v0.10.9_GC_dec_min_2924_tuned

## Description of the config

"image_modifier": {
    "increase_nsb": true,
    "extra_noise_in_dim_pixels": 2.98,
    "extra_bias_in_dim_pixels": 0.858,
    "transition_charge": 8,
    "extra_noise_in_bright_pixels": 3.989
    }

## lstchain_tune_nsb command

```
lstchain_tune_nsb --config standard_lstchain_config.json --input-mc /fefs/aswg/data/mc/DL0/LSTProd2/TrainingDataset/Protons/dec_min_2924/sim_telarray/node_corsika_theta_69.813_az_217.303_/output_v1.4/simtel_corsika_theta_69.813_az_217.303_run10.simtel.gz --input-data /fefs/aswg/data/real/DL1/20220502/v0.9/tailcut84/dl1_LST-1.Run08079.0035.h5 -o tuned_lstchain_config.json
```

## lstmcpipe config command

```
lstmcpipe_generate_config PathConfigAllSkyFullDL1ab --dec_list dec_min_2924 --prod_id 20240906_v0.10.9_GC_dec_min_2924_tuned  --kwargs source_prod_id=20240131_allsky_v0.10.5_all_dec_base
```

Then used the script below to add time and nice options to each step.

```
python add_slurm_options.py lstmcpipe_config_2024-09-06_PathConfigAllSkyFullDL1ab.yaml 
```

## Why this production is needed?

To analyze the Galactic Center data at dec_min_2924.
