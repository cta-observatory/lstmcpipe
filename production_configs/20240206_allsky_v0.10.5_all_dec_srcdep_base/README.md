# Prod 20240206_allsky_v0.10.5_all_dec_srcdep_base

Base production (source-depenedent analysis) for all declinations lines with lstchain v0.10.5


```
lstmcpipe_generate_config PathConfigAllSkyFullDL1ab --dec_list dec_2276 dec_4822 dec_6166 dec_6676 dec_min_1802 dec_min_413 dec_931 dec_min_2924 dec_3476 --prod_id 20240206_allsky_v0.10.5_all_dec_srcdep_base --kwargs source_prod_id=20240131_allsky_v0.10.5_all_dec_base
```

The lstchain config file is manually updated for the source-dependent anlaysis. The difference from the standard lstchain config file is:
```
$ diff lstchain_config_2024-02-06.json  lstchain_config_2024-02-06_srcdep.json 
153,191c153,190
<     "energy_regression_features": [
<         "log_intensity",
<         "width",
<         "length",
<         "x",
<         "y",
<         "wl",
<         "skewness",
<         "kurtosis",
<         "time_gradient",
<         "leakage_intensity_width_2",
<         "sin_az_tel",
<         "alt_tel"
<     ],
<     "disp_method": "disp_norm_sign",
<     "disp_regression_features": [
<         "log_intensity",
<         "width",
<         "length",
<         "wl",
<         "skewness",
<         "kurtosis",
<         "time_gradient",
<         "leakage_intensity_width_2",
<         "sin_az_tel",
<         "alt_tel"
<     ],
<     "disp_classification_features": [
<         "log_intensity",
<         "width",
<         "length",
<         "wl",
<         "skewness",
<         "kurtosis",
<         "time_gradient",
<         "leakage_intensity_width_2",
<         "sin_az_tel",
<         "alt_tel"
<     ],
---
>   "energy_regression_features": [
>     "log_intensity",
>     "width",
>     "length",
>     "wl",
>     "skewness_from_source",
>     "kurtosis",
>     "time_gradient_from_source",
>     "leakage_intensity_width_2",
>     "dist",
>     "alt_tel",
>     "sin_az_tel"
>   ],
>   "disp_method": "disp_norm_sign",
>   "disp_regression_features": [
>     "log_intensity",
>     "width",
>     "length",
>     "wl",
>     "skewness",
>     "kurtosis",
>     "time_gradient",
>     "leakage_intensity_width_2",
>     "alt_tel",
>     "sin_az_tel"
>   ],
>   "disp_classification_features": [
>     "log_intensity",
>     "width",
>     "length",
>     "wl",
>     "skewness",
>     "kurtosis",
>     "time_gradient",
>     "leakage_intensity_width_2",
>     "alt_tel",
>     "sin_az_tel"
>   ],
193,207c192,205
<         "log_intensity",
<         "width",
<         "length",
<         "x",
<         "y",
<         "wl",
<         "signed_skewness",
<         "kurtosis",
<         "signed_time_gradient",
<         "leakage_intensity_width_2",
<         "log_reco_energy",
<         "reco_disp_norm",
<         "reco_disp_sign",
<         "sin_az_tel",
<         "alt_tel"
---
>     "log_intensity",
>     "width",
>     "length",
>     "wl",
>     "skewness_from_source",
>     "kurtosis",
>     "time_gradient_from_source",
>     "leakage_intensity_width_2",
>     "log_reco_energy",
>     "dist",
>     "reco_disp_norm_diff",
>     "reco_disp_sign_correctness",
>     "alt_tel",
>     "sin_az_tel"
233c231
<         Infinity
---
>         1.0
235c233
<     "source_dependent": false,
---
>     "source_dependent": true,
315c313
< }
\ No newline at end of file
---
> }

```


contact: Seiya N.