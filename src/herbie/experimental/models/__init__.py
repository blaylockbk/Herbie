from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from typing import ClassVar
from urllib.parse import urlparse

import requests
from rich.console import Console
from rich.table import Table


class ModelTemplate(ABC):
    """Base class for model templates.

    Subclasses can define PARAMS to specify allowed parameters, their defaults, and aliases.

    Example:
        PARAMS = {
            "product": {
                "default": "prs",
                "aliases": {"native": "nat", "pressure": "prs"},
                "valid": ["sfc", "prs", "nat"],
                "descriptions": {  # optional
                    "sfc": "2D surface level fields",
                    "prs": "3D pressure level fields",
                    "nat": "Native level fields"
                }
            },
            "step": {
                "default": 0,
                "valid": range(0, 49)
            }
        }
    """

    MODEL_NAME: ClassVar[str] = "UNKNOWN"
    MODEL_DESCRIPTION: ClassVar[str] = "UNKNOWN"
    MODEL_WEBSITES: ClassVar[dict[str, str]] = {}

    PARAMS: ClassVar[dict[str, dict]] = {}
    INDEX_SUFFIX: ClassVar[list[str]] = [".idx"]

    def __init__(self, date: datetime, save_dir: Path | None = None, **kwargs):
        if date is None:
            raise ValueError("`date` is required for ModelTemplate initialization")

        self.date = date
        self.save_dir = save_dir

        # Normalize parameters after date is set (templates may use self.date)
        self.params = self._normalize_params(kwargs)

        # Compute valid_date from step (if provided)
        step = self.params.get("step", 0)
        self.valid_date = self.date + timedelta(hours=step)

        self._validate_params()

    def __repr__(self) -> str:
        """Display string representation."""
        params_str = ", ".join(f"{k}={v}" for k, v in self.params.items())
        return (
            f"{self.__class__.__name__}(date={self.date:%Y-%m-%d %H:%M}, {params_str})"
        )

    def _normalize_params(self, kwargs: dict) -> dict:
        """Normalize parameters by applying defaults and resolving aliases.

        Args:
            kwargs: User-provided parameter values

        Returns
        -------
            Normalized parameters dict
        """
        normalized = {}

        # Process each defined parameter
        for param_name, param_config in self.PARAMS.items():
            # Get the value from kwargs
            value = kwargs.get(param_name)

            if value is None:
                # Use default if provided
                if "default" in param_config:
                    value = param_config["default"]
            else:
                # Resolve aliases if provided
                aliases = param_config.get("aliases", {})
                if value in aliases:
                    value = aliases[value]

            if value is not None:
                normalized[param_name] = value

        # Add any extra kwargs that aren't in PARAMS (for flexibility)
        for key, value in kwargs.items():
            if key not in self.PARAMS:
                normalized[key] = value

        return normalized

    def __rich__(self):
        """Rich representation for pretty printing."""
        from rich import box
        from rich.columns import Columns
        from rich.panel import Panel

        # Header info
        header = f"[bold cyan]{self.MODEL_NAME}[/bold cyan] - {self.MODEL_DESCRIPTION}"

        # Current configuration
        config_table = Table(title="Configuration", box=box.ROUNDED, show_header=False)
        config_table.add_column("Parameter", style="bold")
        config_table.add_column("Value")

        config_table.add_row("date", f"{self.date:%Y-%m-%d %H:%M}")
        for key, value in self.params.items():
            config_table.add_row(key, str(value))

        # Valid parameters table (from PARAMS definitions)
        if self.PARAMS:
            params_table = Table(title="Available Parameters", box=box.ROUNDED)
            params_table.add_column("Parameter", style="bold cyan")
            params_table.add_column("Default")
            params_table.add_column("Valid value (alias)")
            params_table.add_column("Description")

            for param_name, param_config in self.PARAMS.items():
                default = param_config.get("default", "-")

                # Build valid values/aliases info
                valid_list = param_config.get("valid")
                aliases = param_config.get("aliases", {})
                descriptions = param_config.get("descriptions", {})

                if valid_list is not None:
                    if isinstance(valid_list, range):
                        valid_str = f"range({valid_list.start}, {valid_list.stop})"
                        info_str = valid_str
                    else:
                        # Build list with descriptions if available
                        current_value = self.params.get(param_name)
                        value_lines = []
                        # Reverse alias mapping: value -> [aliases]
                        alias_map: dict = {}
                        for alias, mapped in aliases.items():
                            alias_map.setdefault(mapped, []).append(alias)

                        for v in valid_list:
                            # Mark the currently selected value
                            if v == current_value:
                                value_marker = "*"
                                style = "[bold yellow]"
                                end_style = "[/bold yellow]"
                            else:
                                value_marker = ""
                                style = ""
                                end_style = ""

                            # Build alias display if any
                            aliases_for_v = alias_map.get(v, [])
                            if aliases_for_v:
                                alias_part = (
                                    " "
                                    + "[dim]("
                                    + ", ".join(str(a) for a in aliases_for_v)
                                    + ")[/dim]"
                                )
                            else:
                                alias_part = ""

                            # Build value line (description shown in separate column)
                            line = f"{style}{v}{value_marker}{alias_part}{end_style}"

                            value_lines.append(line)

                        valid_str = "\n".join(value_lines)

                        # Build parallel description lines for each valid value
                        desc_lines = []
                        for v in valid_list:
                            if descriptions and v in descriptions:
                                desc_lines.append(descriptions[v])
                            else:
                                desc_lines.append("[dim]-[/dim]")

                        desc_str = "\n".join(desc_lines)
                        info_str = valid_str
                else:
                    info_str = "[dim]-[/dim]"

                # If range, show description as dim placeholder
                if isinstance(valid_list, range):
                    desc_str = "[dim]-[/dim]"

                params_table.add_row(
                    param_name,
                    str(default),
                    valid_str if valid_list is not None else "[dim]-[/dim]",
                    desc_str,
                )
                # Spacer row for readability
                params_table.add_row("", "", "", "")
        else:
            params_table = None

        # Data sources availability table
        remote_urls = self.get_remote_urls()
        sources_table = Table(title="Data Sources", box=box.ROUNDED)
        sources_table.add_column("Source", style="bold cyan")
        sources_table.add_column("Exists", justify="center")
        sources_table.add_column("Size", justify="right")
        sources_table.add_column("URL/Path", style="dim", overflow="fold")
        sources_table.add_column("Index", justify="center")

        # Check local file first
        try:
            local_path = self.get_local_path()
            # Use full path if save_dir is provided
            if self.save_dir:
                full_local_path = self.save_dir / local_path
            else:
                full_local_path = local_path

            if full_local_path.exists():
                local_size = full_local_path.stat().st_size
                if local_size < 1024:
                    size_str = f"{local_size} B"
                elif local_size < 1024 * 1024:
                    size_str = f"{local_size / 1024:.1f} KB"
                elif local_size < 1024 * 1024 * 1024:
                    size_str = f"{local_size / (1024 * 1024):.1f} MB"
                else:
                    size_str = f"{local_size / (1024 * 1024 * 1024):.2f} GB"
                # Check for local index files and pick the first matching suffix
                local_index_suffix = None
                for suffix in self.INDEX_SUFFIX:
                    if Path(str(full_local_path) + suffix).exists():
                        local_index_suffix = suffix
                        break

                index_display = (
                    f"[bold green]{local_index_suffix}[/bold green]"
                    if local_index_suffix
                    else "[dim]-[/dim]"
                )

                sources_table.add_row(
                    "[bold green]local[/bold green]",
                    "[bold green]True[/bold green]",
                    size_str,
                    str(full_local_path),
                    index_display,
                )
            else:
                # Local file missing — still check whether local index exists (unlikely)
                local_index_suffix = None
                for suffix in self.INDEX_SUFFIX:
                    if Path(str(full_local_path) + suffix).exists():
                        local_index_suffix = suffix
                        break

                index_display = (
                    f"[bold green]{local_index_suffix}[/bold green]"
                    if local_index_suffix
                    else "[dim]-[/dim]"
                )

                sources_table.add_row(
                    "[bold green]local[/bold green]",
                    "[red]False[/red]",
                    "[dim]-[/dim]",
                    str(full_local_path),
                    index_display,
                )
        except Exception:
            pass

        # Check availability and get file sizes for remote sources
        source_info = self._check_all_urls_with_size(timeout=3)

        for source, url in remote_urls.items():
            info = source_info.get(source, {})
            exists = info.get("exists", False)
            size = info.get("size")

            # Remote existence
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

            # Check remote index existence by trying all index suffixes and capture the suffix
            found_suffix = None
            for suffix in self.INDEX_SUFFIX:
                try:
                    if self._check_url_exists(url + suffix, timeout=3):
                        found_suffix = suffix
                        break
                except Exception:
                    continue

            index_display = (
                f"[bold green]{found_suffix}[/bold green]"
                if found_suffix
                else "[dim]-[/dim]"
            )

            sources_table.add_row(source, status, size_str, url, index_display)

        # Websites
        if self.MODEL_WEBSITES:
            websites_table = Table(
                title="Web Resources", box=box.ROUNDED, show_header=False
            )
            websites_table.add_column("Source", style="bold yellow")
            websites_table.add_column("URL", style="dim", overflow="fold")

            for name, url in self.MODEL_WEBSITES.items():
                websites_table.add_row(name.upper(), url)
        else:
            websites_table = None

        # Combine tables
        tables = [config_table, sources_table]
        if params_table:
            tables.append(params_table)
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

        Returns
        -------
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
        """Validate parameters against their config."""
        for param_name, param_config in self.PARAMS.items():
            value = self.params.get(param_name)

            # Check if parameter is valid (if it exists)
            if value is not None:
                valid_list = param_config.get("valid")
                if valid_list is not None:
                    if isinstance(valid_list, range):
                        if not (value in valid_list):
                            raise ValueError(
                                f"Invalid {param_name} '{value}'. Must be in range({valid_list.start}, {valid_list.stop})"
                            )
                    else:
                        if value not in valid_list:
                            raise ValueError(
                                f"Invalid {param_name} '{value}'. Must be one of {valid_list}"
                            )

    def _check_url_exists(self, url: str, timeout: int = 5) -> bool:
        """Check if a URL exists using HEAD request.

        Args:
            url: URL to check
            timeout: Request timeout in seconds

        Returns
        -------
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

        Returns
        -------
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

        Returns
        -------
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

        Returns
        -------
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

    def get_local_path(self, source: str | None = None) -> Path:
        """Get the local path for a GRIB2 file.

        Parameters
        ----------
        source
            Specific source to get filename from. If None, use first source.
        """
        remote_urls = self.get_remote_urls()

        if source is None:
            source = next(iter(remote_urls.keys()))

        if source not in remote_urls:
            available = ", ".join(remote_urls.keys())
            raise ValueError(
                f"Source '{source}' not found. Available sources: {available}"
            )

        url = remote_urls[source]
        return Path(urlparse(url).path.lstrip("/"))
