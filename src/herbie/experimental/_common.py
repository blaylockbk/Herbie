"""Common utilities for experimental modules: console and logger setup."""

import logging
from typing import Literal, TypeAlias

import polars as pl
from rich.console import Console
from rich.logging import RichHandler

console = Console()
rich_handler = RichHandler(
    console=console,
    rich_tracebacks=True,
    show_level=True,
    show_time=True,
    markup=True,
)
logging.basicConfig(
    level=logging.INFO,
    handlers=[rich_handler],
    datefmt="[%H:%M:%S]",
    format="%(message)s",
)
logger = logging.getLogger(__name__)

# For now, lets just DEBUG
logger.setLevel(logging.DEBUG)

IndexStyle = Literal["wgrib2", "eccodes"]
"""
GRIB2 index files may be created either using `wgrib2` or `eccodes` software,
each output different formats to express details of each GRIB2 message in
a file.
"""


InventoryDataFrame: TypeAlias = pl.DataFrame
"""
Polars DataFrame representing a GRIB2 inventory with columns:
- url: str
- index: int
- start_byte: int
- end_byte: int
- reference_time: datetime
- (other columns)
"""

DownloadGroupDataFrame: TypeAlias = pl.DataFrame
"""
Polars DataFrame of an InventoryDataFrame that is grouped by
download groups.
"""
