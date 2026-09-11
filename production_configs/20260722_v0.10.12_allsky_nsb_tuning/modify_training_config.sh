#!/usr/bin/env bash

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

echo "Apply YAML and text modifications in NSB-* training configs"

SCRIPT_DIR="$script_dir" python3 - <<'PY'
from __future__ import annotations

import os
from pathlib import Path

import yaml

script_dir = Path(os.environ["SCRIPT_DIR"])
nsb_dirs = sorted(p for p in script_dir.iterdir() if p.is_dir() and p.name.startswith("NSB-"))

if not nsb_dirs:
    raise SystemExit("No NSB-* directories found")

updated_files = 0
removed_merge_entries = 0
stages_to_remove = {"train_test_split", "dl1_to_dl2", "dl2_to_irfs"}

for nsb_dir in nsb_dirs:
    files = sorted(list(nsb_dir.glob("*.yml")) + list(nsb_dir.glob("*.yaml")))

    for file_path in files:
        with file_path.open("r", encoding="utf-8") as f:
            text = f.read()

        data = yaml.safe_load(text)
        changed = False

        if isinstance(data, dict):
            stages_to_run = data.get("stages_to_run")
            if isinstance(stages_to_run, list):
                filtered_stages_to_run = [s for s in stages_to_run if s not in stages_to_remove]
                if filtered_stages_to_run != stages_to_run:
                    data["stages_to_run"] = filtered_stages_to_run
                    changed = True

            stages = data.get("stages")
            if isinstance(stages, dict):
                for stage_name in stages_to_remove:
                    if stage_name in stages:
                        stages.pop(stage_name, None)
                        changed = True

                merge_dl1 = stages.get("merge_dl1")
                if isinstance(merge_dl1, list):
                    before = len(merge_dl1)
                    filtered = []
                    for entry in merge_dl1:
                        if not isinstance(entry, dict):
                            filtered.append(entry)
                            continue

                        entry_input = entry.get("input")
                        entry_output = entry.get("output")
                        if (
                            isinstance(entry_input, str) and "TestingDataset" in entry_input
                        ) or (
                            isinstance(entry_output, str) and "TestingDataset" in entry_output
                        ):
                            continue

                        filtered.append(entry)

                    removed = before - len(filtered)
                    if removed > 0:
                        stages["merge_dl1"] = filtered
                        removed_merge_entries += removed
                        changed = True

        new_text = text
        new_text = new_text.replace("*/*.h5", "*.h5")

        if changed:
            dumped = yaml.safe_dump(data, sort_keys=False, default_flow_style=False)
            new_text = dumped
            new_text = new_text.replace("*/*.h5", "*.h5")

        if new_text != text:
            with file_path.open("w", encoding="utf-8") as f:
                f.write(new_text)
            print(f"Updated: {file_path}")
            updated_files += 1

print(f"Done. Updated {updated_files} file(s), removed {removed_merge_entries} merge_dl1 entries.")
PY

