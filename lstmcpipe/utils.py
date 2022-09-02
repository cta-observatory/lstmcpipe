#!/usr/bin/env python

import os
import json
import shutil
import logging
import warnings
import subprocess as sp
from pathlib import Path
from ruamel.yaml import YAML
from pprint import pprint
from copy import deepcopy
from deepdiff import DeepDiff


log = logging.getLogger(__name__)


def save_log_to_file(dictionary, output_file, workflow_step=None):
    """
    Dumps a dictionary (log) into a dicts of dicts with keys each of the pipeline stages.

    Parameters
    ----------
    dictionary : dict
        The dictionary to be dumped to a file
    output_file : str or Path
        Output file to store the log
    workflow_step : str
        Step of the workflow, to be recorded in the log

    Returns
    -------
        None
    """
    if workflow_step is None:
        workflow_step = "NoKEY"

    dict2log = {workflow_step: dictionary}

    with open(output_file, "a+") as fileout:
        YAML().dump(dict2log, fileout)


def batch_mc_production_check(
    dict_jobids_all_stages,
    log_directory,
    prod_id,
    prod_config_file,
    batch_config,
    logs_files,
):
    """
    Check that the dl1_to_dl2 stage, and therefore, the whole workflow has ended correctly.
    The machine information of each job will be dumped to the file.
    The file will take the form `check_MC_prodID_{prod_id}_OK.txt`

    Parameters
    ----------
    dict_jobids_all_stages : dict
        dict containing the {stage: all_job_ids related} information
    log_directory: Path
    prod_id: str
    prod_config_file: str
    batch_config: dict
    logs_files: dict
        Dictionary with logs files

    Returns
    -------
    jobid : str

    """
    debug_log = {}
    all_pipeline_jobs = []

    source_env = batch_config["source_environment"]
    slurm_account = batch_config["slurm_account"]

    for stage, jobids in dict_jobids_all_stages.items():
        all_pipeline_jobs.append(jobids)
        debug_log.update({f"SUMMARY_{stage}": jobids})

    all_pipeline_jobs = ",".join(all_pipeline_jobs)

    # Copy lstmcpipe config used to log directory
    shutil.copyfile(Path(prod_config_file).resolve(), log_directory.joinpath(f"config_MC_prod_{prod_id}.yml"))

    # Save machine info into the check file
    check_prod_file = log_directory.joinpath(f"check_MC_{prod_id}.txt").absolute().as_posix()

    cmd_wrap = f"touch {check_prod_file}; "
    cmd_wrap += (
        f"sacct --format=jobid,jobname,nodelist,cputime,state,exitcode,avediskread,maxdiskread,avediskwrite,"
        f"maxdiskwrite,AveVMSize,MaxVMSize,avecpufreq,reqmem -j {all_pipeline_jobs} >> {check_prod_file}; "
        f"mv slurm-* IRFFITSWriter.provenance.log {log_directory.absolute().as_posix()} "
    )

    batch_cmd = "sbatch -p short --parsable"
    if slurm_account != "":
        batch_cmd += f" -A {slurm_account}"
    batch_cmd += f" --dependency=afterok:{all_pipeline_jobs} -J prod_check" f' --wrap="{source_env} {cmd_wrap}"'

    jobid = os.popen(batch_cmd).read().strip("\n")
    log.info(f"Submitted batch CHECK-job {jobid}")
    debug_log.update({f"prod_check_{jobid}": batch_cmd})

    save_log_to_file(debug_log, logs_files["debug_file"], workflow_step="check_full_workflow")

    return jobid


def rerun_cmd(cmd, outfile, max_ntry=2, subdir_failures='failed_outputs', **run_kwargs):
    """
    rerun r0_to_dl1 process given by `cmd` as long as the exit code is 0 and number of try < max_ntry
    move the failed output file to subdir failed_outputs

    Parameters
    ----------
    cmd: str
    subdir_failures: str
    outfile: Path
        path to the cmd output file
    max_ntry: int
    run_kwargs: kwargs for subprocess.run

    Returns
    -------
    ntry: int
        number of tries actually run
    """
    outfile = Path(outfile)
    ret = -1
    ntry = 1
    while ret != 0 and ntry <= max_ntry:
        ret = sp.run(cmd, **run_kwargs).returncode
        if ret != 0:
            failed_jobs_subdir = outfile.parent.joinpath(subdir_failures)
            if outfile.exists():
                failed_jobs_subdir.mkdir(exist_ok=True)
                outfile_target = failed_jobs_subdir.joinpath(outfile.name)
                print(f"Move failed output file from {outfile} to {outfile_target}. try #{ntry}")
                shutil.move(outfile, outfile_target)

        ntry += 1
    return ntry - 1


