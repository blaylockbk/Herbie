"""
HerbieModel — abstract base class for all Herbie v2 model objects.

Design principles
-----------------
- **Lazy** — no network I/O at construction time.  Sources are resolved
  (and cached) the first time ``inventory()``, ``download()``, or
  ``xarray()`` is called.  ``status()`` is the explicit "go check
  everything" method.

- **Source abstraction** — subclasses return a ``dict[str, Source]``
  from ``_build_sources()``.  The base class handles all the mechanics
  of checking existence, downloading, and caching without knowing the
  specifics of each model.

- **Priority** — by default sources are tried in the order given by
  ``_build_sources()``.  Users override with the ``priority`` argument.

Subclass contract
-----------------
A model subclass must define:

    MODEL_NAME         str
    MODEL_DESCRIPTION  str
    PARAMS             dict  (same shape as experimental ModelTemplate)
    _build_sources()   → dict[str, Source]

Optionally:

    SOURCE_TYPE        str   default 'grib2'; also 'zarr', 'directory'
    MODEL_WEBSITES     dict  reference URLs shown in __rich__ / status()
"""

from __future__ import annotations

import functools
import hashlib
import re
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from typing import ClassVar
from urllib.parse import urlparse

import polars as pl
import requests
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from herbie.v2._config import CONFIG
from herbie.v2._sources import (
    DirectorySource,
    EccodesGribSource,
    GribSource,
    Source,
    ZarrSource,
)

console = Console()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_date(value) -> datetime:
    import pandas as pd

    return pd.to_datetime(value).to_pydatetime().replace(tzinfo=None)


def _parse_fxx(value) -> int:
    if isinstance(value, str):
        import pandas as pd

        return int(pd.to_timedelta(value).total_seconds() / 3600)
    return int(value)


def _url_exists(url: str, timeout: int = 5) -> bool:
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True)
        return r.status_code == 200
    except requests.RequestException:
        return False


def _url_info(url: str, timeout: int = 5) -> dict:
    """Return {'exists': bool, 'size': int | None}."""
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True)
        if r.status_code == 200:
            size = r.headers.get("Content-Length")
            return {"exists": True, "size": int(size) if size else None}
    except requests.RequestException:
        pass
    return {"exists": False, "size": None}


def _fmt_size(n: int | None) -> str:
    if n is None:
        return "[dim]-[/dim]"
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------


