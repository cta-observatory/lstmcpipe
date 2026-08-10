==============================
Pipelines & configs generation
==============================

A *pipeline* is described by a ``lstmcpipe`` config file: the list of stages to run and, for each stage,
the list of input and output paths.
Writing all these paths by hand is error prone, so ``lstmcpipe`` ships one ``PathConfig`` class per supported
pipeline (in :mod:`lstmcpipe.config.paths_config`) that knows where the MC data live on the cluster and builds
the whole directory tree for you.

The command line tool ``lstmcpipe_generate_config`` instantiates one of these classes and dumps the resulting
config file.

.. contents::
    :local:
    :depth: 2


------------------------------
Generating a config: the tools
------------------------------

Quickstart
==========

**On the cluster** (see `Where to run it`_), in an environment with ``lstchain`` and ``lstmcpipe`` installed:

.. code-block:: bash

    lstmcpipe_generate_config PathConfigAllSkyFull --prod_id 20240101_v0.10.5_my_prod --dec_list dec_2276

This writes two files in the current directory:

* ``lstmcpipe_config_<today>_PathConfigAllSkyFull.yaml`` — the lstmcpipe config
* ``lstchain_config_<today>.json`` — a standard lstchain MC config

Both **must be reviewed and edited** (see `After generation: what to check`_) before running:

.. code-block:: bash

    lstmcpipe -c lstmcpipe_config_<today>_PathConfigAllSkyFull.yaml -conf_lst lstchain_config_<today>.json


Command line arguments
======================

.. list-table::
   :header-rows: 1
   :widths: 22 48 30

   * - Argument
     - Description
     - Default
   * - ``config_class``
     - **Positional and required.** Name of the ``PathConfig`` class to use, e.g. ``PathConfigAllSkyFull``.
       See `Which config class should I use?`_. Running the command with ``--help`` prints the list of
       implemented classes.
     - —
   * - ``--prod_id``
     - Production ID. It is used to name the directories and files of the production, so make it unique and
       explicit: date, lstchain version and a hint of what it is, e.g. ``20240101_v0.10.5_dec2276_crab_tuned``.
     - ``prod_00`` (never keep it)
   * - ``--output``, ``-o``
     - Path of the generated lstmcpipe config file.
     - ``lstmcpipe_config_<date>_<config_class>.yaml`` in the current directory
   * - ``--lstchain_conf``
     - Path of the generated lstchain config file.
     - ``lstchain_config_<date>.json`` in the current directory
   * - ``--overwrite``
     - Overwrite the output files if they already exist. Without it, an existing file raises
       ``FileExistsError``.
     - off
   * - ``--dec_list``
     - One or several declination lines, space separated, e.g. ``--dec_list dec_2276 dec_931``.
       Only for classes whose constructor takes a ``dec_list`` (the ``...Full...`` ones).
       For single-declination classes, use ``--kwargs dec=dec_2276`` instead.
     - ``None``
   * - ``--source_prod_id``
     - ``prod_id`` of an existing production to start from. Only for classes that restart from existing data
       (``...DL1ab``, ``PathConfigAllTrainTestDL1b``).
     - ``None``
   * - ``--kwargs``
     - Any other argument of the config class constructor, as ``key=value`` pairs separated by spaces, e.g.
       ``--kwargs dec=dec_2276 zenith=zenith_40deg``.
     - ``None``

``--dec_list``, ``--source_prod_id`` and ``--kwargs`` are all simply forwarded to the constructor of the
requested class, so **the arguments you may use depend on the class you asked for**. Passing an argument a
class does not accept raises ``TypeError: __init__() got an unexpected keyword argument ...``.

.. code-block:: bash

    # these two commands are strictly equivalent
    lstmcpipe_generate_config PathConfigAllSkyFullDL1ab --prod_id NEW --dec_list dec_2276 --source_prod_id OLD
    lstmcpipe_generate_config PathConfigAllSkyFullDL1ab --prod_id NEW --dec_list dec_2276 --kwargs source_prod_id=OLD


Known pitfalls with the arguments
=================================

* **A single declination is not a declination list.** Classes handling a single declination
  (``PathConfigAllSkyTraining``, ``PathConfigAllSkyTesting``, their ``DL1ab`` variants…) take ``dec``, not
  ``dec_list``, and there is no ``--dec`` option: pass ``--kwargs dec=dec_2276``.

* **The values passed to --kwargs are always strings.** They are parsed by splitting on ``=`` and no type
  conversion is done, so boolean arguments cannot be turned off from the command line:
  ``--kwargs run_checker=False`` passes the *string* ``"False"``, which is truthy, and the checker still runs.
  To disable a checker, use the `Python API`_.

* **The flavour of the generated lstchain config depends on the config class.** For an AllSky production, the
  standard lstchain MC config is dumped as is (the same one you would get from ``lstchain_dump_config --mc``).
  For the prod3/prod5 pipelines, which have a fixed pointing, the pointing dependent RF features
  (``alt_tel``, ``sin_az_tel``) are removed from it.

* **--prod_id has a default.** Forgetting it silently produces a production called ``prod_00``.


Where to run it
===============

All the ``AllSky`` classes discover the available pointing nodes by **listing the directories** of the
simulations on the cluster (under ``/fefs/aswg/data/mc/DL0/LSTProd2/``). They therefore must be run **on the
La Palma cluster**, otherwise you get::

    FileNotFoundError: The class must be run on the cluster to load available pointing nodes

Likewise, all the classes restarting from an existing production check that the source production exists
(``run_checker``), which also requires access to ``/fefs/aswg/data/``.

Typically:

.. code-block:: bash

    ssh cp02
    source /fefs/aswg/software/conda/etc/profile.d/conda.sh
    conda activate lstchain-v0.10.5
    cd lstmcpipe/production_configs
    mkdir 20240101_my_prod_id && cd 20240101_my_prod_id
    lstmcpipe_generate_config PathConfigAllSkyFull --prod_id 20240101_my_prod_id --dec_list dec_2276

The available declination lines are the sub-directories of the training dataset, and can be listed with:

.. code-block:: bash

    ls /fefs/aswg/data/mc/DL0/LSTProd2/TrainingDataset/GammaDiffuse/

At the time of writing: ``dec_931``, ``dec_2276`` (Crab), ``dec_3476``, ``dec_4822``, ``dec_5573``,
``dec_6166``, ``dec_6166_high_density``, ``dec_6676``, ``dec_min_413``, ``dec_min_1802``, ``dec_min_2924``.
To choose the one matching your source, see the pointings notebook in :doc:`examples/configs_pointings`.


After generation: what to check
===============================

The generated lstmcpipe config looks like:

