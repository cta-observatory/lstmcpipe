lstmcpipe pipelines
===================


Prod3 & Prod5 pipelines
-----------------------

Here is the typical MC pipeline for the prod3 and prod5 productions

.. mermaid::

    flowchart LR
        subgraph R0
            gamma
            proton
            electron
        end

        gamma --> r0dl1((r0_to_dl1))
        proton --> r0dl1
        electron --> r0dl1

        subgraph DL1
            gamma_dl1
            proton_dl1
            electron_dl1
        end

        r0dl1 --> gamma_dl1[DL1 gamma]
        r0dl1 --> proton_dl1[DL1 proton]
        r0dl1 --> electron_dl1[DL1 electron]


        gamma_dl1 --> train_test_split((train_test_split))
        proton_dl1 --> train_test_split
        train_test_split --> DL1train[DL1 train]
        train_test_split --> DL1test[DL1 test]
        DL1train --> train_pipe((train_pipe))
        train_pipe --> models

        electron_dl1 --> DL1test

        DL1train --> |dl1ab| DL1train
        DL1test --> |dl1ab| DL1test

        models --> DL2
        DL1test --> DL2[DL2 test]

        DL2 --> |dl2_to_irf| IRF[IRFs]
        DL2 --> |dl2_to_sensitivity| SENS[Sensitivity]
        SENS --> plot[png plots]


AllSky production pipeline
--------------------------

Here is the pipeline for the AllSky MC production:

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

        DL1-GammaCrab -----> DL2-GammaCrab
        DL2-GammaCrab[DL2 Gamma Crab \n - node a\n - node b\n - node c]

        DL2-GammaCrab --> |dl2_to_irf| IRF-GammaCrab
        IRF-GammaCrab[IRF Gamma Crab \n - node a\n - node b\n - node c]


