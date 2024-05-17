# New Product Configuration for src9

## Prod_ID

20240430_v0.10.4_src9_dec3476_tuned

##  Description

Config for training RF splitting Gamma Diffuse MC datasets in halves for the declination line of 34.76 deg. 

NSB tuning adapted to the observed data of src9.

## Objective

Prepare full enclosure IRFs for src9.

## Config file creation

The config file was initially cretaed by using lstmcpipe_generate_config:
    lstmcpipe_generate_config PathConfigAllSkyFull --prod_id 20240430_v0.10.4_src9_dec3476_tuned --dec_list dec_3476

Then, some manually changes were added in order to split the datasets and add the specific NSB tuning configuration parameters.
