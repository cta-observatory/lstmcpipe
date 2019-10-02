#!/bin/bash

# T. Vuillaume, 20/06/2019

# Choose the selected options


####################################### OPTIONS #######################################

## env ##
source /fefs/aswg/software/scripts/source_env.sh
lstchain_repo="/fefs/home/thomas.vuillaume/software/cta-observatory/cta-lstchain"


## protons ##
# raw_data_dir="/fefs/aswg/data/mc/DL0/20190415/proton/south_pointing"
# output_dir_base="/fefs/aswg/data/mc/DL1/20190822/proton/south_pointing"
# nfiles_per_job="10"

## gamma diffuse ##
# raw_data_dir="/fefs/aswg/data/mc/DL0/20190415/gamma-diffuse/south_pointing"
# output_dir_base="/fefs/aswg/data/mc/DL1/20190822/gamma-diffuse/south_pointing"
# nfiles_per_job="10"


## gamma ps ##
raw_data_dir="/fefs/aswg/data/mc/DL0/20190415/gamma/south_pointing"
output_dir_base="/fefs/aswg/data/mc/DL1/20190822/gamma/south_pointing"
nfiles_per_job="2"



inv_test_ratio=2    #the train/test split ratio is 1/inv_test_ratio



#######################################################################################


### train/test split ### 
number_files=`ls $raw_data_dir | wc -l`
ntest=`expr $number_files \/ $inv_test_ratio`
ntrain=`expr $number_files \- $ntest`
echo "$number_files RAW files"
echo "$ntrain files in training dataset"
echo "$ntest files in test dataset"
ls $raw_data_dir/* | head -n $ntrain > training.list
ls $raw_data_dir/* | tail -n $ntest > test.list


pwd=$PWD

log_dir="$output_dir_base/logs"
job_logs="$log_dir/jobs"
dir_lists_base="$log_dir/file_lists"

mkdir -p $output_dir_base
mkdir -p $log_dir
mkdir -p $job_logs
rm $log_dir/*
rm $dir_lists_base/*
rm $job_logs/*


for list in "training" "test";
do
    dir_lists="$dir_lists_base-$list"
    output_dir="$output_dir_base/$list"
    mkdir -p $output_dir
    mkdir -p $dir_lists
    rm $dir_lists/*
    rm $output_dir/*
    echo "outputdir: $output_dir"
    echo "lists dir: $dir_lists"
    

    ### training reco ###
    python slice_list.py $list.list -n $nfiles_per_job -o $dir_lists


    ### LSTCHAIN ### 
    counter="0"
    for file in `ls $dir_lists`;
    do
        echo "mc_dl0_to_dl1 job $counter"
        jobo="$job_logs/job$counter.o"
        jobe="$job_logs/job$counter.e"
        # echo $jobo
        # echo $jobe
        filelist="$dir_lists/$file"
        # echo "sbatch -e $jobe -o $jobo lstchain_core.sh $filelist $output_dir"
        sbatch -e $jobe -o $jobo lstchain_core.sh $filelist $output_dir 
        ((counter++))
    done

mv $list.list $log_dir
cp $0 $log_dir
done




