# New Prod Config

## Prod_ID

20221128_src5_dec3476_tuned

## Short description of the config

dec_3476 with NSB tuning to src5 and src-dependent configuration.

## Why this config is needed

Reprocess the data at declination 34.76 with version of lstchain v0.9.9 and with new tunning for new source: src5.

## Other information


### command-line:
```
lstmcpipe_generate_config PathConfigAllSkyFullDL1ab --prod_id 20221128_src5_dec3476_tuned  --dec_list dec_3476 --kwargs source_prod_id=20221027_v0.9.9_base_prod
```
