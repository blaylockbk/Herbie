#!/usr/bin/env python3
"""
Herbie Command Line Interface (CLI).

A tool for accessing archived Numerical Weather Prediction (NWP) model data.
"""

import argparse
import re
import sys
import warnings
from datetime import datetime, timedelta
from pathlib import Path

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
        help="""Model initialization date. Accepts multiple formats:
- YYYYMMDDHH (e.g., 2023031500)
- YYYY-MM-DD (e.g., 2023-03-15, assumes 00Z)
- YYYY-MM-DDTHH:MM (e.g., 2023-03-15T12:00)
- "YYYY-MM-DD HH:MM" (e.g., "2023-03-15 12:00")
Can provide multiple dates for batch processing.""",
    )
    parser.add_argument(
        "-m",
        "--model",
        default="hrrr",
        help="""Model name. Default: hrrr
Common options:
- hrrr (High-Resolution Rapid Refresh)
- gfs (Global Forecast System)
- ifs (ECMWF Integrated Forecast System)""",
    )
    parser.add_argument(
        "--product",
        help="""Model product type.
If not specified, Herbie will use the default product for the model.""",
    )
    parser.add_argument(
        "-f",
        "--fxx",
        nargs="+",
        type=int,
        default=[0],
        help="""Forecast lead time(s) in hours. Default: 0
Can provide multiple forecast hours for batch processing.
Example: -f 0 1 3 6 12 (Available forecast hours vary by model.)""",
    )
    parser.add_argument(
        "-p",
        "--priority",
        nargs="+",
        help="""Data source priority order. Controls order archives are searched.
Default depends on model but typically: [aws, google, nomads, azure, ncep]
Example: Only search for data on Google `-p google`""",
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
                save_dir=args.save_dir,
                overwrite=args.overwrite,
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


class CustomHelpFormatter(argparse.HelpFormatter):
    """Custom formatter that preserves both description and argument help text formatting."""

    def _fill_text(self, text, width, indent):
        """Preserve text formatting for description and epilog."""
        return "".join([indent + line for line in text.splitlines(True)])

    def _split_lines(self, text, width):
        """Preserve line breaks in argument help text."""
        return text.splitlines()


def main():
    """Herbie command line interface (CLI) for accessing NWP model data."""
    parser = argparse.ArgumentParser(
        prog="herbie",
        description="Herbie CLI for accessing NWP model GRIB2 files from various data sources.",
        formatter_class=CustomHelpFormatter,
        epilog="""
Examples:
  # Get the URL for a HRRR surface file from today at 12Z
  herbie data -m hrrr --product sfc -d "2023-03-15 12:00" -f 0

  # Download GFS 0.25° forecast hour 24 temperature at 850mb
  herbie download -m gfs --product 0p25 -d 2023-03-15T00:00 -f 24 --subset ":TMP:850 mb:"

  # View all available variables in a RAP model run
  herbie inventory -m rap -d 2023031512 -f 0

  # Download multiple forecast hours for a date range
  herbie download -m hrrr -d 2023-03-15T00:00 2023-03-15T06:00 -f 1 3 6 --subset ":UGRD:10 m:"

  # Specify custom source priority (check only Google)
  herbie data -m hrrr -d 2023-03-15 -f 0 -p google

  # Advanced: Pass additional arguments to the Herbie class
  herbie download -m hrrr -d 2023-03-15 -f 0 --subset ":TMP:2 m:" --save_dir ./my_data
        """,
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Show Herbie version number.",
    )
    parser.add_argument(
        "--show_versions",
        action="store_true",
        help="Show versions of Herbie and its dependencies.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # Subcommands
    subcommands = [
        (
            "data",
            cmd_data,
            """Find and show a GRIB2 file URL.

This command displays the URL where the specified GRIB2 file is located,
without downloading it. Useful for verifying file availability or
for using the URL in other applications.""",
        ),
        (
            "index",
            cmd_index,
            """Find and show a GRIB2 index file URL.

Returns the URL to the .idx file associated with the GRIB2 file.
Index files contain metadata about the variables in the GRIB2 file.""",
        ),
        (
            "inventory",
            cmd_inventory,
            """Show inventory of GRIB2 fields or subset.

Displays a table of all fields in the GRIB2 file.
Can be filtered using the --subset parameter with a search string.""",
        ),
        (
            "download",
            cmd_download,
            """Download GRIB2 file or subset.

Downloads the complete GRIB2 file or a subset of fields based on
a search string.""",
        ),
        (
            "sources",
            cmd_sources,
            """Return JSON of possible GRIB2 source URLs.

Shows all potential data sources for the requested model data,
formatted as JSON. Useful for debugging or understanding data availability.""",
        ),
        (
            "plot",
            cmd_plot,
            """Quick plot of GRIB2 field (Not implemented).

This feature is planned for future releases.""",
        ),
    ]

    for name, func, help_text in subcommands:
        subparser = subparsers.add_parser(
            name,
            help=help_text.split("\n")[0],
            description=help_text,
            formatter_class=CustomHelpFormatter,
        )
        common_arguments(subparser)
        if name in ("download", "plot", "inventory"):
            subparser.add_argument(
                "--subset",
                help="""Search string for subsetting GRIB fields.

Examples:
- ":TMP:2 m:"         Temperature at 2 meters
- ":(UGRD|VGRD):"     U and V wind components
- ":APCP:"            Accumulated precipitation
- ":500 mb:"          All variables at 500 mb level
- ":CAPE:"            Convective Available Potential Energy
- ":RH:[0-9]+ mb:"    Relative humidity at all pressure levels

Format is a regular expression that matches against the inventory line.
Use 'herbie inventory' command to see available fields.""",
            )
        if name in ("download"):
            subparser.add_argument(
                "-o",
                "--save_dir",
                type=Path,
                help="""Directory to save GRIB2 file.
Directory structure will be <model-name>/<YYYYMMDD>/<file-name>""",
            )
            subparser.add_argument(
                "--overwrite",
                action="store_true",
                help="Overwrite existing GRIB2 file if it exists.",
            )
        subparser.set_defaults(func=func)

    args, unknown_args = parser.parse_known_args()
    print(args)

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
            "\nNOTE: Additional arguments detected and will be passed to the Herbie class:"
            f"\n{unknown_args_dict}"
            "\nRefer to the Herbie documentation for valid parameters.\n"
        )

    if args.product:
        unknown_args_dict['product'] = args.product
    # \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\

    if args.version:
        import importlib.metadata

        print(importlib.metadata.version("herbie-data"))
        sys.exit(0)

    if args.show_versions:
        from herbie.show_versions import show_versions

        show_versions()
        sys.exit(0)

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    args.func(args, **unknown_args_dict)


if __name__ == "__main__":
    main()
