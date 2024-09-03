# Source with dec 6166 at LZA and NSB tuning

## 20240529

Production on the full high density line (dec_6166_high_density) with all nodes and with to NSB of the LZA data 

## Short description of the config

Config for a source src4 with line dec_6166_high_density and NSB tuning corresponding or pedestal std 1.9 pe (reference run 8649, zd=65.5, reference MC simtel_corsika_theta_65.796_az_31.344_run1.simtel.gz)


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

    MC_line='dec_6166_high_density'

    config = paths_config.PathConfigAllSkyFull('20240519_v0.10.11_src4_dense_MC_line', [MC_line])

    config.stages = [
            'r0_to_dl1',
            'merge_dl1',
            'train_pipe',
            'dl1_to_dl2']

    _=config.generate()

    # mask tests too far from the training nodes
    train_zd=90*u.deg-config.train_configs[MC_line]._training_pointings['alt']
    train_az=config.train_configs[MC_line]._training_pointings['az']

    n_test_points=len(config.test_configs[MC_line]._testing_pointings)
    mask_test=np.zeros(n_test_points,dtype=bool)
    for point in np.arange(n_test_points):
 
        zd=90*u.deg-config.test_configs[MC_line]._testing_pointings['alt'][point]
        az=config.test_configs[MC_line]._testing_pointings['az'][point]
 
    
        for test in np.arange(len(train_zd)):
            dist=angular_separation(az,zd,train_az[test],train_zd[test])
        
            if dist < 1.*u.deg:
                print(f"dist {dist} keep {test_zd[test]:6.2f} {zd:6.2f}")
                mask_test[point]=True
       

    # select only the on line tests
    config.test_configs[MC_line]._testing_pointings=config.test_configs[MC_line]_testing_pointings = config.test_configs[MC_line]._testing_pointings[mask_test]


}

 



```

Plot:
```
config.plot_pointings()
```
