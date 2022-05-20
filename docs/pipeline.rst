===================
lstmcpipe pipelines
===================

-----------------------
Prod3 & Prod5 pipelines
-----------------------

Here is the typical MC pipeline for the prod3 and prod5 productions

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


One can also start back from DL1, applying the dl1ab stage:

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


--------------------------
AllSky production pipeline
--------------------------

R0 to IRFs
==========

Standard AllSky production pipeline **for one training declination**

.. mermaid::

    flowchart LR

        R0-Protons[R0 Protons \n - node a\n - node b\n - node c]
        R0-GammaDiffuse[R0 GammaDiffuse \n - node a\n - node b\n - node c]
        R0-GammaCrab[R0 Gamma Crab \n - node a\n - node b\n - node c]

        DL1-Protons[DL1 Protons \n - node a\n - node b\n - node c]
        DL1-GammaDiffuse[DL1 GammaDiffuse \n - node a\n - node b\n - node c]
        DL1-GammaCrab[DL1 Gamma Crab \n - node a\n - node b\n - node c]


        R0-GammaDiffuse --> |r0_to_dl1| DL1-GammaDiffuse
        R0-Protons --> |r0_to_dl1| DL1-Protons
        R0-GammaCrab --> |r0_to_dl1| DL1-GammaCrab


        DL1-GammaDiffuse --> |merge_dl1| DL1-GammaDiffuse-merged[DL1 Gamma Diffuse\nall nodes]
        DL1-Protons --> |merge_dl1| DL1-Protons-merged[DL1 Protons\nall nodes]

        DL1-GammaDiffuse-merged & DL1-Protons-merged --> train_pipe((train_pipe))

        train_pipe --> models

        models --> DL2-GammaCrab

        DL1-GammaCrab --> |merge_dl1| DL1-GammaCrab-merged[DL1 Gamma Crab \n - node a merged\n - node b merged\n - node c merged]
        DL1-GammaCrab-merged ----> DL2-GammaCrab
        DL2-GammaCrab[DL2 Gamma Crab \n - node a merged\n - node b merged\n - node c merged]

        DL2-GammaCrab --> |dl2_to_irf| IRF-GammaCrab
        IRF-GammaCrab[IRF Gamma Crab \n - node a merged\n - node b merged\n - node c merged]


To produce a config to run such a pipeline, typically run **on the cluster**:

.. code-block::

    lstmcpipe_generate_config PathConfigAllSkyFull --prod_id whatagreatprod --dec_list dec_2276


This will generate a lstmcpipe config file and a lstchain config file.

Please:
 * check thoroughly the lstmcpipe config
 * modify the lstchain config as you wish


DL1ab
=====

The DL1ab workflow is very similar, only starting from an existing DL1 dataset.

You typically want to run **on the cluster**:

.. code-block::

    lstmcpipe_generate_config PathConfigAllSkyFullDL1ab --dec_list dec_2276 --source_prod_id whatagreatprod --target_prod_id anothergreatprod


