from lstmcpipe.config.paths_config import PathConfigAllSkyFullDL1ab

prod_id = '20220518_allsky_dec2276_tuned'

cfg = PathConfigAllSkyFullDL1ab('20220511_allsky_std', prod_id, ['dec_2276'])

cfg.generate()

cfg.save_yml(f'lstmcpipe_config_{prod_id}.yml')
