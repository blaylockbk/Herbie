from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import ClassVar
from rich.console import Console
from rich.table import Table
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed


class ModelTemplate(ABC):
    """Base class for model templates."""

    MODEL_NAME: ClassVar[str] = "UNKNOWN"
    MODEL_DESCRIPTION: ClassVar[str] = "UNKNOWN"
    MODEL_WEBSITES: ClassVar[dict[str, str]] = {}

    VALID_PRODUCTS: ClassVar[dict[str, str]] = {}
    DEFAULT_PRODUCT: str | None = None
    DEFAULT_STEP: int = 0
    INDEX_SUFFIX: ClassVar[list[str]] = [".idx"]  # Changed to list

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

        # Remote sources availability table
        remote_urls = self.get_remote_urls()
        sources_table = Table(title="Remote Sources", box=box.ROUNDED)
        sources_table.add_column("Source", style="bold cyan")
        sources_table.add_column("Exists", justify="center")
        sources_table.add_column("Size", justify="right")
        sources_table.add_column("URL", style="dim", overflow="fold")

        # Check availability and get file sizes
        source_info = self._check_all_urls_with_size(timeout=3)

        for source, url in remote_urls.items():
            info = source_info.get(source, {})
            exists = info.get("exists", False)
            size = info.get("size")

            if exists:
                status = "[green]True[/green]"
                if size is not None:
                    # Format size nicely
                    if size < 1024:
                        size_str = f"{size} B"
                    elif size < 1024 * 1024:
                        size_str = f"{size / 1024:.1f} KB"
                    elif size < 1024 * 1024 * 1024:
                        size_str = f"{size / (1024 * 1024):.1f} MB"
                    else:
                        size_str = f"{size / (1024 * 1024 * 1024):.2f} GB"
                else:
                    size_str = "[dim]-[/dim]"
            else:
                status = "[red]False[/red]"
                size_str = "[dim]-[/dim]"

            sources_table.add_row(source, status, size_str, url)

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
        tables = [config_table, sources_table]
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

    def _check_all_urls_with_size(
        self, timeout: int = 5, max_workers: int = 5
    ) -> dict[str, dict]:
        """Check which remote URLs exist and get their file sizes.

        Args:
            timeout: Request timeout in seconds
            max_workers: Maximum number of concurrent requests

        Returns:
            Dictionary mapping source names to info dict with 'exists' and 'size' keys
        """
        remote_urls = self.get_remote_urls()
        results = {}

        def check_url_with_size(url: str) -> dict:
            """Check if URL exists and get size from Content-Length header."""
            try:
                response = requests.head(url, timeout=timeout, allow_redirects=True)
                if response.status_code == 200:
                    # Try to get file size from Content-Length header
                    size = response.headers.get("Content-Length")
                    return {"exists": True, "size": int(size) if size else None}
                else:
                    return {"exists": False, "size": None}
            except requests.RequestException:
                return {"exists": False, "size": None}

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all checks
            future_to_source = {
                executor.submit(check_url_with_size, url): source
                for source, url in remote_urls.items()
            }

            # Collect results as they complete
            for future in as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    results[source] = future.result()
                except Exception:
                    results[source] = {"exists": False, "size": None}

        return results

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

    def _check_url_exists(self, url: str, timeout: int = 5) -> bool:
        """Check if a URL exists using HEAD request.

        Args:
            url: URL to check
            timeout: Request timeout in seconds

        Returns:
            True if URL exists (status 200), False otherwise
        """
        try:
            response = requests.head(url, timeout=timeout, allow_redirects=True)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def check_all_urls(self, timeout: int = 5, max_workers: int = 5) -> dict[str, bool]:
        """Check which remote URLs exist.

        Args:
            timeout: Request timeout in seconds
            max_workers: Maximum number of concurrent requests

        Returns:
            Dictionary mapping source names to existence status
        """
        remote_urls = self.get_remote_urls()
        results = {}

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all checks
            future_to_source = {
                executor.submit(self._check_url_exists, url, timeout): source
                for source, url in remote_urls.items()
            }

            # Collect results as they complete
            for future in as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    results[source] = future.result()
                except Exception:
                    results[source] = False

        return results

    def find_first_existing_url(
        self, priority: list[str] | None = None, timeout: int = 5
    ) -> tuple[str, str] | None:
        """Find the first existing URL from the priority list.

        Args:
            priority: List of source names to check in order.
                     If None, uses dict order from get_remote_urls().
            timeout: Request timeout in seconds

        Returns:
            Tuple of (source_name, url) if found, None otherwise
        """
        remote_urls = self.get_remote_urls()

        # Determine which sources to check and in what order
        if priority is not None:
            # Filter to only requested sources that exist
            sources_to_check = [s for s in priority if s in remote_urls]
        else:
            # Use dict order (which is insertion order)
            sources_to_check = list(remote_urls.keys())

        # Check each source in order until we find one that exists
        for source in sources_to_check:
            url = remote_urls[source]
            if self._check_url_exists(url, timeout):
                return (source, url)

        return None

    def find_first_existing_index(
        self, priority: list[str] | None = None, timeout: int = 5
    ) -> tuple[str, str] | None:
        """Find the first existing index file from the priority list.

        For each source, tries all possible index suffixes in order
        until one is found.

        Args:
            priority: List of source names to check in order.
                     If None, uses dict order from get_remote_urls().
            timeout: Request timeout in seconds

        Returns:
            Tuple of (source_name, index_url) if found, None otherwise
        """
        remote_urls = self.get_remote_urls()

        # Determine which sources to check and in what order
        if priority is not None:
            # Filter to only requested sources that exist
            sources_to_check = [s for s in priority if s in remote_urls]
        else:
            # Use dict order (which is insertion order)
            sources_to_check = list(remote_urls.keys())

        # Check each source in order
        for source in sources_to_check:
            base_url = remote_urls[source]

            # Try each index suffix
            for suffix in self.INDEX_SUFFIX:
                index_url = base_url + suffix
                if self._check_url_exists(index_url, timeout):
                    return (source, index_url)

        return None


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
    INDEX_SUFFIX = [".idx", ".grib2.idx"]  # Try .idx first, then .grib2.idx

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
        """Return all the URLs.

        Note: Dict order defines default priority order.
        """
        date = self.date
        step = self.params.get("step", self.DEFAULT_STEP)
        product = self.params.get("product", self.DEFAULT_PRODUCT)

        path = (
            f"hrrr.{date:%Y%m%d}/conus/hrrr.t{date:%H}z.wrf{product}f{step:02d}.grib2"
        )
        path2 = f"hrrr/{product}/{date:%Y%m%d}/hrrr.t{date:%H}z.wrf{product}f{step:02d}.grib2"

        return {
            "aws": f"https://noaa-hrrr-bdp-pds.s3.amazonaws.com/{path}",
            "google": f"https://storage.googleapis.com/high-resolution-rapid-refresh/{path}",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod/{path}",
            "azure": f"https://noaahrrr.blob.core.windows.net/hrrr/{path}",
            "pando": f"https://pando-rgw01.chpc.utah.edu/{path2}",
            "pando2": f"https://pando-rgw02.chpc.utah.edu/{path2}",
        }
