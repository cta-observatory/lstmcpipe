Allsky Test Diffuse Gammas production, with nsb tuning, for the dec_4822 declination band.

Config files:
- lstmcpipe_config_2022-06-24_PathConfigAllSky_TestDiffuseGammas.yaml
- lstchain_config_2022-06-24.json

The command used for generating the config files is:

```
lstmcpipe_generate_config PathConfigAllSkyFullDL1ab --prod_id 24_05_2022_dec_4822 --kwargs source_prod_id=20220511_allsky_std --dec_list dec_4822 --overwrite
```

And then I changed it by hand.

PathConfigAllSkyFullDL1ab  -> TestDiffuseGammas
24_05_2022_dec_4822 -> 24062022_dec_4822

Plus I changed the file to match the stages and the nodes that need.

The source for which this production is required is "src2"
