# Source with dec 6166 at LZA and NSB tuning

## 20230329

Production on the full node (but still with some nodes missing) and with to NSB of the LZA data 

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

```

Plot:
```
config.plot_pointings()
```
