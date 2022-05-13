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
        `Shell` is forced to True, thus a single string (shell cmd) is expected.

    Returns
    -------
    (subprocess.Popen.stdout).strip('\n')
    """
    cmd = sp.Popen(args, shell=True, stdout=sp.PIPE, stderr=sp.STDOUT, encoding='utf-8')
    stdout, _ = cmd.communicate()

    if cmd.returncode != 0:
        raise ValueError(f"Running {args[0]} failed with return code {cmd.returncode}" f", output: \n {stdout}")
    else:
        return stdout.strip('\n')


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
        slurm_deps=None,
        slurm_options=None,
    ):
        self.base_slurm_command = "sbatch --parsable"
        self.wrap_cmd = ""

        self.slurm_output = f" --output={slurm_output}" if slurm_output is not None else " --output=./slurm-%j.o"
        self.slurm_error = f" --error={slurm_error}" if slurm_error is not None else " --error=./slurm-%j.e"
        self.job_name = f" --job-name={job_name}" if job_name is not None else ""
        self.slurm_account = f" --account={slurm_account}" if slurm_account is not None else ""
        self.slurm_dependencies = self.check_slurm_dependencies(slurm_deps)

        self.slurm_partition = f" --partition={slurm_account}" if slurm_partition is not None else " --partition=short"
        self.slurm_options = f"{slurm_options}" if slurm_options is not None else None

    def __repr__(self):
        # return full string
        return self._slurm_command()

    def compose_wrap_command(self, wrap_command=None, source_env="", backend=""):
        if wrap_command is None:
            raise ValueError("You must pass a command.")
        if source_env != "" and not source_env.strip().endswith(";"):
            source_env += "; "
        if backend != "" and not backend.strip().endswith(";"):
            backend += "; "
        self.wrap_cmd = f' --wrap="{backend}{source_env}{wrap_command}"'

    def _slurm_command(self):
        if self.wrap_cmd == "" or self.wrap_cmd is None:
            _wrap_cmd = " <MISSING COMMAND TO BE RUN>"
            warnings.warn("Missing command to be batched. Add it by SbatchLstMCStage().compose_wrap_command('COMMAND')")
        else:
            _wrap_cmd = self.wrap_cmd

        if self.slurm_options is not None:
            return (
                f"{self.base_slurm_command}{self.job_name}{self.slurm_options}"
                f"{self.slurm_error}{self.slurm_output}{self.slurm_dependencies}"
                f"{self.slurm_account}{_wrap_cmd}"
            )
        else:
            return (
                f"{self.base_slurm_command}{self.job_name}{self.slurm_partition}"
                f"{self.slurm_error}{self.slurm_output}{self.slurm_dependencies}"
                f"{self.slurm_account}{_wrap_cmd}"
            )

    @staticmethod
    def check_slurm_dependencies(slurm_deps, dependency="afterok"):
        if slurm_deps is None:
            return ""
        else:
            if all(items != "" for items in slurm_deps.split(",")):
                return f" --dependency={dependency}:{slurm_deps}"
            else:
                raise ValueError("Slurm dependencies contain an empty value between commas, i.e.; ,'', ")

    def r0_dl1_default_options(self, process_dl1_job_name="r0_dl1", array="0-99%100"):
        self.job_name = f" --job-name={process_dl1_job_name}"
        self.slurm_options = f" --partition=long --array={array}"

    def dl1ab_default_options(self, process_dl1ab_job_name="r0_dl1", array="0-99%100"):
        self.job_name = f" --job-name={process_dl1ab_job_name}"
        self.slurm_options = f" --partition=long --array={array}"

    def merge_dl1_default_options(self):
        self.job_name = " --job-name=merge"
        self.slurm_partition = " --partition=long"

    def train_test_splitting_default_options(self):
        self.job_name = " --job-name=splitting_train_test"
        self.slurm_partition = " --partition=short"

    def trainpipe_default_options(self):
        self.job_name = " --job-name=train_pipe"
        # self.slurm_options = " --partition=long --mem=32G"
        self.slurm_options = " --partition=xxl --mem=100G --cpus-per-task=16"

    def train_plot_rf_feat_default_optios(self):
        self.job_name = " --job-name=RF_importance"
        self.slurm_options = " --partition=short --mem=16G"

    def dl1_dl2_default_options(self):
        self.job_name = " --job-name=dl1_2"
        self.slurm_options = " --partition=short --mem=32G"

    def dl2_irfs_default_options(self):
        self.job_name = " --job-name=dl2_IRFs"
        self.slurm_partition = " --partition=short"

    def dl2_sens_default_options(self):
        self.job_name = " --job-name=dl2_sens"
        self.slurm_options = " --partition=short --mem=32G"

    def dl2_sens_plot_default_options(self):
        self.job_name = " --job-name=dl2_sens_plot"
        self.slurm_partition = " --partition=short"

    @property
    def submit(self):
        if self.wrap_cmd is None or self.wrap_cmd == "":
            raise ValueError(
                "You must first define the command to be batched: " "SbatchLstMCStage().wrap_command('COMMAND')"
            )
        else:
            jobid = run_command(self._slurm_command())
            return jobid

    # def load_from_log(self, jobid):
    #     jobid = ''
    #     NotImplementedError("Sorry, we are working on it")
    #     # TODO
