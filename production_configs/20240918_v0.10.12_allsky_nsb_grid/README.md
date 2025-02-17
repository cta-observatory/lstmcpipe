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
```

## Modifications applied afterwards

- slurm options have been modified to accomodate for the usage of the cluster, adding the `nice` option so that lstmcpipe jobs are sent after lstosa ones and managing jobs times to reduce the time they are hanging
```
python add_slurm_options.py
```

- The `n_estimators` value has been changed to 50 following recommendations from https://github.com/cta-observatory/cta-lstchain/pull/1294 in all config except NSB-0.00. 
```
python change_estimators.py
```

- The lstchain configs have been modified to include the IRF production config from https://github.com/cta-observatory/cta-lstchain/blob/v0.10.12/docs/examples/irf_dl3_tool_config.json 



### Tree structure

Trained models for analysis can be found under:

```
/fefs/aswg/data/models/AllSky
├── 20240918_v0.10.12_allsky_nsb_tuning_0.00
├── 20240918_v0.10.12_allsky_nsb_tuning_0.07
├── 20240918_v0.10.12_allsky_nsb_tuning_0.14
├── 20240918_v0.10.12_allsky_nsb_tuning_0.22
├── 20240918_v0.10.12_allsky_nsb_tuning_0.38
├── 20240918_v0.10.12_allsky_nsb_tuning_0.50
├── 20240918_v0.10.12_allsky_nsb_tuning_0.81
├── 20240918_v0.10.12_allsky_nsb_tuning_1.25
├── 20240918_v0.10.12_allsky_nsb_tuning_1.76
├── 20240918_v0.10.12_allsky_nsb_tuning_2.34
```

Please **DO NOT** use IRFs under `/fefs/aswg/data/IRFs/AllSky/20240918_v0.10.12_allsky_nsb_tuning_*` but refer to production 20250212_v0.10.17_allsky_interp_dl2_irfs for the correct IRFs to use for data analysis.