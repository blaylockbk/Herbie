"""New Herbie Core."""

import functools
import importlib
import inspect
import pkgutil
from datetime import datetime, timedelta
from pathlib import Path
import hashlib

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
        Model name (default extracted from config, else 'hrrr')
    valid_date : str, datetime, optional
        Model valid date time. Only allowed if 'date' is None.
    save_dir : Path
        Directory to save downloaded files (default extracted from config, else '~/herbie-data')
    **kwargs
        Additional model-specific parameters (e.g., step, product, etc.)
    """

    def __init__(
        self,
        date: str | datetime | None = None,
        *,
        model: str | None = None,
        save_dir: Path | str | None = None,
        **kwargs,
    ):
        from .config import settings

        # Cascading configs: specific_model_config -> default_config -> kwargs
        # We need the model name first to know which specific config to load
        model_name = model or settings.get("default", {}).get("model", "hrrr")
        model_name = model_name.lower()

        # Merge configuration starting with default
        combined_kwargs = settings.get("default", {}).copy()
        # Merge model-specific configuration
        combined_kwargs.update(settings.get(model_name, {}))
        # Override with explicit keyword arguments from user
        combined_kwargs.update(kwargs)

        # Extract mapped save_dir
        if save_dir is not None:
            resolved_save_dir = Path(save_dir).expanduser()
        else:
            resolved_save_dir = Path(combined_kwargs.get("save_dir", "~/herbie-data")).expanduser()

        # Clean up combined_kwargs of non-template args
        combined_kwargs.pop("model", None)
        combined_kwargs.pop("save_dir", None)

        if isinstance(date, str):
            date = str_to_datetime(date)

        if date is None:
            raise ValueError("`date` is required; valid_date support was removed")

        # Explicitly assign self.save_dir so the object has it mapped properly.
        self.save_dir = resolved_save_dir

        model_template = get_template(model_name)

        # Only pass kwargs that this specific model template accepts via its PARAMS
        # Or kwargs that were explicitly passed in by the user (which override validation)
        template_kwargs = {}
        for k, v in combined_kwargs.items():
            if k in kwargs:
                # User explicitly passed this, so let it through
                template_kwargs[k] = v
            elif k in model_template.PARAMS:
                # It came from a config. Only keep it if the value is actually valid for THIS model.
                valid_opts = model_template.PARAMS[k].get("valid")
                aliases = model_template.PARAMS[k].get("aliases", {})
                if valid_opts is not None:
                    if isinstance(valid_opts, range):
                        if v in valid_opts or v in aliases:
                            template_kwargs[k] = v
                    else:
                        if v in valid_opts or v in aliases:
                            template_kwargs[k] = v
                else:
                    template_kwargs[k] = v

        self.template = model_template(date=date, save_dir=resolved_save_dir, **template_kwargs)

        self.date = self.template.date
        self.valid_date = self.template.valid_date
        self.step = self.template.params.get("step", 0)
        self.model_name = self.template.MODEL_NAME
        self.remote_urls = self.template.get_remote_urls()
        self.local_path = self.template.get_local_path()
        self.index_source, self.index = self.template.find_first_existing_index()
        self.data_source, self.data = self.template.find_first_existing_url()

    def __repr__(self) -> str:
        """Herbie simple string representation."""
        source = self.data_source if self.data_source else "(not found)"
        return (
            f"Herbie({self.model_name}, {self.date:%Y-%m-%d %H:%M UTC}, "
            f"F{self.step:02d}, source={source})"
        )

    def __bool__(self) -> bool:
        """Return True if a remote GRIB file exists."""
        return self.data is not None

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
        if self.data_source:
            row2.append(f"data@{self.data_source}", style="italic #ff9900")
        else:
            row2.append("data (not found)", style="italic red")
        row2.append("  •  ", style="dim")
        if self.index_source:
            row2.append(f"index@{self.index_source}", style="dim italic #ff9900")
        else:
            row2.append("index (not found)", style="dim italic red")

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

    def _repr_html_(self) -> str:
        """HTML representation for Jupyter Notebooks."""
        # Clean URLs for HTML display
        urls_html = "".join([f'<li><a href="{url}" target="_blank">{url}</a></li>' for url in self.remote_urls])

        # Configuration parameters
        params_html = "".join([f'<tr style="border-bottom: 1px solid var(--jp-border-color3, #eee);"><td style="padding: 4px;"><strong>{k}</strong></td><td style="padding: 4px;"><code>{v}</code></td></tr>' for k, v in self.template.params.items()])

        # Data/Index strings
        data_src = f'<a href="{self.data}" target="_blank">{self.data}</a>' if getattr(self, "data", None) else '<span style="color: red;">Not Found</span>'
        idx_src = f'<a href="{self.index}" target="_blank">{self.index}</a>' if getattr(self, "index", None) else '<span style="color: red;">Not Found</span>'

        # Determine config info
        config_html = ""
        try:
            from herbie.experimental.config import settings
            default_settings = settings.get("default", {})
            model_settings = settings.get(self.model_name, {})

            config_html += '<ul style="margin-top: 5px; padding-left: 20px;">'
            if default_settings:
                config_html += f'<li><strong>Default settings:</strong> <code>{default_settings}</code></li>'
            if model_settings:
                config_html += f'<li><strong>Model "{self.model_name}" settings:</strong> <code>{model_settings}</code></li>'
            config_html += '</ul>'
        except Exception as e:
            config_html = f'<i>Could not load settings: {e}</i>'

        # Valid date handling
        valid_date_str = f"{self.valid_date:%Y-%b-%d %H:%M UTC}" if getattr(self, "valid_date", None) else "N/A"
        date_str = f"{self.date:%Y-%b-%d %H:%M UTC}" if getattr(self, "date", None) else "N/A"
        step_str = f"F{self.step:02d}" if isinstance(self.step, int) else str(self.step)

        html = f"""
        <div style="font-family: var(--jp-ui-font-family, sans-serif); border: 1px solid var(--jp-border-color2, #ddd); border-radius: 4px; padding: 10px; max-width: 800px; background-color: var(--jp-layout-color1, #fff);">
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <div style="background-color: white; border: 1px solid #ccc; padding: 2px 5px; border-radius: 4px; display: inline-flex; overflow: hidden; font-weight: bold; margin-right: 10px;">
                    <span style="color: red; background: white; padding: 0 4px;">▌</span><span style="color: blue; background: #f0ead2; padding: 0 4px;">▌</span><span style="color: black; background: #f0ead2; padding: 0 4px;">Herbie</span>
                </div>
                <div style="font-size: 1.2em; font-weight: bold; color: var(--jp-content-font-color1, #333);">
                    {self.model_name.upper()} <span style="font-size: 0.8em; font-weight: normal; font-style: italic; color: var(--jp-content-font-color2, #777);">{self.template.MODEL_DESCRIPTION}</span>
                </div>
            </div>

            <div style="margin-left: 10px; font-size: 0.95em; color: var(--jp-content-font-color1, #333);">
                <p style="margin: 5px 0;"><strong>Initialized:</strong> {date_str} &nbsp;&nbsp; <strong>Forecast Hour:</strong> {step_str}</p>
                <p style="margin: 5px 0;"><strong>Valid Date:</strong> {valid_date_str}</p>

                <details style="margin-top: 10px; background: var(--jp-layout-color2, #f9f9f9); padding: 5px 10px; border-radius: 4px; border: 1px solid var(--jp-border-color2, #eee);">
                    <summary style="cursor: pointer; font-weight: bold;">File Information</summary>
                    <ul style="margin-top: 5px; padding-left: 20px;">
                        <li><strong>Local Path:</strong> <code>{self.local_path}</code></li>
                        <li><strong>Data Source:</strong> {data_src}</li>
                        <li><strong>Index Source:</strong> {idx_src}</li>
                    </ul>
                </details>

                <details style="margin-top: 5px; background: var(--jp-layout-color2, #f9f9f9); padding: 5px 10px; border-radius: 4px; border: 1px solid var(--jp-border-color2, #eee);">
                    <summary style="cursor: pointer; font-weight: bold;">Model Parameters</summary>
                    <table style="width: 100%; border-collapse: collapse; margin-top: 5px; font-size: 0.9em;">
                        <thead><tr style="border-bottom: 1px solid var(--jp-border-color2, #ccc);">
                            <th style="padding: 4px; text-align: left;">Parameter</th><th style="padding: 4px; text-align: left;">Value</th>
                        </tr></thead>
                        <tbody>
                            {params_html}
                        </tbody>
                    </table>
                </details>

                <details style="margin-top: 5px; background: var(--jp-layout-color2, #f9f9f9); padding: 5px 10px; border-radius: 4px; border: 1px solid var(--jp-border-color2, #eee);">
                    <summary style="cursor: pointer; font-weight: bold;">Configuration Defaults</summary>
                    {config_html}
                </details>

                <details style="margin-top: 5px; background: var(--jp-layout-color2, #f9f9f9); padding: 5px 10px; border-radius: 4px; border: 1px solid var(--jp-border-color2, #eee);">
                    <summary style="cursor: pointer; font-weight: bold;">Remote URLs constructed</summary>
                    <ol style="margin-top: 5px; padding-left: 25px; font-family: monospace; font-size: 0.9em; word-break: break-all;">
                        {urls_html}
                    </ol>
                </details>
            </div>
        </div>
        """
        return html

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
            search_cols = []
            for col_name, dtype in zip(df.columns[6:], df.dtypes[6:]):
                if dtype in (pl.Duration, pl.Datetime, pl.Date, pl.Time):
                    search_cols.append(pl.col(col_name).dt.to_string())
                else:
                    search_cols.append(pl.col(col_name).cast(pl.String))

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

    def get_download_hash(
        self, filters: str | pl.Expr | list[pl.Expr] | None = None
    ) -> str | None:
        """Return a short hash representing the subset indices.

        This hash is used to uniquely identify a downloaded subset file
        following the pattern: <original_name>__subset-<hash>
        """
        index_list = self.inventory(filters)["index"].sort().to_list()

        if not index_list:
            return None

        all_grib_msg = "-".join([f"{i:g}" for i in index_list])
        hash_label = hashlib.blake2b(all_grib_msg.encode(), digest_size=4).hexdigest()

        return hash_label

    def download(
        self,
        filters: pl.Expr | list[pl.Expr] | None = None,
        output_file: Path | None = None,
        max_workers: int = 5,
        overwrite: bool = False,
    ):
        """Download full or subset of GRIB2 files.

        Parameters
        ----------
        filters : pl.Expr | list[pl.Expr] | None
            Filter to apply to the inventory for subsetting.
        output_file : Path | None
            Output file path. If None, uses default local path.
        max_workers : int
            Maximum number of parallel download workers.
        overwrite : bool
            If False (default), skip download if file already exists locally.
            If True, always download and overwrite existing file.
        """
        if output_file is None:
            output_file = self.save_dir / self.local_path

        # If filters provided, append a short hash representing
        # the GRIB message indices to the original filename so
        # subset files are distinguishable but remain sortable.
        if filters is not None:
            hash_label = self.get_download_hash(filters)
            if hash_label is not None:
                new_name = f"{output_file.name}__subset-{hash_label}"
                output_file = output_file.parent / new_name
                logger.debug(
                    f"Subset file will be downloaded with name: [green]{output_file.name}[/green]"
                )

        if output_file.exists() and not overwrite:
            logger.debug(
                f"[yellow]File already exists[/yellow]: {output_file}. Skipping download."
            )
            return output_file

        if not output_file.parent.is_dir():
            output_file.parent.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: [green]{output_file.parent}[/green]")

        df = self.get_download_groups(filters)
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
        overwrite: bool = False,
    ):
        """Load data into xarray.

        Parameters
        ----------
        filters : str | pl.Expr | list[pl.Expr] | None
            Filter to apply to the inventory for subsetting.
        backend_kwargs : dict
            Backend keyword arguments for cfgrib.
        overwrite : bool
            If False (default), skip download if file already exists locally.
            If True, always download and overwrite existing file.
        """
        from .xarray_loader import load_grib2_into_xarray

        local_file = self.download(filters, overwrite=overwrite)

        return load_grib2_into_xarray(local_file, backend_kwargs=backend_kwargs)
