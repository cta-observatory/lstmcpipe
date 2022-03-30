#!/usr/bin/env python

# T. Vuillaume,
# Modifications by E. Garcia
# Code to reduce R0 data to DL1 onsite (La Palma cluster)


import os
import shutil
import logging
from pathlib import Path
from lstmcpipe.workflow_management import save_log_to_file
from lstmcpipe.io.data_management import (
    check_data_path,
    get_input_filelist,
    check_and_make_dir_without_verification,
)


log = logging.getLogger(__name__)


def batch_process_dl1(
    dict_paths,
    conf_file,
    batch_config,
    logs,
    workflow_kind="lstchain",
    new_production=True,
):
    """
    Batch the dl1 processing jobs by particle type.

    Parameters
    ----------
    dict_paths : dict
        Core dictionary with {stage: PATHS} information
    conf_file : str
        Path to a configuration file. If none is given, a standard configuration is applied
    batch_config : dict
        Dict with source environment (to select the desired conda environment to run the r0/1_to_dl1 stage),
        and the slurm user account.
    workflow_kind: str
        One of the supported pipelines. Defines the command to be run on r0 files
    new_production: bool
        Whether to analysis simtel or reprocess existing dl1 files.
    logs: dict
        Dictionary con logs files

    Returns
    -------
    jobids_dl1_processing_stage : str
        string, separated by commas, containing all the jobids of this stage
    """
    log_process_dl1 = {}
    debug_log = {}
    jobids_dl1_processing_stage = []

    log.info("==== START {} dl1 processing ====".format(workflow_kind))

    if new_production:

        for paths in dict_paths["r0_to_dl1"]:
            job_logs, jobid = r0_to_dl1(
                paths["input"],
                paths["output"],
                config_file=conf_file,
                batch_config=batch_config,
                workflow_kind=workflow_kind,
            )
            log_process_dl1.update(job_logs)
            jobids_dl1_processing_stage.append(jobid)
            for jid in jobids_dl1_processing_stage:
                debug_log[jid] = f'r0_dl1 job from input dir: {paths["input"]}'

    else:

        for paths in dict_paths["dl1ab"]:

            # TODO A LOT

            log_process_dl1.update(job_logs)
            jobids_dl1_processing_stage.append(jobid)
            for jid in jobids_dl1_processing_stage:
                debug_log[jid] = f'dl1ab job from input dir: {paths["input"]}'

    # Create a string to be directly passed
    jobids_dl1_processing_stage = ",".join(jobids_dl1_processing_stage)

    save_log_to_file(log_process_dl1, logs["log_file"], "r0_to_dl1")
    save_log_to_file(debug_log, logs["debug_file"], workflow_step="r0_to_dl1")

    log.info("==== END {} dl1 processing ====".format(workflow_kind))

    return jobids_dl1_processing_stage


def r0_to_dl1(
    input_dir,
    output_dir,
    workflow_kind="lstchain",
    config_file=None,
    batch_config=None,
    debug_mode=False,
    keep_rta_file=False,
):
    """
    R0 to DL1 MC onsite conversion.
    Organizes files and launches slurm jobs in two slurm arrays.


    Parameters
    ----------
    input_dir : str or Path
        path to the files directory to analyse
    output_dir : str or Path
        Output path to store files
    config_file : str or Path
        Path to the {lstchain, ctapipe, HiPeRTA} configuration file
    batch_config : dict
        Dictionary containing the full (source + env) source_environment and the slurm_account strings.
        ! NOTE : train_pipe AND dl1_to_dl2 **MUST** be run with the same environment.
    workflow_kind: str
        One of the supported pipelines. Defines the command to be run on r0 files

    # HIPERTA ARGUMENTS
    keep_rta_file : bool
        Flag to indicate whether to keep (keep_rta_file = True) or remove (keep_rta_file = Flase ) the
        `dl1v06_reorganized_*.h5` output file (hiperta_r0_dl1 and re-organiser stages).
        Argument to be passed to the hiperta_r0_to_dl1lstchain script.
    debug_mode : bool
        Flag to activate debug_mode. Only compatible with `hiperta` workflow kind, i.e.,
        HiPeRTA functionality. DEFAULT=False.

    Returns
    -------
    jobid2log : dict
        dictionary log containing {jobid: batch_cmd} information
    jobids_r0_dl1
        A list of all the jobs sent for input dir
    """

    log.info("Starting R0 to DL1 processing for files in dir : {}".format(input_dir))

    source_environment = batch_config["source_environment"]
    slurm_account = batch_config["slurm_account"]

    if workflow_kind == "lstchain":
        base_cmd = f"{source_environment} lstmcpipe_lst_core_r0_dl1 -c {config_file} "
        jobtype_id = "LST"
    elif workflow_kind == "ctapipe":
        base_cmd = f"{source_environment} lstmcpipe_cta_core_r0_dl1 -c {config_file} "
        jobtype_id = "CTA"
    elif workflow_kind == "hiperta":
        base_cmd = (
            f"{source_environment} lstmcpipe_rta_core_r0_dl1 -c {config_file} "
        )
        if keep_rta_file:
            base_cmd += " --keep_rta_file"
        if debug_mode:
            base_cmd += " --debug_mode"

        jobtype_id = "RTA"
    else:
        base_cmd = ''
        jobtype_id = ''
        log.critical("Please, select an allowed workflow kind.")
        exit(-1)

    log.info("Working on DL0 files in {}".format(input_dir))

    check_data_path(input_dir)
    raw_files_list = list(Path(input_dir).rglob("**/*.simtel.gz"))

    if len(raw_files_list) < 50:
        dl1_files_per_job = 20
    else:
        dl1_files_per_job = 50

    with open("r0_to_dl1.list", "w+") as newfile:
        for f in raw_files_list:
            newfile.write(f.resolve().name)
            newfile.write("\n")

    log.info("{} raw R0 files".format(len(raw_files_list)))

    job_logs_dir = output_dir.joinpath("job_logs", "dl1_processing")
    Path(job_logs_dir).mkdir(exist_ok=True)

    log.info("DL1 DATA DIR: {}".format(input_dir))

    jobid2log, jobids_r0_dl1 = submit_dl1_jobs(
        input_dir,
        output_dir,
        base_cmd=base_cmd,
        file_list=raw_files_list,
        job_type_id=jobtype_id,
        dl1_files_per_batched_job=dl1_files_per_job,
        job_logs_dir=job_logs_dir,
        slurm_account=slurm_account,
        filelist_name="r0_to_dl1",
    )

    # copy config into working dir
    if config_file is not None:
        shutil.copyfile(
            config_file,
            job_logs_dir.joinpath(Path(config_file).name)
        )

    # save file lists into logs
    shutil.move("r0_to_dl1.list", job_logs_dir)

    # return it log dictionary
    return jobid2log, jobids_r0_dl1


