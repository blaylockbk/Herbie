"""HRRR and HRRRAK model templates for Herbie v2."""

from __future__ import annotations

from datetime import datetime

from herbie.v2._base import HerbieModel
from herbie.v2._sources import GribSource, ZarrCatalogEntry

# ---------------------------------------------------------------------------
# Utah hrrrzarr store factory (per-variable, per-date access pattern)
# ---------------------------------------------------------------------------


def _utah_store(
    date=None,
    product: str = "analysis",
    variable: str = "TMP",
    level: str = "surface",
    **_,
) -> "xr.Dataset":
    """
    Open one variable from the Utah/MesoWest HRRR Zarr PDS bucket.

    The hrrrzarr bucket stores each variable as a separate zarr group; two
    groups must be opened together with ``open_mfdataset``::

        hrrrzarr/sfc/{YYYYMMDD}/{YYYYMMDD}_{HH}z_anl.zarr/{level}/{variable}
        hrrrzarr/sfc/{YYYYMMDD}/{YYYYMMDD}_{HH}z_anl.zarr/{level}/{variable}/{level}

    Parameters
    ----------
    date
        Model initialisation datetime (required).
    product
        ``'analysis'`` (step=0) or ``'forecast'`` (step≥1).
    variable
        GRIB2 short name, e.g. ``'TMP'``, ``'UGRD'``, ``'REFC'``.
    level
        Level type: ``'surface'``, ``'pressure'``, ``'hybrid'``, etc.
    """
    import s3fs
    import xarray as xr
    import pandas as pd

    if date is None:
        raise ValueError("source='utah' requires date= (e.g. date='2021-01-01 00:00').")
    dt = pd.Timestamp(date)
    product_str = "anl" if product == "analysis" else "fcst"
    root = (
        f"hrrrzarr/sfc/{dt:%Y%m%d}/"
        f"{dt:%Y%m%d}_{dt:%H}z_{product_str}.zarr/{level}/{variable}"
    )

    s3 = s3fs.S3FileSystem(anon=True)

    def _map(path: str):
        return s3fs.S3Map(path, s3=s3)

    return xr.open_mfdataset(
        [_map(root), _map(f"{root}/{level}")],
        engine="zarr",
        combine="by_coords",
    )


class HRRR(HerbieModel):
    """
    High-Resolution Rapid Refresh (HRRR) — CONUS.

    NOAA's 3-km hourly convection-allowing model covering the
    contiguous United States.  Initialized every hour; forecasts extend
    to 18 h (48 h for the 00, 06, 12, and 18 UTC cycles).

    Parameters
    ----------
    date : str or datetime
        Model initialization datetime (UTC).
    step : int or str, default 0
        Forecast lead time in hours (``0``–``18`` or ``0``–``48``).
        Pandas-style timedelta strings (``"6h"``) are also accepted.
    product : {'sfc', 'prs', 'nat', 'subh'}, default 'sfc'
        Output product type:

        ``'sfc'``
            2-D surface fields — the most commonly used product.
            ~100 variables, ~3-km horizontal resolution.
        ``'prs'``
            3-D pressure-level fields.
            ~700 variables across 50 pressure levels.
        ``'nat'``
            Native hybrid-sigma-level fields.
        ``'subh'``
            Sub-hourly (15-minute) output (step 00–18 only).

        Aliases: ``surface→sfc``, ``pressure→prs``,
        ``native→nat``, ``subhourly→subh``.
    priority : list of str, optional
        Source priority order.  Default: aws → google → nomads → azure → pando.
    save_dir : str or Path, optional
        Root directory for local file storage.
    overwrite : bool, default False
        Re-download even if a local copy already exists.

    Examples
    --------
    >>> from herbie.v2 import HRRR
    >>> H = HRRR("2024-06-15 18:00", step=6, product="sfc")
    >>> H.inventory("TMP:2 m above ground")
    >>> ds = H.xarray("TMP:2 m above ground")

    References
    ----------
    * https://rapidrefresh.noaa.gov/hrrr/
    * https://www.nco.ncep.noaa.gov/pmb/products/hrrr/
    * https://registry.opendata.aws/noaa-hrrr/
    """

    MODEL_NAME = "HRRR"
    MODEL_DESCRIPTION = "High-Resolution Rapid Refresh — CONUS"
    MODEL_WEBSITES = {
        "GSL": "https://rapidrefresh.noaa.gov/hrrr/",
        "NOMADS": "https://www.nco.ncep.noaa.gov/pmb/products/hrrr/",
        "AWS": "https://registry.opendata.aws/noaa-hrrr/",
        "Utah": "http://hrrr.chpc.utah.edu/",
    }

    PARAMS = {
        "product": {
            "default": "sfc",
            "valid": ["sfc", "prs", "nat", "subh"],
            "aliases": {
                "surface": "sfc",
                "pressure": "prs",
                "native": "nat",
                "subhourly": "subh",
            },
            "descriptions": {
                "sfc": "2D surface-level fields; 3-km resolution",
                "prs": "3D pressure-level fields; 3-km resolution",
                "nat": "Native hybrid-sigma-level fields; 3-km resolution",
                "subh": "Sub-hourly (15-min) fields; 3-km resolution",
            },
        },
    }

    ZARR_SOURCES: ClassVar[dict] = {
        # ── dynamical.org ──────────────────────────────────────────────────
        # Continuous rolling archives. No date/step needed; slice with .sel().
        # Requires: xarray>=2025.1.2, zarr>=3.0.8
        ("dynamical", "analysis"): ZarrCatalogEntry(
            url="https://data.dynamical.org/noaa/hrrr/analysis/latest.zarr",
            description=(
                "dynamical.org HRRR analysis | 2014–present | 1-hr | dims: time × y × x"
            ),
            time_dim="time",
            lead_time_dim=None,
            open_kwargs={"chunks": "auto"},
        ),
        ("dynamical", "forecast"): ZarrCatalogEntry(
            url="https://data.dynamical.org/noaa/hrrr/forecast-48-hour/latest.zarr",
            description=(
                "dynamical.org HRRR 48-hr forecast | 2018–present | "
                "00/06/12/18Z only | dims: init_time × lead_time × y × x"
            ),
            time_dim="init_time",
            lead_time_dim="lead_time",
            open_kwargs={"chunks": "auto"},
        ),
        # ── Utah / MesoWest hrrrzarr (AWS Open Data) ───────────────────────
        # One zarr group per variable per date. Requires date=, variable=,
        # level= kwargs passed to from_zarr(). Also requires: pip install s3fs
        ("mesowest", "analysis"): ZarrCatalogEntry(
            url="s3://hrrrzarr/sfc/",
            description=(
                "Utah/MesoWest hrrrzarr | 2015–present | per-variable | "
                "pass date=, variable=, level= to from_zarr()"
            ),
            time_dim="time",
            storage_options={"anon": True},
            store_factory=lambda **kw: _utah_store(product="analysis", **kw),
        ),
        ("mesowest", "forecast"): ZarrCatalogEntry(
            url="s3://hrrrzarr/sfc/",
            description=(
                "Utah/MesoWest hrrrzarr | 2015–present | per-variable | "
                "pass date=, variable=, level= to from_zarr()"
            ),
            time_dim="time",
            storage_options={"anon": True},
            store_factory=lambda **kw: _utah_store(product="forecast", **kw),
        ),
    }

    def _build_sources(self) -> dict:
        d = self.date
        step = self.step
        product = self.params["product"]

        path = f"hrrr.{d:%Y%m%d}/conus/hrrr.t{d:%H}z.wrf{product}f{step:02d}.grib2"
        path_pando = (
            f"hrrr/{product}/{d:%Y%m%d}/hrrr.t{d:%H}z.wrf{product}f{step:02d}.grib2"
        )

        idx = [".idx", ".grib2.idx"]
        return {
            "aws": GribSource(
                f"https://noaa-hrrr-bdp-pds.s3.amazonaws.com/{path}", idx
            ),
            "google": GribSource(
                f"https://storage.googleapis.com/high-resolution-rapid-refresh/{path}",
                idx,
            ),
            "nomads": GribSource(
                f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod/{path}", idx
            ),
            "azure": GribSource(
                f"https://noaahrrr.blob.core.windows.net/hrrr/{path}", idx
            ),
            "pando": GribSource(f"https://pando-rgw01.chpc.utah.edu/{path_pando}", idx),
            "pando2": GribSource(
                f"https://pando-rgw02.chpc.utah.edu/{path_pando}", idx
            ),
        }


