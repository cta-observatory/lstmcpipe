#!/usr/bin/env python

import os
import warnings
from pathlib import Path
from ruamel.yaml import YAML
from datetime import date
import re
import numpy as np
import astropy.units as u
from astropy.table import QTable, join
from astropy.coordinates import Angle

from . import base_config
from ..version import __version__
from ..plots.pointings import plot_pointings


_crab_dec = 'dec_2276'


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
        config_to_save.yaml_set_start_comment(
            f"lstmcpipe generated config from {self.__class__.__name__} " f"- {date.today()}\n\n"
        )

        if self.paths == {}:
            raise ValueError("Empty paths, generate first")

        config_to_save['lstmcpipe_version'] = __version__
        config_to_save['prod_type'] = self.__class__.__name__
        config_to_save['prod_id'] = self.prod_id
        config_to_save['stages_to_run'] = self.stages
        config_to_save['stages'] = self.paths

        if os.path.exists(filename) and not overwrite and not append:
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
        self.base_dir = (
            '/fefs/aswg/data/mc/{data_level}/20200629_prod5_trans_80/{particle}/{zenith}/south_pointing/{prod_id}'
        )
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
        base = self.base_dir.format(data_level=data_level, particle=particle, zenith=self.zenith, prod_id=prod_id)
        if particle == 'gamma':
            base = os.path.join(base, gamma_src_offset)
        return base

    def r0_dir(self, particle, gamma_src_offset='off0.4deg'):
        # for R0 dir there is no `prod_id` in the path
        return os.path.realpath(
            self._data_level_dir(data_level='DL0', particle=particle, gamma_src_offset=gamma_src_offset, prod_id='')
        )

    def dl1_dir(self, particle, gamma_src_offset='off0.4deg'):
        return self._data_level_dir(
            data_level='DL1', particle=particle, gamma_src_offset=gamma_src_offset, prod_id=self.prod_id
        )

    def dl2_dir(self, particle, gamma_src_offset='off0.4deg'):
        return self._data_level_dir(
            data_level='DL2', particle=particle, gamma_src_offset=gamma_src_offset, prod_id=self.prod_id
        )

    def irf_dir(self, gamma_src_offset='diffuse'):
        return os.path.join(
            os.path.realpath(
                self._data_level_dir(
                    data_level='IRF', particle='', gamma_src_offset=gamma_src_offset, prod_id=self.prod_id
                )
            ),
            gamma_src_offset,
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
                        {'input': dl1, 'output': {'train': self.train_dir(particle), 'test': self.test_dir(particle)}}
                    )
            else:
                dl1 = self.dl1_dir(particle=particle)
                paths.append(
                    {'input': dl1, 'output': {'train': self.train_dir(particle), 'test': self.test_dir(particle)}}
                )
        return paths

    def merge_output_file(self, particle, step, gamma_src_offset='off0.4deg'):
        if step not in ['train', 'test']:
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
                    paths.append({'input': train, 'output': output_file, 'options': '--no-image'})
            else:
                train = self.train_dir(particle)
                output_file = self.merge_output_file(particle=particle, step='train')
                paths.append({'input': train, 'output': output_file, 'options': '--no-image'})

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
            '/mc/', '/'
        )

        return os.path.realpath(p)

    @property
    def train_pipe(self):
        paths = [
            {
                'input': {
                    'gamma': self.merge_output_file('gamma-diffuse', 'train'),
                    'proton': self.merge_output_file('proton', 'train'),
                },
                'output': self.models_path(),
            }
        ]
        return paths

    @property
    def dl1_to_dl2(self):
        paths = []
        for particle in self.testing_particles:
            if particle == 'gamma':
                for offset in self.point_src_offsets:
                    dl1 = self.merge_output_file(particle=particle, step='test', gamma_src_offset=offset)
                    dl2 = self.dl2_dir(particle, gamma_src_offset=offset)
                    paths.append({'input': dl1, 'path_model': self.models_path(), 'output': dl2})
            else:
                dl1 = self.merge_output_file(particle=particle, step='test')
                dl2 = self.dl2_dir(particle)
                paths.append({'input': dl1, 'path_model': self.models_path(), 'output': dl2})
        return paths

    def dl2_output_file(self, particle, gamma_src_offset='off0.4deg'):
        dl2_filename = os.path.basename(
            self.merge_output_file(particle=particle, step='test', gamma_src_offset=gamma_src_offset)
        ).replace('dl1', 'dl2')
        return os.path.join(self.dl2_dir(particle=particle, gamma_src_offset=gamma_src_offset), dl2_filename)

    def sensitivity_file(self, offset):
        return os.path.join(self.irf_dir(gamma_src_offset=offset), f'sensitivity_{self.prod_id}_{offset}.fits.gz')

    @property
    def dl2_to_sensitivity(self):
        paths = []

        def path_dict(gamma_part, offset):
            d = {
                'input': {
                    'gamma_file': self.dl2_output_file(gamma_part),
                    'proton_file': self.dl2_output_file('proton'),
                    'electron_file': self.dl2_output_file('electron'),
                },
                'output': self.sensitivity_file(offset),
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
                    'electron_file': self.dl2_output_file('electron'),
                },
                'output': os.path.join(self.irf_dir(gamma_src_offset=offset), f'irf_{self.prod_id}_{offset}.fits.gz'),
                'options': '--gh-efficiency 0.7 --theta-containment 0.7 --energy-dependent-gh --energy-dependent-theta '
            }
            if gamma_part == 'gamma':
                d['options'] += ' --point-like'
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
                'output': self.sensitivity_file(offset).replace('fits.gz', 'png'),
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
    def __init__(self, prod_id, source_prod_id, zenith='zenith_20deg', run_checker=True):
        super(PathConfigProd5Trans80DL1ab, self).__init__(prod_id=prod_id, zenith=zenith)
        self.source_prod_id = source_prod_id
        self.stages.remove('r0_to_dl1')
        self.stages.remove('train_test_split')
        self.stages.remove('merge_dl1')
        self.stages.insert(0, 'dl1ab')
        if run_checker:
            self.check_source_prod()

    def check_source_prod(self):
        for step in ['train', 'test']:
            for particle in self.particles:
                if particle == 'gamma':
                    for offset in self.point_src_offsets:
                        dl1_input = self.starting_dl1(particle=particle, step=step, gamma_src_offset=offset)
                else:
                    dl1_input = self.starting_dl1(particle=particle, step=step, gamma_src_offset='')
                if not Path(dl1_input).exists():
                    raise FileNotFoundError(f"file {dl1_input} should exist")

    def starting_dl1(self, particle, step, gamma_src_offset='off0.4deg'):
        former_merged_dl1 = self.merge_output_file(particle=particle, step=step, gamma_src_offset=gamma_src_offset)
        return former_merged_dl1.replace(self.prod_id, self.source_prod_id)

    @property
    def dl1ab(self):
        paths = []
        for step in ['train', 'test']:
            for particle in self.particles:
                if particle == 'gamma':
                    for offset in self.point_src_offsets:
                        dl1_input = self.starting_dl1(particle=particle, step=step, gamma_src_offset=offset)
                        dl1_output = self.dl1_dir(particle, gamma_src_offset=offset)
                        paths.append({'input': dl1_input, 'output': dl1_output})
                else:
                    dl1_input = self.starting_dl1(particle=particle, step=step, gamma_src_offset='')
                    dl1_output = self.dl1_dir(particle, gamma_src_offset='')
                    paths.append({'input': dl1_input, 'output': dl1_output})
        return paths


