lstMCpipe
=========

|code| |documentation| |CI| |coverage|

.. |code| image:: https://img.shields.io/badge/lstmcpipe-code-green
  :target: https://github.com/cta-observatory/lstmcpipe/
.. |CI| image:: https://github.com/cta-observatory/lstmcpipe/workflows/CI/badge.svg?branch=master
  :target: https://github.com/cta-observatory/lstmcpipe/actions?query=workflow%3ACI
.. |coverage| image:: https://codecov.io/gh/cta-observatory/lstmcpipe/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/cta-observatory/lstmcpipe
.. |documentation| image:: https://img.shields.io/badge/lstmcpipe-documentation-orange
  :target: https://cta-observatory.github.io/lstmcpipe/

Scripts to ease the reduction of MC data on the LST cluster at La Palma.   
With this package, the analysis/creation of R1/DL0/DL1/DL2/IRFs can be orchestrated.

Contact:
Thomas Vuillaume, thomas.vuillaume [at] lapp.in2p3.fr
Enrique Garcia, garcia [at] lapp.in2p3.fr
Lukas Nickel, lukas.nickel [at] tu-dortmund.de


Install
-------

As as user:

.. code-block::

    git clone https://github.com/cta-observatory/lstmcpipe.git
    cd lstmcpipe
    conda env create -n lstmcpipe -f environment.yml
    conda activate lstmcpipe
    pip install .

This will setup a new enviroment with lstchain and other needed tools available in supported versions.
At this point in time, this fixes `ctapipe` to the version, that `lstchain` depends on.
Splitting the requirements and supporting different pipelines independently is a work in progress.
HIPERTA (referred to as rta in the following) support is builtin, but no installation instructions can be provided as of now.

Alternatively, you can install `lstmcpipe` in your own enviroment to use different versions of the
analysis pipelines.
WARNING: Due to changing APIs and data models, we cannot support other versions than the ones specified in
the enviroment.

As as developer:

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


Quickstart
----------

The way to launch either the full pipeline (r0 to IRFs) or a workflow with less stages (r0 to merging, for example) is
the same; you should run the same command/launch the same script in any case;

.. code-block:: python

    lstmcpipe -c config_MC_prod.yml -conf_lst lstchain_*.json [-conf_cta CONFIG_FILE_CTA] [-conf_rta CONFIG_FILE_RTA] [--debug] [--log-file LOG_FILE]

The ``lstmcpipe_start.py`` script is the **orchestrator** of the pipeline, it schedules the stages specified in the
``onsite_MC_prod.yml`` file. All the configuration related with the MC pipe must be declared in this file (stages,
particles to be analysed, zenith, pointing, type of MC production...).

Pipeline-specific configuration options (such as cleaning or model parameters) are declared in a different configuration file,
which is passed via the options ``-conf_lst/-conf_cta/-conf_rta``.

Note: You can always launch this command without fear; there is an intermediate step that verifies and
shows the configuration that you are passing to the pipeline.

The use of slurms jobarrays in the r0_to_dl1 stage in combination with a limited amount of maximum jobs running at the same time
reduces the load on the cluster compared to previous versions,
but **please note** that it still requires a lot of resources to process a full MC
production. Think about other LP-IT cluster users.


Stages
------
After launching of the pipeline all selected tasks will be performed in order.
These are referred to as *stages* and are collected in ``lstmcpipe/stages``.
Following is a short overview over each stage, that can be specified in the configuration.

**r0_to_dl1**

In this stage simtel-files are processed up to datalevel 1 and separated into files for training
and for testing.
For efficiency reasons files are processed in batches: N files (depending on paricle type
as that influences the averages duration of the processing) are submitted as one job in a jobarray.
To group the files together, the paths are saved in files that are passed to
python scripts in ``lstmcpipe/scripts`` which then call the selected pipelines 
processing tool. These are:

- lstchain: lstchain_mc_r0_to_dl1
- ctapipe: ctapipe-stage1
- rta: lstmcpipe_hiperta_r0_to_dl1lstchain (``lstmcpipe/hiperta/hiperta_r0_to_dl1lstchain.py``)

Results can be found in ``running_analysis``


**merge_and_copy_dl1**

In this stage the previously created dl1 files are merged so that you end up with
train and test datesets for the next stages.
Cleans and moves the ``running_analysis`` directory into ``DL1`` and ``analysis_logs``.

**train_pipe**

IMPORTANT: From here on out only ``lstchain`` tools are available. More about that at the end.

In this stage the models to reconstruct the primary particles properties are trained
on the gamma-diffuse and proton train data.
At present this means that random forests are created using lstchains
``lstchain_mc_trainpipe``
Models will be stored in the ``models`` directory.


**dl1_to_dl2**

