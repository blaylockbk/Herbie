"""GFS and related NOAA global model templates for Herbie v2."""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from herbie.v2._base import HerbieModel
from herbie.v2._sources import GribSource, ZarrCatalogEntry


class GFS(HerbieModel):
    """
    NOAA Global Forecast System (GFS).

    Global model at 0.25°, 0.50°, or 1.00° resolution.  Initialized
    four times daily (00, 06, 12, 18 UTC) with forecasts to 384 h.

    Parameters
    ----------
    date : str or datetime
        Model initialization datetime (UTC).
    step : int or str, default 0
        Forecast lead time in hours (0–384).
    product : {'pgrb2', 'pgrb2b'}, default 'pgrb2'
        Output product:

        ``'pgrb2'``
            Common fields on pressure levels (~220 variables).
        ``'pgrb2b'``
            Less-common (supplemental) fields.

        Aliases: ``common→pgrb2``, ``uncommon→pgrb2b``.
    resolution : {0.25, 0.5, 1.0}, default 0.25
        Horizontal grid spacing in degrees.
    priority : list of str, optional
        Source priority.  Default: aws → google → nomads → azure → ncar_rda.

    Examples
    --------
    >>> from herbie.v2 import GFS
    >>> H = GFS("2024-01-01", step=24)
    >>> H.inventory("TMP:500 mb")
    >>> ds = H.xarray("TMP:500 mb")

    References
    ----------
    * https://www.nco.ncep.noaa.gov/pmb/products/gfs/
    * https://registry.opendata.aws/noaa-gfs-bdp-pds/
    """

    MODEL_NAME = "GFS"
    MODEL_DESCRIPTION = "NOAA Global Forecast System"
    MODEL_WEBSITES = {
        "NOMADS": "https://www.nco.ncep.noaa.gov/pmb/products/gfs/",
        "AWS": "https://registry.opendata.aws/noaa-gfs-bdp-pds/",
        "Google": "https://console.cloud.google.com/marketplace/product/noaa-public/gfs",
        "Azure": "https://microsoft.github.io/AIforEarthDataSets/data/noaa-gfs.html",
        "NCAR RDA": "https://rda.ucar.edu/datasets/d084001/",
    }

    PARAMS = {
        "product": {
            "default": "pgrb2",
            "valid": ["pgrb2", "pgrb2b"],
            "aliases": {"common": "pgrb2", "uncommon": "pgrb2b"},
            "descriptions": {
                "pgrb2": "Common pressure-level fields; 0.25° resolution",
                "pgrb2b": "Supplemental pressure-level fields; 0.25° resolution",
            },
        },
        "resolution": {
            "default": 0.25,
            "valid": [0.25, 0.5, 1.0],
            "descriptions": {
                0.25: "Quarter-degree (~28 km)",
                0.5: "Half-degree (~56 km)",
                1.0: "One-degree (~111 km)",
            },
        },
    }

    ZARR_SOURCES: ClassVar[dict] = {
        # ── dynamical.org ──────────────────────────────────────────────────
        # Continuous rolling archives. No date/step needed; slice with .sel().
        # Coverage: 2021-05-01 to present.
        # Requires: xarray>=2025.1.2, zarr>=3.0.8
        # Spatial dims are latitude/longitude (regular lat-lon grid, not projected).
        ("dynamical", "analysis"): ZarrCatalogEntry(
            url="https://data.dynamical.org/noaa/gfs/analysis/latest.zarr",
            description=(
                "dynamical.org GFS analysis | 2021–present | 1-hr | "
                "dims: time × latitude × longitude"
            ),
            time_dim="time",
            lead_time_dim=None,
            open_kwargs={"chunks": "auto"},
        ),
        ("dynamical", "forecast"): ZarrCatalogEntry(
            url="https://data.dynamical.org/noaa/gfs/forecast/latest.zarr",
            description=(
                "dynamical.org GFS forecast | 2021–present | 00/06/12/18Z | "
                "0–384 h lead | dims: init_time × lead_time × latitude × longitude"
            ),
            time_dim="init_time",
            lead_time_dim="lead_time",
            open_kwargs={"chunks": "auto"},
        ),
    }

    def _build_sources(self) -> dict:
        d = self.date
        step = self.step
        product = self.params["product"]
        res = self.params["resolution"]
        res_str = f"{res:.2f}".replace(".", "p")  # 0.25 → "0p25"

        # GFS v16.0 layout change on 2021-03-23
        if d < datetime(2021, 3, 23):
            path = f"gfs.{d:%Y%m%d/%H}/gfs.t{d:%H}z.{product}.{res_str}.f{step:03d}"
        else:
            path = (
                f"gfs.{d:%Y%m%d/%H}/atmos/gfs.t{d:%H}z.{product}.{res_str}.f{step:03d}"
            )

        idx = [".idx", ".grb2.inv"]
        return {
            "aws": GribSource(f"https://noaa-gfs-bdp-pds.s3.amazonaws.com/{path}", idx),
            "google": GribSource(
                f"https://storage.googleapis.com/global-forecast-system/{path}", idx
            ),
            "nomads": GribSource(
                f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/{path}", idx
            ),
            "azure": GribSource(
                f"https://noaagfs.blob.core.windows.net/gfs/{path}", idx
            ),
            "ncar_rda": GribSource(
                f"https://data.rda.ucar.edu/d084001/{d:%Y/%Y%m%d}"
                f"/gfs.0p25.{d:%Y%m%d%H}.f{step:03d}.grib2",
                [".idx"],
            ),
        }


