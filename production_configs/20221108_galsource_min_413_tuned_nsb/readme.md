# New Prod Config

## Prod_ID

20221108_galsource_min_413_tuned_nsb

## Short description of the config

dec_min_413 with NSB tuning to galactic source (src1).

## Why this config is needed

Reprocess with the latest version of lstchain v0.9.9. Previous prod_id is `galsource_min_413_tuned_nsb`.

## Other information

RF features following issue #369

### command-line:
```
lstmcpipe_generate_config PathConfigAllSkyFullDL1ab --prod_id 20221108_galsource_min_413_tuned_nsb --kwargs source_prod_id=20221027_v0.9.9_base_prod --dec_list dec_min_413
```
