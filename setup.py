#!/usr/bin/env python
# Licensed under a MIT license - see LICENSE.rst

import os
from pathlib import Path
from setuptools import setup, find_packages


def find_scripts(script_dir, prefix):
    script_list = [f for f in Path(script_dir).iterdir() if f.name.startswith(prefix)]
    return script_list


def readfile(filename):
    with open(filename, "r+") as f:
        return f.read()

### Read package info from codemeta.json ###
import json
with open(os.path.join(os.path.dirname(__file__), "codemeta.json")) as file:
    metadata = json.load(file)

project_name = metadata["name"]
author_names = ""
for aut in metadata["author"]:
    author_names += f"{aut['givenName']} {aut['familyName']},"

version = metadata['version']
description = metadata['description']


scripts_list = find_scripts("lstmcpipe", "onsite_")

entry_points = {
    'console_scripts': [
        'lstmcpipe = lstmcpipe.lstmcpipe_start:main',
        'lstmcpipe_plot_models_importance = lstmcpipe.plots.plot_models_importance:main',
        'lstmcpipe_plot_irfs = lstmcpipe.plots.plot_irfs:main',
        'lstmcpipe_hiperta_r0_to_dl1lstchain = lstmcpipe.hiperta.hiperta_r0_to_dl1lstchain:main',
        'lstmcpipe_dl2_to_sensitivity = lstmcpipe.scripts.script_dl2_to_sensitivity:main',
        'lstmcpipe_utils_move_dir = lstmcpipe.scripts.script_merge_utils_move_dir:main',
        'lstmcpipe_utils_cp_config = lstmcpipe.scripts.script_merge_utils_copy_config:main',
        'lstmcpipe_lst_core_r0_dl1 = lstmcpipe.scripts.script_batch_filelist_lst:main',
        'lstmcpipe_cta_core_r0_dl1 = lstmcpipe.scripts.script_batch_filelist_cta:main',
        'lstmcpipe_rta_core_r0_dl1 = lstmcpipe.scripts.script_batch_filelist_rta:main',
        'lstmcpipe_compare_irfs = lstmcpipe.scripts.script_compare_irfs:main',
    ]
}

setup(
    name=project_name,
    version=version,
    description=description,
    install_requires=[
        "lstchain>=0.6",
        "pyyaml",
        "numpy",
        "astropy",
        "ctaplot>=0.5",
        "pyirf>=0.4",
        "matplotlib",
        "pytest"
    ],
    packages=find_packages(),
    tests_require=['pytest'],
    author=author_names,
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