class PathConfigAllSkyBase(PathConfig):
    """
    Standard paths configuration for a LSTProd2 MC production
    dataset_type: 'Training' or 'Testing'
    """

    def __init__(self, prod_id, dec):
        super().__init__(prod_id)
        self.prod_id = prod_id
        self.dec = dec
        self.base_dir = "/fefs/aswg/data/mc/{data_level}/AllSky/{prod_id}/{dataset_type}/{particle}/{dec}/{pointing}/"

        self.paths = {}
        self.stages = []

    def _extract_pointing(self, text):
        """
        return a tuple ($0, $1) of pointings based on a text pattern `*_theta_{$0}_az_{$1}_`
        """
        return re.search('.*theta\_(.+?)_az\_(.+?)\_', text)  # noqa

    def _data_level_dir(self, prod_id, data_level, particle, pointing, dec, dataset_type):
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
        return os.path.realpath(
            self.base_dir.format(
                data_level=data_level,
                particle=particle,
                pointing=pointing,
                prod_id=prod_id,
                dec=dec,
                dataset_type=dataset_type,
            )
        )

    def r0_dir(self):
        raise NotImplementedError("Should be implemented in child class if necessary")

    def dl1_dir(self, particle, pointing, dataset_type, dec):
        return self._data_level_dir(
            data_level='DL1',
            particle=particle,
            pointing=pointing,
            prod_id=self.prod_id,
            dataset_type=dataset_type,
            dec=dec,
        )

    def dl2_dir(self, particle, pointing, dataset_type, dec):
        return self._data_level_dir(
            data_level='DL2',
            particle=particle,
            pointing=pointing,
            prod_id=self.prod_id,
            dataset_type=dataset_type,
            dec=dec,
        )

    def irf_dir(self, particle, pointing, dataset_type, dec):
        return self._data_level_dir(
            data_level='IRF',
            particle=particle,
            pointing=pointing,
            prod_id=self.prod_id,
            dataset_type=dataset_type,
            dec=dec,
        )

    def models_dir(self):
        p = self.base_dir.format(
            data_level='models', particle='', pointing='', prod_id=self.prod_id, dataset_type='', dec=self.dec
        ).replace('/mc/', '/')
        return os.path.realpath(p)

    @property
    def r0_to_dl1(self):
        raise NotImplementedError("Should be implemented in child class if necessary")

    @property
    def merge_dl1(self):
        raise NotImplementedError("Should be implemented in child class if necessary")

    @property
    def train_pipe(self):
        raise NotImplementedError("Should be implemented in child class if necessary")

    @property
    def dl1_to_dl2(self):
        raise NotImplementedError("Should be implemented in child class if necessary")

    @property
    def dl2_to_irfs(self):
        raise NotImplementedError("Should be implemented in child class if necessary")


