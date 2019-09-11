#!/bin/sh

### core job to run a pipeline step
# outdir and file should be passed to the script
# example: ./core_job.sh /path_to/gamma_20deg_0deg.simtel.gz /path_to/results


### ENV SETUP ###
# TODO: change to a common env.

__conda_setup="$(CONDA_REPORT_ERRORS=false '/fefs/home/thomas.vuillaume/miniconda3/bin/conda' shell.bash hook 2> /dev/null)"
if [ $? -eq 0 ]; then
    \eval "$__conda_setup"
else
    if [ -f "/fefs/home/thomas.vuillaume/miniconda3/etc/profile.d/conda.sh" ]; then
        . "/fefs/home/thomas.vuillaume/miniconda3/etc/profile.d/conda.sh"
        CONDA_CHANGEPS1=false conda activate base
    else
        \export PATH="/fefs/home/thomas.vuillaume/miniconda3/bin:$PATH"
    fi
fi

conda activate cta-dev


############################ OPTIONS ############################

models_outdir="/fefs/aswg/data/models/20190620/south_pointing/"
dl1_gamma_train="/fefs/aswg/data/mc/DL1/20190620/gamma-diffuse/south_pointing/dl1_gamma-diffuse_20deg_180deg_cta-prod3-demo-2147m-LaPalma-baseline-mono_merge_train.h5"
dl1_gamma_test="/fefs/aswg/data/mc/DL1/20190620/gamma/south_pointing/dl1_gamma_20deg_180deg_cta-prod3-demo-2147m-LaPalma-baseline-mono_off0.4_merge_test.h5"
dl1_proton_train="/fefs/aswg/data/mc/DL1/20190620/proton/south_pointing/dl1_proton_20deg_180degcta-prod3-demo-2147m-LaPalma-baseline-mono_merge_train.h5"
dl1_proton_test="/fefs/aswg/data/mc/DL1/20190620/proton/south_pointing/dl1_proton_20deg_180degcta-prod3-demo-2147m-LaPalma-baseline-mono_merge_test.h5"
# config_file=""

############################ OPTIONS ############################


python /home/thomas.vuillaume/software/cta-observatory/cta-lstchain/scripts/lst-rfperformance.py -fg $dl1_gamma_train -fp $dl1_proton_train -gt $dl1_gamma_test -pt $dl1_proton_test -o $models_outdir



