lstMCpipe
=========

|code| |documentation| |slack| |CI| |coverage| |conda| |pypi| |zenodo| |fair|

.. |code| image:: https://img.shields.io/badge/lstmcpipe-code-green
  :target: https://github.com/cta-observatory/lstmcpipe/
.. |CI| image:: https://github.com/cta-observatory/lstmcpipe/workflows/CI/badge.svg?branch=master
  :target: https://github.com/cta-observatory/lstmcpipe/actions?query=workflow%3ACI
.. |coverage| image:: https://codecov.io/gh/cta-observatory/lstmcpipe/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/cta-observatory/lstmcpipe
.. |documentation| image:: https://img.shields.io/badge/lstmcpipe-documentation-orange
  :target: https://cta-observatory.github.io/lstmcpipe/
.. |conda| image:: https://img.shields.io/conda/v/conda-forge/lstmcpipe
   :alt: Conda
.. |pypi| image:: https://badge.fury.io/py/lstmcpipe.svg
  :target: https://badge.fury.io/py/lstmcpipe
.. |zenodo| image:: https://zenodo.org/badge/DOI/10.5281/zenodo.6460727.svg
  :target: https://doi.org/10.5281/zenodo.6460727
.. |fair| image:: https://img.shields.io/badge/fair--software.eu-%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8B-yellow
   :target: https://fair-software.eu
.. |slack| image:: https://img.shields.io/badge/CTA_North_slack-lstmcpipe_prods_channel-darkgreen?logo=slack&link=https%3A%2F%2Fcta-north.slack.com%2Farchives%2FC035H3C2HAS
   :alt: Static Badge



Scripts to ease the reduction of MC data on the LST cluster at La Palma.
With this package, the analysis/creation of R1/DL0/DL1/DL2/IRFs can be orchestrated.

Contact:
Thomas Vuillaume, thomas.vuillaume [at] lapp.in2p3.fr
Enrique Garcia, garcia [at] lapp.in2p3.fr
Lukas Nickel, lukas.nickel [at] tu-dortmund.de


Cite us 📝
----------

If lstMCpipe was used for your analysis, please cite:

https://doi.org/10.48550/arXiv.2212.00120

.. code-block::

  @misc{garcia2022lstmcpipe,
        title={The lstMCpipe library},
        author={Enrique Garcia and Thomas Vuillaume and Lukas Nickel},
        year={2022},
        eprint={2212.00120},
        archivePrefix={arXiv},
        primaryClass={astro-ph.IM}
  }

in addition to the exact lstMCpipe version used from https://doi.org/10.5281/zenodo.6460727


You may also want to include the config file with your published code for reproducibility.


Install 💻
----------

**As an user:**

For lstmcpipe >= 0.10.3, the preferred installation should be conda:

.. code-block::

    conda install lstmcpipe


Former versions:

.. code-block::

    VERSION=0.10.1  # change as desired
    wget https://raw.githubusercontent.com/cta-observatory/lstmcpipe/$VERSION/environment.yml
    conda env create -f environment.yml
    conda activate lstmcpipe
    pip install lstmcpipe==$VERSION


**As a developer:**

.. code-block::

    git clone https://github.com/cta-observatory/lstmcpipe.git
    cd lstmcpipe
    conda env create -n lstmcpipe_dev -f environment.yml
    conda activate lstmcpipe_dev
    pip install -e .
    pre-commit install

This will setup a pre-commit hook: Given that you are in the right enviroment, it will run and format files you are about
to commit with `black`. (You need to stage the changes again after that). This ensures the formatting of the
code follows our guidelines and there is less work dealing with the code checker in the CI.


Requesting a MC analysis 📊
---------------------------

You may find a longer, more detailed, version of these steps in our documentation.

You may find the list of already run productions in the documentation.
Please check in this list that the request you are about to make does not exist already!

To request a MC analysis:

#. Make sure to be part of the `github cta-observatory/lst-dev team <https://github.com/orgs/cta-observatory/teams/lst-dev>`__. If not, ask one of the admins.
#. Clone the repository in the cluster at La Palma.
#. Create a new branch named with you ``prodID``
#. Make a new directory named ``date_ProdID`` in the `production_configs` dir (have a look at the ``production_configs/template_prod`` as an example)
#. Generate your config (see below)
#. Open a pull request into lstMCpipe with a clear description (probably the same as in the readme of your config dir)
#. The requested config must contain:

* a lstchain config file (please provide an exhaustive config that will help others and provide a more explicit provenance information)
* a lstmcpipe config file (to generate it, please refer to the documentation)
* a readme with a short description of why you require this analysis to be run. **Do not add information that should not appear publicly** (such as source names) here. If you are requesting a production for a specific new source, please edit `this table on LST wiki <https://www.lst1.iac.es/wiki/index.php/MC_analysis_and_IRF_production#lstmcpipe_productions>`_. Also add the command line to generate the lstmcpipe config, that will help debugging.

The proposed configuration will be tested for validity by the continuous integration tests and we will interact with you to run the analysis on the cluster at La Palma.

Depending on the number of requests, we may give priorities.

**Need help?**
Join the CTA North slack and ask for help in the |slack|

Launch jobs 🚀
--------------

To generate your lstmcpipe configuration file, use `lstmcpipe_generate_config` command.
If the type of production you want is not listed in the existing ones, you may create your own `PathConfig` class
from an existing one, or generate a config from an existing prod type and edit the file manually.

Once you have your configuration file, you way launch the pipeline with the described stages in the config using:

.. code-block:: python

    lstmcpipe -c config_MC_prod.yml -conf_lst lstchain_*.json [-conf_cta CONFIG_FILE_CTA] [-conf_rta CONFIG_FILE_RTA] [--debug] [--log-file LOG_FILE]

`lstmcpipe` is the **orchestrator** of the pipeline, it schedules the stages specified in the
``config_MC_prod.yml`` file. All the configuration related with the MC pipe must be declared in this file (stages,
particles to be analysed, zenith, pointing, type of MC production...).

Pipeline-specific configuration options (such as cleaning or model parameters) are declared in a different configuration file,
which is passed via the options ``-conf_lst/-conf_cta/-conf_rta``.

Note: You can always launch this command without fear; there is an intermediate step that verifies and
shows the configuration that you are passing to the pipeline.

Note that a complete pipeline still requires quite a lot of resources. Think about other LP-IT cluster users.

