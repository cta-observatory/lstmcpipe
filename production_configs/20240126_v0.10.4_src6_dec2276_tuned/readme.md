# New Prod Config

## Prod_ID

20240126_v0.10.4_src6_dec2276_tuned

## Short description of the config

Config for the processing of MC at dec_2276 with NSB tuning to src6 and src-dependent configuration using a specific NSB tunning for the source.

## Why this config is needed

Reprocess the data at declination 22.76 with version of lstchain v0.10.4 and with new tunning for new source: src6.

## Other information


### command-line:
```
lstmcpipe_generate_config PathConfigAllSkyFullDL1ab --prod_id 20240126_v0.10.4_src6_dec2276_tuned --kwargs source_prod_id=20230901_v0.10.4_allsky_base_prod --dec_list dec_2276
```
