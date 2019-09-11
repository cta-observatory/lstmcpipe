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


filelist=$1
outdir=$2

echo "filelist $filelist"
echo "outdir $outdir"



for file in `cat $filelist`;
do
    echo "processing $file";
    python /fefs/home/thomas.vuillaume/software/cta-observatory/cta-lstchain/scripts/lst-r0_to_dl1.py -f $file -o $outdir
done
