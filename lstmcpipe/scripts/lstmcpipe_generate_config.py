# #!/usr/bin/env python
import argparse
from pathlib import Path
from datetime import date
import warnings

from lstmcpipe.config import paths_config


class ParseKwargs(argparse.Action):
    """
    Parse a string formatted as `option1=foo` into a dict `{option1: foo}`
    """

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, dict())
        for value in values:
            key, value = value.split('=')
            getattr(namespace, self.dest)[key] = value


def list_config_classes():
    """
    List the classes in `lstmcpipe.config.paths_config` that inherit from `lstmcpipe.config.paths_config.PathConfig`

    Returns
    -------
    [object]: list of classes
    """
    all_attrs = []
    for att in list(paths_config.__dict__):
        try:
            cls_base = getattr(paths_config, att).__mro__
            if paths_config.PathConfig in cls_base:
                all_attrs.append(att)
        except:
            pass
    return all_attrs


def dump_lstchain_std_config(filename='lstchain_config.json', overwrite=False):
    try:
        from lstchain.io.config import get_standard_config
    except ImportError:
        warnings.warn("Could not load get_standard_config from lstchain.io.config - standard config won't be generated")
        return None
    import json

    if Path(filename).exists() and not overwrite:
        raise FileExistsError(f"{filename} exists already")

    cfg = get_standard_config()
    cfg['LocalPeakWindowSum']['apply_integration_correction'] = True
    cfg['source_config']['EventSource']['allowed_tels'] = [1]
    with open(filename, 'w') as file:
        json.dump(cfg, file)
    print(f"Modified lstchain config dumped in {filename}")
    return filename


def main():
    parser = argparse.ArgumentParser(description="Generate a lstmcpipe config.")

    # Required arguments
    parser.add_argument(dest='config_class',
                        type=str,
                        help=f'Config class name to use. '
                             f'List of implemented classes: {list_config_classes()}'
                        )

    parser.add_argument('--prod_id',
                        type=str,
                        help='production ID'
                        )

    parser.add_argument('--output', '-o',
                        type=Path,
                        help='Path to the output file to dump the generated config. '
                             'Optional, if not provided, the file is dumped locally',
                        default=None
                        )

    parser.add_argument('--lstchain_conf',
                        type=Path,
                        help='Path to the lstchain config file',
                        default=Path('lstchain_conf.json')
                        )

    parser.add_argument('--overwrite',
                        action='store_true',
                        help='Overwrite lstmcpipe and lstchain configs',
                        )

    parser.add_argument('--kwargs',
                        nargs='*',
                        action=ParseKwargs,
                        help="optional kwargs for the requested config class. Use as: --kwargs option1=foo option2=bar"
                        )

    args = parser.parse_args()

    if not hasattr(paths_config, args.config_class):
        raise NotImplementedError(f"Config class {args.config_class} not implemented in lstmcpipe.config.paths_config")

    output = f'lstmcpipe_config_{date.today()}_{args.config_class}.yaml' if args.output is None else args.output
    prod_id = 'prod_00' if args.prod_id is None else args.prod_id

    # we get the class from its name and instantiate it with the required args
    if args.kwargs:
        cfg = getattr(paths_config, args.config_class)(prod_id, **args.kwargs)
    else:
        cfg = getattr(paths_config, args.config_class)(prod_id)
    cfg.generate()
    cfg.save_yml(output, overwrite=args.overwrite)

    print(f"lstmcpipe config saved in {output}")

    lstchain_file = args.lstchain_conf
    lstchain_file = dump_lstchain_std_config(filename=lstchain_file)
    print(f"To start the process with dumped configs, run:\n\nlstmcpipe -c {output} -conf_lst {lstchain_file}\n\n")


if __name__ == '__main__':
    main()
