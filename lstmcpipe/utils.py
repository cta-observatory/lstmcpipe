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
        debug_log[f"SUMMARY_{stage}"] = jobids

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
    debug_log[f"prod_check_{jobid}"] = batch_cmd

    save_log_to_file(debug_log, logs_files["debug_file"], workflow_step="check_full_workflow")

    return jobid


def rerun_cmd(cmd, outfile, max_ntry=2, subdir_failures="failed_outputs", **run_kwargs):
    """
    Rerun the command up to max_ntry times.
    If all attempts fail, raise an exception.

    Parameters
    ----------
    cmd: list
        Command to run as a list of strings
    outfile: Path
        Path to the cmd output file
    max_ntry: int
        Maximum number of attempts to run the command
    subdir_failures: str
        Subdirectory to move failed output files to
    run_kwargs: kwargs
        Additional keyword arguments for subprocess.run

    Raises
    ------
    RuntimeError
        If the command fails after all retry attempts
    """
    outfile = Path(outfile)
    for ntry in range(1, max_ntry + 1):
        result = sp.run(cmd, **run_kwargs, capture_output=True, text=True, check=False)

        if result.returncode == 0:
            return ntry  # Success, return the number of tries it took

        # Command failed, handle the error
        failed_jobs_subdir = outfile.parent.joinpath(subdir_failures)
        if outfile.exists():
            failed_jobs_subdir.mkdir(exist_ok=True)
            outfile_target = failed_jobs_subdir.joinpath(outfile.name)
            print(f"Move failed output file from {outfile} to {outfile_target}. try #{ntry}")
            shutil.move(outfile, outfile_target)

        # If this was the last try, raise an exception
        if ntry == max_ntry:
            error_message = f"Command failed after {max_ntry} attempts. Last failure details:\n"
            error_message += f"Command: {' '.join(cmd)}\n"
            error_message += f"Return code: {result.returncode}\n"
            error_message += f"STDOUT: {result.stdout}\n"
            error_message += f"STDERR: {result.stderr}\n"
            raise RuntimeError(error_message)

    # This line should never be reached due to the raise in the loop
    raise RuntimeError("Unexpected error in rerun_cmd")


