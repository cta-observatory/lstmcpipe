# (re)production of DL2 and IRFs for the NSB grid production with pointing interpolation

See https://github.com/cta-observatory/cta-lstchain/pull/1320 

After merging this feature, reproduction of test DL2 and IRFs is needed to analyse data.


Steps:
- copied prod `20240918_v0.10.12_allsky_nsb_grid`
- applied `python process.py`
- fixed paths to DL1 files in prod NSB-0.00 