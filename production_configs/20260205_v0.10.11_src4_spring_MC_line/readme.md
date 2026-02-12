# Source with dec 6166 and Spring atmosphere at LZA and NSB tuning

## 20260205

Production on the diffuse gammas for test with the 6166 line produced with Spring atmosphere(dec_6166/spring_atmospheric_profile) and with to NSB of the LZA data 

## Short description of the config

Config for a source src4 with line dec_6166/spring_atmospheric_profile and NSB tuning corresponding or pedestal std 1.9 pe (reference run 8649, zd=65.5, reference MC simtel_corsika_theta_65.796_az_31.344_run1.simtel.gz). The lstchain config is equal to the one of production 20240529_v0.10.11_src4_dense_MC_line

```json
{
  "increase_nsb": true,
  "extra_noise_in_dim_pixels": 2.124,
  "extra_bias_in_dim_pixels": 0.738,
  "transition_charge": 8,
  "extra_noise_in_bright_pixels": 2.766
}
```


The lstmcpipe config is produced as following:


```
from lstmcpipe.config.paths_config import PathConfigAllSkyTesting

cfg = PathConfigAllSkyTesting('20260202_prod_spring', 'dec_6166')
cfg.testing_dir = '/fefs/aswg/data/mc/DL0/LSTProd2/TrainingDataset/GammaDiffuse/dec_6166/spring_atmospheric_profile/sim_telarray/{pointing}/output_v1.4'
generated_paths = cfg.generate()
cfg.save_yml('20260202_prod_spring_config_ori.yml',overwrite=True)

```
 
 We have then replaced the path model with the one of the high density line /fefs/aswg/data/models/AllSky/20240519_v0.10.11_src4_dense_MC_line/dec_6166_high_density 
 

Plot:
```
cfg.plot_pointings()
```