class HRRRAK(HerbieModel):
    """
    High-Resolution Rapid Refresh — Alaska (HRRR-AK).

    The Alaska domain version of the HRRR, running at 3-km resolution
    over Alaska and surrounding waters.  Initialized every 6 hours
    (00, 06, 12, 18 UTC) with forecasts to 48 h.

    Parameters
    ----------
    date : str or datetime
        Model initialization datetime (UTC).
    step : int or str, default 0
        Forecast lead time in hours (0–48).
    product : {'sfc', 'prs', 'nat', 'subh'}, default 'prs'
        Output product type (same options as HRRR).
    priority : list of str, optional
        Source priority.  Default: nomads → aws → google → azure.

    References
    ----------
    * https://www.nco.ncep.noaa.gov/pmb/products/hrrr/
    """

    MODEL_NAME = "HRRRAK"
    MODEL_DESCRIPTION = "High-Resolution Rapid Refresh — Alaska"
    MODEL_WEBSITES = {
        "NOMADS": "https://www.nco.ncep.noaa.gov/pmb/products/hrrr/",
    }

    PARAMS = {
        "product": {
            "default": "prs",
            "valid": ["sfc", "prs", "nat", "subh"],
            "aliases": {
                "surface": "sfc",
                "pressure": "prs",
                "native": "nat",
                "subhourly": "subh",
            },
        },
    }

    def _build_sources(self) -> dict:
        d = self.date
        step = self.step
        product = self.params["product"]

        path = f"hrrr.{d:%Y%m%d}/alaska/hrrr.t{d:%H}z.wrf{product}f{step:02d}.ak.grib2"
        path_pando = (
            f"hrrr/{product}/{d:%Y%m%d}/hrrr.t{d:%H}z.wrf{product}f{step:02d}.ak.grib2"
        )

        idx = [".idx", ".grib2.idx"]
        return {
            "nomads": GribSource(
                f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod/{path}", idx
            ),
            "aws": GribSource(
                f"https://noaa-hrrr-bdp-pds.s3.amazonaws.com/{path}", idx
            ),
            "google": GribSource(
                f"https://storage.googleapis.com/high-resolution-rapid-refresh/{path}",
                idx,
            ),
            "azure": GribSource(
                f"https://noaahrrr.blob.core.windows.net/hrrr/{path}", idx
            ),
            "pando": GribSource(f"https://pando-rgw01.chpc.utah.edu/{path_pando}", idx),
        }
