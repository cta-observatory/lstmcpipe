#!/usr/bin/env python
# Licensed under a MIT license - see LICENSE.rst

import os
from pathlib import Path
import re
from setuptools import setup, find_packages

with open("lstmcpipe/__init__.py") as f:
    __version__ = re.search('^__version__ = "(.*)"$', f.read()).group(1)


def find_scripts(script_dir, prefix):
    script_list = [f for f in Path(script_dir).iterdir() if f.name.startswith(prefix)]
    return script_list


def get_property(prop, project):
    result = re.search(
        r'{}\s*=\s*[\'"]([^\'"]*)[\'"]'.format(prop),
        open(project + "/__init__.py").read(),
    )
    return result.group(1)


def readfile(filename):
    with open(filename, "r+") as f:
        return f.read()


scripts_list = find_scripts("lstmcpipe", "onsite_")

entry_points = {
    "console_scripts": [
        "lstmcpipe = lstmcpipe.lstmcpipe_start:main",
        "lstmcpipe_plot_models_importance = lstmcpipe.plots.plot_models_importance:main",
        "lstmcpipe_plot_irfs = lstmcpipe.plots.plot_irfs:main",
        "lstmcpipe_hiperta_r0_to_dl1lstchain = lstmcpipe.hiperta.hiperta_r0_to_dl1lstchain:main",
        "lstmcpipe_dl2_to_sensitivity = lstmcpipe.scripts.script_dl2_to_sensitivity:main",
        "lstmcpipe_utils_move_dir = lstmcpipe.scripts.script_merge_utils_move_dir:main",
        "lstmcpipe_utils_cp_config = lstmcpipe.scripts.script_merge_utils_copy_config:main",
        "lstmcpipe_lst_core_r0_dl1 = lstmcpipe.scripts.script_batch_filelist_lst:main",
        "lstmcpipe_lst_core_dl1_dl1 = lstmcpipe.scripts.script_batch_filelist_lst_dl1ab:main",
        "lstmcpipe_cta_core_r0_dl1 = lstmcpipe.scripts.script_batch_filelist_cta:main",
        "lstmcpipe_rta_core_r0_dl1 = lstmcpipe.scripts.script_batch_filelist_rta:main",
        "lstmcpipe_compare_irfs = lstmcpipe.scripts.script_compare_irfs:main",
    ]
}

setup(
    name="lstmcpipe",
    version=get_property("__version__", "lstmcpipe"),
    description="MC production with lstchain on LST cluster (La Palma)",
    install_requires=[
        "lstchain",
        "pyyaml",
        "numpy",
        "astropy",
        "ctaplot",
        "pyirf",
        "matplotlib",
    ],
    packages=find_packages(),
    # tests_require=['pytest'],
    author="Thomas Vuillaume",
    author_email="thomas.vuillaume@lapp.in2p3.fr",
    url="https://github.com/cta-observatory/lstmcpipe",
    long_description=readfile("README.rst"),
    license="MIT",
    classifiers=[
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Astronomy",
    ],
    scripts=scripts_list,
    entry_points=entry_points,
)