class PathConfigAllSkyTraining(PathConfigAllSkyBase):
    """
    Base class for training all sky production.
    Handles a single declination from R0 up to RF generation.
    """

    def __init__(self, prod_id, dec):
        super().__init__(prod_id, dec)
        # dec must be read here and not later as a f-string, hence the + dec +
        self.training_dir = (
            "/fefs/aswg/data/mc/DL0/LSTProd2/TrainingDataset/{particle}/"
            + dec
            + "/sim_telarray/{pointing}/output_v1.4/"
        )
        self.training_particles = ['GammaDiffuse', 'Protons']
        self.dataset_type = 'TrainingDataset'
        self.stages = ['r0_to_dl1', 'merge_dl1', 'train_pipe']

    def r0_dir(self, particle, pointing):
        # for R0 dir there is no `prod_id` in the path
        if particle in self.training_particles:
            return self.training_dir.format(particle=particle, pointing=pointing)
        else:
            raise ValueError("unknown particle")

    def _search_pointings(self, particle):
        """
        list directories in r0_path that contain simtel files
        """
        r0_pointing_path = Path(self.r0_dir(particle, pointing='$$$').split('$$$')[0])
        return [
            d.name
            for d in r0_pointing_path.iterdir()
            if d.is_dir() and list(Path(self.r0_dir(particle, d.name)).glob('*.simtel.gz'))
        ]

    def pointing_dirs(self, particle):
        return self.pointings[f'dirname_{particle}']

    def load_pointings(self, join_type='inner'):
        """
        Load and find pointings that exist for all training particles.
        This is overly complicated because pointings directory names are not consistent particle-wise
        see node_theta_16.087_az_108.090_ vs node_corsika_theta_16.087_az_108.090_
        see testing pointings for a simpler implementation if this get solved

        Use join_type to keep only the pointings existing for all training particles or all of them
        Azimuth between -pi and pi. Altitude between pi/2 and -pi/2

        Parameters
        ----------
        join_type: string
            See `astropy.table.join`: (‘inner’ | ‘outer’ | ‘left’ | ‘right’ | ‘cartesian’), default is ‘inner’

        Returns
        -------
        'astropy.table.QTable`
    
        """
        tabs = {}

        for particle in self.training_particles:
            data = []
            for d in self._search_pointings(particle):
                pt = self._extract_pointing(d)
                alt, az = (90.0 - float(pt.groups()[0])) * u.deg, (float(pt.groups()[1])) * u.deg
                data.append([Angle(alt).wrap_at('180d'), Angle(az).wrap_at('360d'), d])
            reshaped_data = [[dd[0] for dd in data], [dd[1] for dd in data], [dd[2] for dd in data]]
            tabs[particle] = QTable(data=reshaped_data, names=['alt', 'az', f'dirname_{particle}'])

        tab = join(
            tabs[self.training_particles[0]],
            tabs[self.training_particles[1]],
            keys=['alt', 'az'],
            table_names=[self.training_particles[0], self.training_particles[1]],
            join_type=join_type,
        )

        # useful only of there are more than 2 training particles in the future
        for part in self.training_particles[2:]:
            tab = join(tab, tabs[part], keys=['alt', 'az'], join_type=join_type)

        self._training_pointings = tab

    @property
    def pointings(self):
        """
        All pointings in rad. Azimuth between -pi and pi. Altitude between pi/2 and -pi/2.

        Returns
        -------
        `astropy.quantity`
        """
        if not hasattr(self, '_training_pointings'):
            try:
                self.load_pointings()
            except FileNotFoundError as e:
                raise FileNotFoundError("The class must be run on the cluster to load available pointing nodes") from e
        return self._training_pointings

    def plot_pointings(self, ax=None, projection='polar', add_grid3d=True, **kwargs):
        """
        Produce a scatter plot of the pointings based on parsed pointings paths

        Parameters
        ----------
        pointings: 2D array of `astropy.quantities` or numpy array in rad
        ax : `matplotlib.pyplot.Axis`
        projection: str or None
            '3d' | 'aitoff' | 'hammer' | 'lambert' | 'mollweide' | 'polar' | 'rectilinear'
        add_grid3d: bool
            add a 3D grid in case of projection='3d'
        kwargs: dict
            kwargs for `matplotlib.pyplot.scatter`

        Returns
        -------
        ax: `matplotlib.pyplot.axis`
        """

        kwargs.setdefault('label', f'Training {self.dec}')
        ax = plot_pointings(
            np.transpose([self.pointings['az'].to(u.rad), self.pointings['alt'].to(u.rad)]) * u.rad,
            ax=ax,
            projection=projection,
            add_grid3d=add_grid3d,
            **kwargs,
        )
        return ax

    def dl1_dir(self, particle, pointing):
        return super().dl1_dir(particle=particle, pointing=pointing, dataset_type=self.dataset_type, dec=self.dec)

    @property
    def r0_to_dl1(self):
        paths = []
        for particle in self.training_particles:
            for pointing in self.pointing_dirs(particle):
                r0 = self.r0_dir(particle, pointing)
                dl1 = self.dl1_dir(particle, pointing)
                paths.append({'input': r0, 'output': dl1})

        return paths

    def training_merged_dl1(self, particle):
        return os.path.join(self.dl1_dir(particle, ''), f'dl1_{self.prod_id}_train_{self.dec}_{particle}_merged.h5')

    @property
    def merge_dl1(self):
        # for the training particles, all the nodes get merged
        paths = []
        for particle in self.training_particles:
            dl1 = self.dl1_dir(particle, '')
            merged_dl1 = self.training_merged_dl1(particle)
            paths.append(
                {
                    'input': dl1,
                    'output': merged_dl1,
                    'options': '--pattern */*.h5 --no-image',
                    'extra_slurm_options': {'partition': 'long', 'time': '06:00:00'},
                }
            )
        return paths

    @property
    def train_pipe(self):
        paths = [
            {
                'input': {
                    'gamma': self.training_merged_dl1('GammaDiffuse'),
                    'proton': self.training_merged_dl1('Protons'),
                },
                'output': self.models_dir(),
                'extra_slurm_options': {'partition': 'xxl', 'mem': '160G', 'cpus-per-task': 16, 'time': '03-00:00:00'}
                if self.dec == _crab_dec
                else {'partition': 'xxl', 'mem': '100G', 'cpus-per-task': 16, 'time': '03-00:00:00'},
            }
        ]
        return paths



