"""New Herbie Core."""

import functools
from pathlib import Path

import polars as pl

from herbie import Herbie

from ._common import logger
from .download import download_grib2_from_dataframe
from .inventory import (
    DownloadGroupDataFrame,
    InventoryDataFrame,
    create_download_groups,
    read_index_file,
)


class NewHerbie(Herbie):
    """New Herbie Class."""

    @functools.cached_property
    def index_as_dataframe(self) -> InventoryDataFrame:
        """Read and cache an index file."""
        if self.idx is None:
            raise ValueError(f"No index file found for {self.grib}.")

        return read_index_file(str(self.idx)).insert_column(
            1, pl.lit(str(self.grib)).alias("grib_source")
        )

    def inventory(
        self, filters: pl.Expr | list[pl.Expr] | None = None
    ) -> InventoryDataFrame:
        """Return the inventory of the GRIB2 file."""
        df = self.index_as_dataframe
        if filters is not None:
            df = df.filter(filters)
            logger.debug(f"Filtered DataFrame to {len(df):,} fields.")
        return df

    def get_download_groups(
        self, filters: pl.Expr | list[pl.Expr] | None = None
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
            output_file = self.get_localFilePath()

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
        filters: pl.Expr | list[pl.Expr] | None = None,
        *,
        backend_kwargs: dict = {},
    ):
        """Load data into xarray."""
        import cfgrib
        import xarray as xr

        # Backend kwargs for cfgrib
        backend_kwargs.setdefault("indexpath", "")
        backend_kwargs.setdefault(
            "read_keys",
            [
                "parameterName",
                "parameterUnits",
                "stepRange",
                "uvRelativeToGrid",
                "shapeOfTheEarth",
                "orientationOfTheGridInDegrees",
                "southPoleOnProjectionPlane",
                "LaDInDegrees",
                "LoVInDegrees",
                "Latin1InDegrees",
                "Latin2InDegrees",
            ],
        )
        backend_kwargs.setdefault("errors", "raise")

        local_file = self.download(filters)

        Hxr = cfgrib.open_datasets(
            local_file,
            backend_kwargs=backend_kwargs,
            decode_timedelta=True,
        )

        if len(Hxr) == 1:
            return Hxr[0]
        else:
            return xr.DataTree.from_dict({f"node{i}": ds for i, ds in enumerate(Hxr)})
