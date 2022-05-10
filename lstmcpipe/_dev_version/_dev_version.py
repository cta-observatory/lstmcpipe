# Try to use setuptools_scm to get the current version; this is only used
# in development installations from the git repository.
# see lstmcpipe/version.py for details
from .. import lstmcpipe_root_dir

try:
    from setuptools_scm import get_version

    version = get_version(root=lstmcpipe_root_dir)
except Exception as e:
    raise ImportError(f"setuptools_scm broken or not installed: {e}")