class GDAS(HerbieModel):
    """
    NOAA Global Data Assimilation System (GDAS).

    Analysis / short-range forecasts from the GFS data-assimilation
    cycle.  Initialized four times daily (00, 06, 12, 18 UTC).

    Parameters
    ----------
    date : str or datetime
        Model initialization datetime (UTC).
    step : int or str, default 0
        Forecast lead time in hours (0–9).
    product : {'pgrb2.0p25', 'pgrb2.1p00'}, default 'pgrb2.0p25'
        Output product and resolution.

    References
    ----------
    * https://www.nco.ncep.noaa.gov/pmb/products/gfs/#GDAS
    """

    MODEL_NAME = "GDAS"
    MODEL_DESCRIPTION = "NOAA Global Data Assimilation System"
    MODEL_WEBSITES = {
        "NOMADS": "https://www.nco.ncep.noaa.gov/pmb/products/gfs/#GDAS",
    }

    PARAMS = {
        "product": {
            "default": "pgrb2.0p25",
            "valid": ["pgrb2.0p25", "pgrb2.1p00"],
        },
    }

    def _build_sources(self) -> dict:
        d = self.date
        step = self.step
        product = self.params["product"]

        if d < datetime(2021, 3, 23):
            path = f"gdas.{d:%Y%m%d/%H}/gdas.t{d:%H}z.{product}.f{step:03d}"
        else:
            path = f"gdas.{d:%Y%m%d/%H}/atmos/gdas.t{d:%H}z.{product}.f{step:03d}"

        idx = [".idx"]
        return {
            "aws": GribSource(f"https://noaa-gfs-bdp-pds.s3.amazonaws.com/{path}", idx),
            "google": GribSource(
                f"https://storage.googleapis.com/global-forecast-system/{path}", idx
            ),
            "nomads": GribSource(
                f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/{path}", idx
            ),
            "azure": GribSource(
                f"https://noaagfs.blob.core.windows.net/gfs/{path}", idx
            ),
        }


class GFSWave(HerbieModel):
    """
    NOAA GFS Wave Products.

    Available since GFS v16.0 (2021-03-22).

    Parameters
    ----------
    date : str or datetime
        Model initialization datetime (UTC).
    step : int, default 0
        Forecast lead time in hours (0–384).
    product : str, default 'global.0p25'
        Wave grid domain and resolution.  Options include
        ``'global.0p25'``, ``'global.0p16'``, ``'arctic.9km'``,
        ``'atlocn.0p16'``, ``'epacif.0p16'``, ``'wcoast.0p16'``.
    """

    MODEL_NAME = "GFSWave"
    MODEL_DESCRIPTION = "NOAA GFS Wave Products"
    MODEL_WEBSITES = {
        "NOMADS": "https://www.nco.ncep.noaa.gov/pmb/products/gfs/#GFSwave",
    }

    PARAMS = {
        "product": {
            "default": "global.0p25",
            "valid": [
                "arctic.9km",
                "atlocn.0p16",
                "epacif.0p16",
                "global.0p16",
                "global.0p25",
                "gsouth.0p25",
                "wcoast.0p16",
            ],
        },
    }

    def _build_sources(self) -> dict:
        d = self.date
        step = self.step
        product = self.params["product"]

        path = (
            f"gfs.{d:%Y%m%d/%H}/wave/gridded/"
            f"gfswave.t{d:%H}z.{product}.f{step:03d}.grib2"
        )
        idx = [".idx"]
        return {
            "aws": GribSource(f"https://noaa-gfs-bdp-pds.s3.amazonaws.com/{path}", idx),
            "nomads": GribSource(
                f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/{path}", idx
            ),
            "google": GribSource(
                f"https://storage.googleapis.com/global-forecast-system/{path}", idx
            ),
        }
