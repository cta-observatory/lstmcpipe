import os
from shutil import which


def export_env(outdir='.'):
    if which('conda') is not None:
        os.system((f"conda env export > {os.path.join(outdir, 'conda_env.yml')}"))
    elif which('pip') is not None:
        os.system(f"python -m pip freeze > {os.path.join(outdir, 'requirements.txt')}")

