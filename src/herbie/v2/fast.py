"""
FastHerbie — bulk inventory aggregation and parallel multi-source download.

Design
------
FastHerbie constructs a collection of HerbieModel objects (one per
date × fxx combination) and exposes a unified pipeline:

1. **Aggregate** — fetch all index files in parallel and concatenate
   their rows into a single Polars DataFrame.  Every row carries the
   full remote URL (``source`` column) and the byte-range
   (``start_byte`` / ``end_byte``) needed to fetch that one GRIB
   message from its file.

2. **Filter** — apply a search string or Polars expression to the
   combined inventory, exactly as ``HerbieModel.inventory(search)``
   does for a single file.

3. **Download** — issue all matching byte-range requests concurrently
   across every source URL and concatenate the results into one GRIB2
   output file.  Because GRIB2 messages are self-contained, the
   concatenated file is valid and readable by wgrib2 / cfgrib.

4. **Partition** — optionally split the output by any column(s) in the
   combined inventory so each unique combination of values is written
   to its own file.  Partitions are downloaded in the same parallel
   pass; only the output routing differs.

Usage
-----
>>> from herbie.v2 import HRRR
>>> from herbie.v2.fast import FastHerbie
>>> import pandas as pd
>>>
>>> fh = FastHerbie(
...     pd.date_range("2024-06-01", periods=24, freq="1h"),
...     model=HRRR,
...     fxx=[0, 1, 3, 6],
...     product="sfc",
... )
>>>
>>> # Inspect the combined inventory (fetches all index files in parallel)
>>> fh.inventory("TMP:2 m above ground")
>>>
>>> # Download all matching messages into one file
>>> path = fh.download("TMP:2 m above ground")
>>>
>>> # One file per model-init hour
>>> paths = fh.download("TMP:2 m above ground", partition_by="model_init_time")
>>>
>>> # One file per (date, fxx) pair — every HerbieModel object gets its own file
>>> paths = fh.download("TMP:2 m above ground", partition_by=["model_init_time", "fxx"])
>>>
>>> # Open the combined data directly as xarray
>>> ds = fh.xarray("TMP:2 m above ground")
"""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

import polars as pl
from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from herbie.v2._base import HerbieModel

console = Console()
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Multi-source download-group builder
# ---------------------------------------------------------------------------


def _create_multi_source_groups(df: pl.DataFrame) -> pl.DataFrame:
    """
    Collapse consecutive GRIB messages from the same source URL into
    contiguous byte-range download groups.

    Unlike ``_inventory.create_download_groups``, which assumes a single
    source file and sorts only by ``grib_message``, this function handles
    DataFrames that span *multiple* source URLs (i.e. many different GRIB
    files).

    A new group is opened whenever:
    • the ``source`` URL changes, **or**
    • the ``grib_message`` sequence number is non-consecutive within a source.

    The result DataFrame has columns:
        ``source``, ``start_byte``, ``end_byte``, ``download_group``

    and is sorted by ``download_group`` so the caller can concatenate
    the downloaded fragments in a deterministic order.

    Parameters
    ----------
    df
        Combined inventory DataFrame.  Must have columns
        ``source``, ``grib_message``, ``start_byte``, ``end_byte``.

    Returns
    -------
    pl.DataFrame
        One row per download group.
    """
    if df.is_empty():
        return pl.DataFrame(
            schema={
                "source": pl.String,
                "start_byte": pl.Int64,
                "end_byte": pl.Int64,
                "download_group": pl.Int32,
            }
        )

    return (
        # Sort so messages from the same source are contiguous and ordered
        df.sort(["source", "grib_message"])
        .with_columns(
            # A group boundary occurs when the source changes OR the
            # message number jumps (non-consecutive within a source).
            download_group=(
                (
                    # Source changed from the previous row  (fill_null(True)
                    # makes the very first row start a new group)
                    (pl.col("source") != pl.col("source").shift(1)).fill_null(True)
                    # Message number is not exactly one more than the previous
                    | (pl.col("grib_message").diff().fill_null(1) != 1)
                )
                .cast(pl.Int32)
                .cum_sum()
            )
        )
        # Merge consecutive messages in the same group into one byte range
        .group_by(["source", "download_group"], maintain_order=True)
        .agg(
            pl.col("start_byte").min(),
            # If *any* message in the group has a null end_byte (i.e. it is the
            # last message in its source file and the file size is unknown),
            # request to end-of-file by setting end_byte = null for the group.
            pl.when(pl.col("end_byte").is_null().any())
            .then(pl.lit(None))
            .otherwise(pl.col("end_byte").max())
            .alias("end_byte"),
        )
        .sort("download_group")
    )


