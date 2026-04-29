"""
HerbieModel — abstract base class for all Herbie v2 model objects.

Design principles
-----------------
- **Lazy** — no network I/O at construction time.  Sources are resolved
  (and cached) the first time ``inventory()``, ``download()``, or
  ``xarray()`` is called.  ``resolve()`` is the explicit "go check
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
    ZarrCatalogEntry,
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
        self.SOURCES: dict[str, Source] = self._build_sources()
        if self.priority:
            # Filter to only the requested sources, in priority order
            self.SOURCES = {
                k: self.SOURCES[k] for k in self.priority if k in self.SOURCES
            }

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
        """Return sources in priority order (user-supplied or model default).

        SOURCES is already reordered at construction time, so this is a
        simple passthrough kept for internal consistency.
        """
        return self.SOURCES

    # ── Local path helpers ─────────────────────────────────────────────────

    # ── Zarr catalog interface ─────────────────────────────────────────────

    ZARR_SOURCES: ClassVar[dict] = {}
    """
    Model-level Zarr catalog.  Override in subclasses as::

        ZARR_SOURCES = {
            ("dynamical", "forecast"): ZarrCatalogEntry(...),
            ("dynamical", "analysis"): ZarrCatalogEntry(...),
        }

    Keys are ``(source, product)`` tuples.  ``source`` identifies the
    provider (e.g. ``'dynamical'``); ``product`` selects a specific dataset
    from that provider (e.g. ``'analysis'``, ``'forecast'``).
    """

    @classmethod
    def from_zarr(
        cls,
        source: str,
        product: str = "forecast",
        **open_kwargs,
    ) -> "xr.Dataset":
        """
        Open a cloud Zarr dataset directly, without date/fxx construction.

        Unlike the normal ``HRRR(date, fxx)`` constructor, this classmethod
        returns the full multi-date (or variable-scoped) Dataset in one call.
        Slice to a specific time/variable with ``.sel()`` afterwards.

        Parameters
        ----------
        source
            Provider name (e.g. ``'dynamical'``, ``'utah'``).
            See ``HRRR.list_zarr_sources()`` for all available options.
        product
            Dataset name within the provider (e.g. ``'forecast'``,
            ``'analysis'``).  Defaults to ``'forecast'`` where it exists.
        **open_kwargs
            Passed through to ``xr.open_zarr`` *or* to ``store_factory``
            for sources that need extra arguments (e.g. ``date=``,
            ``variable=``, ``level=`` for the Utah hrrrzarr store).

        Returns
        -------
        xr.Dataset

        Examples
        --------
        >>> ds = HRRR.from_zarr('dynamical', 'forecast')
        >>> ds['temperature_2m'].sel(
        ...     init_time='2025-01-01T00',
        ...     lead_time='6h',
        ... ).plot()

        >>> ds = HRRR.from_zarr('dynamical', 'analysis')
        >>> ds['temperature_2m'].sel(time='2025-01-01T06').plot()

        >>> ds = HRRR.from_zarr(
        ...     'utah', 'analysis',
        ...     date='2021-01-01 00:00', variable='TMP', level='surface',
        ... )
        """
        import xarray as xr

        catalog: dict = cls.ZARR_SOURCES
        entry = catalog.get((source, product))
        if entry is None:
            available = sorted(catalog.keys())
            raise ValueError(
                f"{cls.__name__}.from_zarr: no entry for "
                f"source={source!r}, product={product!r}.\n"
                f"Available (source, product) pairs: {available}\n"
                f"Call {cls.__name__}.list_zarr_sources() for details."
            )

        from herbie.v2._xarray import open_zarr_catalog

        if cls.verbose if hasattr(cls, "verbose") else True:
            console.print(f"[dim]Opening zarr → [bold]{entry.description}[/bold][/dim]")

        return open_zarr_catalog(entry, **open_kwargs)

    @classmethod
    def list_zarr_sources(cls) -> None:
        """
        Print a table of all available Zarr datasets for this model.

        Shows the ``(source, product)`` key, URL, and dimension structure
        for each entry in ``ZARR_SOURCES``.
        """
        catalog: dict = cls.ZARR_SOURCES
        if not catalog:
            console.print(
                f"[yellow]{cls.__name__} has no Zarr sources defined.[/yellow]"
            )
            return

        t = Table(
            box=box.SIMPLE_HEAD,
            title=f"[bold]{cls.__name__} Zarr Sources[/bold]",
            title_justify="left",
        )
        t.add_column("source", style="bold cyan")
        t.add_column("product", style="cyan")
        t.add_column("Description", overflow="fold", max_width=60)
        t.add_column("URL", style="dim", overflow="fold", max_width=55)

        for (src, prod), entry in sorted(catalog.items()):
            t.add_column  # no-op; columns already added
            t.add_row(
                src,
                prod,
                entry.description,
                f"[link={entry.url}]{entry.url}[/link]",
            )

        console.print(t)

    @property
    def local_path(self) -> Path:
        """
        Predicted local path for the full GRIB2 file.

        Mirrors the URL path structure so that ``rclone sync`` of the
        remote bucket produces the same directory layout as Herbie.
        """
        first: Source = next(iter(self.SOURCES.values()))
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
        first_src = next(iter(self.SOURCES.values()), None)
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
        for attr in ("_found_grib", "_found_index", "_index_df", "_status_results"):
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
        for src in self.SOURCES.values():
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
                for src in self.SOURCES.values():
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
            src = self.SOURCES.get(source)
            if src is None:
                raise ValueError(
                    f"Source {source!r} not found. Available: {list(self.SOURCES)}"
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
        import xarray as xr

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
            if isinstance(ds, xr.DataTree):
                ds = ds.load()
                ds.close()
            else:
                ds = ds.load()
                ds.close()
            local.unlink()

        return ds

    def resolve(self, *sources: str) -> "HerbieModel":
        """
        Resolve source availability and cache the results.

        Returns ``self`` for method chaining.

        Parameters
        ----------
        *sources
            Which sources to check.

            ``resolve()``
                Trigger lazy resolution of the first available GRIB source
                and its companion index file — the same logic used by
                ``inventory()``, ``download()``, and ``xarray()``, but
                made explicit and chainable.  Stops at the first hit.

            ``resolve('all')``
                Fire parallel HEAD requests to *every* source and cache
                the results (availability + file size).  This is the most
                complete picture and is what the ``H`` notebook display and
                ``H.status()`` draw from.

            ``resolve('aws')`` / ``resolve('aws', 'google')``
                Check only the named source(s), in the order given.  The
                first one that responds becomes the active GRIB source,
                overriding any previously cached resolution.  Useful for
                forcing a specific source without changing ``priority``.

        Examples
        --------
        >>> H = HRRR("2025-01-01").resolve('all')   # check everything, chain
        >>> H = HRRR("2025-01-01").resolve()         # first available
        >>> H.resolve('nomads')                      # switch to nomads
        >>> H.resolve('aws', 'google')               # prefer aws, fall back to google
        """
        if not sources:
            # Trigger both lazy cached_property resolutions (stop at first hit)
            _ = self._found_grib
            _ = self._found_index
            return self

        if sources == ("all",):
            # Parallel HEAD check of every source
            check_map: dict[tuple[str, str], str] = {}
            for name, src in self.SOURCES.items():
                if isinstance(src, (GribSource, EccodesGribSource)):
                    check_map[(name, "grib")] = src.url
                    for suffix in src.index_suffixes:
                        check_map[(name, f"idx:{suffix}")] = src.url + suffix
                elif isinstance(src, ZarrSource):
                    check_map[(name, "zarr")] = src.url

            results: dict[tuple[str, str], dict] = {}
            if check_map:
                with ThreadPoolExecutor(max_workers=min(16, len(check_map))) as pool:
                    futures = {
                        pool.submit(_url_info, url): key
                        for key, url in check_map.items()
                    }
                    for future in as_completed(futures):
                        results[futures[future]] = future.result()

            self._status_results = results  # consumed by _repr_html_ and status()

            # Also set _found_grib / _found_index to first available so
            # subsequent inventory/download/xarray calls don't re-check.
            if "_found_grib" not in self.__dict__:
                for name, src in self.SOURCES.items():
                    if isinstance(src, (GribSource, EccodesGribSource)):
                        if results.get((name, "grib"), {}).get("exists"):
                            self.__dict__["_found_grib"] = (name, src.url)
                            break
                        elif isinstance(src, ZarrSource):
                            if results.get((name, "zarr"), {}).get("exists"):
                                self.__dict__["_found_grib"] = (name, src.url)
                                break
                else:
                    self.__dict__.setdefault("_found_grib", (None, None))

            if "_found_index" not in self.__dict__:
                for name, src in self.SOURCES.items():
                    if isinstance(src, (GribSource, EccodesGribSource)):
                        for suffix in src.index_suffixes:
                            if results.get((name, f"idx:{suffix}"), {}).get("exists"):
                                self.__dict__["_found_index"] = (name, src.url + suffix)
                                break
                        if "_found_index" in self.__dict__:
                            break
                else:
                    self.__dict__.setdefault("_found_index", (None, None))

            return self

        # Named source(s) — check in the order given, stop at first hit.
        # Invalidate any prior resolution so the new result takes effect.
        bad = [n for n in sources if n not in self.SOURCES and n != "all"]
        if bad:
            raise ValueError(
                f"Unknown source(s): {bad}. Available: {list(self.SOURCES)}"
            )

        for name in sources:
            src = self.SOURCES[name]
            if isinstance(src, (GribSource, EccodesGribSource)):
                grib_info = _url_info(src.url)
                # Update _status_results so display reflects what we checked
                if not hasattr(self, "_status_results"):
                    self._status_results = {}
                self._status_results[(name, "grib")] = grib_info
                if grib_info["exists"]:
                    # Override cached resolution
                    self.__dict__["_found_grib"] = (name, src.url)
                    self.__dict__.pop("_found_index", None)  # re-resolve index
                    # Find companion index
                    for suffix in src.index_suffixes:
                        idx_url = src.url + suffix
                        idx_info = _url_info(idx_url)
                        self._status_results[(name, f"idx:{suffix}")] = idx_info
                        if idx_info["exists"]:
                            self.__dict__["_found_index"] = (name, idx_url)
                            break
                    else:
                        self.__dict__.setdefault("_found_index", (None, None))
                    return self
            elif isinstance(src, ZarrSource):
                zarr_info = _url_info(src.url)
                if not hasattr(self, "_status_results"):
                    self._status_results = {}
                self._status_results[(name, "zarr")] = zarr_info
                if zarr_info["exists"]:
                    self.__dict__["_found_grib"] = (name, src.url)
                    return self

        # None of the specified sources were found
        self.__dict__["_found_grib"] = (None, None)
        return self

    def status(self) -> None:
        """
        Display source availability and local files in the terminal.

        This is the Rich terminal equivalent of the notebook ``_repr_html_``
        display — it renders whatever Herbie currently knows from cached
        resolution results.  It performs **no network I/O**.

        To populate the display with availability and file sizes, call
        ``H.resolve('all')`` first::

            H.resolve('all').status()

        Or chain directly::

            H = HRRR("2025-01-01").resolve('all')
            H.status()
        """
        from rich.console import Group

        # ── What do we know about each source? ────────────────────────────
        status_cache = self.__dict__.get("_status_results")
        found_name = self.__dict__.get("_found_grib", (None, None))[0]

        # Categorise sources
        grib_srcs = {
            n: s
            for n, s in self.SOURCES.items()
            if isinstance(s, (GribSource, EccodesGribSource))
        }
        dir_srcs = {
            n: s for n, s in self.SOURCES.items() if isinstance(s, DirectorySource)
        }
        zarr_srcs = {n: s for n, s in self.SOURCES.items() if isinstance(s, ZarrSource)}

        # Per-source known state: True=exists, False=missing, None=unknown
        source_known: dict[str, bool | None] = {}
        if status_cache is not None:
            for n, s in self.SOURCES.items():
                if isinstance(s, (GribSource, EccodesGribSource)):
                    source_known[n] = status_cache.get((n, "grib"), {}).get("exists")
                elif isinstance(s, ZarrSource):
                    source_known[n] = status_cache.get((n, "zarr"), {}).get("exists")
                else:
                    source_known[n] = None
        elif found_name is not None:
            passed = False
            for n in self.SOURCES:
                if passed:
                    source_known[n] = None
                elif n == found_name:
                    source_known[n] = True
                    passed = True
                else:
                    source_known[n] = False
        else:
            for n in self.SOURCES:
                source_known[n] = None

        def _indicator(known):
            if known is True:
                return "[green]✓[/green]"
            if known is False:
                return "[red]✗[/red]"
            return "[dim]·[/dim]"

        # ── Logo / header ──────────────────────────────────────────────────
        logo = Text()
        logo.append("▌", style="bold red on white")
        logo.append("▌", style="bold blue on #f0ead2")
        logo.append("Herbie", style="bold black on #f0ead2")
        logo.append(f" {self.MODEL_NAME}", style="bold cyan")
        logo.append(f" — {self.MODEL_DESCRIPTION}", style="dim italic")

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

        renderables = [info_grid]

        # ── Remote GRIB Sources ────────────────────────────────────────────
        if grib_srcs:
            grib_table = Table(
                box=box.SIMPLE_HEAD,
                title="[bold]Remote GRIB Sources[/bold]",
                title_justify="left",
            )
            grib_table.add_column("Source", style="bold cyan")
            grib_table.add_column("", justify="center", width=3)  # ✓/✗
            grib_table.add_column("Size", justify="right")
            grib_table.add_column("URL", style="dim", overflow="fold", max_width=70)

            for name, src in grib_srcs.items():
                ind = _indicator(source_known.get(name))
                size = _fmt_size(
                    status_cache.get((name, "grib"), {}).get("size")
                    if status_cache
                    else None
                )
                # Find first known index suffix
                found_idx_suffix = None
                if status_cache:
                    for suffix in src.index_suffixes:
                        if status_cache.get((name, f"idx:{suffix}"), {}).get("exists"):
                            found_idx_suffix = suffix
                            break
                url_str = f"[link={src.url}]{src.url}[/link]"
                if found_idx_suffix:
                    idx_url = src.url + found_idx_suffix
                    url_str += f" [link={idx_url}]{found_idx_suffix}[/link]"
                name_str = (
                    f"{name}[bold cyan]*[/bold cyan]" if name == found_name else name
                )
                grib_table.add_row(name_str, ind, size, url_str)

            renderables.append(grib_table)

        # ── Remote Directory Sources ───────────────────────────────────────
        if dir_srcs:
            dir_table = Table(
                box=box.SIMPLE_HEAD,
                title="[bold]Remote Directory Sources[/bold]",
                title_justify="left",
            )
            dir_table.add_column("Source", style="bold cyan")
            dir_table.add_column("URL", style="dim", overflow="fold", max_width=70)
            dir_table.add_column("Pattern", style="dim", overflow="fold", max_width=45)
            for name, src in dir_srcs.items():
                pat = src.file_pattern
                pat_display = (pat[:44] + "…") if len(pat) > 45 else pat
                dir_table.add_row(
                    name, f"[link={src.url}]{src.url}[/link]", pat_display
                )
            renderables.append(dir_table)

        # ── Remote Zarr Sources ────────────────────────────────────────────
        if zarr_srcs:
            zarr_table = Table(
                box=box.SIMPLE_HEAD,
                title="[bold]Remote Zarr Sources[/bold]",
                title_justify="left",
            )
            zarr_table.add_column("Source", style="bold cyan")
            zarr_table.add_column("", justify="center", width=3)
            zarr_table.add_column("URL", style="dim", overflow="fold", max_width=60)
            for name, src in zarr_srcs.items():
                ind = _indicator(source_known.get(name))
                name_str = (
                    f"{name}[bold cyan]*[/bold cyan]" if name == found_name else name
                )
                zarr_table.add_row(name_str, ind, f"[link={src.url}]{src.url}[/link]")
            renderables.append(zarr_table)

        # ── Local GRIB Files ───────────────────────────────────────────────
        base = self.local_path
        local_files: list[tuple[Path, str]] = []
        if base.is_file():
            local_files.append((base, "full"))
        if base.parent.exists():
            for p in sorted(base.parent.glob(f"{base.name}__subset-*")):
                local_files.append((p, "subset"))

        loc_table = Table(
            box=box.SIMPLE_HEAD,
            title=f"[bold]Local GRIB Files[/bold]  [dim]{base.parent}[/dim]",
            title_justify="left",
        )
        loc_table.add_column("File", style="yellow")
        loc_table.add_column("Type")
        loc_table.add_column("Size", justify="right")
        if local_files:
            for path, kind in local_files:
                kind_str = (
                    "[bold green]full[/bold green]"
                    if kind == "full"
                    else "[dim]subset[/dim]"
                )
                loc_table.add_row(path.name, kind_str, _fmt_size(path.stat().st_size))
        else:
            loc_table.add_row("[dim]no local files[/dim]", "", "")
        renderables.append(loc_table)

        console.print(
            Panel(
                Group(*renderables),
                title=logo,
                border_style="cyan",
                box=box.ROUNDED,
            )
        )

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
        # ── Design tokens ──────────────────────────────────────────────────
        def _fmt_size_html(n):
            """Format bytes for HTML display, returns dim dash if None."""
            if n is None:
                return "<span style='color:#ccc'>—</span>"
            for unit in ("B", "KB", "MB", "GB"):
                if n < 1024:
                    return f"{n:.1f} {unit}"
                n /= 1024
            return f"{n:.1f} TB"

        BLUE = "#1565c0"
        BLUE_L = "#e8f0fe"
        BLUE_D = "#0d47a1"  # darker for selected border
        GREY_BG = "#f5f5f5"
        GREY_T = "#888"
        GREEN_BG = "#e6f4ea"
        GREEN_T = "#1a7f37"
        RED_BG = "#fce8e6"
        RED_T = "#c0392b"

        # ── Herbie badge (solid bars, always black text) ───────────────────
        badge = (
            "<span style='"
            "display:inline-flex;align-items:center;"
            "border:1px solid #ccc;border-radius:6px;"
            "padding:2px 8px 2px 6px;margin-right:10px;"
            "font-weight:600;background:white;color:black;"
            "font-size:0.9em;white-space:nowrap'>"
            "<span style='width:5px;height:13px;background:#e53935;"
            "border-radius:1px;margin-right:2px;flex-shrink:0'></span>"
            "<span style='width:5px;height:13px;background:#1565c0;"
            "border-radius:1px;margin-right:6px;flex-shrink:0'></span>"
            "Herbie</span>"
        )

        # ── fxx widget ─────────────────────────────────────────────────────
        fxx_widget = (
            f"<span style='display:inline-flex;align-items:center;"
            f"border:1px solid #ccc;border-radius:4px;padding:1px 8px;"
            f"background:#fafafa;font-family:monospace;font-size:0.88em;"
            f"color:#333;min-width:3em;justify-content:center'>"
            f"F{self.fxx:02d}</span>"
        )

        # ── Parameter section ──────────────────────────────────────────────
        # Stack layout: label on top, pills below, description below that
        params_html = ""
        for pname, pval in self.params.items():
            cfg = self.PARAMS.get(pname, {})
            valid = cfg.get("valid")
            descs = cfg.get("descriptions", {})
            aliases = cfg.get("aliases", {})

            rev_alias: dict = {}
            for alias, canonical in aliases.items():
                rev_alias.setdefault(canonical, []).append(alias)

            if valid:
                # Pill row
                pills = ""
                for opt in valid:
                    selected = str(opt) == str(pval)
                    desc = descs.get(opt, "")
                    tooltip = f' title="{desc}"' if desc else ""
                    alias_labels = rev_alias.get(opt, [])
                    alias_html = (
                        (
                            f"<div style='font-size:0.68em;opacity:0.6;"
                            f"margin-top:1px;line-height:1'>"
                            f"{', '.join(alias_labels)}</div>"
                        )
                        if alias_labels
                        else ""
                    )
                    if selected:
                        pill_style = (
                            f"display:inline-flex;flex-direction:column;"
                            f"align-items:center;margin:2px 4px 2px 0;"
                            f"padding:4px 12px;border-radius:14px;"
                            f"background:{BLUE_L};color:{BLUE_D};"
                            f"border:1.5px solid {BLUE};"
                            f"font-size:0.82em;font-weight:700;"
                            f"cursor:default;min-width:2em;text-align:center"
                        )
                    else:
                        pill_style = (
                            f"display:inline-flex;flex-direction:column;"
                            f"align-items:center;margin:2px 4px 2px 0;"
                            f"padding:4px 12px;border-radius:14px;"
                            f"background:{GREY_BG};color:{GREY_T};"
                            f"border:1px solid #ddd;"
                            f"font-size:0.82em;font-weight:400;"
                            f"cursor:default;min-width:2em;text-align:center"
                        )
                    pills += (
                        f"<span{tooltip} style='{pill_style}'>"
                        f"<span>{opt}</span>{alias_html}</span>"
                    )

                sel_desc = descs.get(pval, "")
                desc_html = (
                    (
                        f"<div style='font-size:0.78em;color:#666;"
                        f"margin-top:3px;margin-left:2px'>{sel_desc}</div>"
                    )
                    if sel_desc
                    else ""
                )

                params_html += (
                    f"<div style='margin-bottom:10px'>"
                    f"<div style='font-size:0.82em;font-weight:600;"
                    f"color:#444;margin-bottom:3px;text-transform:uppercase;"
                    f"letter-spacing:0.04em'>{pname}</div>"
                    f"<div style='display:flex;flex-wrap:wrap;align-items:flex-start'>"
                    f"{pills}</div>"
                    f"{desc_html}"
                    f"</div>"
                )
            else:
                # Text-input style for free-form / numeric values
                widget = (
                    f"<span style='display:inline-block;border:1px solid #ccc;"
                    f"border-radius:4px;padding:2px 10px;background:#fafafa;"
                    f"font-family:monospace;font-size:0.88em;color:#333;"
                    f"min-width:4em;text-align:center'>{pval}</span>"
                )
                params_html += (
                    f"<div style='margin-bottom:10px'>"
                    f"<div style='font-size:0.82em;font-weight:600;"
                    f"color:#444;margin-bottom:3px;text-transform:uppercase;"
                    f"letter-spacing:0.04em'>{pname}</div>"
                    f"{widget}</div>"
                )

        # ── Resolved badge ─────────────────────────────────────────────────
        src_name, src_url = (
            self._found_grib if "_found_grib" in self.__dict__ else (None, None)
        )
        if src_name:
            resolved_badge = (
                f"<span style='background:{GREEN_BG};color:{GREEN_T};"
                f"padding:2px 10px;border-radius:10px;font-size:0.82em;"
                f"font-weight:600;border:1px solid #b7dfbf'>{src_name}</span>"
            )
        else:
            resolved_badge = (
                f"<span style='background:{RED_BG};color:{RED_T};"
                f"padding:2px 10px;border-radius:10px;font-size:0.82em;"
                f"font-weight:600;border:1px solid #f0b4ae'>unresolved</span>"
            )

        # ── Source rows ────────────────────────────────────────────────────
        # Determine what we know about each source's availability:
        #
        #   _status_results   → status() was run: full ✓/✗ for every source
        #   _found_grib cache → lazy resolution ran: ✓ for winner, ✗ for
        #                       sources tried before it, blank for the rest
        #   neither           → no marks
        status_cache = self.__dict__.get("_status_results")  # set by resolve()
        found_name = self.__dict__.get("_found_grib", (None, None))[0]
        found_idx = self.__dict__.get("_found_index", (None, None))[0]

        # Build per-source indicator: True=exists, False=missing, None=unknown
        source_known: dict[str, bool | None] = {}
        if status_cache is not None:
            # Full knowledge from status()
            for n, s in self.SOURCES.items():
                if isinstance(s, (GribSource, EccodesGribSource)):
                    source_known[n] = status_cache.get((n, "grib"), {}).get(
                        "exists", False
                    )
                elif isinstance(s, ZarrSource):
                    source_known[n] = status_cache.get((n, "zarr"), {}).get(
                        "exists", False
                    )
                else:
                    source_known[n] = None
        elif found_name is not None:
            # Partial knowledge from lazy resolution
            passed_winner = False
            for n in self.SOURCES:
                if passed_winner:
                    source_known[n] = None  # never checked
                elif n == found_name:
                    source_known[n] = True  # this one was found
                    passed_winner = True
                else:
                    source_known[n] = False  # tried, not found
        else:
            for n in self.SOURCES:
                source_known[n] = None

        def _src_indicator(known: bool | None) -> str:
            if known is True:
                return (
                    "<span style='color:#1a7f37;font-size:0.9em;margin-right:4px'"
                    " title='exists'>&#10003;</span>"
                )
            if known is False:
                return (
                    "<span style='color:#c0392b;font-size:0.9em;margin-right:4px'"
                    " title='not found'>&#10007;</span>"
                )
            return "<span style='display:inline-block;width:14px'></span>"

        # size helper — only populated when status_cache is available
        def _size_cell(name: str) -> str:
            if status_cache is None:
                return ""
            n = status_cache.get((name, "grib"), {}).get("size")
            txt = _fmt_size_html(n)
            return (
                f"<td style='padding:4px 8px;text-align:right;"
                f"white-space:nowrap;font-size:0.78em;color:#666'>{txt}</td>"
            )

        show_size = status_cache is not None
        source_rows_html = ""
        n_sources = len(self.SOURCES)
        for name, src in self._ordered_sources().items():
            indicator = _src_indicator(source_known.get(name))
            size_td = _size_cell(name)
            is_active_grib = name == found_name
            is_active_idx = name == found_idx

            # No row background — keep it clean
            row_bg = ""

            # Arrow-only indicator in the name cell for the active source
            arrow = (
                (
                    f"<span style='color:{BLUE};margin-right:3px;font-size:0.8em'"
                    f" title='Active source — used by inventory, download, xarray'>"
                    f"&#9654;</span>"
                )
                if is_active_grib
                else "<span style='display:inline-block;width:14px'></span>"
            )
            name_html = f"{arrow}<code style='font-size:0.85em'>{name}</code>"

            if isinstance(src, (GribSource, EccodesGribSource)):
                url = src.url
                src_type = "GRIB2" if isinstance(src, GribSource) else "GRIB2/ecCodes"
                # Index link: bold if this source is also the active index source
                found_idx_url = self.__dict__.get("_found_index", (None, None))[1]
                idx_links = ""
                for suffix in src.index_suffixes:
                    iurl = src.url + suffix
                    is_active_this_idx = is_active_idx and found_idx_url == iurl
                    if is_active_this_idx:
                        idx_links += (
                            f"<a href='{iurl}' target='_blank' style='"
                            f"font-size:0.78em;font-family:monospace;"
                            f"font-weight:700;color:{BLUE};text-decoration:none'"
                            f" title='Active index source'>{suffix}</a> "
                        )
                    else:
                        idx_links += (
                            f"<a href='{iurl}' target='_blank' style='"
                            f"font-size:0.78em;font-family:monospace;"
                            f"color:#999;text-decoration:none'>{suffix}</a> "
                        )
                source_rows_html += (
                    f"<tr style='border-bottom:1px solid #e8e8e8;{row_bg}'>"
                    f"<td style='padding:4px 4px 4px 8px;white-space:nowrap;width:18px'>{indicator}</td>"
                    f"<td style='padding:4px 8px 4px 0;white-space:nowrap;text-align:right'>{name_html}</td>"
                    f"<td style='padding:4px 8px;color:#999;font-size:0.8em;white-space:nowrap'>{src_type}</td>"
                    f"<td style='padding:4px 8px;word-break:break-all;font-family:monospace;font-size:0.78em'>"
                    f"<a href='{url}' target='_blank' style='color:{BLUE};text-decoration:none'>{url}</a></td>"
                    f"<td style='padding:4px 8px;white-space:nowrap'>{idx_links}</td>"
                    f"{size_td}"
                    f"</tr>"
                )
            elif isinstance(src, ZarrSource):
                url = src.url
                source_rows_html += (
                    f"<tr style='border-bottom:1px solid #e8e8e8;{row_bg}'>"
                    f"<td style='padding:4px 4px 4px 8px;white-space:nowrap;width:18px'>{indicator}</td>"
                    f"<td style='padding:4px 8px 4px 0;white-space:nowrap;text-align:right'>{name_html}</td>"
                    f"<td style='padding:4px 8px;color:#999;font-size:0.8em'>Zarr</td>"
                    f"<td style='padding:4px 8px;font-family:monospace;font-size:0.78em' colspan='2'>"
                    f"<a href='{url}' target='_blank' style='color:{BLUE};text-decoration:none'>{url}</a></td>"
                    f"{size_td}"
                    f"</tr>"
                )
            elif isinstance(src, DirectorySource):
                url = src.url
                source_rows_html += (
                    f"<tr style='border-bottom:1px solid #e8e8e8;{row_bg}'>"
                    f"<td style='padding:4px 4px 4px 8px;white-space:nowrap;width:18px'>{indicator}</td>"
                    f"<td style='padding:4px 8px 4px 0;white-space:nowrap;text-align:right'>{name_html}</td>"
                    f"<td style='padding:4px 8px;color:#999;font-size:0.8em'>Directory</td>"
                    f"<td style='padding:4px 8px;font-family:monospace;font-size:0.78em' colspan='2'>"
                    f"<a href='{url}' target='_blank' style='color:{BLUE};text-decoration:none'>{url}</a></td>"
                    f"{size_td}"
                    f"</tr>"
                )

        # ── Local file existence indicator ────────────────────────────
        if self.local_path.is_file():
            local_exists_badge = (
                f"<span style='background:{GREEN_BG};color:{GREEN_T};"
                f"padding:1px 7px;border-radius:10px;font-size:0.8em;"
                f"font-weight:600;border:1px solid #b7dfbf'>✔ exists</span>"
            )
        else:
            local_exists_badge = (
                f"<span style='background:{RED_BG};color:{RED_T};"
                f"padding:1px 7px;border-radius:10px;font-size:0.8em;"
                f"font-weight:600;border:1px solid #f0b4ae'>✘ not on disk</span>"
            )

        # ── Info button + MODEL_WEBSITES modal ───────────────────────────
        # Each HerbieModel instance gets a unique ID so multiple cells
        # in the same notebook don't interfere with each other.
        import hashlib as _hl

        _uid = _hl.md5(f"{id(self)}".encode()).hexdigest()[:8]
        modal_id = f"herbie-modal-{_uid}"
        overlay_id = f"herbie-overlay-{_uid}"

        if self.MODEL_WEBSITES:
            links_html = "".join(
                f"<a href='{url}' target='_blank' style='"
                f"display:block;padding:6px 0;color:{BLUE};"
                f"text-decoration:none;font-size:0.9em'>"
                f"&#8599;&nbsp;{label}</a>"
                for label, url in self.MODEL_WEBSITES.items()
            )
            modal_html = (
                f"<!-- overlay -->"
                f"<div id='{overlay_id}' onclick=\""
                f"document.getElementById('{modal_id}').style.display='none';"
                f"document.getElementById('{overlay_id}').style.display='none'\""
                f" style='display:none;position:fixed;inset:0;z-index:999'></div>"
                f"<!-- modal -->"
                f"<div id='{modal_id}' style='"
                f"display:none;position:absolute;top:2.2em;right:0;"
                f"background:white;color:#111;border:1px solid #ddd;"
                f"border-radius:8px;padding:14px 18px;min-width:220px;"
                f"box-shadow:0 4px 16px rgba(0,0,0,0.15);z-index:1000;"
                f"font-family:sans-serif'>"
                f"<div style='font-weight:700;font-size:0.85em;text-transform:uppercase;"
                f"letter-spacing:0.05em;color:#555;margin-bottom:8px'>Resources</div>"
                f"{links_html}"
                f"</div>"
            )
            info_btn_html = (
                f"<div style='position:relative'>"
                f'<button onclick="'
                f"var m=document.getElementById('{modal_id}');"
                f"var o=document.getElementById('{overlay_id}');"
                f"var show=m.style.display==='none';"
                f"m.style.display=show?'block':'none';"
                f"o.style.display=show?'block':'none'\" "
                f"style='background:none;border:1px solid #ccc;border-radius:50%;"
                f"width:22px;height:22px;cursor:pointer;font-size:0.8em;"
                f"color:#999;display:flex;align-items:center;justify-content:center;"
                f"padding:0;line-height:1' title='Resources & links'>"
                f"&#x2139;"
                f"</button>"
                f"{modal_html}"
                f"</div>"
            )
            modal_html = ""  # already embedded in info_btn_html
        else:
            info_btn_html = ""
            modal_html = ""

        # ── Local files (full + subsets) ──────────────────────────────────
        _base = self.local_path
        _local_files: list[tuple[Path, str]] = []
        if _base.is_file():
            _local_files.append((_base, "full"))
        if _base.parent.exists():
            for _p in sorted(_base.parent.glob(f"{_base.name}__subset-*")):
                _local_files.append((_p, "subset"))

        if _local_files:
            _lrows = ""
            for _p, _kind in _local_files:
                _sz = _fmt_size_html(_p.stat().st_size)
                if _kind == "full":
                    _badge = (
                        f"<span style='background:{GREEN_BG};color:{GREEN_T};"
                        f"padding:1px 6px;border-radius:8px;font-size:0.75em;"
                        f"font-weight:600'>full</span>"
                    )
                else:
                    _badge = "<span style='color:#999;font-size:0.75em'>subset</span>"
                _lrows += (
                    f"<tr style='border-bottom:1px solid #f0f0f0'>"
                    f"<td style='padding:3px 8px'>{_badge}</td>"
                    f"<td style='padding:3px 8px;font-family:monospace;font-size:0.78em;color:#555'>"
                    f"{_p.name}</td>"
                    f"<td style='padding:3px 8px;text-align:right;font-size:0.78em;color:#666;"
                    f"white-space:nowrap'>{_sz}</td>"
                    f"</tr>"
                )
            local_files_html = (
                f"<div style='margin-top:8px;font-size:0.82em;font-weight:600;color:#555;"
                f"text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px'>"
                f"Local files</div>"
                f"<table style='border-collapse:collapse;width:100%;"
                f"border:1px solid #e8e8e8;border-radius:4px'>"
                f"<tbody>{_lrows}</tbody>"
                f"</table>"
            )
        else:
            local_files_html = ""

        sep = "<hr style='border:none;border-top:1px solid #eee;margin:10px 0'>"

        return f"""
        <div style="font-family:sans-serif;border:1px solid #ddd;border-radius:8px;
                    padding:14px 16px;max-width:900px;line-height:1.4">

          <!-- Header -->
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px">
            <div style="display:flex;align-items:center">
              {badge}
              <div>
                <span style="font-size:1.2em;font-weight:700">{self.MODEL_NAME}</span>
                <span style="font-size:0.85em;color:#888;margin-left:8px">{self.MODEL_DESCRIPTION}</span>
              </div>
            </div>
            {info_btn_html}
          </div>
          {modal_html}

          <!-- Date / fxx row -->
          <div style="font-size:0.88em;color:#444;margin-bottom:2px">
            <b>Initialized:</b> {self.date:%Y-%b-%d %H:%M UTC}
            &nbsp;{fxx_widget}&nbsp;
            <b>Valid:</b> {self.valid_date:%Y-%b-%d %H:%M UTC}
          </div>

          {sep}

          <!-- Parameters -->
          <details open>
            <summary style="cursor:pointer;font-size:0.88em;font-weight:700;
                            color:#555;letter-spacing:0.05em;text-transform:uppercase;
                            margin-bottom:8px;list-style:none">
              &#9654; Parameters
            </summary>
            <div style="padding:6px 0 2px 0">
              {params_html}
            </div>
          </details>

          {sep}

          <!-- Sources -->
          <details open>
            <summary style="cursor:pointer;font-size:0.88em;font-weight:700;
                            color:#555;letter-spacing:0.05em;text-transform:uppercase;
                            margin-bottom:8px;list-style:none">
              &#9654; Sources ({n_sources})
            </summary>
            <div style="font-size:0.88em;margin-bottom:6px">
              <b>Resolved:</b>&nbsp;{resolved_badge}
              &nbsp;&nbsp;
              <b>Local:</b>&nbsp;{local_exists_badge}&nbsp;<code style="font-size:0.85em;font-family:monospace;
              color:#555">{self.local_path}</code>
            </div>
            <table style="border-collapse:collapse;width:100%;
                          border:1px solid #e8e8e8;border-radius:4px">
              <thead>
                <tr style="background:#f8f8f8;border-bottom:2px solid #e0e0e0">
                  <th style="padding:5px 4px 5px 8px;width:18px"></th>
                  <th style="text-align:right;padding:5px 8px 5px 0;font-size:0.82em;color:#555">Name</th>
                  <th style="text-align:left;padding:5px 8px;font-size:0.82em;color:#555">Type</th>
                  <th style="text-align:left;padding:5px 8px;font-size:0.82em;color:#555">URL</th>
                  <th style="text-align:left;padding:5px 8px;font-size:0.82em;color:#555">Index</th>
                  {"<th style='text-align:right;padding:5px 8px;font-size:0.82em;color:#555'>Size</th>" if show_size else ""}
                </tr>
              </thead>
              <tbody>{source_rows_html}</tbody>
            </table>
            {local_files_html}
          </details>

        </div>"""
