lstMCpipe
=========

.. image:: https://travis-ci.com/cta-observatory/lstmcpipe.svg?branch=master
    :target: https://travis-ci.com/github/cta-observatory/lstmcpipe

Scripts to ease the reduction of MC data on the LST cluster at La Palma.   

Contact:
Thomas Vuillaume, thomas.vuillaume [at] lapp.in2p3.fr
Enrique Garcia, garcia [at] lapp.in2p3.fr


Install
-------

.. code-block::

    git clone https://github.com/cta-observatory/lstmcpipe.git
    cd lstmcpipe
    pip install .


You can install this library as an independent package (Note that it uses various ``lstchain_*`` scripts).
This will give you the possibility to run ``onsite_`` commands from anywhere.


Quickstart
----------

The way to launch either the full pipeline (r0 to IRFs) or a workflow with less stages (r0 to merging, for example) is
the same; you should run the same command/launch the same script in any case;

.. code-block:: python

    python onsite_mc_r0_to_dl3.py -c config_MC_prod.yml -conf_lst lstchain_*.json

The ``onsite_mc_r0_to_dl3.py`` script is the **orchestrator** of the pipeline, it schedules the stages specified in the
`onsite_MC_prod.yml` file. All the configuration related with the MC pipe must be declared in this file (stages,
particles to be analysed, zenith, pointing, type of MC production...).

Note: You can always launch this command without fear; there is an intermediate step that verifies and
shows the configuration that you are passing to the pipeline.


----------

The full workflow schedules the following stages (scripts) per particle;

1. ``onsite_mc_r0_to_dl1.py``
2. ``onsite_mc_merge_and_copy_dl1.py``
3. ``onsite_mc_train.py``
    3.1. ``plots/plot_models_importances.py``
4. ``onsite_mc_dl1_to_dl2.py``
5. ``onsite_mc_dl2_to_irfs.py``

by using the slurm scheduling job manager system at LP cluster and the dependencies between each stage.


Each 'onsite' stage calls a lstchain script; i.e., ``onsite_mc_r0_to_dl1.py`` will call the ``lstchain_mc_r0_to_dl1``
script, and successively.
In the ``onsite_mc_dl2_to_irfs`` stage, the ``lstchain_create_irf_file`` lstchain tool is invoked.

Configuration of the pipeline
*****************************

``onsite_mc_r0_to_dl3.py`` passes the configuration and all the needed arguments to the consecutive stages. The
pipeline uses two configuration files;

- The ``config_MC_prod.yml`` file (details all the MC production related arguments; paths, ``prod3`` or ``prod5`` ...),
- The ``lstchain_*.json`` configuration file (lstchain related configuration; tailcuts, integrator, RF arguments ...).

Changing the default arguments on each script of the pipeline: **Use at your own risk.**

**PLEASE NOTE** that the library is **extremely job heavy**. Think about other LP-IT cluster users.

MC production logs
******************
All the ```r0_to_dl1`` stage job logs are stored ``/fefs/aswg/data/mc/running_analysis/.../job_logs`` and later
moved to ``/fefs/aswg/data/mc/analysis_logs/.../``.

A single MC production is extremely job heavy, it schedules around ~1000 jobs (configurable so that this number can be
reduced), most of them at the ``r0_to_dl1`` stage.

Every time a full MC production is launched, two files with logging information are created:

- ``log_reduced_Prod{3,5}_{PROD_ID}.yml``
- ``log_onsite_mc_r0_to_dl3_Prod{3,5}_{PROD_ID}.yml``

The first one contains a reduced summary of all the scheduled `job ids` (to which particle the job corresponds to),
while the second one contains the same plus all the commands passed to slurm.

You can load the second file as a dictionary as follows (useful to re-schedule precise jobs, if needed);

.. code-block:: python

    import yaml
    with open('/path/to/log/file') as f:
        prod = yaml.safe_load(f)

    # for example;
    print(prod.keys())
    print(prod['r0_to_dl1'].keys())


Steps explanation
-----------------

- `onsite_mc_r0_to_dl1.py`
    - makes the training / testing separation (set to 0.5 0.5 by default).
    - performs the ``r0_to_dl1`` stage for each particle
    - the number of jobs per particle can be configured
    - mandatory input: directory containing DL0 data that you want to analyse. e.g; ``/fefs/aswg/data/mc/DL0/20190909/proton/North_pointing``
    - results can be found in ``running_analysis``

- `onsite_mc_merge_and_copy_dl1.py`
    - to be run once all jobs from ``onsite_mc_dl0_to_dl1.py`` are finished
    - check that all jobs finished without error from the logs
    - merge the DL1 files for training and testing. Mandatory input: directory containing all the DL1 files to be merged
    - clean and move the ``running_analysis`` directory into ``DL1`` and ``analysis_logs``

- `onsite_mc_train.py`
    - train three random forest using the merged DL1 merged files. Two RF regressors for Energy and disp_norm reconstruction and a RF gamma/hadron classifier.
    - models will be stored in the ``models`` directory
    - mandatory arguments: same as ``lstchain_mc_trainpipe.py`` script (gamma-diffuse and proton DL1 files)

- `onsite_mc_dl1_to_dl2.py`
    - perform the ``dl1_to_dl2`` using the trained models and the DL1 data created in previous stages
    - DL2 data can be found in ``DL2`` directory
    - mandatory arguments: same as ``lstchain_dl1_to_dl2.py`` script (models and DL1 files)

- `onsite_mc_dl2_to_irfs.py`
    - runs the lstchain ``lstchain_create_irf_file.py`` tool
    - checks that DL2 files were created successfully and selects the correct DL2 files depending on the IRF configuration arguments
    - mandatory arguments: same as tool script mentioned above (gamma, proton and electron DL2)



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



**Note:** by default, some (job heavy) scripts only print the commands instead of executing them for double check.
Edit them and uncomment ``os.system(cmd)`` to execute all.


Real Data analysis
------------------

Real data analysis is not supposed to be supported by these scripts. Use at your own risk.
