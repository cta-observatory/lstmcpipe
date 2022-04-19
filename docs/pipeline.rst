lstmcpipe pipelines
===================


standard pipeline
-----------------

This is the typical MC pipeline

.. mermaid::

    graph LR
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