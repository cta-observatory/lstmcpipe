# Source with dec 6166 at LZA and NSB tuning

## 20230529

Production on the full node with all nodes and with to NSB of the LZA data 

## Short description of the config

Config for a source src4 with dec 6166 and NSB tuning corresponding or pedestal std 1.9 pe (reference run 8649, zd=65.5, reference MC simtel_corsika_theta_65.796_az_31.344_run1.simtel.gz)


{
  "increase_nsb": true,
  "extra_noise_in_dim_pixels": 2.124,
  "extra_bias_in_dim_pixels": 0.738,
  "transition_charge": 8,
  "extra_noise_in_bright_pixels": 2.766
}

Only test nodes on the declination line are included

The config is produced as following:

{

    config = paths_config.PathConfigAllSkyFull('20230529_v0.9.13_src4_full_line', ['dec_6166'])
    config.generate()
    # mask test outside the line
    n_test_points=len(config.test_configs['dec_6166']._testing_pointings)
    mask_test=np.zeros(n_test_points,dtype=bool)
    for point in np.arange(n_test_points):
        zd=90*u.deg-config.test_configs['dec_6166']._testing_pointings['alt'][point]
        az=config.test_configs['dec_6166']._testing_pointings['az'][point]
    
        for test in np.arange(len(test_zd)):
            dist=angular_separation(az,zd,test_az[test]*u.deg,test_zd[test]*u.deg)
        
            if dist < 1.*u.deg:
                mask_test[point]=True
       
    # select only the on line tests   
    config.test_configs['dec_6166']._testing_pointings=config.test_configs['dec_6166']._testing_pointings = config.test_configs['dec_6166']._testing_pointings[mask_test]
    # generate again
    config.generate()

    config.save_yml('lstmcpipe_config_2023-05-29_PathConfigAllSkyFull.yaml', overwrite=True)



}

 



```

Plot:
```
config.plot_pointings()
```
