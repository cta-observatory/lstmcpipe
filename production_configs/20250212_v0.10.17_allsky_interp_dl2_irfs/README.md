# (re)production of DL2 and IRFs for the NSB grid production with pointing interpolation

See https://github.com/cta-observatory/cta-lstchain/pull/1320 

After merging this feature, reproduction of test DL2 and IRFs is needed to analyse data.    
Uses models from prod [20240918_v0.10.12_allsky_nsb_grid ](https://github.com/cta-observatory/lstmcpipe/tree/master/production_configs/20240918_v0.10.12_allsky_nsb_grid) 

IRFs to use for data analysis can be found under:
```
/fefs/aswg/data/mc/IRF/AllSky/20250212_v0.10.17_allsky_interp_dl2_irfs_nsb_*
└── TestingDataset
    ├── Gamma
    │   ├── dec_2276
    │   ├── dec_3476
    │   ├── dec_4822
    │   ├── dec_6166
    │   ├── dec_6676
    │   ├── dec_931
    │   ├── dec_min_1802
    │   ├── dec_min_2924
    │   └── dec_min_413
    └── GammaDiffuse
        ├── ...
        └── dec_min_413
```


Steps done to produce configs:

- copied prod `20240918_v0.10.12_allsky_nsb_grid`
- applied `python process.py`
- fixed paths to DL1 files in prod NSB-0.00 