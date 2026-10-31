"""
Search-string help for Herbie v2.

Printed when ``inventory(search=...)`` returns zero rows so users get
actionable guidance rather than a silent empty DataFrame.
"""

from __future__ import annotations

_WGRIB2_HELP = """\
[bold cyan]Search tips (wgrib2 index style)[/bold cyan]

The search string is a regular expression matched against a colon-joined
concatenation of the variable, level, and forecast-time columns.

[bold]Common patterns[/bold]
  "TMP"                    → all temperature fields
  "TMP:2 m above ground"   → 2-m temperature only
  ":500 mb:"               → all fields at 500 hPa
  ":[UV]GRD:10 m"          → u and v wind at 10 m above ground
  "UGRD|VGRD"              → u and v wind at any level
  ":surface:"              → all surface-level fields
  "APCP"                   → accumulated precipitation
  "HGT:500 mb"             → 500-hPa geopotential height

[bold]Polars expression alternative[/bold]
  import polars as pl
  H.inventory(pl.col("variable") == "TMP")
  H.inventory([pl.col("level").str.contains("mb"),
               pl.col("variable").is_in(["TMP", "RH"])])
"""

_ECCODES_HELP = """\
[bold cyan]Search tips (ecCodes index style — ECMWF)[/bold cyan]

The search string is matched against the ``param``, ``levtype``,
``levelist``, and ``type`` columns.

[bold]Common patterns[/bold]
  "t"              → temperature (all levels)
  "t:pl"           → temperature on pressure levels
  "u:pl:500"       → u-wind at 500 hPa
  ":sfc:"          → all surface fields
  "2t"             → 2-m temperature
  "tp"             → total precipitation

[bold]Polars expression alternative[/bold]
  import polars as pl
  H.inventory(pl.col("param") == "t")
  H.inventory([pl.col("param").is_in(["u", "v"]),
               pl.col("levelist") == "500"])
"""

_DIRECTORY_HELP = """\
[bold cyan]Search tips (directory listing style — Canadian MSC)[/bold cyan]

Each row in the inventory represents a separate GRIB2 file
containing one variable/level combination.  Filter by column:

[bold]Polars expression examples[/bold]
  import polars as pl
  H.inventory(pl.col("variable") == "TMP")
  H.inventory(pl.col("level") == "AGL-2m")
  H.inventory([pl.col("variable") == "UGRD",
               pl.col("level").str.contains("ISBL")])
"""


def search_help(style: str = "wgrib2") -> str:
    """Return the search-help string for the given index style."""
    mapping = {
        "wgrib2": _WGRIB2_HELP,
        "eccodes": _ECCODES_HELP,
        "directory": _DIRECTORY_HELP,
    }
    return mapping.get(style, _WGRIB2_HELP)


def print_search_help(style: str = "wgrib2") -> None:
    """Print search help using Rich markup."""
    from rich.console import Console
    from rich.panel import Panel

    console = Console()
    console.print(Panel(search_help(style), border_style="dim cyan"))
