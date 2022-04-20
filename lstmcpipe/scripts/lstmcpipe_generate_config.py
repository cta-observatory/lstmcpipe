# #!/usr/bin/env python
import argparse
from pathlib import Path
from datetime import date

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
    cfg.save_yml(output)

    print(f"Config saved in {output}")


if __name__ == '__main__':
    main()
