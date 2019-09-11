# T. Vuillaume, 20/06/2019
# script to merge dl1 files

source source_env.sh

lstchain_dir="/home/thomas.vuillaume/software/cta-observatory/cta-lstchain"


input_dir='/fefs/aswg/data/mc/DL1/20190822/gamma-diffuse/south_pointing/training/'
output_file='/fefs/aswg/data/mc/DL1/20190822/gamma-diffuse/south_pointing/dl1_20190822_proton_training.h5'

# input_dir=$1
# output_file=$2

python $lstchain_dir/scripts/merge_hdf5_files.py -d $input_dir -o $output_file
