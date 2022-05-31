Allsky MC production, with nsb tuning, for the dec_4822 declination band.

Config files:
- lstmcpipe_config_2022-05-24_PathConfigAllSkyFullDL1ab.yaml
- lstchain_config_2022-05-24.json

The command used for generating the config files is:

"lstmcpipe_generate_config PathConfigAllSkyFullDL1ab --prod_id 24_05_2022_dec_4822 --kwargs source_prod_id=20220511_allsky_std --dec_list dec_4822 --overwrite"

In a second moment I changed the prod_id (everywhere) by hand, from "24_05_2022" to "24_05_2022_dec_4822"

The source for which this production is required is "src2"