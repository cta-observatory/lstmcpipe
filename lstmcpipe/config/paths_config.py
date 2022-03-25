import os
import yaml


class PathConfig:
    def __init__(self):
        self.paths = {}

    def generate(self, stages):
        for stage in stages:
            if not hasattr(self, stage):
                raise NotImplementedError(f"The stage {stage} is not implemented for this class")
            self.paths[stage] = getattr(self, stage)
        return self.paths

    def save_yml(self, filename, overwrite=False):
        if self.paths == {}:
            raise ValueError("Empty paths, generate first")
        if os.path.exists(filename) and not overwrite:
            raise FileExistsError(f"{filename} exists. Set overwrite=True")
        with open(filename, 'w') as f:
            yaml.safe_dump(self.paths, f)

    def load_yml(self, filename):
        with open(filename) as f:
            paths = yaml.safe_load(f)
        for keys in paths:
            if not hasattr(self, keys):
                raise NotImplementedError(f"This class does not have an implemented stage called {keys}")



class PathConfigProd5Trans80(PathConfig):
    """
    Standard paths configuration for a prod5_trans_80 MC production
    """

    ## TODO: generate for each gamma pointing offset in stages

    def __init__(self, prod_id, zenith='zenith_20deg'):
        super().__init__()
        self.prod_id = prod_id
        self.zenith = zenith
        self.base_dir = '/fefs/aswg/data/mc/{data_level}/20200629_prod5_trans_80/{particle}/{zenith}/south_pointing/{prod_id}'
        self.training_particles = ['gamma-diffuse', 'protons']
        self.testing_particles = ['gamma', 'electron', 'protons']
        self.point_src_offsets = ['off0.0deg', 'off0.4deg']
        self.particles = self.training_particles + self.testing_particles
        self.paths = {}

    def _data_level_dir(self, prod_id, data_level, particle, gamma_src_offset='off0.4deg'):
        """

        Parameters
        ----------
        data_level: str
            `DL0` or `DL1` or `DL2`
        particle: str
            `proton`, `gamma-diffuse`, `gamma` or `electron`
        gamma_src_offset: str
            for point source gammas only. `off0.0deg` or `off0.4deg`
        Returns
        -------
        str: path to directory
        """
        base = self.base_dir.format(data_level=data_level, particle=particle, zenith=self.zenith, prod_id=prod_id)
        if particle == 'gamma':
            base = os.path.join(base, gamma_src_offset)
        return base

    def r0_dir(self, particle, gamma_src_offset='off0.4deg'):
        # for R0 dir there is no `prod_id` in the path
        return os.path.realpath(self._data_level_dir(data_level='DL0', particle=particle, gamma_src_offset=gamma_src_offset, prod_id=''))

    def dl1_dir(self, particle, gamma_src_offset='off0.4deg'):
        return self._data_level_dir(data_level='DL1', particle=particle, gamma_src_offset=gamma_src_offset,
                                    prod_id=self.prod_id)

    def dl2_dir(self, particle, gamma_src_offset='off0.4deg'):
        return self._data_level_dir(data_level='DL2', particle=particle, gamma_src_offset=gamma_src_offset,
                                    prod_id=self.prod_id)

    @property
    def r0_to_dl1(self):
        paths = []
        for particle in self.particles:
            if particle == 'gamma':
                for offset in self.point_src_offsets:
                    r0 = self.r0_dir(particle=particle, gamma_src_offset=offset)
                    dl1 = self.dl1_dir(particle=particle, gamma_src_offset=offset)
                    paths.append({'input': r0, 'output': dl1})
            else:
                r0 = self.r0_dir(particle=particle)
                dl1 = self.dl1_dir(particle=particle)
                paths.append({'input': r0, 'output': dl1})
        return paths

    def train_dir(self, particle, gamma_src_offset='off0.4deg'):
        return os.path.join(self.dl1_dir(particle, gamma_src_offset=gamma_src_offset), 'train')

    def test_dir(self, particle, gamma_src_offset='off0.4deg'):
        return os.path.join(self.dl1_dir(particle, gamma_src_offset=gamma_src_offset), 'test')

    @property
    def train_test_split(self):
        paths = []
        for particle in self.particles:
            if particle == 'gamma':
                for offset in self.point_src_offsets:
                    dl1 = self.dl1_dir(particle=particle, gamma_src_offset=offset)
                    paths.append(
                        {'input': dl1, 'output': {'train': self.train_dir(particle), 'test': self.test_dir(particle)}})
            else:
                dl1 = self.dl1_dir(particle=particle)
                paths.append({'input': dl1, 'output': {'train': self.train_dir(particle), 'test': self.test_dir(particle)}})
        return paths

    def merge_output_file(self, particle, step, gamma_src_offset='off0.4deg'):
        dl1 = self.dl1_dir(particle=particle, gamma_src_offset=gamma_src_offset)
        return os.path.join(dl1, f'dl1_{particle}_{self.prod_id}_{step}.h5')

    @property
    def merge_dl1(self):
        paths = []
        for particle in self.training_particles:
            if particle == 'gamma':
                for offset in self.point_src_offsets:
                    train = self.train_dir(particle)
                    output_file = self.merge_output_file(particle=particle, step='train', gamma_src_offset=offset)
                    paths.append({'input': train, 'output': output_file})
            else:
                train = self.train_dir(particle)
                output_file = self.merge_output_file(particle=particle, step='train')
                paths.append({'input': train, 'output': output_file})

        for particle in self.testing_particles:
            if particle == 'gamma':
                for offset in self.point_src_offsets:
                    test = self.test_dir(particle)
                    output_file = self.merge_output_file(particle=particle, step='test', gamma_src_offset=offset)
                    paths.append({'input': test, 'output': output_file})
            else:
                test = self.test_dir(particle)
                output_file = self.merge_output_file(particle=particle, step='test')
                paths.append({'input': test, 'output': output_file})

        self.paths['merge_dl1'] = paths
        return paths

    def models_path(self):
        p = self.base_dir.format(data_level='models', particle='', zenith=self.zenith, prod_id=self.prod_id).replace(
            'mc', '')
        return os.path.realpath(p)

    @property
    def train(self):
        paths = [{
            'input': {
                'gamma': self.merge_output_file('gamma-diffuse', 'train'),
                'proton': self.merge_output_file('proton', 'train')
            },
            'output': self.models_path()
        }]
        return paths

    @property
    def dl1_to_dl2(self):
        paths = []
        for particle in self.testing_particles:
            if particle == 'gamma':
                for offset in self.point_src_offsets:
                    dl1 = self.merge_output_file(particle=particle, step='test', gamma_src_offset=offset)
                    dl2 = self.dl2_dir(particle, gamma_src_offset=offset)
                    paths.append({'input': dl1, 'output': dl2})
            else:
                dl1 = self.merge_output_file(particle=particle, step='test')
                dl2 = self.dl2_dir(particle)
                paths.append({'input': dl1, 'output': dl2})
        return paths

    def generate(self):
        stages = ['r0_to_dl1', 'train_test_split', 'merge_dl1', 'train', 'dl1_to_dl2']
        return super().generate(stages)


