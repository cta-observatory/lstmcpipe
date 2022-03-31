import os
from ruamel.yaml import YAML
from datetime import date

from . import base_config

class PathConfig:
    def __init__(self, prod_id):
        self.prod_id = prod_id
        self.paths = {}
        self.stages = []

    def generate(self):
        for stage in self.stages:
            if not hasattr(self, stage):
                raise NotImplementedError(f"The stage {stage} is not implemented for this class")
            self.paths[stage] = getattr(self, stage)
        return self.paths

    def save_yml(self, filename, overwrite=False, append=False):
        """
        Dump the path config to a file

        Parameters
        ----------
        filename: str or Path
        overwrite: bool
        append: bool
        """
        config_to_save = base_config()
        config_to_save.yaml_set_start_comment(f"lstmcpipe generated config from {self.__class__.__name__} "
                                              f"- {date.today()}\n\n")

        if self.paths == {}:
            raise ValueError("Empty paths, generate first")

        config_to_save['prod_id'] = self.prod_id
        config_to_save['stages_to_run'] = self.stages
        config_to_save['stages'] = self.paths

        if os.path.exists(filename) and not (overwrite or append):
            raise FileExistsError(f"{filename} exists. Set overwrite=True or append=True")
        if append and overwrite:
            raise ValueError("Append or overwrite, not both ;-)")
        if append:
            config_to_save.update(YAML().load((open(filename).read())))

        with open(filename, 'w') as f:
            yaml = YAML()
            yaml.indent(mapping=2, offset=2)
            yaml.dump(config_to_save, f)

    def load_yml(self, filename):
        paths = YAML().load(open(filename).read())
        for key, path in paths.items():
            if not hasattr(self, key):
                raise NotImplementedError(f"This class does not have an implemented stage called {keys}")
            else:
                self.paths[key] = path



class PathConfigProd5Trans80(PathConfig):
    """
    Standard paths configuration for a prod5_trans_80 MC production
    """

    def __init__(self, prod_id, zenith='zenith_20deg'):
        super().__init__(prod_id)
        self.prod_id = prod_id
        self.zenith = zenith
        self.base_dir = '/fefs/aswg/data/mc/{data_level}/20200629_prod5_trans_80/{particle}/{zenith}/south_pointing/{prod_id}'
        self.training_particles = ['gamma-diffuse', 'proton']
        self.testing_particles = ['gamma', 'electron', 'proton']
        self.point_src_offsets = ['off0.0deg', 'off0.4deg']
        self.particles = self.training_particles + self.testing_particles
        self.paths = {}
        self.stages = ['r0_to_dl1', 'train_test_split', 'merge_dl1', 'train_pipe', 'dl1_to_dl2',
                  'dl2_to_sensitivity', 'dl2_to_irfs']

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

    def irf_dir(self, gamma_src_offset='diffuse'):
        return os.path.join(os.path.realpath(self._data_level_dir(data_level='IRF', particle='', gamma_src_offset=gamma_src_offset,
                                    prod_id=self.prod_id)), gamma_src_offset)

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
        if not step in ['train', 'test']:
            raise ValueError("Only steps accepted: train or test")
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
    def train_pipe(self):
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

    def dl2_output_file(self, particle, gamma_src_offset='off0.4deg'):
        dl2_filename = os.path.basename(self.merge_output_file(particle=particle, step='test', gamma_src_offset=gamma_src_offset)).replace('dl1', 'dl2')
        return os.path.join(self.dl2_dir(particle=particle, gamma_src_offset=gamma_src_offset),
                            dl2_filename
                            )

    def sensitivity_file(self, offset):
        return os.path.join(self.irf_dir(gamma_src_offset=offset), f'sensitivity_{self.prod_id}_{offset}.fits.gz')

    @property
    def dl2_to_sensitivity(self):
        paths = []

        def path_dict(gamma_part, offset):
            d = {'input': {
                'gamma_file': self.dl2_output_file(gamma_part),
                'proton_file': self.dl2_output_file('proton'),
                'electron_file': self.dl2_output_file('electron')
            },
                'output': self.sensitivity_file(offset)
            }
            return d

        for gamma_part in ['gamma-diffuse', 'gamma']:
            if gamma_part == 'gamma-diffuse':
                paths.append(path_dict(gamma_part, 'diffuse'))
            else:
                for offset in self.point_src_offsets:
                    paths.append(path_dict(gamma_part, offset))

        return paths

    @property
    def dl2_to_irfs(self):
        paths = []

        def path_dict(gamma_part, offset):
            d = {'input': {
                'gamma_file': self.dl2_output_file(gamma_part),
                'proton_file': self.dl2_output_file('proton'),
                'electron_file': self.dl2_output_file('electron')
            },
                'output': os.path.join(self.irf_dir(gamma_src_offset=offset), f'irf_{self.prod_id}_{offset}.fits.gz'),
                'options': '--point-like' if gamma_part == 'gamma' else ''
            }
            return d

        for gamma_part in ['gamma-diffuse', 'gamma']:
            if gamma_part == 'gamma-diffuse':
                paths.append(path_dict(gamma_part, 'diffuse'))
            else:
                for offset in self.point_src_offsets:
                    paths.append(path_dict(gamma_part, offset))

        return paths

    @property
    def plot_irfs(self):
        paths = []

        def path_dict(offset):
            d = {'input': self.sensitivity_file(offset),
                 'output': self.sensitivity_file(offset).replace('fits.gz', 'png')
            }
            return d

        for gamma_part in ['gamma-diffuse', 'gamma']:
            if gamma_part == 'gamma-diffuse':
                paths.append(path_dict('diffuse'))
            else:
                for offset in self.point_src_offsets:
                    paths.append(path_dict(offset))
        return paths

    # def generate(self):
    #     return super().generate(stages)


