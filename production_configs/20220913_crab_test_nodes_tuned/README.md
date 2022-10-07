# 20220913_crab_test_nodes_tuned

All test nodes analysed for Crab: NSB tuning and models trained at dec_2276


```
lstmcpipe_generate_config PathConfigAllSkyTestingDL1ab --prod_id 20220902_crab_test_nodes --kwargs target_prod_id=20220913_crab_test_nodes_tuned dec=dec_2276
```

Then replaced path models with `/fefs/aswg/data/models/AllSky/20220518_allsky_dec2276_tuned/dec_2276` 



Error during merging, restarted by hand the following:


```
lstchain_merge_hdf5_files -d /fefs/aswg/data/mc/DL1/AllSky/20220913_crab_test_nodes_tuned/TestingDataset/node_theta_14.984_az_175.158_/ -o /fefs/aswg/data/mc/DL1/AllSky/20220913_crab_test_nodes_tuned/TestingDataset/dl1_20220913_crab_test_nodes_tuned_node_theta_14.984_az_175.158__merged.h5 --no-image


lstchain_merge_hdf5_files -d /fefs/aswg/data/mc/DL1/AllSky/20220913_crab_test_nodes_tuned/TestingDataset/node_theta_32.059_az_102.217_/ -o /fefs/aswg/data/mc/DL1/AllSky/20220913_crab_test_nodes_tuned/TestingDataset/dl1_20220913_crab_test_nodes_tuned_node_theta_32.059_az_102.217__merged.h5 --no-image

lstchain_merge_hdf5_files -d /fefs/aswg/data/mc/DL1/AllSky/20220913_crab_test_nodes_tuned/TestingDataset/node_theta_32.059_az_355.158_/ -o /fefs/aswg/data/mc/DL1/AllSky/20220913_crab_test_nodes_tuned/TestingDataset/dl1_20220913_crab_test_nodes_tuned_node_theta_32.059_az_355.158__merged.h5 --no-image

lstchain_merge_hdf5_files -d /fefs/aswg/data/mc/DL1/AllSky/20220913_crab_test_nodes_tuned/TestingDataset/node_theta_43.197_az_143.441_/ -o /fefs/aswg/data/mc/DL1/AllSky/20220913_crab_test_nodes_tuned/TestingDataset/dl1_20220913_crab_test_nodes_tuned_node_theta_43.197_az_143.441__merged.h5 --no-image

lstchain_merge_hdf5_files -d /fefs/aswg/data/mc/DL1/AllSky/20220913_crab_test_nodes_tuned/TestingDataset/node_theta_43.197_az_230.005_/ -o /fefs/aswg/data/mc/DL1/AllSky/20220913_crab_test_nodes_tuned/TestingDataset/dl1_20220913_crab_test_nodes_tuned_node_theta_43.197_az_230.005__merged.h5 --no-image

lstchain_merge_hdf5_files -d /fefs/aswg/data/mc/DL1/AllSky/20220913_crab_test_nodes_tuned/TestingDataset/node_theta_52.374_az_175.158_/ -o /fefs/aswg/data/mc/DL1/AllSky/20220913_crab_test_nodes_tuned/TestingDataset/dl1_20220913_crab_test_nodes_tuned_node_theta_52.374_az_175.158__merged.h5 --no-image


lstchain_merge_hdf5_files -d /fefs/aswg/data/mc/DL1/AllSky/20220913_crab_test_nodes_tuned/TestingDataset/node_theta_60.528_az_223.818_/ -o /fefs/aswg/data/mc/DL1/AllSky/20220913_crab_test_nodes_tuned/TestingDataset/dl1_20220913_crab_test_nodes_tuned_node_theta_60.528_az_223.818__merged.h5 --no-image

lstchain_merge_hdf5_files -d /fefs/aswg/data/mc/DL1/AllSky/20220913_crab_test_nodes_tuned/TestingDataset/node_theta_68.068_az_175.158_/ -o /fefs/aswg/data/mc/DL1/AllSky/20220913_crab_test_nodes_tuned/TestingDataset/dl1_20220913_crab_test_nodes_tuned_node_theta_68.068_az_175.158__merged.h5 --no-image
```


