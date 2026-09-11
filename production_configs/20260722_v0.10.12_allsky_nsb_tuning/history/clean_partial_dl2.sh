#!/usr/bin/env bash
# Deletes the DL2 output directories for the 19 test pointings that are
# missing DL2/IRF for NSB 0.07, 0.22, 0.38 (per the *_missing.yaml configs),
# so that lstmcpipe doesn't skip them (overwrite: false) when re-run after
# the path_model fix. Safe to run even if a directory was never created or
# only partially ran (e.g. NSB-0.07, which already failed once on the old
# wrong model path).
set -euo pipefail

nsb_levels=(0.07 0.22 0.38)

missing_nodes=(
  node_theta_32.896_az_0.0_
  node_theta_33.491_az_351.86_
  node_theta_33.491_az_8.14_
  node_theta_35.204_az_15.508_
  node_theta_35.204_az_344.492_
  node_theta_37.861_az_21.6_
  node_theta_37.861_az_338.4_
  node_theta_41.244_az_26.248_
  node_theta_41.244_az_333.752_
  node_theta_45.141_az_29.518_
  node_theta_45.141_az_330.482_
  node_theta_49.374_az_31.575_
  node_theta_49.374_az_328.425_
  node_theta_53.795_az_32.599_
  node_theta_53.795_az_327.401_
  node_theta_58.286_az_32.748_
  node_theta_58.286_az_327.252_
  node_theta_62.749_az_32.15_
  node_theta_62.749_az_327.85_
)

for nsb in "${nsb_levels[@]}"; do
  base="/fefs/aswg/data/mc/DL2/AllSky/20260722_v0.12.3_allsky_nsb_tuning_${nsb}/TestingDataset/GammaDiffuse/dec_6166"
  for node in "${missing_nodes[@]}"; do
    d="${base}/${node}"
    if [[ -d "$d" ]]; then
      echo "Removing: $d"
      rm -rf -- "$d"
    fi
  done
done

echo "Done."
