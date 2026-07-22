#!/usr/bin/env bash

set -euo pipefail

pattern='lstmcpipe_config_*nsb*.json'
search='ing_NSB/TrainingDataset'
replace='ing_NSB/TestingDataset'

count=0

while IFS= read -r -d '' file; do
	sed -i '' "s#${search}#${replace}#g" "$file"
	echo "Updated: $file"
	count=$((count + 1))
done < <(find . -type f -iname "$pattern" -print0)

if [[ $count -eq 0 ]]; then
	echo "No files found matching: $pattern"
else
	echo "Done. Updated $count file(s)."
fi
