# #!/usr/bin/env python
import argparse
from pathlib import Path

from lstmcpipe.config.pipeline_config import load_config
from lstchain.io.config import read_configuration_file


def validate_lstchain(filename):
    read_configuration_file(filename)


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

    load_config(args.lstmcpipe_config_filename)
    if args.lstchain_config_filename is not None:
        validate_lstchain(args.lstchain_config_filename)

    print("Valid configs :)")


if __name__ == '__main__':
    main()

