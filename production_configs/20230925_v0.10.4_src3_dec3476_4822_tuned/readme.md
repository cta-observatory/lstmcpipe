
# New Prod Config

## Prod_ID

20230925_v0.10.4_src3_dec3476_4822_tuned

## Short description of the config

full DL1ab production (dec3476 and dec4822 with NSB tuning for src3) with lstchain v0.10.4

contact: Seiya Nozaki

## Why this config is needed

Reprocess the data at declination 34.76 and 48.22 with version of lstchain v0.10.4 and with tunning for src3.

## Other information

### command-line:
```
lstmcpipe_generate_config PathConfigAllSkyFullDL1ab --prod_id 20230925_v0.10.4_src3_dec3476_4822_tuned --kwargs source_prod_id=20230901_v0.10.4_allsky_base_prod --dec_list dec_3476 dec_4822
```
