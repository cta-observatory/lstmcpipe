#  20220913_crab_theta23_tuned

Following production `20220902_crab_test_nodes` that had no tuning.


Processing of nodes node_theta_23.630_az_100.758 and node_theta_23.630_az_259.265_ only for:
- dl1ab
    -  with tuned config from [crab tuned prod](https://github.com/cta-observatory/lstmcpipe/blob/master/production_configs/20220518_v0.9.6_allsky_dec2276_tuned/lstchain_config_dec_2276_tuned.json)
- merge
- dl1_to_dl2
    - with trained RF from crab tuned prod: `/fefs/aswg/data/models/AllSky/20220518_allsky_dec2276_tuned/dec_2276`
- dl2_to_irfs

See https://github.com/cta-observatory/lst-sim-config/issues/49#issuecomment-1235392024
