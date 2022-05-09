#!/usr/bin/env python


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
        self.wrap_cmd = None
        self.slurm_cmd = None

        self.slurm_output = f" --output={slurm_output}" if slurm_output is not None else " --output=./slurm-%j.o"
        self.slurm_error = f" --error={slurm_error}" if slurm_error is not None else " --error=./slurm-%j.e"
        self.job_name = f" --job-name={job_name}" if job_name is not None else ""
        self.slurm_account = f" --account={slurm_account}" if slurm_account is not None else ""
        self.slurm_dependencies = self.check_slurm_dependencies(slurm_depen)

        self.slurm_partition = f" --partition={slurm_account}" if slurm_partition is not None else " --partition=short"
        self.slurm_options = f" {slurm_options}" if slurm_options is not None else None

    def check_slurm_dependencies(self, slurm_deps, dependency="afterok"):
        if all(items != "" for items in slurm_deps.split(",")):
            self.slurm_dependencies = f" --dependency={dependency}:{slurm_deps}"
        else:
            raise ValueError("Slurm dependencies contain an empty value between commas, i.e.; '' ")

    def wrap_command(self, wrap_cmd, source_env=""):
        if wrap_cmd is None:
            raise ValueError("You must pass the command to be batched")
        self.wrap_cmd = f' --wrap="{source_env} {wrap_cmd}"'

    @property
    def compose_sbatch_command(self, check_cmd=False):
        """Compose the final slurm sbatch command to be batched"""
        if self.wrap_cmd is None:
            raise ValueError("You must define the command to be batched")
        else:
            if self.slurm_options is not None:
                self.slurm_cmd = (
                    f"{self.base_slurm_command}{self.slurm_partition}{self.slurm_account}"
                    f"{self.slurm_error}{self.slurm_output}{self.slurm_dependencies}"
                    f"{self.job_name}{self.wrap_cmd}"
                )
            else:
                self.slurm_cmd = (
                    f"{self.base_slurm_command}{self.slurm_options}"
                    f"{self.slurm_error}{self.slurm_output}{self.slurm_dependencies}"
                    f"{self.job_name}{self.wrap_cmd}"
                )

        if check_cmd:
            print(self.slurm_cmd)

    def r0_dl1_default_options(self):
        self.job_name = " --job-name=train_pipe"
        self.slurm_partition = " --partition=long"
        # TODO finish (array)
        pass

    def dl1ab_default_options(self):
        self.job_name = " --job-name=dl1ab"
        self.slurm_partition = " --partition=long"
        # TODO finish (array)
        pass

    def merge_dl1_default_options(self):
        self.job_name = " --job-name=merge"
        self.slurm_partition = " --partition=short"

    def train_test_splitting_default_options(self):
        self.job_name = " --job-name=splitting_train_test"
        self.slurm_partition = " --partition=short"

    def train_default_options(self):
        self.job_name = " --job-name=train_pipe"
        self.slurm_options = " --partition=long --mem=32G"

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
        jobid = ''
        return jobid

    def load_from_log(self, jobid):
        # TODO
        pass