class PathConfigAllSkyTrainingWithSplit(PathConfigAllSkyTraining):
    def __init__(self, prod_id, dec):
        super().__init__(prod_id, dec)
        self.stages.insert(1, 'train_test_split')

    def dl1_diffuse_test_dir(self, pointing):
        return self.dl1_dir('GammaDiffuse', pointing).replace('TrainingDataset', 'TestingDataset') + '/test'

    def dl1_diffuse_train_dir(self, pointing):
        return self.dl1_dir('GammaDiffuse', pointing) + '/train'

    @property
    def train_test_split(self):
        paths = []
        for pointing in self.pointing_dirs('GammaDiffuse'):
            dl1 = self.dl1_dir('GammaDiffuse', pointing)
            train = self.dl1_diffuse_train_dir(pointing)
            test = self.dl1_diffuse_test_dir(pointing)
            paths.append({'input': dl1, 'output': {'train': train, 'test': test}, 'options': {'test_size': 0.5}})
        return paths

    @property
    def merge_dl1(self):
        # for the training particles, all the nodes get merged
        paths = []
        for particle in self.training_particles:
            dl1 = self.dl1_dir(particle, '')
            merged_dl1 = self.training_merged_dl1(particle)
            pattern = '*/*/*.h5' if particle == 'GammaDiffuse' else '*/*.h5'  # this is needed because search is not recursive in lstchain. can be changed after https://github.com/cta-observatory/cta-lstchain/pull/1286
            paths.append(
                {
                    'input': dl1,
                    'output': merged_dl1,
                    'options': f'--pattern {pattern} --no-image',
                    'extra_slurm_options': {'partition': 'long', 'time': '06:00:00'},
                }
            )
        return paths