def reprocess_dl1(
    input_dir,
    config_file=None,
    dl1_files_per_job=50,
    particle=None,
    prod_id=None,
    batch_config=None,
    offset=None,
    workflow_kind="lstchain",
    n_jobs_parallel=50,
):
    """
    Reprocessing of existing dl1 files.
    Organizes files and launches slurm jobs in two slurm arrays.
    The same train/test split performed with the earlier r0 to dl1
    processing is used.

    Parameters
    ----------
    input_dir : str
        path to the files directory to analyse
    config_file :str
        Path to a configuration file. If none is given, the standard configuration of the selected pipeline is applied
    particle : str
        particle type (gamma/gamma_off/proton/electron). Determines output directory structure, job naming
        and n_r0_files_per_dl1_job if not set explicitly.
    offset : str
        gamma offset
    prod_id :str
        Production ID. If None, _v00 will be used, indicating an official base production. Default = None.
    batch_config : dict
        Dictionary containing the (full) source_environment and the slurm_account strings.
        ! NOTE : train_pipe AND dl1_to_dl2 **MUST** be run with the same environment.
    workflow_kind: str
        One of the supported pipelines. Defines the command to be run on r0 files
    n_jobs_parallel: int
        Number of jobs to be run at the same time per array.
    dl1_files_per_job: int
        Number of dl1 files to be processed per job array that was batched.

    Returns
    -------
    jobid2log : dict
        A dictionary of dictionaries containing the full log information of the script. The first `layer` contains
        only the each jobid that the scripts has batched.

            dict[jobid] = information

        The second layer contains, organized by jobid,
             - the kind of particle that corresponded to the jobid
             - the command that was run to batch the job into the server
             - the path to both the output and error files (job_`jobid`.o and job_`jobid`.e) that were generated
                 when the job was send to the cluster

             dict[jobid].keys() = ['particle', 'sbatch_command', 'jobe_path', 'jobo_path']
    jobids_dl1_dl1
        A list of all the jobs sent by particle (including test and train set types).
    """

    log.info("Starting DL1 to DL1 processing for particle {}".format(particle))

    input_dir = Path(input_dir)

    source_environment = batch_config["source_environment"]
    slurm_account = batch_config["slurm_account"]

    if workflow_kind == "lstchain":
        base_cmd = f"{source_environment} lstmcpipe_lst_core_dl1ab -c {config_file} "
        jobtype_id = "LST"
    elif workflow_kind == "ctapipe":
        base_cmd = f"{source_environment} lstmcpipe_cta_core_r0_dl1 -c {config_file} "
        jobtype_id = "CTA"
    else:
        log.critical("Please, selected an allowed workflow kind.")
        exit(-1)

    job_name = {
        "electron": f"e_{jobtype_id}_dl1dl1",
        "gamma": f"g_{jobtype_id}_dl1dl1",
        "gamma-diffuse": f"gd_{jobtype_id}_dl1dl1",
        "proton": f"p_{jobtype_id}_dl1dl1",
        "gamma_off0.0deg": f"g0.0_{jobtype_id}_dl1dl1",
        "gamma_off0.4deg": f"g0.4_{jobtype_id}_dl1dl1",
    }

    log.info("Working on DL1 files in {}".format(input_dir.as_posix()))
    training_input_path = input_dir / "training"
    check_data_path(training_input_path)
    training_list = get_input_filelist(training_input_path)
    ntrain = len(training_list)
    testing_input_path = input_dir / "testing"
    check_data_path(testing_input_path)
    testing_list = get_input_filelist(testing_input_path)
    ntest = len(testing_list)

    log.info("{} DL1 files in training dataset".format(ntrain))
    log.info("{} DL1 files in test dataset".format(ntest))

    with open("training.list", "w+") as newfile:
        for f in training_list:
            newfile.write(f)
            newfile.write("\n")

    with open("testing.list", "w+") as newfile:
        for f in testing_list:
            newfile.write(f)
            newfile.write("\n")

    if "off" in particle:
        # Take out /off0.Xdeg
        running_dir = (
            Path(input_dir.as_posix().replace("DL1", "running_analysis")).parent.parent
            / prod_id
            / offset
        )
    else:
        running_dir = (
            Path(input_dir.as_posix().replace("DL1", "running_analysis")).parent
            / prod_id
        )

    job_logs_dir = running_dir / "job_logs"
    dl1_output_dir = running_dir / "DL1"

    log.info("RUNNING_DIR: {}".format(running_dir))
    log.info("JOB_LOGS DIR: {}".format(job_logs_dir))
    log.info("DL1 DATA DIR: {}".format(dl1_output_dir))

    for directory in [running_dir, dl1_output_dir, job_logs_dir]:
        check_and_make_dir_without_verification(directory)

    # dumping the training and testing lists and splitting them in sub-lists for parallel jobs
    # copy config into working dir
    if config_file is not None:
        shutil.copyfile(
            config_file, running_dir.joinpath(Path(config_file).name)
        )

    # save file lists into logs
    shutil.move("testing.list", running_dir.joinpath("testing.list"))
    shutil.move("training.list", running_dir.joinpath("training.list"))

    jobid2log, jobids_dl1_dl1 = submit_dl1_jobs(
        base_cmd=base_cmd,
        file_lists={"testing": testing_list, "training": training_list},
        particle=particle,
        job_name=job_name[particle],
        dl1_files_per_batched_job=dl1_files_per_job,
        running_dir=running_dir,
        job_logs_dir=job_logs_dir,
        n_jobs_parallel=n_jobs_parallel,
        slurm_account=slurm_account
    )

    # return it log dictionary
    return jobid2log, jobids_dl1_dl1


