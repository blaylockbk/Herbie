"""New Herbie Core."""

import functools
import importlib
import inspect
import pkgutil
from datetime import datetime, timedelta
from pathlib import Path

import polars as pl
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

import herbie.experimental.models as models

from ._common import DownloadGroupDataFrame, InventoryDataFrame, logger
from .download import download_grib2_from_dataframe
from .inventory import create_download_groups, read_index_file

# Discover available model templates without importing them
AVAILABLE_MODELS: dict[str, str] = {}
_TEMPLATE_CACHE: dict[str, type] = {}

# First, just discover what's available
for _, module_name, _ in pkgutil.iter_modules(models.__path__):
    if module_name.startswith("_"):
        continue

    # Store module path for lazy loading
    AVAILABLE_MODELS[module_name] = f"herbie.experimental.models.{module_name}"

logger.debug(
    f"Found {len(AVAILABLE_MODELS)} model templates: {AVAILABLE_MODELS.keys()}"
)


def get_template(model_name: str) -> type:
    """Get a model template, loading it lazily if needed."""
    model_name = model_name.lower()

    # Check cache first
    if model_name in _TEMPLATE_CACHE:
        logger.debug(f"Using cached template for [blue]{model_name}[/blue]")
        return _TEMPLATE_CACHE[model_name]

    # Check if model exists
    if model_name not in AVAILABLE_MODELS:
        raise ValueError(
            f"Model '{model_name}' not found. Available models: {AVAILABLE_MODELS.keys()}"
        )

    # Lazy load the template
    logger.debug(f"Loading template for [blue]{model_name}[/blue]")
    module = importlib.import_module(AVAILABLE_MODELS[model_name])

    # Find the Template class
    for name, obj in inspect.getmembers(module, inspect.isclass):
        if name.endswith("Template") and obj.__module__ == module.__name__:
            _TEMPLATE_CACHE[model_name] = obj
            logger.debug(
                f"Loaded template [green]{name}[/green] for [blue]{model_name}[/blue]"
            )
            return obj

    raise RuntimeError(f"No Template class found in {module_name}")


def str_to_datetime(value: str) -> datetime:
    """Convert a date/time string to a datetime object."""
    value = value.strip()
    for fmt in (
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y%m%d",
        "%Y%m%d%H%M",
    ):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass

    raise ValueError(f"Could not parse {value} to datetime.")


