from lstmcpipe.config.paths_config import PathConfigAllSky


class PathConfigAllSky4822(PathConfigAllSky):

    def __init__(self, prod_id, dec):
        super().__init__(prod_id, dec)
        self.training_dir = \
        "/home/georgios.voutsinas/ws/AllSky/TrainingDataset/{particle}/" + dec + "/sim_telarray/{pointing}/output_v1.4/"


pc = PathConfigAllSky4822('allsky_dec4822_std', 'dec_4822')
pc.generate()
pc.save_yml('lstmcpipe_config_allsky_dec4822_std.yml')


