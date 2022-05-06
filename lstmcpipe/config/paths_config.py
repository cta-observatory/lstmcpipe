#!/usr/bin/env python

import os
from pathlib import Path
from ruamel.yaml import YAML
from datetime import date
from copy import deepcopy
import re

from . import base_config
from ..version import __version__


class PathConfig:
    """
    Base class to generate a Path configuration for a production
    """

    def __init__(self, prod_id):
        self.prod_id = prod_id
        self.paths = {}
        self.stages = []

    def generate(self):
        """
        Generate the stages paths. They are copied into self.paths and returned.

        Returns
        -------
        dict: paths config
        """
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

        config_to_save['lstmcpipe_version'] = __version__
        config_to_save['prod_type'] = self.__class__.__name__
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
            yaml.dump(config_to_save, f)


class PathConfigProd5Trans80(PathConfig):
    """
    Standard paths configuration for a prod5_trans_80 MC production
    """

    def __init__(self, prod_id, zenith='zenith_20deg'):
        super().__init__(prod_id)
        self.prod_id = prod_id
        self.zenith = zenith
        self.base_dir = \
            '/fefs/aswg/data/mc/{data_level}/20200629_prod5_trans_80/{particle}/{zenith}/south_pointing/{prod_id}'
        self.training_particles = ['gamma-diffuse', 'proton']
        self.testing_particles = ['gamma', 'electron', 'proton', 'gamma-diffuse']
        self.point_src_offsets = ['off0.0deg', 'off0.4deg']
        self.paths = {}
        self.stages = [
            'r0_to_dl1',
            'train_test_split',
            'merge_dl1',
            'train_pipe',
            'dl1_to_dl2',
            'dl2_to_sensitivity',
            'dl2_to_irfs',
        ]

    @property
    def particles(self):
        return list(set(self.training_particles + self.testing_particles))

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
        base = self.base_dir.format(
            data_level=data_level,
            particle=particle,
            zenith=self.zenith,
            prod_id=prod_id
        )
        if particle == 'gamma':
            base = os.path.join(base, gamma_src_offset)
        return base

    def r0_dir(self, particle, gamma_src_offset='off0.4deg'):
        # for R0 dir there is no `prod_id` in the path
        return os.path.realpath(self._data_level_dir(data_level='DL0',
                                                     particle=particle,
                                                     gamma_src_offset=gamma_src_offset,
                                                     prod_id='')
                                )

    def dl1_dir(self, particle, gamma_src_offset='off0.4deg'):
        return self._data_level_dir(data_level='DL1',
                                    particle=particle,
                                    gamma_src_offset=gamma_src_offset,
                                    prod_id=self.prod_id)

    def dl2_dir(self, particle, gamma_src_offset='off0.4deg'):
        return self._data_level_dir(data_level='DL2',
                                    particle=particle,
                                    gamma_src_offset=gamma_src_offset,
                                    prod_id=self.prod_id)

    def irf_dir(self, gamma_src_offset='diffuse'):
        return os.path.join(
            os.path.realpath(self._data_level_dir(data_level='IRF',
                                                  particle='',
                                                  gamma_src_offset=gamma_src_offset,
                                                  prod_id=self.prod_id)
                             ),
            gamma_src_offset
        )

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
        return os.path.join(
            self.dl1_dir(particle, gamma_src_offset=gamma_src_offset),
            'train'
        )

    def test_dir(self, particle, gamma_src_offset='off0.4deg'):
        return os.path.join(
            self.dl1_dir(particle, gamma_src_offset=gamma_src_offset),
            'test'
        )

    @property
    def train_test_split(self):
        paths = []
        for particle in self.particles:
            if particle == 'gamma':
                for offset in self.point_src_offsets:
                    dl1 = self.dl1_dir(particle=particle, gamma_src_offset=offset)
                    paths.append(
                        {'input': dl1,
                         'output': {
                             'train': self.train_dir(particle),
                             'test': self.test_dir(particle)}
                         })
            else:
                dl1 = self.dl1_dir(particle=particle)
                paths.append({
                    'input': dl1,
                    'output': {
                        'train': self.train_dir(particle),
                        'test': self.test_dir(particle)
                    }
                })
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
                    paths.append({
                        'input': train,
                        'output': output_file,
                        'options': '--no-image'
                    })
            else:
                train = self.train_dir(particle)
                output_file = self.merge_output_file(particle=particle, step='train')
                paths.append({
                    'input': train,
                    'output': output_file,
                    'options': '--no-image'
                })

        for particle in self.testing_particles:
            if particle == 'gamma':
                for offset in self.point_src_offsets:
                    test = self.test_dir(particle)
                    output_file = self.merge_output_file(particle=particle, step='test', gamma_src_offset=offset)
                    paths.append({
                        'input': test,
                        'output': output_file
                    })
            else:
                test = self.test_dir(particle)
                output_file = self.merge_output_file(particle=particle, step='test')
                paths.append({
                    'input': test,
                    'output': output_file
                })

        self.paths['merge_dl1'] = paths
        return paths

    def models_path(self):
        p = self.base_dir.format(
            data_level='models',
            particle='',
            zenith=self.zenith,
            prod_id=self.prod_id
        ).replace('/mc/', '/')

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
                    paths.append({
                        'input': dl1,
                        'path_model': self.models_path(),
                        'output': dl2
                    })
            else:
                dl1 = self.merge_output_file(particle=particle, step='test')
                dl2 = self.dl2_dir(particle)
                paths.append({
                    'input': dl1,
                    'path_model': self.models_path(),
                    'output': dl2
                })
        return paths

    def dl2_output_file(self, particle, gamma_src_offset='off0.4deg'):
        dl2_filename = os.path.basename(self.merge_output_file(particle=particle,
                                                               step='test',
                                                               gamma_src_offset=gamma_src_offset)).replace('dl1', 'dl2')
        return os.path.join(
            self.dl2_dir(particle=particle, gamma_src_offset=gamma_src_offset),
            dl2_filename
        )

    def sensitivity_file(self, offset):
        return os.path.join(
            self.irf_dir(gamma_src_offset=offset),
            f'sensitivity_{self.prod_id}_{offset}.fits.gz'
        )

    @property
    def dl2_to_sensitivity(self):
        paths = []

        def path_dict(gamma_part, offset):
            d = {
                'input': {
                    'gamma_file': self.dl2_output_file(gamma_part),
                    'proton_file': self.dl2_output_file('proton'),
                    'electron_file': self.dl2_output_file('electron')
                },
                'output': self.sensitivity_file(offset)
            }
            return d

        # sensitivity can be computed only on point source gammas at the moment
        for offset in self.point_src_offsets:
            paths.append(path_dict('gamma', offset))

        return paths

    @property
    def dl2_to_irfs(self):
        paths = []

        def path_dict(gamma_part, offset):
            d = {
                'input': {
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
            d = {
                'input': self.sensitivity_file(offset),
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


class PathConfigProd5Trans80DL1ab(PathConfigProd5Trans80):

    def __init__(self, starting_prod_id, new_prod_id, zenith='zenith_20deg'):
        super(PathConfigProd5Trans80DL1ab, self).__init__(prod_id=new_prod_id, zenith=zenith)
        self.starting_prod_id = starting_prod_id
        self.stages.remove('r0_to_dl1')
        self.stages.remove('train_test_split')
        self.stages.remove('merge_dl1')
        self.stages.insert(0, 'dl1ab')

    def starting_dl1(self, particle, step, gamma_src_offset='off0.4deg'):
        former_merged_dl1 = self.merge_output_file(particle=particle, step=step, gamma_src_offset=gamma_src_offset)
        return former_merged_dl1.replace(self.prod_id, self.starting_prod_id)

    @property
    def dl1ab(self):
        paths = []
        for step in ['train', 'test']:
            for particle in self.particles:
                if particle == 'gamma':
                    for offset in self.point_src_offsets:
                        dl1_input = self.starting_dl1(particle=particle, step=step, gamma_src_offset=offset)
                        dl1_output = self.dl1_dir(particle, gamma_src_offset=offset)
                        paths.append({
                            'input': dl1_input,
                            'output': dl1_output
                        })
                else:
                    dl1_input = self.starting_dl1(particle=particle, step=step, gamma_src_offset='')
                    dl1_output = self.dl1_dir(particle, gamma_src_offset='')
                    paths.append({
                        'input': dl1_input,
                        'output': dl1_output
                    })
        return paths


class PathConfigAllSky(PathConfig):
    """
    Standard paths configuration for a prod5_trans_80 MC production
    """

    def __init__(self, prod_id, dec):
        super().__init__(prod_id)
        self.prod_id = prod_id
        self.base_dir = "/fefs/aswg/data/mc/{data_level}/AllSky/{prod_id}/{particle}/" + dec + "/{pointing}/"
        self.training_dir = "/home/georgios.voutsinas/ws/AllSky/TrainingDataset/{particle}/" + dec + "/sim_telarray/{pointing}/output_v1.4/"
        self.testing_dir = "/home/georgios.voutsinas/ws/AllSky/TestDataset/sim_telarray/{pointing}/output_v1.4/"

        self.training_particles = ['GammaDiffuse', 'Protons']
        self.testing_particles = ['Crab']

        self.paths = {}
        self.stages = ['r0_to_dl1', 'merge_dl1', 'train_pipe', 'dl1_to_dl2', 'dl2_to_irfs']

    def _search_pointings(self, particle):
        pointing_dirs_ = os.listdir(self.r0_dir(particle=particle, pointing='$$$').split('$$$')[0])
        # Check that pointings contain simtel files
        pointing_dirs = []
        for pointing in pointing_dirs_:
            fullpath = self.r0_dir(particle, pointing)
            if [f for f in os.listdir(fullpath) if f.endswith('.simtel.gz')]:
                pointing_dirs.append(pointing)
        return pointing_dirs

    def training_pointings(self, particle):
        if not hasattr(self, '_training_pointings'):
            try:
                self.load_pointings()
            except FileNotFoundError as e:
                raise FileNotFoundError(
                    "The class must be run on the cluster to load available pointing nodes"
                ) from e
        return self._training_pointings[particle]

    def testing_pointings(self, particle):
        if not hasattr(self, '_testing_pointings'):
            try:
                self.load_pointings()
            except FileNotFoundError as e:
                raise FileNotFoundError(
                    "The class must be run on the cluster to load available pointing nodes"
                ) from e
        return self._testing_pointings[particle]

    def load_pointings(self):
        self._training_pointings = self._get_training_pointings()
        self._testing_pointings = self._get_testing_pointings()

    def _extract_pointing(self, text):
        """
        return a tuple ($0, $1) of pointings based on a text pattern `*_theta_{$0}_az_{$1}_`
        """
        return re.search('.*theta\_(.+?)_az\_(.+?)\_', text)

    def _get_training_pointings(self):
        """
        Find pointings that exist for all training particles
        This is overly complicated because pointings directory names are not consistent particle-wise
        see node_theta_16.087_az_108.090_ vs node_corsika_theta_16.087_az_108.090_
        see testing pointings for a simpler implementation if this get solved
        """
        all_pointings = {}
        for particle in self.training_particles:
            all_pointings[particle] = self._search_pointings(particle)
        intersected_pointings = deepcopy(all_pointings)

        for particle, pointings_text in all_pointings.items():
            for pointing_text in pointings_text:
                pointing_tuple = self._extract_pointing(pointing_text)
                for other_particles, other_pointings_text in all_pointings.items():
                    other_pointings_tuples = [self._extract_pointing(pt) for pt in other_pointings_text]
                    if pointing_tuple not in other_pointings_tuples:
                        if pointing_text in intersected_pointings:
                            intersected_pointings[particle].remove(pointing_text)

        return intersected_pointings

    def _get_testing_pointings(self):
        particle = self.testing_particles[0]
        pointings = set(self._search_pointings(particle))
        for particle in self.testing_particles[1:]:
            pointings.intersection_update(self._search_pointings(particle))
        return {particle: pointings for particle in self.testing_particles}

    def _data_level_dir(self, prod_id, data_level, particle, pointing):
        """

        Parameters
        ----------
        data_level: str
            `DL0` or `DL1` or `DL2`
        particle: str
            `proton`, `gamma-diffuse`, `gamma` or `electron`
        prod_id:
        pointing:

        Returns
        -------
        str: path to directory
        """
        if data_level not in ['models', 'DL1', 'DL2', 'IRF']:
            raise ValueError("data_level should be DL1, DL2 or IRF")
        return self.base_dir.format(data_level=data_level, particle=particle, pointing=pointing, prod_id=prod_id)

    def r0_dir(self, particle, pointing):
        # for R0 dir there is no `prod_id` in the path
        if particle in self.training_particles:
            return self.training_dir.format(particle=particle, pointing=pointing)
        elif particle in self.testing_particles:
            return self.testing_dir.format(pointing=pointing)
        else:
            raise ValueError("unknown particle")

    def dl1_dir(self, particle, pointing):
        return self._data_level_dir(data_level='DL1', particle=particle, pointing=pointing, prod_id=self.prod_id)

    def dl2_dir(self, particle, pointing):
        return self._data_level_dir(data_level='DL2', particle=particle, pointing=pointing, prod_id=self.prod_id)

    def irf_dir(self, pointing):
        return os.path.realpath(self._data_level_dir(data_level='IRF',
                                                     particle='',
                                                     pointing=pointing,
                                                     prod_id=self.prod_id)
                                )

    @property
    def r0_to_dl1(self):
        paths = []
        for particle in self.training_particles:
            for pointing in self.training_pointings(particle):
                r0 = self.r0_dir(particle, pointing)
                dl1 = self.dl1_dir(particle, pointing)
                paths.append({'input': r0, 'output': dl1})
        for particle in self.testing_particles:
            for pointing in self.testing_pointings(particle):
                r0 = self.r0_dir(particle, pointing)
                dl1 = self.dl1_dir(particle, pointing)
                paths.append({'input': r0, 'output': dl1})
        return paths

    def training_merged_dl1(self, particle):
        return os.path.join(
            os.path.realpath(self.dl1_dir(particle, '')),
            f'dl1_{particle}_merged.h5'
        )

    def testing_merged_dl1(self, particle, pointing):
        return os.path.join(
            os.path.realpath(self.dl1_dir(particle, '')),
            f'dl1_{particle}_{pointing}_merged.h5'
        )

    @property
    def merge_dl1(self):
        # for the training particles, all the nodes get merged
        paths = []
        for particle in self.training_particles:
            dl1 = self.dl1_dir(particle, '')
            merged_dl1 = self.training_merged_dl1(particle)
            paths.append({
                'input': dl1,
                'output': merged_dl1,
                'options': '--pattern */*.h5 --no-image',
            })

        # for the testing, we merge per node
        for particle in self.testing_particles:
            for pointing in self.testing_pointings(particle):
                dl1 = self.dl1_dir(particle, pointing)
                merged_dl1 = self.testing_merged_dl1(particle, pointing)
                paths.append({
                    'input': dl1,
                    'output': merged_dl1,
                    'options': '--no-image'
                })

        return paths

    def models_path(self):
        p = self.base_dir.format(data_level='models', particle='', pointing='', prod_id=self.prod_id).replace(
            '/mc/', '/')
        return os.path.realpath(p)

    @property
    def train_pipe(self):
        paths = [{
            'input': {
                'gamma': self.training_merged_dl1('GammaDiffuse'),
                'proton': self.training_merged_dl1('Protons'),
            },
            'output': self.models_path(),
            'slurm_options': '-p long --mem=80G'
        }]
        return paths

    @property
    def dl1_to_dl2(self):
        paths = []
        for particle in self.testing_particles:
            for pointing in self.testing_pointings(particle):
                paths.append({
                    'input': self.testing_merged_dl1(particle, pointing),
                    'path_model': self.models_path(),
                    'output': self.dl2_dir(particle, pointing)
                })
        return paths

    def dl2_output_file(self, particle, pointing):
        filename = os.path.basename(self.testing_merged_dl1(particle, pointing).replace('dl1_', 'dl2_'))
        return os.path.join(self.dl2_dir(particle, pointing), filename)

    @property
    def dl2_to_irfs(self):
        paths = []

        for particle in self.testing_particles:
            for pointing in self.testing_pointings(particle):
                paths.append({
                    'input': {'gamma_file': self.dl2_output_file(particle, pointing),
                              'proton_file': None,
                              'electron_file': None,
                              },
                    'output': os.path.join(self.irf_dir(pointing), f'irf_{self.prod_id}_{pointing}.fits.gz'),
                    'options': '--point-like'
                }
                )

        return paths



class PathConfigAllSkyDL1ab(PathConfigAllSky):

    def __init__(self, starting_prod_id, new_prod_id, dec):
        super().__init__(prod_id=new_prod_id, dec=dec)
        self.starting_prod_id = starting_prod_id
        self.stages.remove('r0_to_dl1')
        self.stages.insert(0, 'dl1ab')
        # the new stages are then: dl1ab, merge, train, dl1_to_dl2, dl2_to_irfs
        self.dec = dec

    @property
    def dl1ab(self):
        paths = []
        former_config = PathConfigAllSky(self.starting_prod_id, self.dec)
        def append_path(particle, pointing):
            former_dl1 = former_config.dl1_dir(particle, pointing)
            if Path(former_dl1).exists() and [f for f in Path(former_dl1).iterdir() if f.as_posix().endswith('.h5')]:
                target_dl1 = self.dl1_dir(particle, pointing)
                paths.append({'input': former_dl1, 'output': target_dl1})
                
        for particle in self.training_particles:
            for pointing in self.training_pointings(particle):
                append_path(particle, pointing)

        for particle in self.testing_particles:
            for pointing in self.testing_pointings(particle):
                append_path(particle, pointing)

        return paths
