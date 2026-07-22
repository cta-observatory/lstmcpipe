#!/usr/bin/env bash
#
# First step : merge the TestingDataset and TrainingDataset from the 20240918 production into a single TestingDataset in the 20260722 production.
#
# For each NSB tuning value (0.07, 0.14, 0.22, 0.38, 0.50):
#   Merges GammaDiffuse/dec_6166/node_*/test  (TestingDataset) and
#          GammaDiffuse/dec_6166/node_*/train (TrainingDataset)
#   from the 20240918 production into a single flattened
#   TestingDataset/GammaDiffuse/dec_6166/node_*/ dir under the
#   20260722 production. Symlinks, does not copy.
#
# Usage:
#   ./step_1_symlink_dl1.sh [--dry-run]
#
set -euo pipefail

NSB_VALUES=(0.07 0.14 0.22 0.38 0.50)

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "[DRY RUN] No changes will be made."
fi

n_linked=0
n_skipped_exists=0
n_skipped_collision=0
n_missing_src=0

link_node_dir() {
    local src_dir="$1"   # .../GammaDiffuse/dec_6166  (contains node_* dirs)
    local subdir="$2"    # "test" or "train"
    local dest_base="$3" # .../GammaDiffuse/dec_6166  (target)
    local label="$4"

    if [[ ! -d "${src_dir}" ]]; then
        echo "WARNING: source not found, skipping: ${src_dir}" >&2
        n_missing_src=$((n_missing_src + 1))
        return
    fi

    for node_path in "${src_dir}"/node_*; do
        [[ -d "${node_path}/${subdir}" ]] || continue
        local node_name
        node_name="$(basename "${node_path}")"
        local dest_node_dir="${dest_base}/${node_name}"

        if [[ "${DRY_RUN}" == false ]]; then
            mkdir -p "${dest_node_dir}"
        fi

        for f in "${node_path}/${subdir}"/*; do
            [[ -f "${f}" ]] || continue
            local fname
            fname="$(basename "${f}")"
            local dest_link="${dest_node_dir}/${fname}"

            if [[ -e "${dest_link}" || -L "${dest_link}" ]]; then
                if [[ -L "${dest_link}" && "$(readlink -f "${dest_link}")" == "$(readlink -f "${f}")" ]]; then
                    n_skipped_exists=$((n_skipped_exists + 1))
                else
                    echo "COLLISION [${label}] ${dest_link} already exists and points elsewhere. Skipped." >&2
                    n_skipped_collision=$((n_skipped_collision + 1))
                fi
                continue
            fi

            if [[ "${DRY_RUN}" == true ]]; then
                echo "LINK ${f} -> ${dest_link}"
            else
                ln -s "${f}" "${dest_link}"
            fi
            n_linked=$((n_linked + 1))
        done
    done
}

for NSB in "${NSB_VALUES[@]}"; do
    BASE_OLD="/fefs/aswg/data/mc/DL1/AllSky/20240918_v0.10.12_allsky_nsb_tuning_${NSB}"
    BASE_NEW="/fefs/aswg/data/mc/DL1/AllSky/20260722_v0.10.12_allsky_nsb_tuning_${NSB}"

    SRC_TESTING="${BASE_OLD}/TestingDataset/GammaDiffuse/dec_6166"
    SRC_TRAINING="${BASE_OLD}/TrainingDataset/GammaDiffuse/dec_6166"
    DEST="${BASE_NEW}/TestingDataset/GammaDiffuse/dec_6166"

    echo "=== NSB ${NSB} ==="
    if [[ "${DRY_RUN}" == true ]]; then
        echo "MKDIR -p ${DEST}"
    else
        mkdir -p "${DEST}"
    fi
    link_node_dir "${SRC_TESTING}"  "test"  "${DEST}" "Testing/NSB=${NSB}"
    link_node_dir "${SRC_TRAINING}" "train" "${DEST}" "Training/NSB=${NSB}"
done

echo "----------------------------------------"
echo "Linked:              ${n_linked}"
echo "Already correct:     ${n_skipped_exists}"
echo "Collisions skipped:  ${n_skipped_collision}"
echo "Missing source dirs: ${n_missing_src}"
[[ "${n_skipped_collision}" -gt 0 ]] && echo "REVIEW COLLISIONS ABOVE. Same filenames existed in both test/ and train/ sources."