def dump_lstchain_std_config(filename='lstchain_config.json', allsky=False, overwrite=False):
    from lstchain.io.config import get_standard_config

    filename = Path(filename)

    if filename.exists() and not overwrite:
        raise FileExistsError(f"{filename} exists already")

    std_cfg = get_standard_config()
    cfg = deepcopy(std_cfg)

    cfg['LocalPeakWindowSum']['apply_integration_correction'] = True
    cfg['GlobalPeakWindowSum']['apply_integration_correction'] = True
    cfg['source_config']['EventSource']['allowed_tels'] = [1]
    cfg['random_forest_energy_regressor_args']['min_samples_leaf'] = 10
    cfg['random_forest_disp_regressor_args']['min_samples_leaf'] = 10
    cfg['random_forest_disp_classifier_args']['min_samples_leaf'] = 10
    cfg['random_forest_particle_classifier_args']['min_samples_leaf'] = 10
    cfg['random_forest_energy_regressor_args']['n_jobs'] = -1
    cfg['random_forest_disp_regressor_args']['n_jobs'] = -1
    cfg['random_forest_disp_classifier_args']['n_jobs'] = -1
    cfg['random_forest_particle_classifier_args']['n_jobs'] = -1

    if allsky:
        for rf_feature in [
            'energy_regression_features',
            'disp_regression_features',
            'disp_classification_features',
            'particle_classification_features',
        ]:
            cfg[rf_feature] = std_cfg[rf_feature]
            if 'alt_tel' not in cfg[rf_feature]:
                cfg[rf_feature].append('alt_tel')
            if 'az_tel' not in cfg[rf_feature]:
                cfg[rf_feature].append('az_tel')

    extra_msg = "for AllSky prod" if allsky else ""
    print(f"Updating std lstchain config {extra_msg} with")
    diff = DeepDiff(std_cfg, cfg)
    pprint(diff)

    with open(filename, 'w') as file:
        json.dump(cfg, file, indent=4)
    print(f"\nModified lstchain config dumped in {filename}. Check full config thoroughly.")


def run_command(*args):
    """
    Runs the command passed through args, as a subprocess.Popen() call.

    Based on:
    https://github.com/cta-observatory/cta-lstchain/blob/master/lstchain/scripts/tests/test_lstchain_scripts.py#L43

    Parameters
    ----------
    args: str or iter
        `Shell` is forced to True, thus a single string (shell cmd) is expected.

    Returns
    -------
    (subprocess.Popen.stdout).strip('\n')
    """
    cmd = sp.Popen(args, shell=True, stdout=sp.PIPE, stderr=sp.STDOUT, encoding='utf-8')
    stdout, _ = cmd.communicate()

    if cmd.returncode != 0:
        raise ValueError(f"Running `{args[0]}` failed with return code {cmd.returncode}, output: \n {stdout}")
    else:
        return stdout.strip('\n')


