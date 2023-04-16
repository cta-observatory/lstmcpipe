# prod 20230414_v0.9.13_dec_931_az_tel

Reprocessing of faulty dec_931.
This production should be used instead of `20230127_v0.9.12_base_prod_az_tel` for dec_931.

See related issues:
- https://github.com/cta-observatory/lstmcpipe/issues/371
- https://github.com/cta-observatory/lst-sim-config/issues/55


The config was generated using:

```
lstmcpipe_generate_config PathConfigAllSkyFull --prod_id 20230414_v0.9.13_dec_931_az_tel --output lstmcpipe_config.yml --overwrite --lstchain_conf lstchain_config.json --dec_list dec_931
```

After failure of the merging step, the faulty DL1 files were removed to allow proper merging and the processing was started again, commenting the r0_to_dl1 step.
