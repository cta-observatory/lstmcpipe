# PROD 20221021_crab_full_lstchain097

Full pipeline for Crab (dec_2276) with latest lstchain release v0.9.7

Generated with:

```
lstmcpipe_generate_config PathConfigAllSkyFull --prod_id 20221021_crab_full_lstchain097 --dec_list dec_2276
```

Added to lstchain config:
```
"image_modifier": {
    "increase_nsb": true,
    "extra_noise_in_dim_pixels": 1.62,
    "extra_bias_in_dim_pixels": 0.655,
    "transition_charge": 8,
    "extra_noise_in_bright_pixels": 2.08,
    "increase_psf": false,
    "smeared_light_fraction": 0
  },
```