The previously trained models are evaluated on the merged dl1 files using ``lstchain_dl1_to_dl2`` from
the lstchain package.
DL2 data can be found in ``DL2`` directory.

**dl2_to_irfs**

Point-like IRFs are produced for each set of offset gammas.
The processing is performed by calling ``lstchain_create_irf_files``. 


**dl2_to_sensitivity**
A sensitivity curve is estimated using a script based on pyirf which performs a cut optimisation
similar to EventDisplay.
The script can be found in ``lstmcpipe/scripts/script_dl2_to_sensitivity.py``.
This does not use the IRFs and cuts computed in dl2_to_irfs, so this can not be compared to observed data.
It is a mere benchmark for the pipeline.


Logs and data output
--------------------
**NOTE**: ``lstmcpipe`` expects the data to be located in a specific structure on the cluster.
Output will be written in a stanardized way next to the input data to make sure everyone can access it.
Analysing a custom dataset requires replicating parts of the directory structure and is not the
intended use case for this package.

All the ```r0_to_dl1`` stage job logs are stored ``/fefs/aswg/data/mc/running_analysis/.../job_logs`` and later
moved to ``/fefs/aswg/data/mc/analysis_logs/.../``.

Every time a full MC production is launched, two files with logging information are created:

- ``log_reduced_Prod{3,5}_{PROD_ID}.yml``
- ``log_onsite_mc_r0_to_dl3_Prod{3,5}_{PROD_ID}.yml``

The first one contains a reduced summary of all the scheduled `job ids` (to which particle the job corresponds to),
while the second one contains the same plus all the commands passed to slurm.

Steps explanation
-----------------

Job dependency between stages is done automatically. Also, the directory structure is created by every stage.
    - If the full workflow is launched, directories will not be verified as containing data. Overwriting will only happen when a MC prods sharing the same ``prod_id`` and analysed the same day is run
    - If each step is launched independently (advanced users), no overwriting directory will take place prior confirmation from the user

Example of default directory structure for a prod5 MC prod:

.. code-block::


   /fefs/aswg/data/
    ├── mc/
    |   ├── DL0/20200629_prod5_trans_80/{particle}/zenith_20deg/south_pointing/
    |   |   └── simtel files
    |   |
    |   ├── running_analysis/20200629_prod5_trans_80/{particle}/zenith_20deg/south_pointing/
    |   |   └── YYYYMMDD_v{lstchain}_{prod_id}/
    |   |       └── temporary dir for r0_to_dl1 + merging stages
    |   |
    |   ├── analysis_logs/20200629_prod5_trans_80/{particle}/zenith_20deg/south_pointing/
    |   |   └── YYYYMMDD_v{lstchain}_{prod_id}/
    |   |       ├── file_lists_training/
    |   |       ├── file_lists_testing/
    |   |       └── job_logs/
    |   |
    |   ├── DL1/20200629_prod5_trans_80/{particle}/zenith_20deg/south_pointing/
    |   |   └── YYYYMMDD_v{lstchain}_{prod_id}/
    |   |       ├── dl1 files
    |   |       ├── training/
    |   |       └── testing/
    |   |
    |   ├── DL2/20200629_prod5_trans_80/{particle}/zenith_20deg/south_pointing/
    |   |   └── YYYYMMDD_v{lstchain}_{prod_id}/
    |   |       └── dl2 files
    |   |
    |   └── IRF/20200629_prod5_trans_80/zenith_20deg/south_pointing/
    |       └── YYYYMMDD_v{lstchain}_{prod_id}/
    |           ├── off0.0deg/
    |           ├── off0.4deg/
    |           └── diffuse/
    |
    └── models/
        └── 20200629_prod5_trans_80/zenith_20deg/south_pointing/
            └── YYYYMMDD_v{lstchain}_{prod_id}/
                ├── reg_energy.sav
                ├── reg_disp_vector.sav
                └── cls_gh.sav



Real Data analysis
------------------

Real data analysis is not supposed to be supported by these scripts. Use at your own risk.


Pipeline Support
----------------

So far the reference pipeline is ``lstchain`` and only with it a full analysis is possible.
There is however support for ``ctapipe`` and ``hiperta`` as well.
The processing up to dl1 is relatively agnostic of the pipeline; working implementations exist for all of them.

In the case of ``hiperta`` a custom script converts the dl1 output to ``lstchain`` compatible files and the later stages
run using ``lstchain`` scripts.

In the case of ``ctapipe`` dl1 files can be produced using ``ctapipe-stage1``. Once the dependency issues are solved and
ctapipe 0.12 is released, this will most likely switch to using ``ctapipe-process``. We do not have plans to keep supporting older
versions longer than necessary currently.
Because the files are not compatible to ``lstchain`` and there is no support for higher datalevels in ``ctapipe`` yet, it is not possible
to use any of the following stages. This might change in the future.