class PathConfigAllSkyTesting(PathConfigAllSkyBase):
    def __init__(self, prod_id, dec):
        super().__init__(prod_id, dec)
        self.testing_dir = "/fefs/aswg/data/mc/DL0/LSTProd2/TestDataset/sim_telarray/{pointing}/output_v1.4/"
        self.dataset_type = 'TestingDataset'
        self.particle = 'Gamma'
        self.stages = ['r0_to_dl1', 'merge_dl1', 'dl1_to_dl2', 'dl2_to_irfs']

    def pointing_dirs(self):
        return self.pointings[f'dirname_{self.particle}']

    def r0_dir(self, pointing):
        return self.testing_dir.format(pointing=pointing)

    def _search_pointings(self):
        """
        list directories in r0_path that contain simtel files
        """
        r0_pointing_path = Path(self.r0_dir(pointing='$$$').split('$$$')[0])
        return [
            d.name
            for d in r0_pointing_path.iterdir()
            if d.is_dir() and list(Path(self.r0_dir(d.name)).glob('*.simtel.gz'))
        ]

    def load_pointings(self):
        """
        Load pointings.
        Azimuth between -pi and pi. Altitude between pi/2 and -pi/2

        Returns
        -------
        'astropy.table.QTable`
        """
        data = []
        for d in self._search_pointings():
            pt = self._extract_pointing(d)
            alt, az = (90.0 - float(pt.groups()[0])) * u.deg, (float(pt.groups()[1])) * u.deg
            data.append([Angle(alt).wrap_at('180d'), Angle(az).wrap_at('360d'), d])
        reshaped_data = [[dd[0] for dd in data], [dd[1] for dd in data], [dd[2] for dd in data]]
        self._testing_pointings = QTable(data=reshaped_data, names=['alt', 'az', f'dirname_{self.particle}'])

    @property
    def pointings(self):
        """
        All pointings in rad. Azimuth between -pi and pi. Altitude between pi/2 and -pi/2

        Returns
        -------
        `astropy.table.QTable`
        """
        if not hasattr(self, '_testing_pointings'):
            try:
                self.load_pointings()
            except FileNotFoundError as e:
                raise FileNotFoundError("The class must be run on the cluster to load available pointing nodes") from e
        return self._testing_pointings

    def plot_pointings(self, ax=None, projection='polar', add_grid3d=False, **kwargs):
        """
        Produce a scatter plot of the pointings based on parsed pointings paths

        Parameters
        ----------
        pointings: 2D array of `astropy.quantities` or numpy array in rad
        ax : `matplotlib.pyplot.Axis`
        projection: str or None
            '3d' | 'aitoff' | 'hammer' | 'lambert' | 'mollweide' | 'polar' | 'rectilinear'
        add_grid3d: bool
            add a 3D grid in case of projection='3d'
        kwargs: dict
            kwargs for `matplotlib.pyplot.scatter`

        Returns
        -------
        ax: `matplotlib.pyplot.axis`
        """
        kwargs.setdefault('label', 'Testing')
        ax = plot_pointings(
            np.transpose([self.pointings['az'].to(u.rad), self.pointings['alt'].to(u.rad)]) * u.rad,
            ax=ax,
            projection=projection,
            add_grid3d=add_grid3d,
            **kwargs,
        )
        return ax

    def dl1_dir(self, pointing, dec=''):
        # no declination for DL1 for TestingDataset
        return super().dl1_dir(particle=self.particle, pointing=pointing, dataset_type=self.dataset_type, dec=dec)

    def dl2_dir(self, pointing):
        # no declination for DL2 for TestingDataset
        return super().dl2_dir(particle=self.particle, pointing=pointing, dataset_type=self.dataset_type, dec=self.dec)

    def irf_dir(self, pointing):
        return super().irf_dir(particle=self.particle, pointing=pointing, dataset_type=self.dataset_type, dec=self.dec)


    @property
    def r0_to_dl1(self):
        paths = []
        for pointing in self.pointing_dirs():
            r0 = self.r0_dir(pointing)
            dl1 = self.dl1_dir(pointing)
            paths.append({'input': r0, 'output': dl1})
        return paths

    def testing_merged_dl1(self, pointing):
        particle = self.particle
        return os.path.join(self.dl1_dir(''), f'dl1_{self.prod_id}_{particle}_test_{pointing}_merged.h5')

    @property
    def merge_dl1(self):
        # for the training particles, all the nodes get merged
        paths = []
        # for the testing, we merge per node
        for pointing in self.pointing_dirs():
            dl1 = self.dl1_dir(pointing)
            merged_dl1 = self.testing_merged_dl1(pointing)
            paths.append({'input': dl1, 'output': merged_dl1, 'options': '--no-image'})

        return paths

    @property
    def dl1_to_dl2(self):
        paths = []
        for pointing in self.pointing_dirs():
            paths.append(
                {
                    'input': self.testing_merged_dl1(pointing),
                    'path_model': self.models_dir(),
                    'output': self.dl2_dir(pointing),
                    'extra_slurm_options': {'mem': '80GB' if self.dec == _crab_dec else '60GB'},
                }
            )
        return paths

    def dl2_output_file(self, pointing):
        filename = os.path.basename(self.testing_merged_dl1(pointing).replace('dl1_', 'dl2_'))
        return os.path.join(self.dl2_dir(pointing), filename)

    def irf_output_file(self, pointing):
        filename =  os.path.join(self.irf_dir(pointing), f'irf_{self.prod_id}_{self.particle}_{self.dec}_{pointing}.fits.gz')
        return os.path.join(self.irf_dir(pointing), filename)

    @property
    def dl2_to_irfs(self):
        paths = []

        for pointing in self.pointing_dirs():
            pp = {
                    'input': {
                        'gamma_file': self.dl2_output_file(pointing),
                        'proton_file': None,
                        'electron_file': None,
                    },
                    'output': self.irf_output_file(pointing),
                    'options': '--gh-efficiency 0.7 --theta-containment 0.7 --energy-dependent-gh --energy-dependent-theta ',
                    'extra_slurm_options': {'mem': '6GB'},
                }
            if self.particle == 'Gamma':
                pp['options'] += ' --point-like'
            paths.append(pp)

        return paths