.. code-block:: yaml

    workflow_kind: lstchain
    prod_id: 20240101_v0.10.5_my_prod
    source_environment:
      source_file: /fefs/aswg/software/conda/etc/profile.d/conda.sh
      conda_env: lstchain-v0.10.7          # <-- edit: the env used to run the production
    slurm_config:
      user_account: dpps                   # <-- edit: `aswg` unless you are lstanalyzer
    lstmcpipe_version: 0.11.0
    prod_type: PathConfigAllSkyFull
    stages_to_run:                         # <-- you may remove stages you do not want to run
      - r0_to_dl1
      - merge_dl1
      - train_pipe
      - dl1_to_dl2
      - dl2_to_irfs
    stages:
      r0_to_dl1:
        - input: /fefs/aswg/data/mc/DL0/LSTProd2/TrainingDataset/GammaDiffuse/dec_2276/sim_telarray/node_.../output_v1.4
          output: /fefs/aswg/data/mc/DL1/AllSky/20240101_v0.10.5_my_prod/TrainingDataset/dec_2276/GammaDiffuse/node_...
      merge_dl1:
        - input: /fefs/aswg/data/mc/DL1/AllSky/.../GammaDiffuse
          output: /fefs/aswg/data/mc/DL1/AllSky/.../dl1_..._merged.h5
          options: --pattern */*.h5 --no-image        # <-- options passed to the lstchain script
          extra_slurm_options:                        # <-- slurm options for this job only
            partition: long
            time: '06:00:00'

Checklist:

#. ``source_environment.conda_env``: the conda environment used to run the production (the generated value is
   only a default, it is **not** your current environment).
#. ``slurm_config.user_account``: ``dpps`` is the account of ``lstanalyzer``; regular users should use ``aswg``.
#. ``stages_to_run``: remove the stages you do not want to run. The entries left in ``stages`` are ignored
   (with a warning). ``r0_to_dl1`` and ``dl1ab`` cannot both be in ``stages_to_run``.
#. the paths themselves: number of pointing nodes, declinations, and the ``prod_id`` appearing in the output
   paths.
#. ``options`` and ``extra_slurm_options`` of the stages, if you need more memory/time or different
   ``lstchain`` options (e.g. ``--gh-efficiency`` for the IRFs).
#. the **lstchain** config, in particular the NSB tuning parameters (see ``lstchain_tune_nsb``).

The config can then be validated with:

.. code-block:: bash

    lstmcpipe_validate_config lstmcpipe_config_<date>_<config_class>.yaml

Note that the config file is a plain YAML file: it can be edited, or even written entirely by hand, if none of
the classes below matches your use case.


Python API
==========

Everything the command line does can be done in python, which is the way to go to pass non-string arguments
(such as ``run_checker=False``) or to inspect/plot the production before dumping it:

.. code-block:: python

    from lstmcpipe.config.paths_config import PathConfigAllSkyFull

    cfg = PathConfigAllSkyFull('20240101_v0.10.5_my_prod', ['dec_2276', 'dec_931'])
    cfg.generate()                                    # builds the paths dict
    cfg.save_yml('lstmcpipe_config.yaml', overwrite=True)

    # useful checks before dumping
    cfg.plot_pointings()                              # training and testing pointings
    print(cfg.paths['r0_to_dl1'])                     # paths of a given stage

``run_checker=False`` skips the verification that the source production exists, which is handy to prepare a
config for a production that is not finished yet, or to work off-cluster:

.. code-block:: python

    from lstmcpipe.config.paths_config import PathConfigAllSkyFullDL1ab

    cfg = PathConfigAllSkyFullDL1ab('NEW_PROD', 'SOURCE_PROD', ['dec_2276'], run_checker=False)


--------------------------------
Which config class should I use?
--------------------------------

.. list-table::
   :header-rows: 1
   :widths: 26 20 26 28

   * - Class
     - Starts from
     - Stages
     - Required arguments
   * - :ref:`PathConfigAllSkyFull <allsky-full>`
     - R0 (simtel)
     - ``r0_to_dl1``, ``merge_dl1``, ``train_pipe``, ``dl1_to_dl2``, ``dl2_to_irfs``
     - ``--prod_id``, ``--dec_list``
   * - :ref:`PathConfigAllSkyFullDL1ab <allsky-dl1ab>`
     - DL1 of an existing prod
     - ``dl1ab``, ``merge_dl1``, ``train_pipe``, ``dl1_to_dl2``, ``dl2_to_irfs``
     - ``--prod_id``, ``--dec_list``, ``--source_prod_id``
   * - :ref:`PathConfigAllTrainTestDL1b <allsky-traintest-dl1b>`
     - merged DL1b of an existing prod
     - ``train_pipe``, ``dl1_to_dl2``
     - ``--prod_id``, ``--dec_list``, ``--source_prod_id``
   * - :ref:`PathConfigAllSkyFullSplitDiffuse <allsky-split-diffuse>`
     - R0 (simtel)
     - ``r0_to_dl1``, ``train_test_split``, ``merge_dl1``, ``train_pipe``, ``dl1_to_dl2``, ``dl2_to_irfs``
     - ``--prod_id``, ``--dec_list``
   * - :ref:`PathConfigAllSkyTraining <allsky-blocks>`
     - R0 (training particles)
     - ``r0_to_dl1``, ``merge_dl1``, ``train_pipe``
     - ``--prod_id``, ``--kwargs dec=``
   * - :ref:`PathConfigAllSkyTrainingWithSplit <allsky-blocks>`
     - R0 (training particles)
     - ``r0_to_dl1``, ``train_test_split``, ``merge_dl1``, ``train_pipe``
     - ``--prod_id``, ``--kwargs dec=``
   * - :ref:`PathConfigAllSkyTesting <allsky-blocks>`
     - R0 (test gammas)
     - ``r0_to_dl1``, ``merge_dl1``, ``dl1_to_dl2``, ``dl2_to_irfs``
     - ``--prod_id``, ``--kwargs dec=``
   * - :ref:`PathConfigAllSkyTestingGammaDiffuse <allsky-blocks>`
     - DL1 diffuse test set produced by ``PathConfigAllSkyTrainingWithSplit``
     - ``merge_dl1``, ``dl1_to_dl2``, ``dl2_to_irfs``
     - ``--prod_id``, ``--kwargs dec=``
   * - :ref:`PathConfigAllSkyTrainingDL1ab <allsky-blocks>`
     - training DL1 of an existing prod
     - ``dl1ab``, ``merge_dl1``, ``train_pipe``
     - ``--prod_id``, ``--source_prod_id``, ``--kwargs dec=``
   * - :ref:`PathConfigAllSkyTestingDL1ab <allsky-blocks>`
     - testing DL1 of an existing prod
     - ``dl1ab``, ``merge_dl1``, ``dl1_to_dl2``, ``dl2_to_irfs``
     - ``--prod_id``, ``--source_prod_id``, ``--kwargs dec=``
   * - :ref:`PathConfigProd5Trans80 <prod5>`
     - R0 (prod5 trans_80)
     - ``r0_to_dl1``, ``train_test_split``, ``merge_dl1``, ``train_pipe``, ``dl1_to_dl2``,
       ``dl2_to_sensitivity``, ``dl2_to_irfs``
     - ``--prod_id``
   * - :ref:`PathConfigProd5Trans80DL1ab <prod5-dl1ab>`
     - DL1 of an existing prod5 prod
     - ``dl1ab``, ``train_pipe``, ``dl1_to_dl2``, ``dl2_to_sensitivity``, ``dl2_to_irfs``
     - ``--prod_id``, ``--source_prod_id``

In short:

* you want a **complete AllSky production from the simulations**: ``PathConfigAllSkyFull``
  (or ``PathConfigAllSkyFullSplitDiffuse`` if you need full-enclosure IRFs);
* you want a **tuned production** (e.g. NSB matching a given field of view) from an existing one:
  ``PathConfigAllSkyFullDL1ab``;
* you only want to **retrain models and re-apply them** on existing DL1b: ``PathConfigAllTrainTestDL1b``;
* you want to **run only a part of the pipeline**, one declination at a time, or to assemble a non standard
  production: the building blocks listed in :ref:`allsky-blocks`.

.. _prod5:

-----------------------
Prod3 & Prod5 pipelines
-----------------------

Here is the typical MC pipeline for the prod3 and prod5 productions

..
    All mermaid graph are commented here and images pointing to URLs. TO FIX.

..
    .. mermaid::

        flowchart LR
            subgraph R0
                gamma[R0 gamma]
                proton[R0 proton]
                electron[R0 electron]
            end

            gamma --> |r0_to_dl1| gamma_dl1[DL1 gamma]
            proton --> |r0_to_dl1| proton_dl1[DL1 proton]
            electron --> |r0_to_dl1| electron_dl1[DL1 electron]

            subgraph DL1
                direction LR
                gamma_dl1
                proton_dl1
                electron_dl1
            end


            subgraph DL1-test[DL1 test]
                direction LR
                gamma_dl1_test[DL1 gamma]
                proton_dl1_test[DL1 proton]
                electron_dl1_test[DL1 electron]
            end

            subgraph DL1-train[DL1 train]
                gamma_dl1_train[DL1 gamma]
                proton_dl1_train[DL1 proton]
            end


            gamma_dl1 --> train_test_split((train_test_split))
            proton_dl1 --> train_test_split
            train_test_split --> DL1-train
            train_test_split --> gamma_dl1_test & proton_dl1_test
            DL1-train --> train_pipe((train_pipe))
            train_pipe --> models
            models .-> real-data

            electron_dl1 --> electron_dl1_test

            subgraph DL2-test[DL2 test]
                direction LR
                gamma_dl2_test[DL2 gamma]
                proton_dl2_test[DL2 proton]
                electron_dl2_test[DL2 electron]
            end

            models --> DL2-test
            DL1-test --> DL2-test

            DL2-test --> |dl2_to_irf| IRF[IRFs]
            DL2-test --> |dl2_to_sensitivity| SENS[Sensitivity]
            SENS --> plot[png plots]

.. image:: https://mermaid.ink/img/pako:eNqdVV1rwjAU_SshD0NBh_row57cYOD2oI9tKZmNGkiTkqQbYv3vy4dN01YtW0C4vfec9Nx7LvYMdzzDcAmBPnvKf3ZHJBRYb2IGrkeWXweBiiPYzJqkOQeU5yjazFyQtIuF4IozU3VRp4wp3inhAHUcQDDLYtY82heA6fQFVGKWKp5mdF65rAmj1XreE-Fe2yO5tGf1xNViesS64KmB7BvD0oh2xxkRGk_0zeFwfXfm2lsT7OdDIb2J3VYyVVgqK9oEyZ-FpZ5_3-o27qHpbeiw_e1WBCLM9WKi5K5kjxvS7IH9ZegO1V9v18MybSOpLChRo1E3Mx53F_IuuQF2KxbuWx_AtT0DT113Grq_MZBTkALXXZg41N9kLSHX_xtUNmX3DJ51SWBEpxlSKBxdaL69oLcNdyxf1Nu7-N_2LlLPf7gJAW5oewPo8PZeB-NMdM10TDBGtcshYNEAKvtqnhKxr8D75i3SP5kMgCVmkijyTdSpAtvXz220bTIB2ZQssaBcRQU72EAmcAJzLHJEMv2ZOBt8DNUR5ziGSx1meI9KqmIYs4uGloU2Hr9mRHEBl3tEJZ5AVCq-PbEdXCpR4hq0Ikh7nNdJbDkf7nNkv0qXX-IaAyQ?type=png)](https://mermaid.live/edit#pako:eNqdVV1rwjAU_SshD0NBh_row57cYOD2oI9tKZmNGkiTkqQbYv3vy4dN01YtW0C4vfec9Nx7LvYMdzzDcAmBPnvKf3ZHJBRYb2IGrkeWXweBiiPYzJqkOQeU5yjazFyQtIuF4IozU3VRp4wp3inhAHUcQDDLYtY82heA6fQFVGKWKp5mdF65rAmj1XreE-Fe2yO5tGf1xNViesS64KmB7BvD0oh2xxkRGk_0zeFwfXfm2lsT7OdDIb2J3VYyVVgqK9oEyZ-FpZ5_3-o27qHpbeiw_e1WBCLM9WKi5K5kjxvS7IH9ZegO1V9v18MybSOpLChRo1E3Mx53F_IuuQF2KxbuWx_AtT0DT113Grq_MZBTkALXXZg41N9kLSHX_xtUNmX3DJ51SWBEpxlSKBxdaL69oLcNdyxf1Nu7-N_2LlLPf7gJAW5oewPo8PZeB-NMdM10TDBGtcshYNEAKvtqnhKxr8D75i3SP5kMgCVmkijyTdSpAtvXz220bTIB2ZQssaBcRQU72EAmcAJzLHJEMv2ZOBt8DNUR5ziGSx1meI9KqmIYs4uGloU2Hr9mRHEBl3tEJZ5AVCq-PbEdXCpR4hq0Ikh7nNdJbDkf7nNkv0qXX-IaAyQ


To generate a config for that pipeline, you may run:

.. code-block::

    lstmcpipe_generate_config PathConfigProd5Trans80 --prod_id whatagreatprod

``PathConfigProd5Trans80`` also accepts a ``zenith`` argument (default ``zenith_20deg``), which selects the
zenith directory of the prod5 dataset:

.. code-block::

    lstmcpipe_generate_config PathConfigProd5Trans80 --prod_id whatagreatprod --kwargs zenith=zenith_40deg

Note that this pipeline is the only one running the ``dl2_to_sensitivity`` stage; the sensitivity plots
(``.png`` next to the ``.fits.gz`` files) are produced automatically as part of that stage.

**IMPORTANT NOTE:** prod5 MC files need the config to set "focal_length_choice": "EQUIVALENT" to be analyzed with ``lstchain >= v0.9``

In the lstchain config, please set:

.. code-block:: json

    "source_config": {
        "EventSource": {
            "focal_length_choice": "EQUIVALENT"
        }
    }


.. _prod5-dl1ab:

Prod5 DL1ab
===========

One can also start back from DL1, applying the dl1ab stage:

..
    .. mermaid::

        flowchart LR
            subgraph DL1a
                gamma[DL1 gamma]
                proton[DL1 proton]
                electron[DL1 electron]
            end

            gamma --> |dl1ab| gamma_dl1[DL1 gamma]
            proton --> |dl1ab| proton_dl1[DL1 proton]
            electron --> |dl1ab| electron_dl1[DL1 electron]

            subgraph DL1b
                direction LR
                gamma_dl1
                proton_dl1
                electron_dl1
            end


            subgraph DL1-test[DL1 test]
                direction LR
                gamma_dl1_test[DL1 gamma]
                proton_dl1_test[DL1 proton]
                electron_dl1_test[DL1 electron]
            end

            subgraph DL1-train[DL1 train]
                gamma_dl1_train[DL1 gamma]
                proton_dl1_train[DL1 proton]
            end


            gamma_dl1 --> train_test_split((train_test_split))
            proton_dl1 --> train_test_split
            train_test_split --> DL1-train
            train_test_split --> gamma_dl1_test & proton_dl1_test
            DL1-train --> train_pipe((train_pipe))
            train_pipe --> models
            models .-> real-data

            electron_dl1 --> electron_dl1_test

            subgraph DL2-test[DL2 test]
                direction LR
                gamma_dl2_test[DL2 gamma]
                proton_dl2_test[DL2 proton]
                electron_dl2_test[DL2 electron]
            end

            models --> DL2-test
            DL1-test --> DL2-test

            DL2-test --> |dl2_to_irf| IRF[IRFs]
            DL2-test --> |dl2_to_sensitivity| SENS[Sensitivity]
            SENS --> plot[png plots]

.. image:: https://mermaid.ink/img/pako:eNqVVMGKwjAQ_ZWQw6KgC_boYU-6sODuwR5tKbFNNZCmJU13Eeu_b5o0aVKt7BaE6Zs3M6_zYq4wLTMM1zCn5U96RlyA3T5iQD51czxxVJ3BZrdCGuqeEyoKdJCYjuIhU_FSlEyldOjkMMWp4H3WvPR5zLKI6VC1BMvlG2gzukLHViOJfLkbqWd4ZA1ZtqfCDPUKDGhLHGn3WzgO35MRLolEtjPrsvK7XuOl-Jg71VvB_cilwLVQyrog_rOAxNY9dsnnTNrl06Z98yVzRLTRKoofyrOcZ_osyXfSXZZtqXxVFUpwUleUiNlsjMzn7umZLNSkMaqo9hOfcHwfwMt467rUdnIkVKTCRnUXG70DosiF_NfSWqd0DF4lzDGiywwJZNbjGqkK75x9YGFgTl3wv1MXJLZu0lWH8-zUObTpU9d_uDZFi3YW2y3eT5lkMCRbNapMCM9b8LF_P8hfHT8h1pjVRJBvIi4tCLdf4SEckL6wg1VRRUtxqNhJBV1buIAF5gUimbxyrx07guKMCxzBtQwznKOGighG7CapTSWtxNuMiJLDdY5ojRcQNaIMLyyFa8EbbEgbgqR7hWVhVfSp73Z1xd9-AWAY62k?type=png)](https://mermaid.live/edit#pako:eNqVVMGKwjAQ_ZWQw6KgC_boYU-6sODuwR5tKbFNNZCmJU13Eeu_b5o0aVKt7BaE6Zs3M6_zYq4wLTMM1zCn5U96RlyA3T5iQD51czxxVJ3BZrdCGuqeEyoKdJCYjuIhU_FSlEyldOjkMMWp4H3WvPR5zLKI6VC1BMvlG2gzukLHViOJfLkbqWd4ZA1ZtqfCDPUKDGhLHGn3WzgO35MRLolEtjPrsvK7XuOl-Jg71VvB_cilwLVQyrog_rOAxNY9dsnnTNrl06Z98yVzRLTRKoofyrOcZ_osyXfSXZZtqXxVFUpwUleUiNlsjMzn7umZLNSkMaqo9hOfcHwfwMt467rUdnIkVKTCRnUXG70DosiF_NfSWqd0DF4lzDGiywwJZNbjGqkK75x9YGFgTl3wv1MXJLZu0lWH8-zUObTpU9d_uDZFi3YW2y3eT5lkMCRbNapMCM9b8LF_P8hfHT8h1pjVRJBvIi4tCLdf4SEckL6wg1VRRUtxqNhJBV1buIAF5gUimbxyrx07guKMCxzBtQwznKOGighG7CapTSWtxNuMiJLDdY5ojRcQNaIMLyyFa8EbbEgbgqR7hWVhVfSp73Z1xd9-AWAY62k

The corresponding class is ``PathConfigProd5Trans80DL1ab``. It replaces the ``r0_to_dl1``,
``train_test_split`` and ``merge_dl1`` stages by a single ``dl1ab`` stage applied to the **already merged**
DL1 files of the source production:

.. code-block::

    lstmcpipe_generate_config PathConfigProd5Trans80DL1ab --prod_id anothergreatprod --source_prod_id whatagreatprod

The class checks at generation time that all the merged DL1 files of ``source_prod_id`` exist, and raises
``FileNotFoundError`` on the first missing one. Use the `Python API`_ with ``run_checker=False`` to bypass
this check. The ``zenith`` argument is available here as well.


.. _allsky:

--------------------------
AllSky production pipeline
--------------------------

.. _allsky-full:

R0 to IRFs
==========

Standard AllSky production pipeline **for one training declination**

..
    .. mermaid::

        flowchart LR

            R0-Protons[R0 Protons \n - node a\n - node b\n - node c]
            R0-GammaDiffuse[R0 GammaDiffuse \n - node a\n - node b\n - node c]
            R0-GammaTest[R0 Gamma Test \n - node a\n - node b\n - node c]

            DL1-Protons[DL1 Protons \n - node a\n - node b\n - node c]
            DL1-GammaDiffuse[DL1 GammaDiffuse \n - node a\n - node b\n - node c]
            DL1-GammaTest[DL1 Gamma Test \n - node a\n - node b\n - node c]


            R0-GammaDiffuse --> |r0_to_dl1| DL1-GammaDiffuse
            R0-Protons --> |r0_to_dl1| DL1-Protons
            R0-GammaTest --> |r0_to_dl1| DL1-GammaTest


            DL1-GammaDiffuse --> |merge_dl1| DL1-GammaDiffuse-merged[DL1 Gamma Diffuse\nall nodes]
            DL1-Protons --> |merge_dl1| DL1-Protons-merged[DL1 Protons\nall nodes]

            DL1-GammaDiffuse-merged & DL1-Protons-merged --> train_pipe((train_pipe))

            train_pipe --> models .-> real_data[Real Data]

            models --> DL2-GammaTest

            DL1-GammaTest --> |merge_dl1| DL1-GammaTest-merged[DL1 Gamma Test \n - node a merged\n - node b merged\n - node c merged]
            DL1-GammaTest-merged ----> DL2-GammaTest
            DL2-GammaTest[DL2 Gamma Test \n - node a merged\n - node b merged\n - node c merged]

            DL2-GammaTest --> |dl2_to_irf| IRF-GammaTest
            IRF-GammaTest[IRF Gamma Test \n - node a merged\n - node b merged\n - node c merged]

.. image:: https://mermaid.ink/img/pako:eNqtVV1rgzAU_SshD6OFOloffdiT2xh0MNzemiJ3JrZCjCVGxmj735eoVTMjbN18Orkf5557c9UjTgrKcIBTXnwke5AKrSMiiEDtEy29F1moQpSbaIlaiIgO8JDQqQgG-H2Ak61F8gh5DmGWplXJDNPwfC3dGytVx4XM6adMPVe4XnUNanxth4bGatFw_aXHjrBusmP7ZZeTV4A87w6d5DJWRUz56jRqwLUBzqTW576d6TLGayv8rqDJzZncMbdEr_bRwXAu2okAzus5lFvnVTu5W9-Q9tKcTTituc1FNw7CuqaSkIn4kB3YbNbj-XxI2tvrlFxX5SW61VAy4DEFBZtIIxRqZMlpQ01WuPbtQTsXa3rGxjse8Gj7UBMyXMKxKWlNU-vdD8ihvM_wrRfC_y9JEyWa0VDum93NZHpCT9GDS5hl3ujTfwnDC6xxDhnV3-ejKUiw2rOcERxoSFkKFVcEE3HWodVBLwa7p5kqJA5S4CVbYKhU8fopEhwoWbFLUJjBTkLeRbE66bn5EdT_g_MXmSDsTg?type=png)](https://mermaid.live/edit#pako:eNqtVV1rgzAU_SshD6OFOloffdiT2xh0MNzemiJ3JrZCjCVGxmj735eoVTMjbN18Orkf5557c9UjTgrKcIBTXnwke5AKrSMiiEDtEy29F1moQpSbaIlaiIgO8JDQqQgG-H2Ak61F8gh5DmGWplXJDNPwfC3dGytVx4XM6adMPVe4XnUNanxth4bGatFw_aXHjrBusmP7ZZeTV4A87w6d5DJWRUz56jRqwLUBzqTW576d6TLGayv8rqDJzZncMbdEr_bRwXAu2okAzus5lFvnVTu5W9-Q9tKcTTituc1FNw7CuqaSkIn4kB3YbNbj-XxI2tvrlFxX5SW61VAy4DEFBZtIIxRqZMlpQ01WuPbtQTsXa3rGxjse8Gj7UBMyXMKxKWlNU-vdD8ihvM_wrRfC_y9JEyWa0VDum93NZHpCT9GDS5hl3ujTfwnDC6xxDhnV3-ejKUiw2rOcERxoSFkKFVcEE3HWodVBLwa7p5kqJA5S4CVbYKhU8fopEhwoWbFLUJjBTkLeRbE66bn5EdT_g_MXmSDsTg

To produce a config to run such a pipeline, typically run **on the cluster**:

.. code-block::

    lstmcpipe_generate_config PathConfigAllSkyFull --prod_id whatagreatprod --dec_list dec_2276


This will generate a lstmcpipe config file and a lstchain config file.

Please:
 * check thoroughly the lstmcpipe config
 * modify the lstchain config as you wish

Several declination lines can be trained in a single production. They are simply listed after ``--dec_list``:

.. code-block::

    lstmcpipe_generate_config PathConfigAllSkyFull --prod_id whatagreatprod --dec_list dec_2276 dec_931 dec_min_413

In that case, one set of models is trained per declination, and the ``dl1_to_dl2`` and ``dl2_to_irfs`` stages
are run once per declination on the (single, declination independent) test dataset. The ``r0_to_dl1`` and
``merge_dl1`` stages of the test dataset are generated only once, for the first declination of the list.


.. _allsky-dl1ab:

DL1ab
=====

The DL1ab workflow is very similar, only starting from an existing DL1 dataset.

This workflow is typically used when a tuned production is needed for a given dataset.
For example, a production specifically tuned to match the Crab FoV NSB level and analyse Crab data.
In this case, you should produce your own lstchain config file using lstchain tools (see lstchain documentation).


..
    .. mermaid::

        flowchart LR

            DL1-Protons[DL1 Protons \n - node a\n - node b\n - node c]
            DL1-Protonsb[DL1 Protons tuned \n - node a\n - node b\n - node c]
            DL1-GammaDiffuse[DL1 GammaDiffuse \n - node a\n - node b\n - node c]
            DL1-GammaDiffuseb[DL1 GammaDiffuse tuned \n - node a\n - node b\n - node c]
            DL1-GammaTest[DL1 Gamma Test \n - node a\n - node b\n - node c]
            DL1-GammaTestb[DL1 Gamma Test tuned \n - node a\n - node b\n - node c]

            DL1-GammaDiffuse --> |dl1ab| DL1-GammaDiffuseb
            DL1-Protons --> |dl1ab| DL1-Protonsb
            DL1-GammaTest --> |r0_to_dl1| DL1-GammaTestb


            DL1-GammaDiffuseb --> |merge_dl1| DL1-GammaDiffuse-merged[DL1 Gamma Diffuse tuned\nall nodes]
            DL1-Protonsb --> |merge_dl1| DL1-Protons-merged[DL1 Protons tuned\nall nodes]

            DL1-GammaDiffuse-merged & DL1-Protons-merged --> train_pipe((train_pipe))

            train_pipe --> models .-> real-data

            models --> DL2-GammaTest

            DL1-GammaTestb --> |merge_dl1| DL1-GammaTest-merged[DL1 Gamma Test tuned \n - node a merged\n - node b merged\n - node c merged]
            DL1-GammaTest-merged ----> DL2-GammaTest
            DL2-GammaTest[DL2 Gamma Test \n - node a merged\n - node b merged\n - node c merged]

            DL2-GammaTest --> |dl2_to_irf| IRF-GammaTest
            IRF-GammaTest[IRF Gamma Test \n - node a merged\n - node b merged\n - node c merged]


.. image:: https://mermaid.ink/img/pako:eNqtVMtugzAQ_BXLhyqRQtVw5NATbVUplaq0t1BFCzaNJWMiY1RVIf9eY6A8bA5Jy2nZnR3PPuwTTnJCcYBTnn8lB5AKbbaRiATSX7hZe68yV7kodtpGrY0iHfaQ0IkIBnY8sJMPiyIecahSUHIp0xNkGYQsTcuCGrah4y9ksc12vcB3WqieD9W_V_PEU6KLZLmLRZ53jyrC1xBXdiesuVnwbp4OuQ1W3u1VvtcZ1aSYWtHMAJrMjMpPOslsEZ6JkUE_RpPSlQPnpvTCsXtO-jY4ZB6t54TTrbzNRjcOSnOqksDE_siOdLHo7eWyI-x9Bp7p03iBbrUpKXCPgIIO2sZqWLjx-8Za2ky351tah-1-zuwXaoDDNbNdSety7XDfDIfwBu2Pbo4_d3MuleKg77bZr1eUybRCz9vHqaCRa6f__ksQXmFtZ8CIfnJP9WERVgea0QgH2iQ0hZKrCEfirKHlUQ-fPhCmcomDFHhBVxhKlb99iwQHSpa0A4UMPiVkvyhqkl6at9088ecfuL_tWw?type=png)](https://mermaid.live/edit#pako:eNqtVMtugzAQ_BXLhyqRQtVw5NATbVUplaq0t1BFCzaNJWMiY1RVIf9eY6A8bA5Jy2nZnR3PPuwTTnJCcYBTnn8lB5AKbbaRiATSX7hZe68yV7kodtpGrY0iHfaQ0IkIBnY8sJMPiyIecahSUHIp0xNkGYQsTcuCGrah4y9ksc12vcB3WqieD9W_V_PEU6KLZLmLRZ53jyrC1xBXdiesuVnwbp4OuQ1W3u1VvtcZ1aSYWtHMAJrMjMpPOslsEZ6JkUE_RpPSlQPnpvTCsXtO-jY4ZB6t54TTrbzNRjcOSnOqksDE_siOdLHo7eWyI-x9Bp7p03iBbrUpKXCPgIIO2sZqWLjx-8Za2ky351tah-1-zuwXaoDDNbNdSety7XDfDIfwBu2Pbo4_d3MuleKg77bZr1eUybRCz9vHqaCRa6f__ksQXmFtZ8CIfnJP9WERVgea0QgH2iQ0hZKrCEfirKHlUQ-fPhCmcomDFHhBVxhKlb99iwQHSpa0A4UMPiVkvyhqkl6at9088ecfuL_tWw


The workflow then starts from a base production (the `source_prod_id`), produces new tuned DL1 (dl1ab steps) and trains a new set of models.

To prepare the lstmcpipe config, you want to:

- find a base production to start with (see the list of productions in the `documentation <productions>` and look for the latest "base" or "unuted" one) 
- run **on the cluster**:

.. code-block::

    lstmcpipe_generate_config PathConfigAllSkyFullDL1ab --dec_list dec_2276 --prod_id anothergreatprod --kwargs source_prod_id=whatagreatprod

or, equivalently, using the dedicated option:

.. code-block::

    lstmcpipe_generate_config PathConfigAllSkyFullDL1ab --dec_list dec_2276 --prod_id anothergreatprod --source_prod_id whatagreatprod

At generation time, the pointing nodes of the source production are checked one by one: a node that exists in
the simulations but not in the source production triggers a warning and is dropped from the new production.
Read the warnings, they tell you what will *not* be reprocessed.


.. _allsky-traintest-dl1b:

Retrain and apply a model
=========================

..
    .. mermaid::

        flowchart LR

        subgraph pa[PROD A]
            direction TB
            gamma[DL1b merged gamma training]
            proton[DL1b merged proton training]
            gammaps[DL1b gamma testing\n- node 1\n- node  2\n...]
        end

        gamma & proton --> models

        %% DL1train --> train_pipe((train_pipe))

        models[models B] .-> real-data

        models & gammaps --> DL2-GammaTest[DL2 gamma testing\n- node 1\n- node  2\n...]


.. image:: https://mermaid.ink/img/pako:eNqVUstqwzAQ_BUhSEkgNsRHHwoNLr2ktKS5WaFsrI0jsB7IMqWE_HvXUkwa6KXyQePVzKxG0pk3ViIv-bGzX80JfGCbrTDCMBr9cGg9uBNzUL9v36rsaZ8WxiGVxyYoa9hufau2oDXU1WZ1YBp9izJVWPCgjDLtLwPnbbDmjptKf5Gji-sT-2qJfSCSECZjhkKw1Q2ygnCe51cHNHLKlLQPU6sse2SaFF0_EWYzRk3iFuJqRJ9OOZzPb3ixmPhJXaeJrfcsJ5FH6DIJAe5Z1PcaJFpXmyJ7Gf93FIWiFf9LNn58yensNChJd3geewkeTqhR8JKgxCMMXRBcmAtRB0d7wmepgvW8PELX45LDEOzHt2l4GfyAE6lSQHevpyJGzWt6K_HJXH4Ay4i5SA?type=png)](https://mermaid.live/edit#pako:eNqVUstqwzAQ_BUhSEkgNsRHHwoNLr2ktKS5WaFsrI0jsB7IMqWE_HvXUkwa6KXyQePVzKxG0pk3ViIv-bGzX80JfGCbrTDCMBr9cGg9uBNzUL9v36rsaZ8WxiGVxyYoa9hufau2oDXU1WZ1YBp9izJVWPCgjDLtLwPnbbDmjptKf5Gji-sT-2qJfSCSECZjhkKw1Q2ygnCe51cHNHLKlLQPU6sse2SaFF0_EWYzRk3iFuJqRJ9OOZzPb3ixmPhJXaeJrfcsJ5FH6DIJAe5Z1PcaJFpXmyJ7Gf93FIWiFf9LNn58yensNChJd3geewkeTqhR8JKgxCMMXRBcmAtRB0d7wmepgvW8PELX45LDEOzHt2l4GfyAE6lSQHevpyJGzWt6K_HJXH4Ay4i5SA

The workflow starts from an existing PROD A with merged DL1b datasets, trains a new set of models and applies them to create a new set of DL2.
**Note: In case of source-dependent analysis, the missing parameters are computed on the fly by lstchain, allowing the use of this PathConfig to not recreate DL1 files.**

Example of command to generate such a config:

.. code-block::

    lstmcpipe_generate_config PathConfigAllTrainTestDL1b --dec_list dec_2276 dec_931 --prod_id MY_NEW_PROD --kwargs source_prod_id=PROD-A

Only two stages are generated: ``train_pipe`` (from the merged DL1b of PROD-A) and ``dl1_to_dl2``.
No DL1 file is created, which makes it by far the cheapest way to test a new set of training options
(RF parameters, features, source-dependent analysis...) on an existing production.

At generation time, the merged training DL1 files of the source production are checked for each declination.
A declination whose files are missing is **silently dropped** (with a warning) from the production: check the
generated config contains all the declinations you asked for.

Since this production retrains models, consider reusing the lstchain config of the source production, so that
only the training options you meant to change actually differ.


.. _allsky-split-diffuse:

Using GammaDiffuse to produce full-enclosure IRFs
=================================================

The configs `PathConfigAllSkyTrainingWithSplit`, `PathConfigAllSkyTestingGammaDiffuse` and `PathConfigAllSkyFullSplitDiffuse` introduce the possibility to divide the GammaDiffuse dataset into training and testing datasets:

.. image:: https://mermaid.ink/img/pako:eNqdV9tq4zAQ_RUhaGkhCZbT5vawD0vYZaGFJZunbUJQbCU1-IassHGa_vsqll3XsseR6ydJ58zozIw0tt-wE7kMz_DOj_45r5QL9LRYhasQySc5bPecxq9oYfV_80hEYdJ3mUMUenlcjzNHeFGIlt_L1VC67POYvmQDuq4hW4Vs64ijECdHWOg2iflJg4DOvd3ukLAOivagoj2oaG-gaP5EvigJVAQKMtXTvV57SuD0EDg_xLxkS5YIIzFHbZ5q81OHYghOvdBoV8kEMiA4VA_Bv3JAhEEiXJ_I8yGN3NxISasrbCY2CG4mflV_P2B8z9zOYSgz82g-802C-szvEpt2OAu3ytFROTquQUaqGCnMOCnGyVTMcxbIS8Pa2jjpufo8KdeDqBDbYqkQtZDUpKlPo37_GzpzayOijfR4bmud2kun0bTe5T63Gng3VetCad6KFT1rF9kB3ySx74nzR28wIgO3VtkCoPR1cZZlVAltvzSacikC6Q4a81rUTIIoA1GOoiyOdcXntpPPiqnT0VQZ6_WsZ0VnVPYunUAboVvIQ6Y3y8Em9mJ2d1eO7-8LfeVaRg9krH6CBnLIGfU3LhX0ZSFHaC5H68Lq5qZgXozmT7bebHL0FrqzKg2ub1fA8ghUzvSFDOa-7B-1vlMKy_O2NHpB2fBRhwnbawQH7o_o1-JHZ50e37XrbCZsrxGctj5um3_x1GsLICmItHwPfWSsU6pqUjQkBZG6FD0-1R3k6qUvS-tzw7bQ3Wj9iNCuSq3JQrs2nAvcw3KLgHqu_Dd6uyytsHhlAVvhmRy6bEcPvljhVfguqfQgoj9p6OCZ4AfWw4dYdgM296gsQYBnO-oncjWm4d8oCgqSnOLZGz7iGSH2YDgcTh6mZPpo2RNCejiVy2MyGFnDkfUwehxJ0H7v4VPmwBqMp9ajPSZkPJ5Mh9PhqIeZ64mIP6u_ueyn7v0_3oNg4Q?type=png

.. 
    .. mermaid::

        flowchart LR

        subgraph R0-Protons-dec1[R0-$$p^+$$-dec1]
            direction TB
            node-rpa[node-a]
            node-rpb[node-b]
            node-rpc[node-c]
        end

        subgraph R0-GammaDiffuse-dec1[R0-$$\gamma$$-diffuse-dec1]
            direction TB
            node-rga[node-a]
            node-rgb[node-b]
            node-rgc[node-c]
        end

        subgraph DL1-GammaDiffuse-dec1[DL1-$$\gamma$$-diffuse-dec1]
            direction TB
            node-ga[node-a]
            node-gb[node-b]
            node-gc[node-c]
        end

        subgraph DL1-Protons-dec1[DL1-$$p^+$$-dec1]
            direction TB
            node-rga1[node-a]
            node-rgb1[node-b]
            node-rgc1[node-c]
        end

        subgraph R0-GammaTest[R0-$$\gamma$$-test]
            direction TB
            node-x
            node-y
            node-z
        end

        subgraph DL1-GammaDiffuse-train[DL1-$$\gamma$$-diffuse]
            direction TB
            node-tra[node-a]
            node-trb[node-b]
            node-trc[node-c]
        end

        subgraph DL1-GammaDiffuse-test[DL1-$$\gamma$$-diffuse]
            direction TB
            dl1-gammadiffuse-node-a[node-a]
            dl1-gammadiffuse-node-b[node-b]
            dl1-gammadiffuse-node-c[node-c]
        end

        subgraph DL1-GammaDiffuse-test-merged[DL1-$$\gamma$$-diffuse-merged]
            direction TB
            dl1-gammadiffuse-merged-node-a[node-a]
            dl1-gammadiffuse-merged-node-b[node-b]
            dl1-gammadiffuse-merged-node-c[node-c]
        end

        subgraph DL1-GammaTest[DL1-$$\gamma$$-test]
            dl1-gamma-node-x[node-x]
            dl1-gamma-node-y[node-y]
            dl1-gamma-node-z[node-z]
        end

        subgraph DL1-GammaTestMerged[DL1-GammaTestMerged]
            direction TB
            dl1-gamma-node-x-merged[node-x]
            dl1-gamma-node-y-merged[node-y]
            dl1-gamma-node-z-merged[node-z]
        end


        R0-GammaDiffuse-dec1 --> |r0_to_dl1| DL1-GammaDiffuse-dec1
        R0-Protons-dec1 --> |r0_to_dl1| DL1-Protons-dec1
        R0-GammaTest --> |r0_to_dl1| DL1-GammaTest


        node-ga --> |train-test_split| node-tra
        node-ga --> |train-test_split| dl1-gammadiffuse-node-a
        dl1-gammadiffuse-node-a ---> |merge_dl1| dl1-gammadiffuse-merged-node-a


        node-tra --> |merge_dl1| DL1-GammaDiffuse-dec1-merged[DL1-$$\gamma$$-diffuse train]
        node-trb --> |merge_dl1| DL1-GammaDiffuse-dec1-merged
        node-trc --> |merge_dl1| DL1-GammaDiffuse-dec1-merged

        DL1-Protons-dec1 ---> |merge_dl1| DL1-Protons-dec1-merged[DL1-$$p^+$$-dec1]
        
        DL1-GammaDiffuse-dec1-merged & DL1-Protons-dec1-merged --> train_pipe((train_pipe))

        train_pipe --> models .-> real_data[Real Data]

        %% models --> DL2-GammaTest
        models & dl1-gamma-node-x-merged ---> |dl1_to_dl2| dl2-gamma-node-x


        DL1-GammaTest -----> |merge_dl1| DL1-GammaTestMerged

        subgraph  DL2-GammaDiffuseTest
            direction TB
            dl2-gammadiffuse-node-a
            dl2-gammadiffuse-node-b
            dl2-gammadiffuse-node-c
        end

        subgraph  IRF-GammaDiffuseTest
            direction TB
            irf-gammadiffuse-node-a
            irf-gammadiffuse-node-b
            irf-gammadiffuse-node-c
        end

        subgraph DL2-GammaTest
            direction TB
            dl2-gamma-node-x
            dl2-gamma-node-y
            dl2-gamma-node-z
        end

        subgraph IRF-GammaTest
            direction TB
            irf-gamma-node-x
            irf-gamma-node-y
            irf-gamma-node-z
        end

        dl2-gamma-node-x --> |dl2_to_irf| irf-gamma-node-x

        models & dl1-gammadiffuse-merged-node-a[node-a] ..-> dl2-gammadiffuse-node-a .-> |dl2_to_irf| irf-gammadiffuse-node-a
    

To use, you may run:

.. code-block::

    lstmcpipe_generate_config PathConfigAllSkyFullSplitDiffuse --dec_list dec_2276 --prod_id MY_NEW_PROD

``PathConfigAllSkyFullSplitDiffuse`` runs the whole thing at once. The two sub-configs it relies on can also be
used separately (see :ref:`allsky-blocks`):

* ``PathConfigAllSkyTrainingWithSplit`` produces the DL1 and splits the GammaDiffuse dataset (50% train /
  50% test, node by node). The test half is written under ``TestingDataset/`` while the train half stays under
  ``TrainingDataset/``;
* ``PathConfigAllSkyTestingGammaDiffuse`` picks up that diffuse test half, merges it per node and runs
  ``dl1_to_dl2`` and ``dl2_to_irfs`` on it. It **must** be run on a production generated with
  ``PathConfigAllSkyTrainingWithSplit``, otherwise the input DL1 files do not exist.

Because the gammas are diffuse, the IRFs produced here are full-enclosure (no ``--point-like`` option), while
the point-source test gammas of the standard pipeline give point-like IRFs.


.. _allsky-blocks:

Building blocks: partial and per-declination configs
====================================================

The ``...Full...`` classes above are assemblies of smaller classes, each handling **a single declination** and
a part of the pipeline. They are directly usable and are the right tool when you want to run only a piece of a
production, for instance to re-run the testing part of a production whose training is already done, or to add
a declination to an existing production.

They all take a ``dec`` argument (**not** ``dec_list``), which must be passed through ``--kwargs``:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Class
     - Example command
   * - ``PathConfigAllSkyTraining``
     - .. code-block:: bash

           lstmcpipe_generate_config PathConfigAllSkyTraining \
               --prod_id MY_PROD --kwargs dec=dec_2276
   * - ``PathConfigAllSkyTrainingWithSplit``
     - .. code-block:: bash

           lstmcpipe_generate_config PathConfigAllSkyTrainingWithSplit \
               --prod_id MY_PROD --kwargs dec=dec_2276
   * - ``PathConfigAllSkyTesting``
     - .. code-block:: bash

           lstmcpipe_generate_config PathConfigAllSkyTesting \
               --prod_id MY_PROD --kwargs dec=dec_2276
   * - ``PathConfigAllSkyTestingGammaDiffuse``
     - .. code-block:: bash

           lstmcpipe_generate_config PathConfigAllSkyTestingGammaDiffuse \
               --prod_id MY_PROD --kwargs dec=dec_2276
   * - ``PathConfigAllSkyTrainingDL1ab``
     - .. code-block:: bash

           lstmcpipe_generate_config PathConfigAllSkyTrainingDL1ab \
               --prod_id NEW_PROD --source_prod_id OLD_PROD --kwargs dec=dec_2276
   * - ``PathConfigAllSkyTestingDL1ab``
     - .. code-block:: bash

           lstmcpipe_generate_config PathConfigAllSkyTestingDL1ab \
               --prod_id NEW_PROD --source_prod_id OLD_PROD --kwargs dec=dec_2276

What each of them does:

``PathConfigAllSkyTraining``
    ``r0_to_dl1``, ``merge_dl1`` and ``train_pipe`` for the training particles (``GammaDiffuse`` and
    ``Protons``) of one declination. Only the pointing nodes existing for **both** particles are kept
    (inner join on the pointings). It stops at the models: no DL2, no IRF.

``PathConfigAllSkyTrainingWithSplit``
    same as above plus a ``train_test_split`` stage that splits the GammaDiffuse nodes into a train and a test
    dataset. Use it when you want full-enclosure IRFs (see the previous section).

``PathConfigAllSkyTesting``
    ``r0_to_dl1``, ``merge_dl1``, ``dl1_to_dl2`` and ``dl2_to_irfs`` for the point-source test gammas.
    The DL1 of the test dataset are declination independent (and generated only once), but the DL2 and IRFs
    are produced with the models of the declination given by ``dec``: the models of that declination must
    exist under the same ``prod_id``.

``PathConfigAllSkyTestingGammaDiffuse``
    the same, for the diffuse gamma test dataset created by ``PathConfigAllSkyTrainingWithSplit``. It has no
    ``r0_to_dl1`` stage, since its DL1 come from the split.

``PathConfigAllSkyTrainingDL1ab`` / ``PathConfigAllSkyTestingDL1ab``
    the ``dl1ab`` counterparts of the two above: instead of starting from the simulations, they re-run the DL1
    parameterisation on the DL1 of ``source_prod_id`` (typically with a tuned lstchain config). Pointing nodes
    missing in the source production are warned about and dropped.

Since each class generates a valid, self-contained config, a production can also be run in several steps: for
instance generate and run a ``PathConfigAllSkyTraining`` config for a new declination, then a
``PathConfigAllSkyTesting`` config with the same ``prod_id`` to produce the DL2 and IRFs.