# ---------------------------------------------------------------------------
# FastHerbie
# ---------------------------------------------------------------------------


class FastHerbie:
    """
    Create and operate on a collection of HerbieModel objects.

    FastHerbie constructs one HerbieModel per ``(date, fxx)`` pair, then
    provides a single interface to aggregate their inventories and
    download matching GRIB messages in parallel — across *all* source
    files simultaneously — into one or more output files.

    Parameters
    ----------
    dates
        Iterable of date-like values (strings, datetimes, pd.Timestamps).
        ``pd.date_range(...)`` works perfectly.
    model
        A ``HerbieModel`` *subclass* (not an instance).  E.g. ``HRRR``, ``GFS``.
    fxx
        Forecast lead time(s) in hours.  Either a single ``int``/``str`` or
        an iterable of ints.  The cross-product of ``dates`` × ``fxx`` is
        used when multiple values are provided.
    **kwargs
        Forwarded to the model constructor (``product``, ``priority``,
        ``save_dir``, ``overwrite``, etc.).

    Attributes
    ----------
    objects : list[HerbieModel]
        The constructed model objects (one per date × fxx combination).

    Examples
    --------
    >>> fh = FastHerbie(
    ...     pd.date_range("2024-01-01", periods=6, freq="1h"),
    ...     model=HRRR,
    ...     fxx=[0, 3, 6],
    ...     product="sfc",
    ... )
    >>> len(fh)          # 6 dates × 3 fxx values = 18
    18
    >>> fh.inventory("TMP:2 m above ground")   # combined index
    >>> fh.download("TMP:2 m above ground")    # single output file
    >>> fh.download("TMP:2 m", partition_by="model_init_time")  # one file / hour
    """

    def __init__(
        self,
        dates: Iterable,
        *,
        model: type[HerbieModel],
        fxx: int | str | Iterable = 0,
        **kwargs,
    ):
        if not (isinstance(model, type) and issubclass(model, HerbieModel)):
            raise TypeError(
                f"'model' must be a HerbieModel subclass (e.g. HRRR), "
                f"not an instance or unrelated type.  Got {type(model)!r}."
            )

        self.model_cls = model

        dates_list = list(dates)
        fxx_list: list = [fxx] if isinstance(fxx, (int, str)) else list(fxx)

        # Build (date, fxx) cross-product — construction is fast (no network I/O)
        self.objects: list[HerbieModel] = [
            model(date=d, fxx=f, **kwargs) for d in dates_list for f in fxx_list
        ]

    # ── Dunder ────────────────────────────────────────────────────────────

    def __len__(self) -> int:
        return len(self.objects)

    def __iter__(self):
        return iter(self.objects)

    def __repr__(self) -> str:
        n = len(self.objects)
        return (
            f"FastHerbie({self.model_cls.MODEL_NAME}, "
            f"{n} object{'s' if n != 1 else ''})"
        )

    # ── Combined inventory ─────────────────────────────────────────────────

    def inventory(
        self,
        search: str | pl.Expr | list[pl.Expr] | None = None,
        *,
        max_workers: int = 20,
        verbose: bool = True,
    ) -> pl.DataFrame:
        """
        Fetch all index files in parallel and return a combined inventory.

        Each row in the result represents one GRIB message and includes:

        * ``source``          — full remote URL of the GRIB2 file
        * ``start_byte``      — byte offset of the message in that file
        * ``end_byte``        — last byte of the message (``null`` for the
          last message in each file, which signals "read to EOF")
        * ``model_init_time`` — model initialization datetime
        * ``fxx``             — forecast lead time in hours
        * All variable/level/forecast columns from the index file

        The ``source`` + ``start_byte`` / ``end_byte`` triple is everything
        ``download()`` needs to issue a targeted HTTP Range request.

        Parameters
        ----------
        search
            Filter applied to each object's inventory before concatenation.
            Accepts the same forms as ``HerbieModel.inventory(search)``:
            a regex string, a ``pl.Expr``, or a ``list[pl.Expr]``.
        max_workers
            Number of parallel threads for fetching index files.
        verbose
            Show a progress bar while fetching.

        Returns
        -------
        pl.DataFrame
            Combined inventory; empty if nothing matched or all fetches failed.
        """
        frames: list[pl.DataFrame] = []
        errors: list[tuple[HerbieModel, Exception]] = []
        lock = Lock()

        def _fetch_one(obj: HerbieModel) -> pl.DataFrame | None:
            try:
                df = obj.inventory(search)
                if df.is_empty():
                    return None
                return df.with_columns(
                    pl.lit(obj.date).cast(pl.Datetime).alias("model_init_time"),
                    pl.lit(obj.fxx).cast(pl.Int32).alias("fxx"),
                )
            except Exception as exc:
                with lock:
                    errors.append((obj, exc))
                return None

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
            transient=True,
            disable=not verbose,
        ) as progress:
            task = progress.add_task(
                f"[cyan]Fetching {self.model_cls.MODEL_NAME} "
                f"inventories ({len(self.objects)} objects)",
                total=len(self.objects),
            )
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                future_to_obj = {
                    pool.submit(_fetch_one, obj): obj for obj in self.objects
                }
                for future in as_completed(future_to_obj):
                    result = future.result()
                    if result is not None:
                        with lock:
                            frames.append(result)
                    progress.update(task, advance=1)

        if errors and verbose:
            console.print(
                f"[yellow]⚠  {len(errors)} inventory fetch(es) failed[/yellow]"
            )
            for obj, exc in errors[:5]:
                console.print(f"   {obj!r}: [red]{exc}[/red]")
            if len(errors) > 5:
                console.print(f"   … and {len(errors) - 5} more")

        if not frames:
            return pl.DataFrame()

        return pl.concat(frames, how="diagonal")

    # ── Download ──────────────────────────────────────────────────────────

    def download(
        self,
        search: str | pl.Expr | list[pl.Expr] | None = None,
        *,
        dest: Path | str | None = None,
        dest_dir: Path | str | None = None,
        partition_by: str | list[str] | None = None,
        max_workers: int = 10,
        inventory_workers: int = 20,
        overwrite: bool = False,
        verbose: bool = True,
    ) -> Path | list[Path]:
        """
        Download matching GRIB messages from all source files in parallel.

        **How it works**

        1. All index files are fetched concurrently (``inventory_workers``
           threads) to build the combined inventory DataFrame.
        2. ``search`` is applied to filter down to the messages of interest.
        3. Consecutive messages from the same source URL are merged into
           contiguous byte-range groups — typically collapsing many messages
           into far fewer HTTP Range requests.
        4. All range requests are dispatched concurrently
           (``max_workers`` threads).
        5. The downloaded fragments are concatenated in deterministic order
           into the output file(s).

        Parameters
        ----------
        search
            Inventory filter.  Rows where this matches will be downloaded.
            ``None`` downloads every message across every object — use with
            care on large collections.
        dest
            Explicit output path for the *single-file* case.  Auto-generated
            when ``None`` and ``partition_by`` is not set.  Ignored when
            ``partition_by`` is given.
        dest_dir
            Directory for output file(s).  Defaults to the first object's
            ``save_dir``.
        partition_by
            Column name(s) in the combined inventory by which to split the
            output into separate files.  Each unique combination of values
            is written to its own GRIB2 file inside ``dest_dir``.

            Useful values:

            ``"model_init_time"``
                One file per model initialization time.
            ``"fxx"``
                One file per forecast lead time.
            ``["model_init_time", "fxx"]``
                One file per (date, fxx) pair — mirrors one file per
                HerbieModel object.
            ``"variable"``
                One file per GRIB variable name (wgrib2 style).

        max_workers
            Maximum concurrent download threads (for byte-range fetches).
        inventory_workers
            Maximum concurrent threads for fetching index files.
        overwrite
            Re-download files that already exist locally.
        verbose
            Show progress information.

        Returns
        -------
        Path
            When ``partition_by`` is ``None``: path of the single output.
        list[Path]
            When ``partition_by`` is set: one path per partition, in the
            order they appear in the inventory.
        """
        from herbie.v2._download import download_groups as _download_groups

        # ── Resolve output directory ───────────────────────────────────────
        base_dir = Path(
            dest_dir
            if dest_dir is not None
            else (self.objects[0].save_dir if self.objects else ".")
        ).expanduser()
        base_dir.mkdir(parents=True, exist_ok=True)

        # ── Build combined inventory ───────────────────────────────────────
        if verbose:
            console.print(
                f"[bold]FastHerbie[/bold] {self.model_cls.MODEL_NAME} — "
                f"building combined inventory for {len(self.objects)} object(s)"
            )

        df = self.inventory(search, max_workers=inventory_workers, verbose=verbose)

        if df.is_empty():
            raise ValueError(
                f"No GRIB messages matched search={search!r} across "
                f"{len(self.objects)} {self.model_cls.MODEL_NAME} object(s).\n"
                "Call .inventory() without a search filter to see available fields."
            )

        n_messages = len(df)

        # ── Normalise partition_by ─────────────────────────────────────────
        if isinstance(partition_by, str):
            partition_by = [partition_by]

        if partition_by is not None:
            missing = [c for c in partition_by if c not in df.columns]
            if missing:
                raise ValueError(
                    f"Partition column(s) {missing} not found in the inventory.\n"
                    f"Available columns: {df.columns}"
                )

        # ── Single-file download ───────────────────────────────────────────
        if partition_by is None:
            out_path = (
                Path(dest)
                if dest is not None
                else base_dir / self._auto_filename(df, search)
            )
            if out_path.exists() and not overwrite:
                if verbose:
                    console.print(f"[dim]Already exists → {out_path}[/dim]")
                return out_path

            groups = _create_multi_source_groups(df)
            if verbose:
                n_srcs = df["source"].n_unique()
                console.print(
                    f"[bold]Downloading[/bold] {n_messages:,} messages "
                    f"from {n_srcs} source file(s) "
                    f"→ {len(groups)} range requests "
                    f"→ [yellow]{out_path.name}[/yellow]"
                )
            return _download_groups(
                groups, out_path, max_workers=max_workers, verbose=verbose
            )

        # ── Partitioned download ───────────────────────────────────────────
        # Use polars partition_by to split the DataFrame; each partition is
        # then grouped into range requests and downloaded independently.
        # We collect (key_tuple, partition_df) pairs first so we can report
        # a useful summary before any I/O begins.
        partitions: list[tuple[tuple, pl.DataFrame]] = []
        for part_df in df.partition_by(partition_by, maintain_order=True):
            # Extract the partition key from the first row (all rows share it)
            key_vals = tuple(part_df[0, col] for col in partition_by)
            partitions.append((key_vals, part_df))

        if verbose:
            console.print(
                f"[bold]FastHerbie[/bold] {self.model_cls.MODEL_NAME} — "
                f"downloading {n_messages:,} messages into "
                f"{len(partitions)} partition(s) "
                f"(by: {', '.join(partition_by)})"
            )

        results: list[Path] = []
        for key_vals, part_df in partitions:
            fname = self._partition_filename(key_vals, partition_by)
            out_path = base_dir / fname

            if out_path.exists() and not overwrite:
                if verbose:
                    console.print(f"[dim]Already exists → {fname}[/dim]")
                results.append(out_path)
                continue

            groups = _create_multi_source_groups(part_df)
            n_part = len(part_df)
            key_label = "  ".join(
                f"[cyan]{k}[/cyan]=[green]{_fmt_key(v)}[/green]"
                for k, v in zip(partition_by, key_vals)
            )
            if verbose:
                console.print(
                    f"  {key_label}  "
                    f"({n_part:,} msg, {len(groups)} requests) "
                    f"→ [yellow]{fname}[/yellow]"
                )
            out = _download_groups(
                groups, out_path, max_workers=max_workers, verbose=verbose
            )
            results.append(out)

        return results

    # ── xarray ────────────────────────────────────────────────────────────

    def xarray(
        self,
        search: str | pl.Expr | list[pl.Expr] | None = None,
        *,
        dest: Path | str | None = None,
        dest_dir: Path | str | None = None,
        partition_by: str | list[str] | None = None,
        max_workers: int = 10,
        inventory_workers: int = 20,
        overwrite: bool = False,
        remove_grib: bool = True,
        verbose: bool = True,
    ):
        """
        Download matching GRIB messages and open as ``xarray.Dataset``(s).

        Delegates to ``download()`` for the GRIB acquisition step, then
        opens each output file with cfgrib.

        Parameters
        ----------
        search, dest, dest_dir, partition_by, max_workers, inventory_workers,
        overwrite, verbose
            Same as ``download()``.
        remove_grib
            If ``True``, delete the downloaded GRIB file(s) after loading
            into memory (saves disk space when working with subsets).

        Returns
        -------
        xr.Dataset
            When ``partition_by`` is ``None`` *and* cfgrib produces a single
            hypercube.
        list[xr.Dataset]
            When ``partition_by`` is set, or when cfgrib produces multiple
            hypercubes.  ``xr.concat`` along ``"time"`` is attempted before
            falling back to a raw list.
        """
        import xarray as xr
        from herbie.v2._xarray import load_xarray

        paths = self.download(
            search,
            dest=dest,
            dest_dir=dest_dir,
            partition_by=partition_by,
            max_workers=max_workers,
            inventory_workers=inventory_workers,
            overwrite=overwrite,
            verbose=verbose,
        )

        single_file = isinstance(paths, Path)
        path_list: list[Path] = [paths] if single_file else list(paths)

        datasets = []
        for path in path_list:
            try:
                ds = load_xarray(path)
                if remove_grib:
                    # Load all data into memory before unlinking
                    if isinstance(ds, list):
                        ds = [d.load() for d in ds]
                        for d in ds:
                            d.close()
                    else:
                        ds = ds.load()
                        ds.close()
                    path.unlink(missing_ok=True)
                datasets.append(ds)
            except Exception as exc:
                if verbose:
                    console.print(
                        f"[yellow]⚠  xarray failed for {path.name}: {exc}[/yellow]"
                    )
                datasets.append(None)

        if single_file:
            return datasets[0]

        valid = [d for d in datasets if d is not None]
        if not valid:
            return datasets

        # Flatten any nested lists produced by cfgrib on multi-hypercube files
        flat: list = []
        for item in valid:
            if isinstance(item, list):
                flat.extend(item)
            else:
                flat.append(item)

        try:
            return xr.concat(flat, dim="time")
        except Exception:
            return flat

    # ── Private helpers ───────────────────────────────────────────────────

    def _auto_filename(
        self, df: pl.DataFrame, search: str | pl.Expr | list | None
    ) -> str:
        """
        Generate a unique output filename for the single-file case.

        The filename encodes the model name, object count, and a short hash
        of the search expression so repeated calls with different filters
        produce distinct files.
        """
        model = self.model_cls.MODEL_NAME
        n = len(self.objects)
        # Stable hash: based on the search string and the set of source URLs
        sources_str = "|".join(sorted(df["source"].unique().to_list()))
        key = f"{search!r}|{sources_str}"
        h = hashlib.blake2b(key.encode(), digest_size=6).hexdigest()
        return f"{model}__bulk_n{n}__{h}.grib2"

    @staticmethod
    def _partition_filename(key_vals: tuple, columns: list[str]) -> str:
        """
        Build a safe filename from the partition key column names and values.

        Example::

            columns  = ["model_init_time", "fxx"]
            key_vals = (datetime(2024, 6, 1, 12), 6)
            → "HRRR__model_init_time=20240601T12Z__fxx=6.grib2"

        Datetime values are formatted as ``YYYYMMDDThhZ``; all other values
        are converted to strings with unsafe filesystem characters stripped.
        """
        parts = []
        for col, val in zip(columns, key_vals):
            val_str = _fmt_key(val)
            # Strip / replace characters unsafe for most filesystems
            val_str = (
                val_str.replace(":", "")
                .replace("/", "-")
                .replace("\\", "-")
                .replace(" ", "_")
            )
            parts.append(f"{col}={val_str}")
        return "__".join(parts) + ".grib2"


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _fmt_key(val) -> str:
    """Format a partition-key value as a compact, human-readable string."""
    # Python datetime / numpy datetime64 / pandas Timestamp
    if hasattr(val, "strftime"):
        return val.strftime("%Y%m%dT%HZ")
    type_str = type(val).__name__.lower()
    if "datetime" in type_str or "timestamp" in type_str:
        try:
            import pandas as pd

            return pd.Timestamp(val).strftime("%Y%m%dT%HZ")
        except Exception:
            pass
    return str(val)
