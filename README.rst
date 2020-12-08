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


You can install this as an independent package (although it will uses various ``lstchain_`` scripts). This will give you the possibility to run ``onsite_`` commands from
anywhere.
This is not mandatory though and you can simply run the scripts as ``python onsite_.py``

Quickstart
----------

The MC full pipeline (r0 to dl2) is launched by running the ``onsite_mc_r0_to_dl3.py`` script.

.. code-block::

    python onsite_mc_r0_to_dl3.py -conf_lst lstchain_*.json --prod_id (f.eg:) local_tail_8_4

Note: You can launch this command without fearing; there is an intermediate step that verifies and
shows the all the information that you are passing to the pipeline.

``onsite_mc_r0_to_dl3.py`` is the orchestrator of the pipeline, it schedules the following stages (scripts)
per particle;

1. ``onsite_mc_r0_to_dl1.py``
2. ``onsite_mc_merge_and_copy_dl1.py``
3. ``onsite_mc_train.py``
4. ``onsite_mc_dl1_to_dl2.py``

Each stage calls a certain lstchain script; i.e., ``onsite_mc_r0_to_dl1.py`` will call ``lstchain_mc_r0_to_dl1`` entry
point, and successively.

``onsite_mc_r0_to_dl3.py`` also passes all the needed information and arguments to the consecutive stages,
thus **ALL** the configuration that the pipeline would need is passed;

* Between lines ~35 to ~75 of ``onsite_mc_r0_to_dl3.py`` (MC production related configuration).
* Through the ``lstchain_*.json`` file (lstchain pipe related configuration).

Changing the default arguments on each of the steps of the pipeline: **Use at your own risk.**

**PLEASE NOTE** that the library is **extremely job heavy**. Think about other LP-IT cluster users.

MC production logs
******************
TBD


Steps explanation
-----------------

- `onsite_mc_r0_to_dl1.py`
    - mandatory input: directory you want to analyse. e.g.   
    ``/fefs/aswg/data/mc/DL0/20190909/proton/North_pointing``
    
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
