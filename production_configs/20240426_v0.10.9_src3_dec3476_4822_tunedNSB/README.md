# Source with dec 3476/4822 and NSB tuning for moon data (x3-4 the previous production, which was made to reproduce the specific dark background of the source due to its proximity to the galactic plane). The mean_diffuse_nsb_std for this dataset is approximately 3 p.e.

## Prod_ID
20240426_v0.10.9_src3_dec3476_4822_tunedNSB

## 20240426
lstmcpipe_generate_config PathConfigAllSkyFull --prod_id 20240426_v0.10.9_src3_dec3476_4822_tunedNSB --dec_list dec_3476 dec_4822

## Short description of the config

Config for a source with dec within 3476/4822 and NSB tuning:

    "image_modifier": {
       "increase_nsb": true,
       "extra_noise_in_dim_pixels": 6.974,
       "extra_bias_in_dim_pixels": 1.825,
       "transition_charge": 8,
       "extra_noise_in_bright_pixels": 4.195
    }	

## Why this config is needed 

See wiki page (src 3)
https://www.lst1.iac.es/wiki/index.php/MC_analysis_and_IRF_production#lstmcpipe_productions