def dump_lstchain_std_config(filename='lstchain_config.json', allsky=True, overwrite=False):
    from lstchain.io.config import get_mc_config

    filename = Path(filename)

    if filename.exists() and not overwrite:
        raise FileExistsError(f"{filename} exists already")

    std_cfg = get_mc_config()
    cfg = deepcopy(std_cfg)

    if not allsky:
        for rf_feature in [
            'energy_regression_features',
            'disp_regression_features',
            'disp_classification_features',
            'particle_classification_features',
        ]:
            cfg[rf_feature] = std_cfg[rf_feature]
            for feature in ['alt_tel', 'az_tel', 'sin_az_tel']:
                if feature in cfg[rf_feature]:
                    cfg[rf_feature].remove(feature)

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
        slurm_dependencies=None,
        extra_slurm_options=None,
        source_environment="",
        backend="",
    ):
        self.base_slurm_command = "sbatch --parsable"
        self.stage = stage
        self.wrap_cmd = wrap_command

        self.slurm_output = "./slurm-%j.o" if slurm_output is None else slurm_output
        self.slurm_error = "./slurm-%j.e" if slurm_error is None else slurm_error
        self.job_name = job_name
        self.slurm_account = slurm_account
        self.slurm_dependencies = slurm_dependencies
        self.extra_slurm_options = extra_slurm_options

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
        else:
            # Remove trailing semicolon and any extra spaces
            wrap_command = wrap_command.rstrip(";").strip()
            # exit if any command fails
            wrap_command = wrap_command + ' || exit ' + r'\$?'
        if source_env != "" and not source_env.strip().endswith(";"):
            source_env = f"{source_env.strip()}; "
        if backend != "" and not backend.strip().endswith(";"):
            backend = f"{backend.strip()}; "
        self.wrap_cmd = f'--wrap="{backend}{source_env}{wrap_command}"'

    @property
    def slurm_command(self):
        slurm_options_string = ""
        for key, value in self.slurm_options.items():
            if key == "job_name":
                slurm_options_string += f"--job-name={value} "
            elif key == "dependencies":
                slurm_options_string += f"{self._construct_slurm_dependencies()} "
            elif value is not None or value != "":
                slurm_options_string += f"--{key}={value} "
        return f"{self.base_slurm_command} {slurm_options_string} {self.wrap_cmd}"

    def _construct_slurm_dependencies(self):
        dependency_type = "afterok"
        slurm_deps = self.slurm_options.get('dependencies', None)
        if slurm_deps is None or slurm_deps == "":
            return ""
        elif all(items != "" for items in slurm_deps.split(",")):
            return f"--dependency={dependency_type}:{slurm_deps.replace(',',':')}"
        else:
            raise ValueError("Slurm dependencies contain an empty value between commas, i.e.; ,'', ")

    def stage_default_options(self, stage):
        if self.stage not in self._valid_stages:
            raise ValueError(f"Please select a valid stage: \n{', '.join(self._valid_stages)}")

        default_options = {'partition': 'short'}

        stage_options_dict = {
            "r0_to_dl1": getattr(self, "r0_dl1_default_options"),
            "dl1ab": getattr(self, "dl1ab_default_options"),
            "merge_dl1": getattr(self, "merge_dl1_default_options"),
            "train_test_splitting": getattr(self, "train_test_splitting_default_options"),
            "train_pipe": getattr(self, "trainpipe_default_options"),
            "RF_importance": getattr(self, "train_plot_rf_feat_default_options"),
            "dl1_to_dl2": getattr(self, "dl1_dl2_default_options"),
            "dl2_to_irfs": getattr(self, "dl2_irfs_default_options"),
            "dl2_sens": getattr(self, "dl2_sens_default_options"),
            "dl2_sens_plot": getattr(self, "dl2_sens_plot_default_options"),
        }

        default_options.update(stage_options_dict[stage])
        return default_options

    def submit(self):
        if self.wrap_cmd is not None and self.wrap_cmd != "":
            jobid = run_command(self.slurm_command)
            return jobid
        else:
            raise ValueError(
                "You must first define the command to be batched: " "SbatchLstMCStage().wrap_command('COMMAND')"
            )

    @property
    def slurm_options(self):
        self._construct_slurm_options_dict()
        return self._slurm_options

    def _construct_slurm_options_dict(self):
        """
        Construct the complet set of slurm options with the following priority order:
        - default ones for the stage
        - the general ones (job_name, error, output, account)
        - extra_slurm_options
        """
        # set all the slurm options with the following priority order: default, general, extra_slurm_options
        self._slurm_options = {}
        self._slurm_options.update(self.stage_default_options(self.stage))

        if self.job_name is not None:
            self._slurm_options['job-name'] = self.job_name
        if self.slurm_account is not None:
            self._slurm_options['account'] = self.slurm_account
        if self.slurm_error is not None:
            self._slurm_options['error'] = self.slurm_error
        if self.slurm_output is not None:
            self._slurm_options['output'] = self.slurm_output
        if self.slurm_dependencies is not None:
            self._slurm_options['dependencies'] = self.slurm_dependencies
        if self.extra_slurm_options is not None:
            self._slurm_options.update(self.extra_slurm_options)

    @property
    def r0_dl1_default_options(self):
        return {'job-name': 'r0_dl1', 'partition': 'long', 'array': '0-0%100'}

    @property
    def dl1ab_default_options(self):
        return {'job-name': 'dl1ab', 'array': '0-0%100', 'partition': 'long'}

    @property
    def merge_dl1_default_options(self):
        return {'job-name': 'merge', 'partition': 'long'}

    @property
    def train_test_splitting_default_options(self):
        return {'job-name': 'train_test_split', 'partition': 'short'}

    @property
    def trainpipe_default_options(self):
        return {'job-name': 'train_pipe', 'partition': 'xxl', 'mem': '100GB', 'cpus-per-task': 16}

    @property
    def train_plot_rf_feat_default_options(self):
        return {'job-name': 'RF_importance', 'partition': 'short', 'mem': '16GB'}

    @property
    def dl1_dl2_default_options(self):
        return {'job-name': 'dl1_dl2', 'partition': 'short', 'mem': '32GB'}

    @property
    def dl2_irfs_default_options(self):
        return {'job-name': 'dl2_irfs', 'partition': 'short'}

    @property
    def dl2_sens_default_options(self):
        return {'job-name': 'dl2_sens', 'mem': '32GB'}

    @property
    def dl2_sens_plot_default_options(self):
        return {'job-name': 'dl2_sens_plot', 'partition': 'short'}
