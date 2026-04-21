"""
FastHerbie — bulk construction of HerbieModel objects.

Mirrors the ``FastHerbie`` pattern from Herbie v1 but works with any
``HerbieModel`` subclass and avoids network I/O at construction time
(all source-resolution happens lazily when you call ``.download()`` or
``.xarray()``).

Usage
-----
>>> from herbie.v2 import HRRR
>>> from herbie.v2.fast import FastHerbie
>>>
>>> # Loop over dates
>>> fh = FastHerbie(
...     pd.date_range("2024-01-01", periods=24, freq="1h"),
...     model=HRRR,
...     fxx=6,
...     product="sfc",
... )
>>> fh.download("TMP:2 m above ground", max_workers=10)
>>> datasets = fh.xarray("TMP:2 m above ground")
>>>
>>> # Loop over fxx
>>> fh2 = FastHerbie(
...     ["2024-01-01"],
...     model=HRRR,
...     fxx=range(0, 18),
...     product="sfc",
... )
"""

from __future__ import annotations

from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)

from herbie.v2._base import HerbieModel

console = Console()


class FastHerbie:
    """
    Create and operate on a collection of HerbieModel objects in parallel.

    Parameters
    ----------
    dates
        Iterable of date-like values (strings, datetimes, pandas Timestamps).
        A ``pandas.DatetimeIndex`` or ``pd.date_range(...)`` works perfectly.
    model
        A ``HerbieModel`` subclass (not an instance).  E.g. ``HRRR``, ``GFS``.
    fxx
        Forecast lead time(s).  Either a single int/str or an iterable of ints.
        If multiple values are given, the cross-product with ``dates`` is used.
    **kwargs
        All other keyword arguments are forwarded to the model constructor
        (``product``, ``priority``, ``save_dir``, etc.).

    Attributes
    ----------
    objects : list[HerbieModel]
        The constructed model objects (one per date × fxx combination).
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
                f"not an instance or unrelated type."
            )

        self.model_cls = model

        # Normalise dates
        dates_list = list(dates)

        # Normalise fxx
        if isinstance(fxx, (int, str)):
            fxx_list = [fxx]
        else:
            fxx_list = list(fxx)

        # Build all (date, fxx) pairs
        pairs = [(d, f) for d in dates_list for f in fxx_list]

        # Construct objects (fast — no network I/O)
        self.objects: list[HerbieModel] = [
            model(date=d, fxx=f, **kwargs) for d, f in pairs
        ]

    def __len__(self) -> int:
        return len(self.objects)

    def __iter__(self):
        return iter(self.objects)

    def __repr__(self) -> str:
        return f"FastHerbie({self.model_cls.MODEL_NAME}, {len(self.objects)} objects)"

    # ── Bulk operations ────────────────────────────────────────────────────

    def download(
        self,
        search: str | None = None,
        *,
        max_workers: int = 5,
        overwrite: bool = False,
        verbose: bool = True,
    ) -> list[Path]:
        """
        Download files for all objects in parallel.

        Parameters
        ----------
        search
            Inventory filter (same as ``HerbieModel.download(search)``).
        max_workers
            Maximum concurrent downloads.
        overwrite
            Re-download files that already exist locally.
        verbose
            Show overall progress bar.

        Returns
        -------
        list[Path]
            Local paths of downloaded files (in the same order as
            ``self.objects``).
        """
        results: dict[int, Path] = {}
        errors: dict[int, Exception] = {}

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
                f"[cyan]FastHerbie {self.model_cls.MODEL_NAME} "
                f"({'subset' if search else 'full'})",
                total=len(self.objects),
            )

            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                futures = {
                    pool.submit(
                        obj.download, search, overwrite=overwrite, verbose=False
                    ): i
                    for i, obj in enumerate(self.objects)
                }
                for future in as_completed(futures):
                    i = futures[future]
                    try:
                        results[i] = future.result()
                    except Exception as exc:
                        errors[i] = exc
                    progress.update(task, advance=1)

        if errors:
            console.print(f"[yellow]⚠ {len(errors)} download(s) failed:[/yellow]")
            for i, exc in errors.items():
                console.print(f"  [{i}] {self.objects[i]!r}: [red]{exc}[/red]")

        return [results.get(i) for i in range(len(self.objects))]

    def xarray(
        self,
        search: str | None = None,
        *,
        max_workers: int = 5,
        overwrite: bool = False,
        remove_grib: bool = True,
    ):
        """
        Download and open all objects as xarray Datasets.

        Datasets are returned in the same order as ``self.objects``.
        Uses ``xarray.concat`` along the ``time`` dimension when all
        datasets share the same variables and grid.

        Parameters
        ----------
        search
            Inventory filter.
        max_workers
            Concurrent download workers.
        overwrite
            Re-download existing files.
        remove_grib
            Remove temporary subset files after loading.

        Returns
        -------
        xr.Dataset or list[xr.Dataset]
            Single concatenated dataset if merge succeeds; otherwise a
            list of datasets.
        """
        import xarray as xr

        # Download first
        self.download(search, max_workers=max_workers, overwrite=overwrite)

        datasets = []
        for obj in self.objects:
            try:
                ds = obj.xarray(search, remove_grib=remove_grib)
                datasets.append(ds)
            except Exception as exc:
                console.print(f"[yellow]⚠ xarray failed for {obj!r}: {exc}[/yellow]")
                datasets.append(None)

        # Filter out None
        valid = [d for d in datasets if d is not None]
        if not valid:
            return datasets

        # Attempt concatenation
        try:
            return xr.concat(valid, dim="time")
        except Exception:
            return datasets

    def inventory(
        self,
        search: str | None = None,
    ):
        """
        Return inventory DataFrames for all objects as a single Polars DataFrame.

        A ``model_init_time`` column is added to identify each object's
        initialization time.

        Parameters
        ----------
        search
            Inventory filter applied to each object's index.
        """
        import polars as pl

        frames = []
        for obj in self.objects:
            try:
                df = obj.inventory(search)
                df = df.with_columns(
                    pl.lit(obj.date).cast(pl.Datetime).alias("model_init_time"),
                    pl.lit(obj.fxx).alias("fxx"),
                )
                frames.append(df)
            except Exception as exc:
                console.print(f"[yellow]⚠ inventory failed for {obj!r}: {exc}[/yellow]")

        if not frames:
            return pl.DataFrame()
        return pl.concat(frames, how="diagonal")
