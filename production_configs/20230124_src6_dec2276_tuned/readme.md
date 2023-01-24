# New Prod Config

## Prod_ID

20230124_src6_dec2276_tuned

## Short description of the config

dec_2276 with NSB tuning to src6 and src-dependent configuration.

## Why this config is needed

Reprocess the data at declination 22.76 with version of lstchain v0.9.12 and with new tunning for new source: src6.

## Other information


### command-line:
```
lstmcpipe_generate_config PathConfigAllSkyFullDL1ab --prod_id 20230124_src6_dec2276_tuned --dec_list dec_2276 --kwargs source_prod_id=20221215_v0.9.12_base_prod
```
