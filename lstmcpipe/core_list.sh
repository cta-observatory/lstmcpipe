#!/bin/sh
# slurm core job - send a job with the command passed as arg1, the output folder on arg2 on every line in the file passed as arg3

source /fefs/aswg/software/virtual_env/.bashrc
conda activate cta

CMD=$1
output_dir=$2
filelist=$3

for file in `cat $filelist`;
do
    echo "processing $file";
    $CMD -f $file -o $output_dir
done
