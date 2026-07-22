#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source_dir="$script_dir/dec_6166"
target_dir="$script_dir/dec_6166_high_density"

if [[ ! -d "$source_dir" ]]; then
	echo "Source directory not found: $source_dir"
	exit 1
fi

if [[ ! -d "$target_dir" ]]; then
	echo "Target directory not found: $target_dir"
	exit 1
fi

echo "Step 1/3: Rename lstmcpipe_config*.json -> *.yaml"

renamed=0
rename_skipped=0

while IFS= read -r -d '' json_file; do
	yml_file="${json_file%.json}.yaml"
	if [[ -e "$yml_file" ]]; then
		echo "Skipping rename (destination exists): $json_file -> $yml_file"
		rename_skipped=$((rename_skipped + 1))
		continue
	fi

	mv "$json_file" "$yml_file"
	echo "Renamed: $json_file -> $yml_file"
	renamed=$((renamed + 1))
done < <(find "$script_dir" -type f -name "lstmcpipe_config*.json" -print0)

echo "Rename step done. Renamed $renamed file(s), skipped $rename_skipped file(s)."

echo "Step 2/3: Remove r0_to_dl1 and merge_dl1 entries with TestingDataset in input/output"

SCRIPT_DIR="$script_dir" python3 - <<'PY'
from __future__ import annotations

import os
import sys
from pathlib import Path

import yaml

script_dir = Path(os.environ["SCRIPT_DIR"])
patterns = ("lstmcpipe_config*.yml", "lstmcpipe_config*.yaml")

files = []
for pattern in patterns:
	files.extend(script_dir.rglob(pattern))

if not files:
	print("No lstmcpipe config files found for Step 2.")
	sys.exit(0)


def has_testing_dataset(entry: object) -> bool:
	if not isinstance(entry, dict):
		return False

	for key in ("input", "output"):
		value = entry.get(key)
		if isinstance(value, str) and "TestingDataset" in value:
			return True

	return False


updated = 0
removed_total = 0

for file_path in sorted(set(files)):
	with file_path.open("r", encoding="utf-8") as handle:
		cfg = yaml.safe_load(handle)

	if not isinstance(cfg, dict):
		continue

	stages = cfg.get("stages")
	if not isinstance(stages, dict):
		continue

	changed = False
	for stage_name in ("r0_to_dl1", "merge_dl1"):
		entries = stages.get(stage_name)
		if not isinstance(entries, list):
			continue

		before = len(entries)
		filtered = [entry for entry in entries if not has_testing_dataset(entry)]
		removed = before - len(filtered)

		if removed > 0:
			stages[stage_name] = filtered
			removed_total += removed
			changed = True

	if changed:
		with file_path.open("w", encoding="utf-8") as handle:
			yaml.safe_dump(cfg, handle, sort_keys=False, default_flow_style=False)
		print(f"Updated: {file_path}")
		updated += 1

print(f"Step 2 done. Updated {updated} file(s), removed {removed_total} entries.")
PY

echo "Step 3/3: Replace 2026-07-22_allsky_nsb_tuning -> 20260722_v0.10.12_allsky_nsb_tuning"

replaced_files=0

while IFS= read -r -d '' cfg_file; do
	if grep -Eq "2026-07-22_allsky_nsb_tuning|_0\\.5([^0-9]|$)" "$cfg_file"; then
		sed -E -i '' \
			-e 's/2026-07-22_allsky_nsb_tuning/20260722_v0.10.12_allsky_nsb_tuning/g' \
			-e 's/_0\.5([^0-9]|$)/_0.50\1/g' \
			"$cfg_file"
		echo "Updated: $cfg_file"
		replaced_files=$((replaced_files + 1))
	fi
done < <(find "$script_dir" -type f \( -name "lstmcpipe_config*.yml" -o -name "lstmcpipe_config*.yaml" \) -print0)

echo "Step 3 done. Updated $replaced_files file(s)."

echo "Step 4/4: Fix TestingDataset output path and node prefix"

step4_updated=0

while IFS= read -r -d '' cfg_file; do
	if grep -Eq "TestingDataset/dl1_|node_theta" "$cfg_file"; then
		sed -E -i '' \
			-e 's#TestingDataset/dl1_#TestingDataset/GammaDiffuse/dec_6166/dl1_#g' \
			-e 's/node_theta/GammaDiffuse_test_node_corsika_theta/g' \
			"$cfg_file"
		echo "Updated: $cfg_file"
		step4_updated=$((step4_updated + 1))
	fi
done < <(find "$script_dir" -type f \( -name "lstmcpipe_config*.yml" -o -name "lstmcpipe_config*.yaml" \) -print0)

echo "Step 4 done. Updated $step4_updated file(s)."

