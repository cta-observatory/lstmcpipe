LST scripts
===========

.. image:: https://travis-ci.com/vuillaut/LST_scripts.svg?branch=master
    :target: https://travis-ci.com/vuillaut/LST_scripts

Scripts to ease the reduction of MC data on the LST cluster at La Palma.   

Contact:
Thomas Vuillaume, thomas.vuillaume [at] lapp.in2p3.fr
Enrique Garcia, garcia [at] lapp.in2p3.fr


Install
-------

.. code-block::

    git clone https://github.com/vuillaut/LST_scripts.git 
    cd LST_scripts 
    pip install .    


You can install this as an independent package (although it will uses various ``lstchain_*`` scripts). This will give you the possibility to run ``onsite_`` commands from
anywhere.
This is not mandatory though and you can simply run the scripts as ``python onsite_*.py``

Quickstart
----------

The MC full pipeline (r0 to dl2) is launched by running the ``onsite_mc_r0_to_dl3.py`` script.

.. code-block::

    python onsite_mc_r0_to_dl3.py -c config_MC_prod.yml -conf_lst lstchain_*.json --prod_id [e.g:] local_tail_8_4

Note: You can launch this command without fearing; there is an intermediate step that verifies and
shows the all the information that you are passing to the pipeline.

The ``onsite_mc_r0_to_dl3.py`` script is the **orchestrator** of the pipeline, it schedules the following stages
(scripts) per particle;

1. ``onsite_mc_r0_to_dl1.py``
2. ``onsite_mc_merge_and_copy_dl1.py``
3. ``onsite_mc_train.py``
4. ``onsite_mc_dl1_to_dl2.py``

by using the slurm scheduling job manager system at LP cluster and the dependencies between each stage.


Each 'onsite' stage calls a lstchain script; i.e., ``onsite_mc_r0_to_dl1.py`` will call the ``lstchain_mc_r0_to_dl1``
script, and successively.

Configuration of the pipeline
*****************************

``onsite_mc_r0_to_dl3.py`` passes the configuration and all the needed arguments to the consecutive stages. The
pipeline uses two configuration files;

- The ``config_MC_prod.yml`` file (details all the MC production related arguments; paths, ``prod3`` or ``prod5`` ...),
- The ``lstchain_*.json`` configuration file (lstchain related configuration; tailcuts, integrator, RF arguments ...).

Changing the default arguments on each of the steps of the pipeline: **Use at your own risk.**

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

You can load the second file as a dictionary as follows;

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
    - mandatory input: directory you want to analyse. e.g; ``/fefs/aswg/data/mc/DL0/20190909/proton/North_pointing``
    - it will create the directory structure for you    
    - creates batch jobs    
    - results can be found in `running_analysis`    
- `onsite_mc_merge_and_copy_dl1.py`
    - to be run once all jobs from `onsite_mc_dl0_to_dl1.py` are finished
    - check that jobs finished without error from the logs
    - merge the DL1 files for training and testing
    - clean and move the `running_analysis` into `DL1` and `analysis_logs`
- `onsite_mc_train.py`
- `onsite_mc_dl1_to_dl2`
- `onsite_mc_dl2_to_dl3.py` (TBD)
        

Note: by default, some (job heavy) scripts only print the commands instead of executing them for double check.
Edit them and uncomment `os.system(cmd)` to execute all.


Real Data analysis
------------------

Real data analysis is not supposed to be supported by these scripts. Use at your own risk.
