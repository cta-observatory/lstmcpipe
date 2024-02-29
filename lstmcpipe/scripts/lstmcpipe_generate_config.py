# #!/usr/bin/env python
import argparse
from pathlib import Path
from datetime import date

from lstmcpipe.config import paths_config
from lstmcpipe.utils import dump_lstchain_std_config


class ParseKwargs(argparse.Action):
    """
    Parse a string formatted as `option1=foo` into a dict `{option1: foo}`
    """

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, dict())
        for value in values:
            key, value = value.split("=")
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
        except:  # noqa
            pass
    return all_attrs


def build_argparser():
    parser = argparse.ArgumentParser(description="Generate a lstmcpipe config.")

    # Required arguments
    parser.add_argument(
        dest="config_class",
        type=str,
        help=f"Config class name to use. " f"List of implemented classes: {list_config_classes()}",
    )

    parser.add_argument("--prod_id", type=str, help="production ID")

    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Path to the output file to dump the generated lstmcpipe config. "
        "Optional, if not provided, the file is dumped locally",
        default=None,
    )

    parser.add_argument("--overwrite", action="store_true", help="Overwrite config file")

    parser.add_argument(
        "--lstchain_conf",
        type=Path,
        help="Path to the lstchain config to dump. " "Optional, if not provided, the file is dumped locally",
        default=None,
    )

    parser.add_argument(
        "--dec_list",
        nargs="+",
        help="Use only with AllSkyFull prods",
        default=None,
    )

    parser.add_argument(
        "--source_prod_id",
        type=str,
        help="Use only with prods starting from an existing source prod",
        default=None,
    )

    parser.add_argument(
        "--kwargs",
        nargs="*",
        action=ParseKwargs,
        help="optional kwargs for the requested config class. Use as: --kwargs option1=foo option2=bar",
    )

    return parser


def main():
    parser = build_argparser()
    args = parser.parse_args()

    if not hasattr(paths_config, args.config_class):
        raise NotImplementedError(f"Config class {args.config_class} not implemented in lstmcpipe.config.paths_config")

    output = f"lstmcpipe_config_{date.today()}_{args.config_class}.yaml" if args.output is None else args.output
    prod_id = "prod_00" if args.prod_id is None else args.prod_id

    kwargs = {}
    if args.dec_list:
        kwargs.update({"dec_list": args.dec_list})
    if args.source_prod_id:
        kwargs.update({"source_prod_id": args.source_prod_id})
    if args.kwargs:
        kwargs.update(args.kwargs)

    # we get the class from its name and instantiate it with the required args
    cfg = getattr(paths_config, args.config_class)(prod_id, **kwargs)
    cfg.generate()
    cfg.save_yml(output, overwrite=args.overwrite)

    print(f"lstmcpipe config saved in {output}")

    lstchain_file = f"lstchain_config_{date.today()}.json" if args.lstchain_conf is None else args.lstchain_conf

    if "AllSky" in args.config_class:
        allsky = True
    else:
        allsky = False
    dump_lstchain_std_config(filename=lstchain_file, allsky=allsky, overwrite=args.overwrite)
    print(f"To start the process with dumped configs, run:\n\nlstmcpipe -c {output} -conf_lst {lstchain_file}\n\n")


if __name__ == "__main__":
    main()