class PathConfigAllSkyTestingGammaDiffuse(PathConfigAllSkyTesting):
    def __init__(self, prod_id, dec):
        """
        This config must be used after a PathConfigAllSkyTrainingWithSplit has been generated and run.
        It uses the test dataset of GammaDiffuse created by the train_test_split stage of PathConfigAllSkyTrainingWithSplit, 
        merges the nodes and runs the dl1_to_dl2 and dl2_to_irfs stages.
        """
        super().__init__(prod_id, dec)
        self.stages = ['merge_dl1', 'dl1_to_dl2', 'dl2_to_irfs']
        self.train_config = PathConfigAllSkyTrainingWithSplit(prod_id, dec)
        # self.pointings = self.train_config.pointings
        self.particle = 'GammaDiffuse'

    def testing_merged_dl1(self, pointing, dec):
        particle = self.particle
        return os.path.join(self.dl1_dir('', dec=dec), f'dl1_{self.prod_id}_{particle}_test_{dec}_{pointing}_merged.h5')

    def load_pointings(self):
        self.train_config.load_pointings()
        self._testing_pointings = self.train_config._training_pointings


    @property
    def merge_dl1(self):
        paths = []
        for pointing in self.train_config.pointing_dirs(self.particle):
            dl1 = self.dl1_dir(pointing, dec=self.dec)
            merged_dl1 = self.testing_merged_dl1(pointing, dec=self.dec)
            paths.append(
                {
                    'input': dl1, 
                    'output': merged_dl1, 
                    'options': '--pattern */*.h5 --no-image',
                    'extra_slurm_options': {'partition': 'long', 'time': '06:00:00'},
                }
            )
        return paths

    @property
    def dl1_to_dl2(self):
        paths = []
        for pointing in self.pointing_dirs():
            paths.append(
                {
                    'input': self.testing_merged_dl1(pointing, dec=self.dec),
                    'path_model': self.models_dir(),
                    'output': self.dl2_dir(pointing),
                    'extra_slurm_options': {'mem': '80GB' if self.dec == _crab_dec else '60GB'},
                }
            )
        return paths

    def dl2_output_file(self, pointing):
        filename = os.path.basename(self.testing_merged_dl1(pointing, dec=self.dec).replace('dl1_', 'dl2_'))
        return os.path.join(self.dl2_dir(pointing), filename)


class PathConfigAllSkyFull(PathConfig):
    def __init__(self, prod_id, dec_list):
        """
        Does training and testing for a list of declinations

        Parameters
        ----------
        prod_id: str
        dec_list: [str]
        """
        super().__init__(prod_id)
        self.prod_id = prod_id
        self.dec_list = dec_list
        self.stages = ['r0_to_dl1', 'merge_dl1', 'train_pipe', 'dl1_to_dl2', 'dl2_to_irfs']

        self.train_configs = {dec: PathConfigAllSkyTraining(prod_id, dec) for dec in dec_list}
        self.test_configs = {dec: PathConfigAllSkyTesting(prod_id, dec) for dec in dec_list}

    @property
    def r0_to_dl1(self):
        paths = []
        for dec in self.dec_list:
            paths.extend(self.train_configs[dec].r0_to_dl1)
        paths.extend(self.test_configs[self.dec_list[0]].r0_to_dl1)
        return paths

    @property
    def merge_dl1(self):
        paths = []
        for dec in self.dec_list:
            paths.extend(self.train_configs[dec].merge_dl1)
        paths.extend(self.test_configs[self.dec_list[0]].merge_dl1)
        return paths

    @property
    def train_pipe(self):
        paths = []
        for dec in self.dec_list:
            paths.extend(self.train_configs[dec].train_pipe)
        return paths

    @property
    def dl1_to_dl2(self):
        paths = []
        for dec in self.dec_list:
            paths.extend(self.test_configs[dec].dl1_to_dl2)
        return paths

    @property
    def dl2_to_irfs(self):
        paths = []
        for dec in self.dec_list:
            paths.extend(self.test_configs[dec].dl2_to_irfs)
        return paths

    def plot_pointings(self, ax=None, projection='polar', add_grid3d=False, train_kwargs=None, test_kwargs=None):
        """
        Produce a scatter plot of the pointings based on parsed pointings paths

        Parameters
        ----------
        ax : `matplotlib.pyplot.Axis`
        projection: str or None
            '3d' | 'aitoff' | 'hammer' | 'lambert' | 'mollweide' | 'polar' | 'rectilinear'
        add_grid3d: bool
            add a 3D grid in case of projection='3d'
        train_kwargs: dict | None
            kwargs for `matplotlib.pyplot.scatter`
        test_kwargs: dict | None
            kwargs for `matplotlib.pyplot.scatter`

        Returns
        -------
        `matplotlib.pyplot.axis`
        """
        train_kwargs = {} if train_kwargs is None else train_kwargs
        test_kwargs = {} if test_kwargs is None else test_kwargs
        test_kwargs.setdefault('color', 'black')
        test_kwargs.setdefault('marker', '*')

        dec = list(self.train_configs)[0]
        ax = self.train_configs[dec].plot_pointings(ax=ax, projection=projection, add_grid3d=add_grid3d, **train_kwargs)
        for dec, tr in list(self.train_configs.items())[1:]:
            ax = tr.plot_pointings(ax=ax, projection=projection, add_grid3d=False, **train_kwargs)

        ax = list(self.test_configs.values())[0].plot_pointings(
            ax=ax, projection=projection, add_grid3d=False, **test_kwargs
        )
        return ax


