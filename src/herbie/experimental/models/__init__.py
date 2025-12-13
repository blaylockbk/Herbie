from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import ClassVar
from rich.console import Console
from rich.table import Table


class ModelTemplate(ABC):
    """Base class for model templates."""

    MODEL_NAME: ClassVar[str] = "UNKNOWN"
    MODEL_DESCRIPTION: ClassVar[str] = "UNKNOWN"
    MODEL_WEBSITES: ClassVar[dict[str, str]] = {}

    VALID_PRODUCTS: ClassVar[dict[str, str]] = {}
    DEFAULT_PRODUCT: str | None = None
    DEFAULT_STEP: int = 0
    INDEX_SUFFIX: ClassVar[str] = ".idx"

    def __init__(self, date: datetime, **kwargs):
        self.date = date
        self.params = kwargs
        self._validate_params()

    def __repr__(self) -> str:
        """Display string representation."""
        params_str = ", ".join(f"{k}={v}" for k, v in self.params.items())
        return (
            f"{self.__class__.__name__}(date={self.date:%Y-%m-%d %H:%M}, {params_str})"
        )

    def __rich__(self):
        """Rich representation for pretty printing."""
        from rich.panel import Panel
        from rich.columns import Columns
        from rich import box

        # Header info
        header = f"[bold cyan]{self.MODEL_NAME}[/bold cyan] - {self.MODEL_DESCRIPTION}"

        # Current configuration
        config_table = Table(title="Configuration", box=box.ROUNDED, show_header=False)
        config_table.add_column("Parameter", style="bold")
        config_table.add_column("Value")

        config_table.add_row("date", f"{self.date:%Y-%m-%d %H:%M}")
        for key, value in self.params.items():
            config_table.add_row(key, str(value))

        # Valid products table
        if self.VALID_PRODUCTS:
            products_table = Table(title="Valid Products", box=box.ROUNDED)
            products_table.add_column("Product", style="bold magenta")
            products_table.add_column("Description")

            for product, description in self.VALID_PRODUCTS.items():
                # Highlight the default product
                if product == self.DEFAULT_PRODUCT:
                    products_table.add_row(
                        f"{product} [green](default)[/green]", description
                    )
                else:
                    products_table.add_row(product, description)
        else:
            products_table = None

        # Websites
        if self.MODEL_WEBSITES:
            websites_table = Table(
                title="Web Resources", box=box.ROUNDED, show_header=False
            )
            websites_table.add_column("Source", style="bold yellow")
            websites_table.add_column("URL", style="underline")

            for name, url in self.MODEL_WEBSITES.items():
                websites_table.add_row(name.upper(), url)
        else:
            websites_table = None

        # Combine tables
        tables = [config_table]
        if products_table:
            tables.append(products_table)
        if websites_table:
            tables.append(websites_table)

        return Panel(
            Columns(tables, equal=False, expand=True),
            title=header,
            border_style="cyan",
            padding=(1, 2),
        )

    def display(self):
        """Print the rich representation to console."""
        console = Console()
        console.print(self)

    @abstractmethod
    def get_remote_urls(self) -> dict[str, str]:
        """Return dict of remote URLs."""
        pass

    def _validate_params(self) -> None:
        """Validate parameters."""
        pass


class HRRRTemplate(ModelTemplate):
    """HRRR Model Template."""

    MODEL_NAME = "HRRR"
    MODEL_DESCRIPTION = "High-Resolution Rapid Refresh - CONUS"
    MODEL_WEBSITES = {
        "gsl": "https://rapidrefresh.noaa.gov/hrrr/",
        "nomads": "https://www.nco.ncep.noaa.gov/pmb/products/hrrr/",
        "utah": "http://hrrr.chpc.utah.edu/",
    }
    VALID_PRODUCTS = {
        "sfc": "2D surface level fields; 3-km resolution",
        "prs": "3D pressure level fields; 3-km resolution",
        "nat": "Native level fields; 3-km resolution",
        "subh": "Subhourly grids; 3-km resolution",
    }
    DEFAULT_PRODUCT = "prs"
    INDEX_SUFFIX = ".idx"

    def _validate_params(self) -> None:
        """Validate parameters."""
        product = self.params.get("product", self.DEFAULT_PRODUCT)
        if product not in self.VALID_PRODUCTS.keys():
            raise ValueError(
                f"Invalid product '{product}'. Must be one of {self.VALID_PRODUCTS}"
            )

        step = self.params.get("step", self.DEFAULT_STEP)
        if not isinstance(step, int) or step < 0 or step > 48:
            raise ValueError(f"Invalid forecast hour '{step}'. Must be 0-48")

    def get_remote_urls(self) -> dict[str, str]:
        """Return all the URLs."""
        date = self.date
        step = self.params.get("step", self.DEFAULT_STEP)
        product = self.params.get("product", self.DEFAULT_PRODUCT)

        path = (
            f"hrrr.{date:%Y%m%d}/conus/hrrr.t{date:%H}z.wrf{product}f{step:02d}.grib2"
        )
        path2 = f"hrrr/{product}/{date:%Y%m%d}/hrrr.t{date:%H}z.wrf{product}f{step:02d}.grib2"

        # Note: Order defines default priority order
        return {
            "aws": f"https://noaa-hrrr-bdp-pds.s3.amazonaws.com/{path}",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod/{path}",
            "google": f"https://storage.googleapis.com/high-resolution-rapid-refresh/{path}",
            "azure": f"https://noaahrrr.blob.core.windows.net/hrrr/{path}",
            "pando": f"https://pando-rgw01.chpc.utah.edu/{path2}",
            "pando2": f"https://pando-rgw02.chpc.utah.edu/{path2}",
        }
