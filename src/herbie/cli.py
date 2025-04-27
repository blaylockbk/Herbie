import argparse
import re
import sys
from datetime import datetime, timedelta

import pandas as pd

from herbie import FastHerbie, Herbie

# Set the display option to show all rows and columns
pd.set_option("display.max_rows", None)  # None means no truncation of rows
pd.set_option("display.max_columns", None)  # None means no truncation of columns
pd.set_option("display.width", None)  # To avoid line wrapping
pd.set_option("display.max_colwidth", None)  # To show the full content of each cell


def parse_range(arg):
    """Parses a range string like '2024-01-01T00:2024-01-01T06:3' or '0:12:3' into a list"""
    if ":" in arg:
        start, end, step = arg.split(":")
        try:  # Try parsing as datetime range
            start_dt = datetime.fromisoformat(start)
            end_dt = datetime.fromisoformat(end)
            step = timedelta(hours=int(step))
            return [
                start_dt + i * step for i in range(((end_dt - start_dt) // step) + 1)
            ]
        except ValueError:
            # Fallback to int range
            start, end, step = map(int, (start, end, step))
            return list(range(start, end + 1, step))
    return [arg]  # single item


def common_arguments(parser):
    """Arguments common across all subcommands."""
    parser.add_argument("-m", "--model", default="hrrr", help="Model name.")
    parser.add_argument(
        "-d",
        "--date",
        nargs="+",
        required=True,
        help="One or more dates (model initialization date).",
    )
    parser.add_argument(
        "-f",
        "--fxx",
        nargs="+",
        default=["0"],
        help="Forecast lead time, in hours.",
    )
    parser.add_argument("-p", "--priority", nargs="+", help="Model source priority.")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output from Herbie.",
    )
    return parser


def resolve_dates_and_fxx(args):
    dates = []
    for d in args.date:
        dates.extend(parse_range(d))
    fxxs = []
    for f in args.fxx:
        fxxs.extend(parse_range(f))
    return dates, fxxs


def cmd_data(args):
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
            )
            print(H.grib)


def cmd_index(args):
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
            )
            print(H.idx)


def cmd_inventory(args):
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
            )
            print(H.inventory(args.subset).to_string(index=False))


def cmd_download(args):
    """Execute `download` subcommand; downloads requested."""
    dates, fxxs = resolve_dates_and_fxx(args)
    for d in dates:
        for f in fxxs:
            H = Herbie(
                date=d,
                model=args.model,
                fxx=int(f),
                priority=args.priority,
                verbose=args.verbose,
            )
            H.download(args.subset, verbose=args.verbose)


def cmd_plot(args):
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
            )
            hp = HerbiePlot(H)
            hp.plot(search_string=args.subset)


def main():
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
    for name, func in [
        ("data", cmd_data),
        ("index", cmd_index),
        ("inventory", cmd_inventory),
        ("download", cmd_download),
        ("plot", cmd_plot),
    ]:
        sub = common_arguments(subparsers.add_parser(name, help=f"{name} command"))
        if name in ("download", "plot", "inventory"):
            sub.add_argument(
                "--subset",
                help="Search string for subsetting GRIB fields.",
            )
        sub.set_defaults(func=func)

    args = parser.parse_args()

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

    args.func(args)


if __name__ == "__main__":
    main()