class HerbieModel(ABC):
    """Abstract base class for all Herbie v2 model objects."""

    # --- Subclasses define these ---
    MODEL_NAME: ClassVar[str] = ""
    MODEL_DESCRIPTION: ClassVar[str] = ""
    MODEL_WEBSITES: ClassVar[dict[str, str]] = {}
    PARAMS: ClassVar[dict] = {}
    SOURCE_TYPE: ClassVar[str] = "grib2"  # 'grib2', 'zarr', 'directory'

    def __init__(
        self,
        date: str | datetime,
        fxx: int | str = 0,
        *,
        product: str | None = None,
        priority: list[str] | None = None,
        save_dir: Path | str | None = None,
        overwrite: bool = False,
        verbose: bool = True,
        **kwargs,
    ):
        # ── Parse inputs (no network I/O) ──────────────────────────────────
        self.date = _parse_date(date)
        self.fxx = _parse_fxx(fxx)
        self.valid_date = self.date + timedelta(hours=self.fxx)
        self.priority = priority
        self.save_dir = Path(save_dir or CONFIG["save_dir"]).expanduser()
        self.overwrite = overwrite
        self.verbose = verbose

        # Resolve and validate model-specific parameters
        # product is a convenience alias; merge with **kwargs
        if product is not None:
            kwargs["product"] = product
        self.params = self._resolve_params(kwargs)

        # Build source map (string construction only — fast, no network)
        self._sources: dict[str, Source] = self._build_sources()

    # ── Abstract interface ─────────────────────────────────────────────────

    @abstractmethod
    def _build_sources(self) -> dict[str, Source]:
        """
        Return an ordered dict of ``{source_name: Source}``.
        Dict insertion order defines the default search priority.
        """
        ...

    # ── Parameter handling ─────────────────────────────────────────────────

    def _resolve_params(self, kwargs: dict) -> dict:
        """
        Merge PARAMS defaults with user-supplied kwargs, apply aliases,
        and validate all values.

        ``kwargs`` may include any key defined in ``PARAMS`` plus any
        extra model-specific kwargs (they are stored as-is).
        """
        resolved: dict = {}

        # Apply defaults first, then override with caller-supplied values
        for name, cfg in self.PARAMS.items():
            value = kwargs.get(name, cfg.get("default"))
            if value is None:
                continue
            # Resolve aliases
            value = cfg.get("aliases", {}).get(value, value)
            resolved[name] = value

        # Pass through extra kwargs not declared in PARAMS
        for key, value in kwargs.items():
            if key not in self.PARAMS:
                resolved[key] = value

        # Validate declared params
        for name, cfg in self.PARAMS.items():
            value = resolved.get(name)
            if value is None:
                continue
            valid = cfg.get("valid")
            if valid is not None and value not in valid:
                aliases = list(cfg.get("aliases", {}).keys())
                raise ValueError(
                    f"Invalid {name}={value!r} for {self.MODEL_NAME}. "
                    f"Must be one of {list(valid)}"
                    + (f" or aliases {aliases}" if aliases else "")
                )

        return resolved

    # ── Source ordering ────────────────────────────────────────────────────

    def _ordered_sources(self) -> dict[str, Source]:
        """Return sources in priority order (user-supplied or model default)."""
        if self.priority is None:
            return self._sources
        return {k: self._sources[k] for k in self.priority if k in self._sources}

    # ── Local path helpers ─────────────────────────────────────────────────

    @property
    def local_path(self) -> Path:
        """
        Predicted local path for the full GRIB2 file.

        Mirrors the URL path structure so that ``rclone sync`` of the
        remote bucket produces the same directory layout as Herbie.
        """
        first: Source = next(iter(self._sources.values()))
        if isinstance(first, (GribSource, EccodesGribSource)):
            relative = Path(urlparse(first.url).path.lstrip("/"))
            return self.save_dir / relative
        elif isinstance(first, ZarrSource):
            relative = Path(urlparse(first.url).path.lstrip("/"))
            return self.save_dir / relative
        else:
            # DirectorySource: use URL hostname + path
            relative = Path(urlparse(first.url).path.lstrip("/"))
            return self.save_dir / relative

    def _subset_path(self, search: str | pl.Expr | None) -> Path:
        """
        Local path for a subset file.  Appends ``__subset-<hash>`` to
        the full-file name so subsets are sortable alongside the original.
        """
        if search is None:
            return self.local_path
        h = hashlib.blake2b(str(search).encode(), digest_size=4).hexdigest()
        name = f"{self.local_path.name}__subset-{h}"
        return self.local_path.parent / name

    # ── Lazy source resolution (cached) ───────────────────────────────────

    @functools.cached_property
    def _found_grib(self) -> tuple[str | None, str | None]:
        """
        Lazily find the first available GRIB2 source.

        Checks local first, then iterates remote sources in priority
        order.  Result is cached so subsequent calls are free.

        Returns
        -------
        (source_name, url_or_path) or (None, None)
        """
        # Local file takes priority
        if self.local_path.exists() and not self.overwrite:
            return ("local", str(self.local_path))

        for name, src in self._ordered_sources().items():
            if isinstance(src, (GribSource, EccodesGribSource)):
                if _url_exists(src.url):
                    return (name, src.url)
        return (None, None)

    @functools.cached_property
    def _found_index(self) -> tuple[str | None, str | None]:
        """
        Lazily find the first available index file.

        Search order:
        1. Local index file next to a previously downloaded GRIB file.
        2. Remote index files at each source URL + suffix.
        3. Generate an index locally with ``wgrib2 -s`` if wgrib2 is
           installed and the full GRIB file exists locally.

        Returns
        -------
        (source_name, url_or_path) or (None, None)
        """
        from herbie.v2._inventory import generate_index_file

        # ── 1. Local index file ────────────────────────────────────────────
        local = self.local_path
        first_src = next(iter(self._sources.values()), None)
        suffixes = (
            first_src.index_suffixes
            if isinstance(first_src, (GribSource, EccodesGribSource))
            else [".idx"]
        )

        if local.exists():
            for suffix in suffixes:
                for candidate in [
                    local.parent / (local.name + suffix),
                    local.with_suffix(suffix),
                ]:
                    if candidate.exists():
                        return ("local", str(candidate))

        # ── 2. Remote index ────────────────────────────────────────────────
        for name, src in self._ordered_sources().items():
            if not isinstance(src, (GribSource, EccodesGribSource)):
                continue
            for suffix in src.index_suffixes:
                idx_url = src.url + suffix
                if _url_exists(idx_url):
                    return (name, idx_url)

        # ── 3. wgrib2 local generation fallback ────────────────────────────
        if local.exists():
            idx_path = generate_index_file(local)
            if idx_path is not None:
                if self.verbose:
                    console.print(
                        f"[dim]Generated index with wgrib2 → {idx_path.name}[/dim]"
                    )
                return ("generated", str(idx_path))

        return (None, None)

    def _invalidate_cache(self) -> None:
        """
        Clear cached source-resolution results.

        Call this after a download completes so that ``_found_grib`` and
        ``_found_index`` re-evaluate and pick up the newly local file.
        Also clears ``_index_df`` so inventory re-reads from the new file.
        """
        for attr in ("_found_grib", "_found_index", "_index_df"):
            self.__dict__.pop(attr, None)

    # ── Convenience properties ─────────────────────────────────────────────

    @property
    def grib_source(self) -> str | None:
        """Name of the source where the GRIB file was found, or None."""
        return self._found_grib[0] if "_found_grib" in self.__dict__ else None

    @property
    def grib(self) -> str | None:
        """URL or local path of the GRIB file, or None."""
        return self._found_grib[1] if "_found_grib" in self.__dict__ else None

    @property
    def idx_source(self) -> str | None:
        """Name of the source where the index file was found, or None."""
        return self._found_index[0] if "_found_index" in self.__dict__ else None

    @property
    def idx(self) -> str | None:
        """URL or local path of the index file, or None."""
        return self._found_index[1] if "_found_index" in self.__dict__ else None

    # ── Index as DataFrame (cached) ────────────────────────────────────────

    @functools.cached_property
    def _index_df(self) -> pl.DataFrame:
        """Read and cache the full inventory DataFrame."""
        from herbie.v2._inventory import read_index

        # DirectorySource: build inventory from directory listing
        if self.SOURCE_TYPE == "directory":
            frames = []
            for name, src in self._ordered_sources().items():
                if not isinstance(src, DirectorySource):
                    continue
                df = read_index(
                    src.url,
                    style="directory",
                    source_url=src.url,
                    directory_pattern=src.file_pattern,
                    parse_metadata=src.parse_metadata,
                )
                if not df.is_empty():
                    frames.append(df)
            if not frames:
                return pl.DataFrame()
            return pl.concat(frames, how="diagonal")

        # GRIB2 source: find index file then parse it
        idx_src, idx_url = self._found_index
        if idx_url is None:
            raise ValueError(
                f"No index file found for {self!r}.\n"
                "Try H.download() to fetch the full file first, then rebuild the object."
            )

        # Determine index style from the source descriptor
        style = "wgrib2"
        for src in self._sources.values():
            if isinstance(src, (GribSource, EccodesGribSource)):
                style = src.index_style
                break

        # The GRIB data URL may differ from the source the index came from
        _, grib_url = self._found_grib
        grib_url = grib_url or ""

        return read_index(idx_url, style, source_url=grib_url)

    # ── Public API ─────────────────────────────────────────────────────────

    def inventory(
        self,
        search: str | pl.Expr | list[pl.Expr] | None = None,
    ) -> pl.DataFrame:
        """
        Return the GRIB2 file inventory as a Polars DataFrame.

        Parameters
        ----------
        search
            Filter to apply.

            ``str``
                Regex applied to a colon-joined concatenation of the
                variable/level/forecast columns (classic Herbie search
                string).  Examples::

                    "TMP:2 m above ground"
                    ":500 mb:"
                    ":[UV]GRD:10 m"

            ``pl.Expr`` or ``list[pl.Expr]``
                Applied directly to the DataFrame, enabling column-level
                filtering::

                    pl.col("variable") == "TMP"
                    [pl.col("level").str.contains("mb"),
                     pl.col("variable").is_in(["TMP", "RH"])]

            ``None``
                Return the full unfiltered inventory.
        """
        df = self._index_df

        if search is None:
            return df

        if isinstance(search, str):
            # Build a searchable string from all non-byte columns
            search_cols = [
                c
                for c in df.columns
                if c
                not in {
                    "grib_message",
                    "start_byte",
                    "end_byte",
                    "source",
                    "reference_time",
                }
            ]
            cast_exprs = []
            for c in search_cols:
                dtype = df.schema[c]
                if dtype in (pl.Duration, pl.Datetime, pl.Date, pl.Time):
                    cast_exprs.append(pl.col(c).dt.to_string())
                else:
                    cast_exprs.append(pl.col(c).cast(pl.String))

            result = df.filter(
                pl.concat_str(cast_exprs, separator=":").str.contains(search)
            )

            if result.is_empty() and self.verbose:
                from herbie.v2._search_help import print_search_help

                # Determine style
                style = "wgrib2"
                for src in self._sources.values():
                    if isinstance(src, EccodesGribSource):
                        style = "eccodes"
                        break
                    if isinstance(src, DirectorySource):
                        style = "directory"
                        break
                console.print(
                    f"[yellow]⚠ No GRIB messages matched search={search!r}[/yellow]"
                )
                print_search_help(style)

            return result

        if isinstance(search, pl.Expr):
            return df.filter(search)

        if isinstance(search, list):
            expr = functools.reduce(lambda a, b: a & b, search)
            return df.filter(expr)

        return df

    def download(
        self,
        search: str | pl.Expr | list[pl.Expr] | None = None,
        *,
        source: str | None = None,
        max_workers: int = 5,
        overwrite: bool | None = None,
        verbose: bool | None = None,
    ) -> Path:
        """
        Download the GRIB2 file (full or subset).

        Parameters
        ----------
        search
            Same as ``inventory(search)``.  If not None, downloads only
            the matching GRIB messages (byte-range subset download).
        source
            Force a specific source name (e.g. ``'aws'``).  Overrides
            the normal priority ordering.
        max_workers
            Maximum parallel download threads (subset downloads only).
        overwrite
            Override the instance-level ``overwrite`` setting.
        verbose
            Override the instance-level ``verbose`` setting.

        Returns
        -------
        pathlib.Path
            Local path of the downloaded file.
        """
        from herbie.v2._download import download_file, download_groups
        from herbie.v2._inventory import create_download_groups

        ov = self.overwrite if overwrite is None else overwrite
        vb = self.verbose if verbose is None else verbose

        dest = self._subset_path(search)

        if dest.exists() and not ov:
            if vb:
                console.print(f"[dim]Already exists → {dest}[/dim]")
            return dest

        # Determine which URL to download from
        if source is not None:
            src = self._sources.get(source)
            if src is None:
                raise ValueError(
                    f"Source {source!r} not found. Available: {list(self._sources)}"
                )
            grib_url = (
                src.url if isinstance(src, (GribSource, EccodesGribSource)) else None
            )
        else:
            _, grib_url = self._found_grib
            source = self._found_grib[0]

        if grib_url is None:
            raise ValueError(
                f"No GRIB2 file found for {self!r}. The data may not be available yet."
            )

        dest.parent.mkdir(parents=True, exist_ok=True)

        # Full-file download
        if search is None:
            if vb:
                console.print(
                    f"[bold]Downloading[/bold] {self.MODEL_NAME} "
                    f"from [{source}] → [yellow]{dest.name}[/yellow]"
                )
            result = download_file(grib_url, dest, verbose=vb)
            # Invalidate cached source resolution so _found_grib and
            # _found_index re-evaluate against the newly local file.
            self._invalidate_cache()
            return result

        # Subset download
        idx_df = self.inventory(search)
        if idx_df.is_empty():
            raise ValueError(
                f"No GRIB messages matched search={search!r}. "
                "Use H.inventory() to see available fields."
            )

        # Override the source URL in the inventory so the downloader
        # fetches from the right place
        idx_df = idx_df.with_columns(pl.lit(grib_url).alias("source"))
        groups = create_download_groups(idx_df)

        if vb:
            console.print(
                f"[bold]Downloading subset[/bold] ({len(idx_df)} messages, "
                f"{len(groups)} groups) from [{source}] → [yellow]{dest.name}[/yellow]"
            )

        return download_groups(groups, dest, max_workers=max_workers, verbose=vb)

    def xarray(
        self,
        search: str | pl.Expr | list[pl.Expr] | None = None,
        *,
        backend_kwargs: dict | None = None,
        remove_grib: bool = True,
        overwrite: bool = False,
        **download_kwargs,
    ):
        """
        Open data as an ``xarray.Dataset``.

        Downloads the file (or subset) if not already present locally,
        then opens it with cfgrib.

        Parameters
        ----------
        search
            Same as ``inventory(search)``.
        backend_kwargs
            Forwarded to ``cfgrib.open_datasets``.
        remove_grib
            If True, delete the temporary subset file after loading into
            memory.  Ignored for full files (they are never removed).
        overwrite
            Re-download even if the file already exists locally.
        """
        if self.SOURCE_TYPE == "zarr":
            from herbie.v2._xarray import open_zarr

            _, src = self._found_grib
            return open_zarr(src)

        from herbie.v2._xarray import load_xarray

        local = self._subset_path(search)

        # Don't remove if the file already existed before we started
        pre_existing = local.exists()
        if pre_existing and remove_grib:
            remove_grib = False  # never remove a pre-existing full file

        # Full files are never removed
        if search is None and remove_grib:
            remove_grib = False

        if not local.exists() or overwrite:
            self.download(search, overwrite=overwrite, **download_kwargs)

        ds = load_xarray(local, backend_kwargs=backend_kwargs)

        if remove_grib:
            if isinstance(ds, list):
                ds = [d.load() for d in ds]
                for d in ds:
                    d.close()
            else:
                ds = ds.load()
                ds.close()
            local.unlink()

        return ds

    def status(self) -> None:
        """
        Check and display the availability of all sources and local files.

        This is the *only* method that performs parallel HEAD requests to
        all sources simultaneously.  Other methods (inventory, download,
        xarray) are lazy and check sources one at a time.
        """
        # Check all remote sources in parallel
        remote_urls: dict[str, str] = {}
        for name, src in self._sources.items():
            if isinstance(src, (GribSource, EccodesGribSource)):
                remote_urls[name] = src.url

        results: dict[str, dict] = {}
        with ThreadPoolExecutor(max_workers=min(8, len(remote_urls))) as pool:
            futures = {
                pool.submit(_url_info, url): name for name, url in remote_urls.items()
            }
            for future in as_completed(futures):
                results[futures[future]] = future.result()

        # Check local files
        local_files: list[tuple[Path, str]] = []
        base = self.local_path
        if base.exists():
            local_files.append((base, "full"))
        # Subsets (same parent dir, matching name pattern)
        if base.parent.exists():
            for p in sorted(base.parent.glob(f"{base.name}__subset-*")):
                local_files.append((p, "subset"))

        # ── Rich display ───────────────────────────────────────────────────
        # Header
        logo = Text()
        logo.append("▌", style="bold red on white")
        logo.append("▌", style="bold blue on #f0ead2")
        logo.append("Herbie", style="bold black on #f0ead2")
        logo.append(f" {self.MODEL_NAME}", style="bold cyan")
        logo.append(f" — {self.MODEL_DESCRIPTION}", style="dim italic")

        # Remote sources table
        src_table = Table(box=box.SIMPLE_HEAD, title="[bold]Remote Sources[/bold]")
        src_table.add_column("Source", style="bold cyan")
        src_table.add_column("Exists", justify="center")
        src_table.add_column("Size", justify="right")
        src_table.add_column("URL", style="dim", overflow="fold", max_width=60)

        for name in self._sources:
            if name not in results:
                continue
            info = results[name]
            exists_str = "[green]✓[/green]" if info["exists"] else "[red]✗[/red]"
            size_str = _fmt_size(info["size"])
            src_table.add_row(name, exists_str, size_str, remote_urls[name])

        # Local files table
        loc_table = Table(
            box=box.SIMPLE_HEAD,
            title=f"[bold]Local Files[/bold]  [dim]{base.parent}[/dim]",
        )
        loc_table.add_column("File", style="yellow")
        loc_table.add_column("Type")
        loc_table.add_column("Size", justify="right")

        if local_files:
            for path, kind in local_files:
                size = _fmt_size(path.stat().st_size)
                kind_str = (
                    "[bold green]full[/bold green]"
                    if kind == "full"
                    else "[dim]subset[/dim]"
                )
                loc_table.add_row(path.name, kind_str, size)
        else:
            loc_table.add_row("[dim]no local files[/dim]", "", "")

        # Info row
        info_grid = Table.grid(padding=(0, 2))
        info_grid.add_column()
        info_grid.add_column()
        info_grid.add_row(
            f"[bold]Initialized:[/bold] [green]{self.date:%Y-%b-%d %H:%M UTC}[/green]"
            f"  [bold]F{self.fxx:02d}[/bold]",
            f"[bold]Valid:[/bold] [green]{self.valid_date:%Y-%b-%d %H:%M UTC}[/green]",
        )
        param_str = "  ".join(f"{k}=[cyan]{v}[/cyan]" for k, v in self.params.items())
        info_grid.add_row(param_str, "")

        from rich.columns import Columns

        panel = Panel(
            Columns([info_grid, src_table, loc_table], equal=False, expand=True),
            title=logo,
            border_style="cyan",
            box=box.ROUNDED,
        )
        console.print(panel)

    # ── Display ───────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        params = ", ".join(f"{k}={v!r}" for k, v in self.params.items())
        src = (
            f", source={self.__dict__['_found_grib'][0]!r}"
            if "_found_grib" in self.__dict__
            else ""
        )
        return (
            f"{self.MODEL_NAME}({self.date:%Y-%m-%d %H:%M UTC}, "
            f"F{self.fxx:02d}, {params}{src})"
        )

    def __bool__(self) -> bool:
        """True if a GRIB2 file (local or remote) has been found."""
        return self._found_grib[0] is not None

    def __rich__(self) -> Panel:
        logo = Text()
        logo.append("▌", style="bold red on white")
        logo.append("▌", style="bold blue on #f0ead2")
        logo.append("Herbie", style="bold black on #f0ead2")
        logo.append(f" {self.MODEL_DESCRIPTION}", style="dim italic")

        grid = Table.grid(padding=(0, 2))
        grid.add_column()

        row1 = Text()
        row1.append(self.MODEL_NAME, style="bold cyan")
        row1.append(" • initialized ", style="dim")
        row1.append(f"{self.date:%Y-%b-%d %H:%M UTC}", style="green")
        row1.append(f"  F{self.fxx:02d}", style="bold bright_green")
        grid.add_row(row1)

        row2 = Text()
        row2.append(self.local_path.name, style="italic yellow")
        row2.append("  •  ", style="dim")
        if "_found_grib" in self.__dict__ and self._found_grib[0]:
            row2.append(f"source={self._found_grib[0]}", style="italic #ff9900")
        else:
            row2.append("(source not yet resolved)", style="dim")
        grid.add_row(row2)

        return Panel(
            grid,
            title=logo,
            title_align="left",
            border_style="cyan",
            box=box.ROUNDED,
            padding=(0, 1),
        )

    def _repr_html_(self) -> str:
        params_html = "".join(
            f"<tr><td><b>{k}</b></td><td><code>{v}</code></td></tr>"
            for k, v in self.params.items()
        )
        src_name, src_url = (
            self._found_grib if "_found_grib" in self.__dict__ else (None, None)
        )
        src_html = (
            f'<a href="{src_url}" target="_blank">{src_url}</a>'
            if src_url
            else "<i>not yet resolved</i>"
        )

        return f"""
        <div style="font-family: sans-serif; border: 1px solid #ddd; border-radius: 4px;
                    padding: 12px; max-width: 800px;">
          <div style="display: flex; align-items: center; margin-bottom: 8px;">
            <span style="background:white; border:1px solid #ccc; padding:2px 5px;
                         border-radius:4px; font-weight:bold; margin-right:10px;">
              <span style="color:red;">▌</span><span style="color:blue;
              background:#f0ead2;">▌</span><span style="background:#f0ead2;">Herbie</span>
            </span>
            <b style="font-size:1.1em;">{self.MODEL_NAME}</b>
            <span style="font-size:.9em; color:#666; margin-left:8px;">{self.MODEL_DESCRIPTION}</span>
          </div>
          <p style="margin:4px 0">
            <b>Initialized:</b> {self.date:%Y-%b-%d %H:%M UTC} &nbsp;
            <b>F{self.fxx:02d}</b> &nbsp;
            <b>Valid:</b> {self.valid_date:%Y-%b-%d %H:%M UTC}
          </p>
          <details style="margin-top:8px">
            <summary style="cursor:pointer;font-weight:bold">Parameters</summary>
            <table style="border-collapse:collapse;margin-top:4px">{params_html}</table>
          </details>
          <details style="margin-top:4px">
            <summary style="cursor:pointer;font-weight:bold">Source</summary>
            <p style="margin:4px 0"><b>Name:</b> {src_name or "not yet resolved"}</p>
            <p style="margin:4px 0"><b>URL:</b> {src_html}</p>
            <p style="margin:4px 0"><b>Local:</b> <code>{self.local_path}</code></p>
          </details>
        </div>"""
