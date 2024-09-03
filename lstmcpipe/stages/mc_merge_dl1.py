#!/usr//bin/env python3

import logging
from pathlib import Path
from ..utils import save_log_to_file, SbatchLstMCStage

log = logging.getLogger(__name__)


def batch_merge_dl1(dict_paths, batch_config, logs, jobid_from_splitting, workflow_kind="lstchain"):
    """
    Function to batch the onsite_mc_merge_and_copy function once the all the r0_to_dl1 jobs (batched by particle type)
    have finished.

    Batch 8 merge_and_copy_dl1 jobs ([train, test] x particle) + the move_dl1 and move_dir jobs (2 per particle).

    Parameters
    ----------
    dict_paths : dict
        Core dictionary with {stage: PATHS} information
    batch_config : dict
        Dictionary containing the (full) source_environment and the slurm_account strings to be passed
        to `merge_dl1` and `compose_batch_command_of_script` functions.
    workflow_kind : str
        Defines workflow kind (lstchain, ctapipe, hiperta)
    logs: dict
        Dictionary with logs files
    jobid_from_splitting: str

    Returns
    -------
    jobids_for_train : str
         Comma-separated str with all the job-ids to be passed to the next
         stage of the workflow (as a slurm dependency)

    """
    log_merge = {}
    all_jobs_merge_stage = []
    debug_log = {}
    log.info('==== START batch merge_and_copy_dl1_workflow ====')
    for paths in dict_paths:
        job_logs, jobid_debug = merge_dl1(
            paths["input"],
            paths["output"],
            merging_options=paths.get('options', None),
            batch_configuration=batch_config,
            wait_jobs_split=jobid_from_splitting,
            workflow_kind=workflow_kind,
            extra_slurm_options=paths.get("extra_slurm_options", None),
        )

        log_merge.update(job_logs)
        all_jobs_merge_stage.append(jobid_debug)
    save_log_to_file(log_merge, logs["log_file"], "merge_dl1")
    save_log_to_file(debug_log, logs["debug_file"], workflow_step="merge_dl1")
    log.info('==== END batch merge_and_copy_dl1_workflow ====')
    return ','.join(all_jobs_merge_stage)


def merge_dl1(
    input_dir,
    output_file,
    batch_configuration,
    wait_jobs_split="",
    merging_options=None,
    workflow_kind="lstchain",
    extra_slurm_options=None,
):
    """

    Parameters
    ----------
    input_dir: str
    output_file: str
    batch_configuration: dict
    wait_jobs_split: str
    merging_options: dict
    workflow_kind: str
    extra_slurm_options: dict
        Extra slurm options to be passed to the sbatch command

    Returns
    -------
    log_merge: dict
    jobid_merge: str

    """
    merging_options = "" if merging_options is None else merging_options
    if workflow_kind in ["lstchain", "hiperta"]:
        cmd = f'lstchain_merge_hdf5_files -d {input_dir} -o {output_file} {merging_options}'

    else:
        cmd = f'ctapipe-merge --input-dir {input_dir} --output {output_file} {merging_options}'

    sbatch_merge_dl1 = SbatchLstMCStage(
        "merge_dl1",
        wrap_command=cmd,
        slurm_error=Path(output_file).parent.joinpath("merging-output_%j.e"),
        slurm_output=Path(output_file).parent.joinpath("merging-output_%j.o"),
        slurm_dependencies=wait_jobs_split,
        extra_slurm_options=extra_slurm_options,
        slurm_account=batch_configuration["slurm_account"],
        source_environment=batch_configuration["source_environment"],
    )

    jobid_merge = sbatch_merge_dl1.submit()
    log_merge = {jobid_merge: sbatch_merge_dl1.slurm_command}
    log.info(f"\nMerging DL1 file from {input_dir} dir into {output_file} file.")
    log.info(f"Submitted batch job {jobid_merge}")
    return log_merge, jobid_merge
