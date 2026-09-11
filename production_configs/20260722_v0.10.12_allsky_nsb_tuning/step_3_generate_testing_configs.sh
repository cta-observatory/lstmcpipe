# #!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

nsb_dirs=()
while IFS= read -r -d '' nsb_dir; do
  nsb_dirs+=("$nsb_dir")
done < <(find "$script_dir" -maxdepth 1 -type d -name "NSB-*" -print0 | sort -z)

if [[ ${#nsb_dirs[@]} -eq 0 ]]; then
  echo "No NSB-* directories found under: $script_dir"
  exit 1
fi

for nsb_dir in "${nsb_dirs[@]}"; do
  nsb_tag="${nsb_dir##*/}"
  nsb_value="${nsb_tag#NSB-}"

  output_file="$nsb_dir/lstmcpipe_config_20260722_test_nsb${nsb_value}.yaml"
  prod_id="20260722_v0.10.12_allsky_nsb_tuning_${nsb_value}"

  echo "Generating: $output_file"

  lstmcpipe_generate_config PathConfigAllSkyTestingGammaDiffuse \
    -o "$output_file" \
    --prod_id "$prod_id" \
    --kwargs dec=dec_6166 \
    --overwrite

  sed -i \
    -e 's/_test_dec_6166_node_/_test_node_/g' \
    -e 's#/DL2/AllSky/20260722_v0\.10\.12_allsky_nsb_tuning_#/DL2/AllSky/20260722_v0.12.3_allsky_nsb_tuning_#g' \
    -e 's#/DL2/AllSky/20260722_v0\.12\.3_allsky_nsb_tuning_\([^/]*\)/TestingDataset/GammaDiffuse/dec_6166/node_corsika_theta_#/DL2/AllSky/20260722_v0.12.3_allsky_nsb_tuning_\1/TestingDataset/GammaDiffuse/dec_6166/node_theta_#g' \
    -e 's#/IRF/AllSky/20260722_v0\.10\.12_allsky_nsb_tuning_#/IRF/AllSky/20260722_v0.12.3_allsky_nsb_tuning_#g' \
    -e 's#irf_20260722_v0\.10\.12_allsky_nsb_tuning_\([^_]*\)_GammaDiffuse_dec_6166_node_corsika_theta_#irf_20260722_v0.12.3_allsky_nsb_tuning_\1_GammaDiffuse_dec_6166_node_theta_#g' \
    -e 's/conda_env: lstchain-v0\.10\.7/conda_env: lstchain-v0.12.3/' \
    "$output_file"

  echo "Patched: $output_file"
done

echo "Done. Generated and patched ${#nsb_dirs[@]} config file(s)."
