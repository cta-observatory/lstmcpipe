# New Prod Config

## Prod_ID

20230601_v0.9.13_dec_4822_dec_6166

## Short description of the config

Create a production with lstchain-v0.9.13 with all testing nodes for dec_4822 and dec_6166. The stage r0_to_dl1 is the only stage used because this production will be used as the base prod. to latter tune the NSB.

## Why this config is needed

Processing of source 7 with MC processed with lstchain-v0.9.13 for dec. bands dec_4822 and dec_6166 with all available testing nodes.

## Command used to produce the lstmcpipe config

`lstmcpipe_generate_config PathConfigAllSkyFull --prod_id 20230601_v0.9.13_dec_4822_dec_6166 --dec_list dec_4822 dec_6166`

Also, I removed the stages merge_dl1, train_pipe, dl1_to_dl2 and dl2_to_irfs from the lstmcpipe config file.
