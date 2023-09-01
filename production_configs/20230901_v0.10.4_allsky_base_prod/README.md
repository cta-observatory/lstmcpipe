# New Prod Config

## 20230901_v0.10.4_base_prod

## Short description of the config

Full allsky production with lstchain v0.10.4 standard settings (https://github.com/cta-observatory/cta-lstchain/blob/v0.10.4/lstchain/data/lstchain_standard_config.json)
Only change to the config is the added `integration_correction`, that is needed for
simulations.

## Why this config is needed

There have been datamodel-changes in the transition from lstchain 0.9 to 0.10, which is why a new production is in order.
Also old `lstchain` configs dont necessarily work with the new versions (e.g. due to floating point `verbose` values).

This request includes all declination lines and no NSB-tuning in order act as a new baseline.
For the same reason all processing steps are included.
That should make it possible to directly compare the performance to the older `20230127_v0.9.12_base_prod_az_tel` production.

For Crab or other high-NSB sources, a `dl1ab` reprocessing or another podcution will thus be needed.

## Command to produce
```
lstmcpipe_generate_config PathConfigAllSkyFull --prod_id 20230901_v0.10.4_allsky_base_prod --dec_list dec_2276 dec_931 dec_min_413 dec_6676 dec_4822 dec_3476
```
to produce the list of steps.
Then change `lstchain` version in the `mcpipe` config.
For the lstchain config, use the standard config of that version from here:
https://github.com/cta-observatory/cta-lstchain/blob/v0.10.4/lstchain/data/lstchain_standard_config.json
and set `apply_integration_correction` to `true`
