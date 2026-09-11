# symlink existing DL1 files from the 20240918 production into the 20260722 production, for each NSB tuning value (0.07, 0.14, 0.22, 0.38, 0.50).
./step_1_symlink_dl1.sh

# Merge the TestingDataset and TrainingDataset from the 20240918 production into a single TestingDataset in the 20260722 production.
python step_2_gen_config_merge_dl1.py
lstmcpipe -c lstmcpipe_merge_dl1_20260722_v0.10.12_allsky_nsb_tuning_0.07_dec_6166.yaml -conf_lst lstchain_config.json
lstmcpipe -c lstmcpipe_merge_dl1_20260722_v0.10.12_allsky_nsb_tuning_0.14_dec_6166.yaml -conf_lst lstchain_config.json
lstmcpipe -c lstmcpipe_merge_dl1_20260722_v0.10.12_allsky_nsb_tuning_0.22_dec_6166.yaml -conf_lst lstchain_config.json
lstmcpipe -c lstmcpipe_merge_dl1_20260722_v0.10.12_allsky_nsb_tuning_0.38_dec_6166.yaml -conf_lst lstchain_config.json
lstmcpipe -c lstmcpipe_merge_dl1_20260722_v0.10.12_allsky_nsb_tuning_0.50_dec_6166.yaml -conf_lst lstchain_config.json

# Create the lstmcpipe config files for the DL2 step, using the merged TestingDataset from the previous step.
./step_3_generate_testing_configs.sh

# generate training configs
lstmcpipe_generate_nsb_levels_configs --dec_list dec_6166_high_density --prod_id 20260722_v0.12.3 --nsb 0.07 0.14 0.22 0.38 0.50 --overwrite
./modify_training_config.sh

# run the training pipeline (r0_to_dl1, merge_dl1, train_pipe) for each NSB
lstmcpipe -c NSB-0.07/lstmcpipe_config_nsb0.07.yml -conf_lst NSB-0.07/lstchain_config_nsb0.07.json
lstmcpipe -c NSB-0.14/lstmcpipe_config_nsb0.14.yml -conf_lst NSB-0.14/lstchain_config_nsb0.14.json
lstmcpipe -c NSB-0.22/lstmcpipe_config_nsb0.22.yml -conf_lst NSB-0.22/lstchain_config_nsb0.22.json
lstmcpipe -c NSB-0.38/lstmcpipe_config_nsb0.38.yml -conf_lst NSB-0.38/lstchain_config_nsb0.38.json
lstmcpipe -c NSB-0.50/lstmcpipe_config_nsb0.50.yml -conf_lst NSB-0.50/lstchain_config_nsb0.50.json

# run the testing pipeline (dl1_to_dl2, dl2_to_irfs) for each NSB, once training is complete
lstmcpipe -c NSB-0.07/lstmcpipe_config_20260722_test_nsb0.07.yaml -conf_lst NSB-0.07/lstchain_config_nsb0.07.json
lstmcpipe -c NSB-0.14/lstmcpipe_config_20260722_test_nsb0.14.yaml -conf_lst NSB-0.14/lstchain_config_nsb0.14.json
lstmcpipe -c NSB-0.22/lstmcpipe_config_20260722_test_nsb0.22.yaml -conf_lst NSB-0.22/lstchain_config_nsb0.22.json
lstmcpipe -c NSB-0.38/lstmcpipe_config_20260722_test_nsb0.38.yaml -conf_lst NSB-0.38/lstchain_config_nsb0.38.json
lstmcpipe -c NSB-0.50/lstmcpipe_config_20260722_test_nsb0.50.yaml -conf_lst NSB-0.50/lstchain_config_nsb0.50.json