def submit_dl1_jobs(
    input_dir,
    output_dir,
    base_cmd,
    file_list,
    job_type_id,
    dl1_files_per_batched_job,
    job_logs_dir,
    slurm_account,
    filelist_name,
    n_jobs_parallel=100,
    dl1_processing="r0_dl1",
):
    jobid2log = {}
    jobids_dl1 = []

    log.info("output dir: {}".format(output_dir))

    number_of_sublists = len(file_list) // dl1_files_per_batched_job + int(
        len(file_list) % dl1_files_per_batched_job > 0
    )
    for i in range(number_of_sublists):
        output_file = job_logs_dir.joinpath("{}_{}.sublist".format(filelist_name, i)).resolve().as_posix()
        with open(output_file, "w+") as out:
            for line in file_list[
                i * dl1_files_per_batched_job: dl1_files_per_batched_job * (i + 1)
            ]:
                out.write(line)
                out.write("\n")

    log.info(f"{number_of_sublists} files generated for file list at {input_dir.resolve().as_posix()}")

    sublist_names = [f.as_posix() for f in Path(job_logs_dir).glob("*.sublist")]  # Number of sublists ??

    slurm_options = {
        "output": job_logs_dir.joinpath(f"job_%A_%a.o").as_posix(),
        "error": job_logs_dir.joinpath(f"job_%A_%a.e").as_posix(),
        "array": f"0-{len(sublist_names)-1}%{n_jobs_parallel}",
        "job-name": f"{job_type_id}-{dl1_processing}"
    }

    # All files to long queue
    slurm_options.update({"partition": "long"})
    # `sbatch -A` is the --account slurm argument
    if slurm_account != '':
        slurm_options.update({"account": slurm_account})

    # start 1 jobarray with all files included. The job selects its file based on its task id
    cmd = f'{base_cmd} -f {" ".join(sublist_names)} --output_dir {output_dir}'
    slurm_cmd = "sbatch --parsable "
    for key, value in slurm_options.items():
        slurm_cmd += f"--{key} {value} "
    slurm_cmd += f'--wrap="{cmd}"'

    jobid = os.popen(slurm_cmd).read().strip("\n")
    log.debug(f"Submitted batch job {jobid}")

    jobid2log.update({jobid: slurm_cmd})

    return jobid2log, jobids_dl1
