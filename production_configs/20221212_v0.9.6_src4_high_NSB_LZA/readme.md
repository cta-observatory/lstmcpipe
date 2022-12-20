# Source with dec 6166 at LZA and NSB tuning

## 20221212

LZA production as 20221025_src4_high_NSB_LZA but with lstchain release 0.9.6

## Short description of the config

Config for a source src4 with dec 6166 and NSB tuning corresponding or pedestal std 1.9 pe (reference run 8649, zd=65.5, reference MC simtel_corsika_theta_65.796_az_31.344_run1.simtel.gz)


{
  "increase_nsb": true,
  "extra_noise_in_dim_pixels": 2.124,
  "extra_bias_in_dim_pixels": 0.738,
  "transition_charge": 8,
  "extra_noise_in_bright_pixels": 2.766
}


Config generated with:
```
from lstmcpipe.config import paths_config
import astropy.units as u

config = paths_config.PathConfigAllSkyFullDL1ab('20221212_v0.9.6_src4_high_NSB_LZA', '20221027_v0.9.9_base_prod', ['dec_6166'])

mask_train = config.train_configs['dec_6166']._training_pointings['alt'] < 38 *u.deg
mask_test = config.test_configs['dec_6166']._testing_pointings['alt'] < 38 *u.deg

config.test_configs['dec_6166']._testing_pointings = config.test_configs['dec_6166']._testing_pointings[mask_test]
config.train_configs['dec_6166']._training_pointings = config.train_configs['dec_6166']._training_pointings[mask_train]

config.generate()

config.save_yml('lstmcpipe_config_2022-11-02_PathConfigAllSkyFullDL1ab.yaml', overwrite=True)

```

Plot:
```
config.plot_pointings()
```