class PathConfigAllSkyTrainingDL1ab(PathConfigAllSkyTraining):
    def __init__(self, prod_id, source_prod_id, dec, run_checker=True):
        """
        Parameters
        ----------
        prod_id: str
            the new prod ID
        source_prod_id: str
            the source prod ID (must exist)
        dec: str
            the declination
        run_checker: boolean
            True to check if the source prod exists
        """
        super().__init__(prod_id, dec)
        self.stages = ['dl1ab', 'merge_dl1', 'train_pipe']
        self.source_prod_id = source_prod_id
        self.source_config = PathConfigAllSkyTraining(source_prod_id, dec)
        if run_checker:
            self.check_source_prod()

    def check_source_prod(self):
        marked_for_removal = []
        for particle in self.training_particles:
            for pidx, pointing in enumerate(self.pointing_dirs(particle)):
                source_dl1 = Path(self.source_config.dl1_dir(particle, pointing))
                if not source_dl1.exists():
                    warnings.warn(
                        f"{source_dl1} does not exist but MC file for {particle} - {pointing} does. "
                        f"This node will be removed from production."
                    )
                    marked_for_removal.append(pidx)
        self._training_pointings.remove_rows(pidx)

    @property
    def dl1ab(self):
        paths = []
        for particle in self.training_particles:
            for pointing in self.pointing_dirs(particle):
                source_dl1 = self.source_config.dl1_dir(particle, pointing)
                target_dl1 = self.dl1_dir(particle, pointing)
                paths.append({'input': source_dl1, 'output': target_dl1})

        return paths


class PathConfigAllSkyTestingDL1ab(PathConfigAllSkyTesting):
    def __init__(self, prod_id, source_prod_id, dec, run_checker=True):
        """
        Parameters
        ----------
        prod_id: str
            the new prod ID
        source_prod_id: str
            the source prod ID (must exist)
        dec: str
            the declination
        run_checker: boolean
            True to check if the source prod exists
        """
        super().__init__(prod_id, dec)
        self.stages = ['dl1ab', 'merge_dl1', 'dl1_to_dl2', 'dl2_to_irfs']
        self.source_prod_id = source_prod_id
        self.source_config = PathConfigAllSkyTesting(source_prod_id, dec)
        if run_checker:
            self.check_source_prod()

    def check_source_prod(self):
        marked_for_removal = []
        for pidx, pointing in enumerate(self.pointing_dirs()):
            source_dl1 = Path(self.source_config.dl1_dir(pointing))
            if not source_dl1.exists():
                warnings.warn(
                    f"{source_dl1} does not exist but MC file for {pointing} does. "
                    f"This node will be removed from production."
                )
                marked_for_removal.append(pidx)
        self._testing_pointings.remove_rows(marked_for_removal)

    @property
    def dl1ab(self):
        paths = []
        for pointing in self.pointing_dirs():
            source_dl1 = self.source_config.dl1_dir(pointing)
            target_dl1 = self.dl1_dir(pointing)
            paths.append({'input': source_dl1, 'output': target_dl1})

        return paths