class Herbie:
    """New Herbie Class.

    Parameters
    ----------
    date : str, datetime, optional
        Model initialization date and time
    model : str
        Model name (default: "hrrr")
    valid_date : str, datetime, optional
        Model valid date time. Only allowed if 'date' is None.
    save_dir : Path
        Directory to save downloaded files
    **kwargs
        Additional model-specific parameters (e.g., step, product, etc.)
    """

    def __init__(
        self,
        date: str | datetime | None = None,
        *,
        model="hrrr",
        save_dir: Path = Path("~/herbie-data/").expanduser(),
        **kwargs,
    ):
        if isinstance(date, str):
            date = str_to_datetime(date)

        if date is None:
            raise ValueError("`date` is required; valid_date support was removed")

        model_template = get_template(model)
        self.template = model_template(date=date, save_dir=save_dir, **kwargs)

        self.date = self.template.date
        self.valid_date = self.template.valid_date
        self.step = self.template.params.get("step", 0)
        self.model_name = self.template.MODEL_NAME
        self.remote_urls = self.template.get_remote_urls()
        self.local_path = self.template.get_local_path()
        self.index_source, self.index = self.template.find_first_existing_index()
        self.data_source, self.data = self.template.find_first_existing_url()
        self.save_dir = save_dir

    def __repr__(self) -> str:
        """Herbie simple string representation."""
        return (
            f"Herbie({self.model_name}, {self.date:%Y-%m-%d %H:%M UTC}, "
            f"F{self.step:02d}, source={self.data_source})"
        )

    def __rich__(self) -> Panel:
        """Rich representation with panel layout."""
        # Create Herbie logo
        logo = Text()
        logo.append("▌", style="bold red on white")
        logo.append("▌", style="bold blue on #f0ead2")
        logo.append("Herbie", style="bold black on #f0ead2")
        logo.append(f" {self.template.MODEL_DESCRIPTION}", style="dim italic")

        # Create content table (no borders, just clean layout)
        content = Table.grid(padding=(0, 2))
        content.add_column(style="bold cyan", justify="right")
        content.add_column(style="white")

        # Row 1: Model and product info
        row1 = Text()
        row1.append(f"{self.model_name}", style="bold cyan")
        row1.append(" • ", style="dim")
        row1.append("initialized ", style="dim")
        row1.append(f"{self.date:%Y-%b-%d %H:%M UTC}", style="green")
        row1.append(f"  F{self.step:02d}", style="bright_green bold")

        # Row 2: Date, forecast hour, and source
        row2 = Text()
        row2.append(f"{self.local_path.name}", style="italic yellow")
        row2.append("  •  ", style="dim")
        row2.append(f"data@{self.data_source}", style="italic #ff9900")
        row2.append("  •  ", style="dim")
        row2.append(f"index@{self.index_source}", style="dim italic #ff9900")

        content.add_row("", row1)
        content.add_row("", row2)

        return Panel(
            content,
            title=logo,
            title_align="left",
            border_style="cyan",
            box=box.ROUNDED,
            padding=(0, 1),
        )

    def display(self):
        """Print the rich representation to console."""
        console = Console()
        console.print(self)

    @functools.cached_property
    def index_as_dataframe(self) -> InventoryDataFrame:
        """Read and cache an index file."""
        if self.index is None:
            raise ValueError(f"No index file found for {self.data}.")

        return read_index_file(str(self.index)).insert_column(
            1, pl.lit(str(self.data)).alias("grib_source")
        )

    def inventory(
        self, filters: str | pl.Expr | list[pl.Expr] | None = None
    ) -> InventoryDataFrame:
        """Return the inventory of the GRIB2 file.

        Parameters
        ----------
        filters
            Filter to apply to the inventory.

            If **string**, filters messages by searching a colon-separated
            concatenation of all DataFrame columns (from column 6 onward).
            The string is treated as a regex pattern. This is the classic
            filtering behavior.

            For example
                - `'TMP:.*mb'` - Temperature fields at all pressure levels
                - `'TMP'` - All temperature fields
                - `'[U|V]GRD:10 m above ground'` - u and v wind components at 10 m above ground

            If **polars expression** or **list of expressions**, applies the
            expression(s) directly to filter the DataFrame.

            For example
                - `pl.col("variable").str.contains('TMP')`
                - `pl.col("level") == "500 mb"`

            If **None**, returns the full unfiltered inventory.

        """
        df = self.index_as_dataframe

        if filters is None:
            return df

        if isinstance(filters, str):
            # Concatenate relevant columns for string searching
            search_cols = [pl.col(i).cast(pl.String) for i in df.columns[6:]]
            df = df.filter(
                pl.concat_str(search_cols, separator=":").str.contains(filters)
            )
        else:
            df = df.filter(filters)

        logger.debug(f"Filtered DataFrame to {len(df):,} fields.")
        return df

    def get_download_groups(
        self, filters: str | pl.Expr | list[pl.Expr] | None = None
    ) -> DownloadGroupDataFrame:
        """Show the download groups."""
        return self.inventory(filters).pipe(create_download_groups)

    def download(
        self,
        filters: pl.Expr | list[pl.Expr] | None = None,
        output_file: Path | None = None,
        max_workers: int = 5,
    ):
        """Download full or subset of GRIB2 files."""
        df = self.get_download_groups(filters)

        if output_file is None:
            output_file = self.save_dir / self.local_path

        if not output_file.parent.is_dir():
            output_file.parent.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: [green]{output_file.parent}[/green]")

        return download_grib2_from_dataframe(
            df,
            output_file=output_file,
            max_workers=max_workers,
        )

    def xarray(
        self,
        filters: str | pl.Expr | list[pl.Expr] | None = None,
        *,
        backend_kwargs: dict = {},
    ):
        """Load data into xarray."""
        from .xarray_loader import load_grib2_into_xarray

        local_file = self.download(filters)

        return load_grib2_into_xarray(local_file, backend_kwargs=backend_kwargs)
