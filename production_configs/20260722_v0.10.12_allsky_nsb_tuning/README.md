# 20260722_v0.10.12_allsky_nsb_tuning

Trains RF models at NSB tuning levels `[0.07, 0.14, 0.22, 0.38, 0.50]` on the full
statistics of `dec_6166`, and evaluates them on the `dec_6166_high_density`
GammaDiffuse testing dataset (51 pointings per NSB level).

DL1 files are reused (symlinked) from the `20240918` production rather than
re-run from R0.

This directory is the cleaned-up, reproducible version of the production. It
was reconstructed from `run.sh`, the slurm job logs, and
`lstchain_dl1_to_dl2.provenance.log` after the fact, since several scripts
were duplicated/abandoned mid-course while debugging (see "Notes" below).

## Pipeline

See `run.sh` for the exact, ordered sequence of commands. Summary:

1. `./step_1_symlink_dl1.sh` — symlink existing DL1 files from the 20240918
   production into this production, per NSB level.
2. `python step_2_gen_config_merge_dl1.py` then
   `lstmcpipe -c lstmcpipe_merge_dl1_..._dec_6166.yaml -conf_lst lstchain_config.json`
   for each NSB — merges the 20240918 TestingDataset + TrainingDataset DL1
   files into a single TestingDataset for this production.
3. `./step_3_generate_testing_configs.sh` — generates
   `NSB-X/lstmcpipe_config_20260722_test_nsbX.yaml`, the DL1→DL2→IRF testing
   config for each NSB, from the merged TestingDataset produced in step 2.
4. `lstmcpipe_generate_nsb_levels_configs --dec_list dec_6166_high_density --prod_id 20260722_v0.12.3 --nsb 0.07 0.14 0.22 0.38 0.50 --overwrite`
   then `./modify_training_config.sh` — generates and trims
   `NSB-X/lstmcpipe_config_nsbX.yml`, the r0_to_dl1 → merge_dl1 → train_pipe
   config for each NSB.
5. Run `lstmcpipe -c NSB-X/lstmcpipe_config_nsbX.yml -conf_lst NSB-X/lstchain_config_nsbX.json`
   for each NSB — trains the RF models.
6. Once training is complete, run
   `lstmcpipe -c NSB-X/lstmcpipe_config_20260722_test_nsbX.yaml -conf_lst NSB-X/lstchain_config_nsbX.json`
   for each NSB — produces the DL2 test files and IRFs.

`lstchain_config_nsbX.json` differs between NSB levels only in
`nsb_tuning`/`nsb_tuning_rate_GHz` (this is the whole point of the
production); the root `lstchain_config.json` has `nsb_tuning: false` and is
only used for the merge_dl1 step in (2), which is NSB-independent.

## Status (as of 2026-09-11)

**Training is complete for all 5 NSB levels** — RF models
(`reg_energy.sav`, `reg_disp_norm.sav`, `cls_gh.sav`, `cls_disp_sign.sav`)
exist under `dec_6166_high_density` for each level.

**Testing (DL2 + IRF) is incomplete for 4 of 5 NSB levels.** Out of the 51
pointings defined per NSB level in `lstmcpipe_config_20260722_test_nsbX.yaml`:

| NSB  | IRFs produced |
|------|---------------|
| 0.07 | 32 / 51 |
| 0.14 | 51 / 51 |
| 0.22 | 32 / 51 |
| 0.38 | 32 / 51 |
| 0.50 | 48 / 51 |

To complete testing, re-run step 6 above for the affected NSB levels —
`lstmcpipe` will pick up only the missing/failed nodes.

## Notes on this cleanup

Several files that existed alongside this production while it was being
debugged were removed as dead ends or duplicates once cross-checked against
`lstchain_dl1_to_dl2.provenance.log` (which records the config file and
input/output paths of every real `lstchain_dl1_to_dl2` invocation) and git
history:

- A separate root-level testing config family
  (`lstmcpipe_config_20260722_v0.12.3_allsky_nsb_tuning_0.XX.yaml`, generated
  by a since-removed `generate_dl1_dl2_configs.sh`) pointed at DL1 test files
  that don't exist under that naming. Every one of the 227 `completed`
  entries in the provenance log used the `NSB-X/lstmcpipe_config_20260722_test_nsbX.yaml`
  family instead; the other one only ever produced errors.
- `modify_configs.sh` was an earlier, abandoned alternative to
  `modify_training_config.sh` (the original README already crossed it out).
- `NSB-0.07/lstmcpipe_config_nsb0.07.yml` had a stale `prod_id` and paths
  (missing the `20260722_v0.12.3_` prefix) left over from before that
  convention was fixed; it has been corrected here to match the other 4 NSB
  levels and the actual location of the 0.07 models on disk.
