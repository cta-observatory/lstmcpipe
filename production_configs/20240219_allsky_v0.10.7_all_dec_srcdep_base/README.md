# Prod 20240219_allsky_v0.10.7_all_dec_srcdep_base

Base production for all declinations lines with lstchain v0.10.7 & source-dependent approach


```
lstmcpipe_generate_config PathConfigAllTrainTestDL1b --dec_list dec_2276 dec_4822 dec_6166 dec_6676 dec_min_1802 dec_min_413 dec_931 dec_min_2924 dec_3476 --prod_id 20240219_allsky_v0.10.7_all_dec_srcdep_base --kwargs source_prod_id=20240131_allsky_v0.10.5_all_dec_base
```

```
lstchain_dump_config -o lstchain_config_2024-02-19_srcdep.json --mc --update-with lstchain_src_dep_config.json
```

contact: Seiya N.
