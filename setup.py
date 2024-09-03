#!/usr/bin/env python
# Licensed under a MIT license - see LICENSE.rst

import json
from pathlib import Path
from setuptools import setup, find_packages


def find_scripts(script_dir, prefix):
    script_list = [f for f in Path(script_dir).iterdir() if f.name.startswith(prefix)]
    return script_list


# Read package info from codemeta.json
with open(Path(__file__).parent.joinpath("codemeta.json")) as file:
    metadata = json.load(file)

project_name = metadata["name"]
author_names = ""
for aut in metadata["author"]:
    author_names += f"{aut['givenName']} {aut['familyName']},"

version = metadata["version"]
description = metadata["description"]

scripts_list = find_scripts("lstmcpipe", "onsite_")

entry_points = {
    "console_scripts": [
        "lstmcpipe = lstmcpipe.lstmcpipe_start:main",
        "lstmcpipe_plot_models_importance = lstmcpipe.plots.plot_models_importance:main",
        "lstmcpipe_plot_irfs = lstmcpipe.plots.plot_irfs:main",
        "lstmcpipe_hiperta_r0_to_dl1lstchain = lstmcpipe.hiperta.hiperta_r0_to_dl1lstchain:main",
        "lstmcpipe_dl2_to_sensitivity = lstmcpipe.scripts.script_dl2_to_sensitivity:main",
        "lstmcpipe_train_test_split = lstmcpipe.scripts.script_train_test_splitting:main",
        "lstmcpipe_lst_core_r0_dl1 = lstmcpipe.scripts.script_batch_filelist_lst:main",
        "lstmcpipe_lst_core_dl1ab = lstmcpipe.scripts.script_batch_filelist_lst_dl1ab:main",
        "lstmcpipe_cta_core_r0_dl1 = lstmcpipe.scripts.script_batch_filelist_cta:main",
        "lstmcpipe_rta_core_r0_dl1 = lstmcpipe.scripts.script_batch_filelist_rta:main",
        "lstmcpipe_compare_irfs = lstmcpipe.scripts.script_compare_irfs:main",
        "lstmcpipe_validate_config = lstmcpipe.scripts.script_lstmcpipe_validate_config:main",
        "lstmcpipe_generate_config = lstmcpipe.scripts.lstmcpipe_generate_config:main",
        "lstmcpipe_generate_nsb_levels_configs = lstmcpipe.scripts.generate_nsb_levels_configs:main",
    ]
}

setup(
    name=project_name,
    version=version,
    description=description,
    setup_requires=["setuptools_scm<8.0"],
    install_requires=[
        "lstchain>=0.9.0",
        "numpy",
        "astropy",
        "ctaplot>=0.5",
        "pyirf>=0.4",
        "matplotlib",
        "pytest",
        "ruamel.yaml>=0.17",
        "setuptools_scm<8.0",
        "deepdiff",
    ],
    packages=find_packages(exclude="lstmcpipe._dev_version"),
    tests_require=[
        "pytest",
        "lstchain>=0.10.0",
    ],
    author=author_names,
    author_email="thomas.vuillaume@lapp.in2p3.fr",
    url="https://github.com/cta-observatory/lstmcpipe",
    long_description="Visit https://github.com/cta-observatory/lstmcpipe",
    license="MIT",
    classifiers=[
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Astronomy",
    ],
    scripts=scripts_list,
    entry_points=entry_points,
    include_package_data=True,
    package_data={'lstmcpipe': ['codemeta.json']},
    data_files=[('lstmcpipe', ['lstmcpipe/base_config_lstmcpipe.yaml'])],
    use_scm_version={
        "write_to": Path(__file__).parent.joinpath("lstmcpipe/_version.py"),
        "write_to_template": "__version__ = '{version}'",
    },
)
