# PROD 20240917_v0.10.12_src15_dec_min_2924_tuned

I need this production to analyse the LST-1 data of src15 (see https://www.lst1.iac.es/wiki/index.php/MC_analysis_and_IRF_production#lstmcpipe_productions) with dec 29.24 deg. The median of the NSB standard deviation for this dataset is approximately 2.308 p.e.

```
lstmcpipe_generate_config PathConfigAllSkyFullDL1ab --dec_list dec_min_2924 --prod_id 20240917_v0.10.12_src15_dec_min_2924_tuned --kwargs source_prod_id=20240131_allsky_v0.10.5_all_dec_base
```

Config for the NSB tuning:

```
"image_modifier": {
    "increase_nsb": true,
    "extra_noise_in_dim_pixels": 3.843,
    "extra_bias_in_dim_pixels": 1.07,
    "transition_charge": 8,
    "extra_noise_in_bright_pixels": 5.178
  }
```

Contact: Lisa N
