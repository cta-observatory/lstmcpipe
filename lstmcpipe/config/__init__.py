import os
from shutil import which
from .pipeline_config import parse_config_and_handle_global_vars

__all__ = ["parse_config_and_handle_global_vars"]

def export_env(outdir='.'):
    if which('conda') is not None:
        os.system((f"conda env export > {os.path.join(outdir, 'conda_env.yml')}"))
    elif which('pip') is not None:
        os.system(f"python -m pip freeze > {os.path.join(outdir, 'requirements.txt')}")