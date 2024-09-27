# allsky production with NSB grid


Production for all declination bands with a NSB-wise grid using the following parameters:

| NSB (p.e.) | Tailcut cleaning values |
|------------|-------------------------|
| 0.07       | (8, 4)                  |
| 0.14       | (8, 4)                  |
| 0.22       | (8, 4)                  |
| 0.38       | (10, 5)                 |
| 0.50       | (10, 5)                 |
| 0.81       | (12, 6)                 |
| 1.25       | (14, 7)                 |
| 1.76       | (16, 8)                 |
| 2.34       | (18, 9)                 |


The GammaDiffuse dataset has been divided into training and test datasets with a 50-50% ratio.

```
lstmcpipe_generate_nsb_levels_configs -c PathConfigAllSkyFullSplitDiffuse --nsb 0.0 0.07 0.14 0.22 0.38 0.50 0.81 1.25 1.76 2.34 -pid 20240918_v0.10.12

python add_slurm_options.py
```

The `n_estimators` value has been changed to 50 following recommendations from https://github.com/cta-observatory/cta-lstchain/pull/1294 in all config except NSB-0.00
