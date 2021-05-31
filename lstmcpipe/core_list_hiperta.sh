#!/bin/sh
# slurm core job - send a job with the command passed as arg1, the output folder on arg2 on every line in the file passed as arg3

# this source is not working because jobs are not accesing /local todo: find a way to access it to be sure to load
#  the right env
# source /local/home/lstanalyzer/.bashrc

source /home/enrique.garcia/.bashrc
conda activate hipe-prod

CMD=$1
output_dir=$2
filelist=$3

for file in `cat $filelist`;
do
    echo "processing $file";
    $CMD -i $file -o $output_dir
done
