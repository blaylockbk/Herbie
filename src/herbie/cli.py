"""
Herbie Command Line Interface (CLI).

TODO:
- [ ] parse unknown_args so they can be used in the Herbie class for models that have extra arguments
"""

import argparse
import re
import sys
import warnings
from datetime import datetime, timedelta

import pandas as pd

from herbie import FastHerbie, Herbie

# Set the display option to show all rows and columns
pd.set_option("display.max_rows", None)  # None means no truncation of rows
pd.set_option("display.max_columns", None)  # None means no truncation of columns
pd.set_option("display.width", None)  # To avoid line wrapping
pd.set_option("display.max_colwidth", None)  # To show the full content of each cell


def common_arguments(parser):
    """Arguments common across all subcommands."""
    parser.add_argument(
        "-d",
        "--date",
        nargs="+",
        required=True,
        help="Model initialization date in form YYYYMMDDHH, YYYY-MM-DD, or YYYY-MM-DDTHH:MM.",
    )
    parser.add_argument(
        "-m",
        "--model",
        default="hrrr",
        help="Model name.",
    )
    parser.add_argument(
        "--product",
        help="Model product type.",
    )
    parser.add_argument(
        "-f",
        "--fxx",
        nargs="+",
        type=int,
        default=[0],
        help="Forecast lead time, in hours.",
    )
    parser.add_argument(
        "-p",
        "--priority",
        nargs="+",
        help="Model source priority.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output from Herbie.",
    )
    return parser


def resolve_dates_and_fxx(args):
    # Just return the dates and fxx as they are directly from the input arguments
    return args.date, args.fxx


def cmd_data(args, **kwargs):
    """Execute `data` subcommand; gets URL to requested GRIB2 file."""
    dates, fxxs = resolve_dates_and_fxx(args)
    H_class = FastHerbie if len(dates) > 1 else Herbie
    for d in dates:
        for f in fxxs:
            H = H_class(
                date=d,
                model=args.model,
                fxx=int(f),
                priority=args.priority,
                verbose=args.verbose,
                **kwargs,
            )
            print(H.grib)


def cmd_sources(args, **kwargs):
    """Execute `sources` subcommand; gets URL to requested GRIB2 file."""
    import json

    dates, fxxs = resolve_dates_and_fxx(args)
    H_class = FastHerbie if len(dates) > 1 else Herbie
    for d in dates:
        for f in fxxs:
            H = H_class(
                date=d,
                model=args.model,
                fxx=int(f),
                priority=args.priority,
                verbose=args.verbose,
                **kwargs,
            )
            print(json.dumps(H.SOURCES, indent=2))


def cmd_index(args, **kwargs):
    """Execute `index` subcommand; gets URL to requested GRIB2 index file."""
    dates, fxxs = resolve_dates_and_fxx(args)
    for d in dates:
        for f in fxxs:
            H = Herbie(
                date=d,
                model=args.model,
                fxx=int(f),
                priority=args.priority,
                verbose=args.verbose,
                **kwargs,
            )
            print(H.idx)


def cmd_inventory(args, **kwargs):
    """Execute `inventory` subcommand; prints inventory from index file."""
    dates, fxxs = resolve_dates_and_fxx(args)
    for d in dates:
        for f in fxxs:
            H = Herbie(
                date=d,
                model=args.model,
                fxx=int(f),
                priority=args.priority,
                verbose=args.verbose,
                **kwargs,
            )
            print(H.inventory(args.subset).to_string(index=False))


def cmd_download(args, **kwargs):
    """Execute `download` subcommand; downloads requested files."""
    dates, fxxs = resolve_dates_and_fxx(args)
    for d in dates:
        for f in fxxs:
            H = Herbie(
                date=d,
                model=args.model,
                fxx=int(f),
                priority=args.priority,
                verbose=args.verbose,
                **kwargs,
            )
            H.download(args.subset, verbose=args.verbose)


def cmd_plot(args, **kwargs):
    """Execute `plot` subcommand; plots requested data."""
    raise NotImplementedError(
        "The Herbie plotting CLI is not implemented. "
        "I would love your help building this if you have some ideas. "
        "Please submit a pull request."
    )
    from herbie.plot import HerbiePlot

    dates, fxxs = resolve_dates_and_fxx(args)
    for d in dates:
        for f in fxxs:
            H = Herbie(
                date=d,
                model=args.model,
                fxx=int(f),
                priority=args.priority,
                verbose=args.verbose,
                **kwargs,
            )
            hp = HerbiePlot(H)
            hp.plot(search_string=args.subset)


def main():
    """Herbie command line interface (CLI)."""
    parser = argparse.ArgumentParser(
        prog="herbie", description="Herbie CLI for accessing GRIB2 files."
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Show Herbie version.",
    )
    parser.add_argument(
        "--show_versions",
        action="store_true",
        help="Show versions of Herbie and its dependencies.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # Subcommands
    subcommands = [
        ("data", cmd_data, "Show GRIB2 file URL for a given date and lead time."),
        ("index", cmd_index, "Show GRIB2 index file URL for a given date."),
        ("inventory", cmd_inventory, "Show inventory of GRIB2 fields or subset."),
        ("download", cmd_download, "Download GRIB2 file or subset."),
        ("sources", cmd_sources, "Return json of possible GRIB2 sources URLs."),
        ("plot", cmd_plot, "Quick plot of GRIB2 field (Not implemented)."),
    ]

    for name, func, help_text in subcommands:
        subparser = subparsers.add_parser(name, help=help_text, description=help_text)
        common_arguments(subparser)
        if name in ("download", "plot", "inventory"):
            subparser.add_argument(
                "--subset", help="Search string for subsetting GRIB fields."
            )
        subparser.set_defaults(func=func)

    args, unknown_args = parser.parse_known_args()

    # \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    # Handle Extra Arguments
    # (prone to errors if user doesn't know what they are doing)

    # Turn unknown_args list into a dict
    unknown_args_dict = {}
    key = None
    for item in unknown_args:
        if item.startswith("--"):
            key = item[2:]
            unknown_args_dict[key] = None
        else:
            if key is not None:
                unknown_args_dict[key] = item
                key = None  # reset key

    if len(unknown_args_dict):
        print(
            "\nWARNING: You have extra arguments..."
            f"{unknown_args_dict}"
            "...Hope you know what you are doing.\n"
        )
    # \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\

    if args.version:
        import importlib.metadata

        print(importlib.metadata.version("herbie-data"))
        sys.exit(0)

    if args.show_versions:
        from herbie.show_versions import (
            show_versions,  # <-- you might put the function here
        )

        show_versions()
        sys.exit(0)

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    args.func(args, **unknown_args_dict)


if __name__ == "__main__":
    main()
