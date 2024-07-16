# Product Configuration for src10

## Prod_ID

20240716_v0.10.7_src10_dec3476_tuned

##  Description

Config for reprocessing of Gamma Diffuse MC at declination line of 34.76 deg, based on 20240430_v0.10.4_src9_dec3476_tuned.

NSB tuning adapted to the observed data of src10.

## Objective

Need diffuse MC with tuning for new source: src10

## Config file creation

The config file was initially cretaed by using lstmcpipe_generate_config:
'''
lstmcpipe_generate_config PathConfigAllSkyFullDL1ab  --dec_list dec_3476 --prod_id 20240716_v0.10.7_src10_dec3476_tuned --kwargs source_prod_id=20240430_v0.10.4_src9_dec3476_tuned
'''

Added image_modifier to tune NSB to src10.
Manually edited to split dataset similar as 20240430_v0.10.4_src9_dec3476_tuned.
