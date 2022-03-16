# #!/usr/bin/env python
import argparse
import yaml
from pathlib import Path

# from lstmcpipe.config import load_config
from lstmcpipe.config.pipeline_config import config_valid
from lstchain.io.config import read_configuration_file


def validate_lstmcpipe(filename):
    # config = load_config(filename)
    with open(filename) as f:
        config = yaml.safe_load(f)
    if 'prod_id' not in config:
        raise ValueError(f"No prod ID in config {filename}")
    config_valid(config)


def validate_lstchain(filename):
    read_configuration_file(filename)


def main():
    parser = argparse.ArgumentParser(description="Validate your lstmcpipe config")

    # Required arguments
    parser.add_argument(dest='lstmcpipe_config_filename',
                        type=Path,
                        help='Path to lstmcpipe config file',
                        )

    # optional
    parser.add_argument('--lstchain_config', '-lc',
                        action='store',
                        type=Path,
                        dest='lstchain_config_filename',
                        help='Path to the lstchain config file.',
                        default=None,
                        )

    args = parser.parse_args()

    validate_lstmcpipe(args.lstmcpipe_config_filename)
    if args.lstchain_config_filename is not None:
        validate_lstchain(args.lstchain_config_filename)


if __name__ == '__main__':
    main()
