#!/bin/sh
# slurm core job - send a job with the command passed as arg1, the output folder on arg2 on every line in the file passed as arg3
# output files are constructed by replacing "simtel.{compression}" with "dl1.h5" on the filename

source /fefs/aswg/software/virtual_env/.bashrc
conda activate cta

CMD=$1
output_dir=$2
filelist=$3

for file in `cat $filelist`;
do
    filename=$(basename $file)
    output=$output_dir/${filename%.simtel.*}.dl1.h5
    echo "processing $file, outputting to $output";
    $CMD --input $file --output $output
done
