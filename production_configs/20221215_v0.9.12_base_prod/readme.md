# New Prod Config

## template_prod

## Short description of the config

Full MC / model dataset with lstchain v0.9.12 standard settings

## Why this config is needed

Processing standard AGN data (+Crab) with recent lstchain (after the discussion in slack). Last full production with Models date from May 2022.
For now requesting a standard 'un-tuned' production to evaluate blind reconstruction and to test how a 'bad NSB setting' can spoil the SED.

Declination tracks needed:

dec_2276
dec_3476
dec_4822
dec_6676
dec_931
dec_min_413

Command to produce this request:

>> lstmcpipe_generate_config PathConfigAllSkyFull --prod_id 20221215_v0.9.12_base_prod --output lstmcpipe_config.yml --overwrite --lstchain_conf lstchain_config.json --dec_list dec_2276 dec_3476 dec_4822 dec_6676 dec_931 dec_min_413


## Note on dec_931
16/04/2023, T. Vuillaume.

dec_931 from this prod is faulty and thus should not be used!
Please use prod `20230414_v0.9.13_dec_931_az_tel` instead.