class SbatchLstMCStage:
    """
    Base class to (slurm) sbatch a lstMCpipe stage
    """

    def __init__(
        self,
        stage,
        wrap_command,
        slurm_output=None,
        slurm_error=None,
        job_name=None,
        slurm_account=None,
        slurm_partition=None,
        slurm_deps=None,
        slurm_options=None,
        source_environment="",
        backend="",
    ):
        self.base_slurm_command = "sbatch --parsable"

        self.slurm_output = f"--output={slurm_output}" if slurm_output is not None else "--output=./slurm-%j.o"
        self.slurm_error = f"--error={slurm_error}" if slurm_error is not None else "--error=./slurm-%j.e"
        self.job_name = f"--job-name={job_name}" if job_name is not None else ""
        self.slurm_account = f"--account={slurm_account}" if slurm_account is not None else ""

        self.slurm_partition = f"--partition={slurm_account}" if slurm_partition is not None else "--partition=short"
        self.slurm_options = f"{slurm_options}" if slurm_options is not None else None

        self.stage_default_options(stage)
        self.slurm_dependencies = None
        self.check_slurm_dependencies(slurm_deps)
        self.wrap_cmd = wrap_command
        self.compose_wrap_command(wrap_command, source_environment, backend)

    def __str__(self):
        # return full string
        return self.slurm_command

    @property
    def _valid_stages(self):
        return [
            "r0_to_dl1",
            "dl1ab",
            "merge_dl1",
            "train_test_splitting",
            "train_pipe",
            "RF_importance",
            "dl1_to_dl2",
            "dl2_to_irfs",
            "dl2_sens",
            "dl2_sens_plot",
        ]

    def compose_wrap_command(self, wrap_command=None, source_env="", backend=""):
        if wrap_command is None or wrap_command == "":
            warnings.warn("You must pass a command to be batched! ")
        if source_env != "" and not source_env.strip().endswith(";"):
            source_env = source_env.strip() + "; "
        if backend != "" and not backend.strip().endswith(";"):
            backend = backend.strip() + "; "
        self.wrap_cmd = f'--wrap="{backend}{source_env}{wrap_command}"'

    @property
    def slurm_command(self):
        if self.slurm_options is not None:
            return (
                f"{self.base_slurm_command} {self.job_name} {self.slurm_options}"
                f" {self.slurm_error} {self.slurm_output} {self.slurm_dependencies}"
                f" {self.slurm_account} {self.wrap_cmd}"
            )
        else:
            return (
                f"{self.base_slurm_command} {self.job_name} {self.slurm_partition}"
                f" {self.slurm_error} {self.slurm_output} {self.slurm_dependencies}"
                f" {self.slurm_account} {self.wrap_cmd}"
            )

    def check_slurm_dependencies(self, slurm_deps, dependency="afterok"):
        if slurm_deps is None:
            self.slurm_dependencies = ""
        else:
            if all(items != "" for items in slurm_deps.split(",")):
                self.slurm_dependencies = f"--dependency={dependency}:{slurm_deps}"
            else:
                raise ValueError("Slurm dependencies contain an empty value between commas, i.e.; ,'', ")

    def stage_default_options(self, stage):
        if stage not in self._valid_stages or stage is None:
            raise ValueError(f"Please select a valid stage: \n{', '.join(self._valid_stages)}")

        _default_options = {
            "r0_to_dl1": getattr(self, "r0_dl1_options"),
            "dl1ab": getattr(self, "dl1ab_options"),
            "merge_dl1": getattr(self, "set_merge_dl1_default_options"),
            "train_test_splitting": getattr(self, "set_train_test_splitting_default_options"),
            "train_pipe": getattr(self, "set_trainpipe_default_options"),
            "RF_importance": getattr(self, "set_train_plot_rf_feat_default_options"),
            "dl1_to_dl2": getattr(self, "set_dl1_dl2_default_options"),
            "dl2_to_irfs": getattr(self, "set_dl2_irfs_default_options"),
            "dl2_sens": getattr(self, "set_dl2_sens_default_options"),
            "dl2_sens_plot": getattr(self, "set_dl2_sens_plot_default_options"),
        }
        _default_options[stage]()

    def submit(self):
        if self.wrap_cmd is None or self.wrap_cmd == "":
            raise ValueError(
                "You must first define the command to be batched: " "SbatchLstMCStage().wrap_command('COMMAND')"
            )
        else:
            jobid = run_command(self.slurm_command)
            return jobid

    def r0_dl1_options(self, process_dl1_job_name="r0_dl1", array="0-0%100", partition="long", extra_slurm_options=""):
        self.job_name = f"--job-name={process_dl1_job_name}"
        self.slurm_options = f"--partition={partition} --array={array} {extra_slurm_options}"

    def dl1ab_options(self, process_dl1ab_job_name="dl1ab", array="0-0%100", partition="long", extra_slurm_options=""):
        self.job_name = f"--job-name={process_dl1ab_job_name}"
        self.slurm_options = f"--partition={partition} --array={array} {extra_slurm_options}"

    def set_merge_dl1_default_options(self):
        self.job_name = "--job-name=merge"
        self.slurm_partition = "--partition=long"

    def set_train_test_splitting_default_options(self):
        self.job_name = "--job-name=train_test_splitting"
        self.slurm_partition = "--partition=short"

    def set_trainpipe_default_options(self):
        self.job_name = "--job-name=train_pipe"
        # self.slurm_options = " --partition=long --mem=32G"
        self.slurm_options = "--partition=xxl --mem=100G --cpus-per-task=16"

    def set_train_plot_rf_feat_default_options(self):
        self.job_name = "--job-name=RF_importance"
        self.slurm_options = "--partition=short --mem=16G"

    def set_dl1_dl2_default_options(self):
        self.job_name = "--job-name=dl1_2"
        self.slurm_options = "--partition=short --mem=32G"

    def set_dl2_irfs_default_options(self):
        self.job_name = "--job-name=dl2_IRFs"
        self.slurm_partition = "--partition=short"

    def set_dl2_sens_default_options(self):
        self.job_name = "--job-name=dl2_sens"
        self.slurm_options = "--partition=short --mem=32G"

    def set_dl2_sens_plot_default_options(self):
        self.job_name = "--job-name=dl2_sens_plot"
        self.slurm_partition = "--partition=short"
