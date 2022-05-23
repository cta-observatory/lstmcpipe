from lstmcpipe.config.paths_config import PathConfigAllSkyFull

prod_id = '20220511_allsky_std'

pcf = PathConfigAllSkyFull(prod_id,
        ['dec_2276','dec_3476','dec_4822','dec_931','dec_min_413'])

pcf.generate()

pcf.save_yml(f'lstmcpipe_config_{prod_id}.yml')


from lstchain.io.config import get_standard_config
import json
filename = f'lstchain_config_{prod_id}.json'

cfg = get_standard_config()
cfg['LocalPeakWindowSum']['apply_integration_correction'] = True
cfg['GlobalPeakWindowSum']['apply_integration_correction'] = True
cfg['source_config']['EventSource']['allowed_tels'] = [1]
cfg['random_forest_energy_regressor_args']['min_samples_leaf'] = 10
cfg['random_forest_disp_regressor_args']['min_samples_leaf'] = 10
cfg['random_forest_disp_classifier_args']['min_samples_leaf'] = 10
cfg['random_forest_particle_classifier_args']['min_samples_leaf'] = 10
with open(filename, 'w') as file:
    json.dump(cfg, file, indent=4)

print(f"Modified lstchain config dumped in {filename}")
