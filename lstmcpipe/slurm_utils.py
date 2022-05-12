#!/usr/bin/env python

import warnings
import subprocess as sp


def run_command(*args):
    """
    Runs the command passed through args, as a subprocess.run() call.

    Based on:
    https://github.com/cta-observatory/cta-lstchain/blob/master/lstchain/scripts/tests/test_lstchain_scripts.py#L43

    Parameters
    ----------
    args: str or iter

    Returns
    -------
    subprocess.CompletedProcess()
    """
    cmd = sp.run(args, stdout=sp.PIPE, stderr=sp.STDOUT, encoding='utf-8')

    if cmd.returncode != 0:
        raise ValueError(f"Running {args[0]} failed with return code {cmd.returncode}" f", output: \n {cmd.stdout}")
    else:
        return cmd


class SbatchLstMCStage:
    """
    Base class to (slurm) sbatch a lstMCpipe stage
    """

    def __init__(
        self,
        slurm_output=None,
        slurm_error=None,
        job_name=None,
        slurm_account=None,
        slurm_partition=None,
        slurm_depen=None,
        slurm_options=None,
    ):
        self.base_slurm_command = "sbatch --parsable"
        self.wrap_cmd = ""

        self.slurm_output = f"--output={slurm_output}" if slurm_output is not None else "--output=./slurm-%j.o"
        self.slurm_error = f"--error={slurm_error}" if slurm_error is not None else "--error=./slurm-%j.e"
        self.job_name = f"--job-name={job_name}" if job_name is not None else ""
        self.slurm_account = f"--account={slurm_account}" if slurm_account is not None else ""
        self.slurm_dependencies = self.check_slurm_dependencies(slurm_depen)

        self.slurm_partition = f"--partition={slurm_account}" if slurm_partition is not None else "--partition=short"
        self.slurm_options = f"{slurm_options}" if slurm_options is not None else None

    def __repr__(self):
        # return full string
        return self._slurm_command()

    def __str__(self):
        # return list to be passed to subprocess
        return self._slurm_command().split()

    def check_slurm_dependencies(self, slurm_deps, dependency="afterok"):
        if slurm_deps is None:
            self.slurm_dependencies = ""
        else:
            if all(items != "" for items in slurm_deps.split(",")):
                self.slurm_dependencies = f"--dependency={dependency}:{slurm_deps}"
            else:
                raise ValueError("Slurm dependencies contain an empty value between commas, i.e.; ,'', ")

    def wrap_command(self, wrap_command=None, source_env="", backend=""):
        if wrap_command is None:
            raise ValueError("You must pass a command.")
        self.wrap_cmd = f'--wrap="{backend}{source_env}{wrap_command}"'

    def _slurm_command(self):
        if self.wrap_cmd == "" or self.wrap_cmd is None:
            _wrap_cmd = ""
            warnings.warn("Missing command to be batched. Add it by SbatchLstMCStage().wrap_command('COMMAND')")
        else:
            _wrap_cmd = self.wrap_cmd

        if self.slurm_options is not None:
            return (
                f"{self.base_slurm_command} {self.job_name} {self.slurm_options}"
                f" {self.slurm_error} {self.slurm_output} {self.slurm_dependencies}"
                f" {self.slurm_account} {_wrap_cmd}"
            )
        else:
            return (
                f"{self.base_slurm_command} {self.job_name} {self.slurm_partition}"
                f" {self.slurm_error} {self.slurm_output} {self.slurm_dependencies}"
                f" {self.slurm_account} {_wrap_cmd}"
            )

    def r0_dl1_default_options(self, process_dl1_job_name="r0_dl1", array="0-99%100"):
        self.job_name = f"--job-name={process_dl1_job_name}"
        self.slurm_options = f"--partition=long --array={array}"

    def dl1ab_default_options(self, process_dl1ab_job_name="r0_dl1", array="0-99%100"):
        self.job_name = f"--job-name={process_dl1ab_job_name}"
        self.slurm_options = f"--partition=long --array={array}"

    def merge_dl1_default_options(self):
        self.job_name = "--job-name=merge"
        self.slurm_partition = "--partition=long"

    def train_test_splitting_default_options(self):
        self.job_name = "--job-name=splitting_train_test"
        self.slurm_partition = "--partition=short"

    def train_default_options(self):
        self.job_name = "--job-name=train_pipe"
        # self.slurm_options = "--partition=long --mem=32G"
        self.slurm_options = "--partition=xxl --mem=100G --cpus-per-task=16"

    def dl1_dl2_default_options(self):
        self.job_name = "--job-name=dl1_2"
        self.slurm_options = "--partition=short --mem=32G"

    def dl2_irfs_default_options(self):
        self.job_name = "--job-name=dl2_IRFs"
        self.slurm_partition = "--partition=short"

    def dl2_sens_default_options(self):
        self.job_name = "--job-name=dl2_sens"
        self.slurm_options = "--partition=short --mem=32G"

    def dl2_sens_plot_default_options(self):
        self.job_name = "--job-name=dl2_sens_plot"
        self.slurm_partition = "--partition=short"

    @property
    def submit(self):
        if self.wrap_cmd is None or self.wrap_cmd == "":
            raise ValueError(
                "You must first define the command to be batched: " "SbatchLstMCStage().wrap_command('COMMAND')"
            )
        else:
            cmd = run_command(self._slurm_command().split())
            jobid = cmd.stdout.strip("\n")
            return jobid

    # def load_from_log(self, jobid):
    #     jobid = ''
    #     NotImplementedError("Sorry, we are working on it")
    #     # TODO