class PathConfigAllSkyFullDL1ab(PathConfigAllSkyFull):
    def __init__(self, prod_id, source_prod_id, dec_list, run_checker=True):
        """
        Parameters
        ----------
        prod_id: str
            the new prod ID
        source_prod_id: str
            the source prod ID (must exist)
        dec_list: [str]
            list of declinations
        run_checker: boolean
            True to check if the source prod exists
        """
        super().__init__(prod_id, dec_list)
        self.source_prod_id = source_prod_id
        self.stages = ['dl1ab', 'merge_dl1', 'train_pipe', 'dl1_to_dl2', 'dl2_to_irfs']
        self.train_configs = {
            dec: PathConfigAllSkyTrainingDL1ab(prod_id, source_prod_id, dec, run_checker=run_checker)
            for dec in dec_list
        }
        self.test_configs = {
            dec: PathConfigAllSkyTestingDL1ab(prod_id, source_prod_id, dec, run_checker=run_checker) for dec in dec_list
        }

    @property
    def dl1ab(self):
        paths = []
        for dec in self.dec_list:
            paths.extend(self.train_configs[dec].dl1ab)
        # we do only one DL1 test for one dec (dec does not matter, so we take the first one)
        paths.extend(self.test_configs[self.dec_list[0]].dl1ab)
        return paths


class PathConfigAllTrainTestDL1b(PathConfigAllSkyFullDL1ab):
    def __init__(self, prod_id, source_prod_id, dec_list, run_checker=True):
        """
        Config for an allsky train-test analysis from an existing source prod.
        It runs:
            - train_pipe from existing merged DL1 files (source_prod_id)
            - dl1_to_dl2 from existing merged DL1 files (source_prod_id)
        Note that in of source-dependent analysis,
        missing src-dep parameters are recomputed on the fly during the train stage by lstchain.
        """
        super().__init__(prod_id, source_prod_id, dec_list)
        self.dec_list = dec_list
        self.source_prod_id = source_prod_id
        self.source_configs = PathConfigAllSkyFullDL1ab(
            source_prod_id, source_prod_id, dec_list, run_checker=run_checker
        )
        self.target_configs = PathConfigAllSkyFullDL1ab(prod_id, source_prod_id, dec_list, run_checker=run_checker)
        self.stages = ['train_pipe', 'dl1_to_dl2']
        if run_checker:
            self.check_source_prod()

    @property
    def dl1_to_dl2(self):
        paths = []
        for dec in self.dec_list:
            src_paths = self.source_configs.test_configs[dec].dl1_to_dl2
            target_paths = self.target_configs.test_configs[dec].dl1_to_dl2
            new_path = src_paths.copy()
            for ii, p in enumerate(new_path):
                new_path[ii]['path_model'] = target_paths[ii]['path_model']
                new_path[ii]['output'] = target_paths[ii]['output']
            paths.extend(new_path)
        return paths

    @property
    def train_pipe(self):
        paths = []
        for dec in self.dec_list:
            src_paths = self.source_configs.train_configs[dec].train_pipe
            # print(src_paths)
            target_paths = self.target_configs.train_configs[dec].train_pipe
            new_path = src_paths.copy()
            for ii, _ in enumerate(new_path):
                new_path[ii]['output'] = target_paths[ii]['output']
            paths.extend(new_path)
        return paths

    def check_source_prod(self):
        """
        Check that merged dl1 files for training exist in the source prod.
        Otherwise, remove the dec from the list of decs to be processed and warn the user.
        """

        dec_to_remove = []
        for dec in self.dec_list:
            for path in self.source_configs.train_configs[dec].merge_dl1:
                # the output from merging must exist to train  the model
                source_dl1 = Path(path['output'])
                if not source_dl1.exists():
                    warnings.warn(f"{source_dl1} does not exist" f"This training will be removed from production.")
                    dec_to_remove.append(dec)

        self.dec_list = list(set(self.dec_list) - set(dec_to_remove))


class PathConfigAllSkyFullSplitDiffuse(PathConfigAllSkyFull):
    def __init__(self, prod_id, dec_list):
        super().__init__(prod_id, dec_list)
        self.stages = ['r0_to_dl1', 'train_test_split', 'merge_dl1', 'train_pipe', 'dl1_to_dl2', 'dl2_to_irfs']

        self.train_configs = {dec: PathConfigAllSkyTrainingWithSplit(prod_id, dec) for dec in dec_list}
        self.test_configs = {dec: PathConfigAllSkyTesting(prod_id, dec) for dec in dec_list}
        self.test_diffuse_config = {dec: PathConfigAllSkyTestingGammaDiffuse(prod_id, dec) for dec in dec_list}

    @property
    def train_test_split(self):
        paths = []
        for dec in self.dec_list:
            paths.extend(self.train_configs[dec].train_test_split)
        return paths

    @property
    def merge_dl1(self):
        paths = super().merge_dl1
        for dec in self.dec_list:
            paths.extend(self.test_diffuse_config[dec].merge_dl1)
        return paths

    @property
    def dl1_to_dl2(self):
        paths = super().dl1_to_dl2
        for dec in self.dec_list:
            paths.extend(self.test_diffuse_config[dec].dl1_to_dl2)
        return paths

    @property
    def dl2_to_irfs(self):
        paths = super().dl2_to_irfs
        for dec in self.dec_list:
            paths.extend(self.test_diffuse_config[dec].dl2_to_irfs)
        return paths