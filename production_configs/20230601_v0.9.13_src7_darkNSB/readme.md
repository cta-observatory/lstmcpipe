# New Prod Config

## Prod_ID

20230601_v0.9.13_src7_darkNSB

## Short description of the config

Reprocess production of 20230601_v0.9.13_dec_4822_dec_6166 matching the NSB noise to source 7 in dark conditions.

## Why this config is needed

Add NSB noise to match the NSB in the FoV of source 7 in the production 20230601_v0.9.13_dec_4822_dec_6166

## Command used to produce the lstmcpipe config

`lstmcpipe_generate_config PathConfigAllSkyFullDL1ab --dec_list dec_4822 dec_6166 --prod_id 20230601_v0.9.13_src7_darkNSB --kwargs source_prod_id=20230601_v0.9.13_dec_4822_dec_6166`

Also, I increased the memory for the DL2 to IRF stage o 100 GB following the fix memory issue in prod. 20230329_v0.9.13_src4_full_line.
