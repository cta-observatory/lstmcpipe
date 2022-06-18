# #!/usr/bin/env python
import argparse
from pathlib import Path
import tempfile
import subprocess

from lstmcpipe.config.pipeline_config import load_config
from lstchain.io.config import read_configuration_file
from ctapipe.utils import get_dataset_path


def mc_r0_path():
    return get_dataset_path("gamma_test_large.simtel.gz")


def run_lstchain_mc_r0_dl1(simtel_file, outdir, config_file):
    cmd = ['lstchain_mc_r0_to_dl1', '-f', simtel_file, '-o', outdir, '-c', config_file]
    return subprocess.run(cmd)


def test_r0_dl1(config_file):
    tmpdir = tempfile.mkdtemp()
    run_lstchain_mc_r0_dl1(mc_r0_path(), tmpdir, config_file)


def test_dl1ab(config_file):
    tmpdir = tempfile.mkdtemp()
    dl1file = Path(tmpdir, 'dl1_gamma_test_large.h5')
    dl1fileout = Path(tmpdir, 'dl1ab.h5')
    run_lstchain_mc_r0_dl1(mc_r0_path(), tmpdir, config_file)
    cmd = ['lstchain_dl1ab', '-f', dl1file, '-o', dl1fileout, '-c', config_file]
    subprocess.run(cmd)


def validate_lstchain(config_file, stage):
    if stage == 'r0_to_dl1':
        test_r0_dl1(config_file)
    elif stage == 'dl1ab':
        test_dl1ab(config_file)
    else:
        # else we simply validate that reading the config is ok
        read_configuration_file(config_file)


def main():
    parser = argparse.ArgumentParser(description="Validate your lstmcpipe config")

    # Required arguments
    parser.add_argument(
        dest='lstmcpipe_config_filename',
        type=Path,
        help='Path to lstmcpipe config file',
    )

    # optional
    parser.add_argument(
        '--lstchain_config',
        '-lc',
        action='store',
        type=Path,
        dest='lstchain_config_filename',
        help='Path to the lstchain config file.',
        default=None,
    )

    args = parser.parse_args()

    config = load_config(args.lstmcpipe_config_filename)
    if args.lstchain_config_filename is not None:
        validate_lstchain(args.lstchain_config_filename, stage=config['stages_to_run'][0])

    print("\n\nValid configs :)")


if __name__ == '__main__':
    main()

