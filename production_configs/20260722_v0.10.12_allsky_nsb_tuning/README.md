
Steps:

```
conda activate lstchain-v0.12.3
```

1. run `./step_1_symlink_dl1.sh` to create test DL1 dataset
2. run `./step2_merge_dl1.sh` and wait for jobs to be done
3. run `lstmcpipe_generate_nsb_levels_configs --dec_list dec_6166_high_density --nsb_ratios 0.07 0.14 0.22 0.38 0.50`
4. run `./modify_configs.sh`
5. run `lstmcpipe -c lstmcpipe_config.yaml -conf_lst lstchain_conf.json` for each NSB
