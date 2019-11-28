LST scripts
===========
Scripts to ease the reduction of MC data on the LST cluster at La Palma.   

Contact:
Thomas Vuillaume, thomas.vuillaume [at] lapp.in2p3.fr


Install
-------

You can install this as an independant package. This will give you the possibility to run ``onsite_`` commands from
anywhere.
This is not mandartory though and you can simply run the scripts as ``python onsite_.py``



Steps
-----

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
- `onsite_mc_perf.py` (TBD)
        

Note: by default, some (job heavy) scripts only print the commands instead of executing them for double check.
Edit them and uncomment `os.system(cmd)` to execute all.


Real Data analysis
------------------

Real data analysis is not supposed to be supported by these scripts. Use at your own risk.
