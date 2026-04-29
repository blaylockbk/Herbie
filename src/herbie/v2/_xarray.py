"""
xarray loading for Herbie v2.

Dispatches on source type:
  GribSource / EccodesGribSource  →  cfgrib
  ZarrSource                      →  xarray.open_zarr
  DirectorySource                 →  cfgrib (after downloading matching files)

Public API
----------
load_xarray(local_file, *, backend_kwargs) → xr.Dataset | list[xr.Dataset]
open_zarr(source) → xr.Dataset
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import xarray as xr

if TYPE_CHECKING:
    from herbie.v2._sources import ZarrSource


_CFGRIB_READ_KEYS = [
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
]


def load_xarray(
    local_file: Path,
    *,
    backend_kwargs: dict | None = None,
) -> xr.Dataset | list[xr.Dataset]:
    """
    Open a local GRIB2 file (or subset file) with cfgrib.

    Returns a single ``xr.Dataset`` when cfgrib produces one hypercube,
    or a list when multiple are produced (e.g. HRRR subhourly).
    """
    import cfgrib

    bk = dict(backend_kwargs or {})
    bk.setdefault("indexpath", "")
    bk.setdefault("read_keys", _CFGRIB_READ_KEYS)
    bk.setdefault("errors", "raise")

    datasets = cfgrib.open_datasets(
        local_file,
        backend_kwargs=bk,
        decode_timedelta=True,
    )

    # Attach CF grid mapping
    for ds in datasets:
        _attach_crs(ds)

    if len(datasets) == 1:
        return datasets[0]

    # Try to merge multiple hypercubes (e.g. subhourly)
    try:
        import itertools

        data_vars = set(itertools.chain(*[list(ds) for ds in datasets]))
        data_vars.discard("gribfile_projection")
        merged = xr.concat(datasets, dim="step", data_vars=list(data_vars))
        return merged
    except Exception:
        return datasets


def _attach_crs(ds: xr.Dataset) -> None:
    """Attach a ``gribfile_projection`` coordinate with CF grid mapping attrs."""
    try:
        cf_params = _get_cf_crs(ds)
    except Exception:
        cf_params = {}

    ds.coords["gribfile_projection"] = None
    ds.coords["gribfile_projection"].attrs = cf_params

    for var in list(ds):
        ds[var].attrs.setdefault("grid_mapping", "gribfile_projection")


def _get_cf_crs(ds: xr.Dataset) -> dict:
    """Extract CF grid-mapping attributes from cfgrib-decoded keys."""
    # Pick the first data variable that has grid-mapping GRIB keys
    for var in ds.data_vars:
        da = ds[var]
        name = da.attrs.get("GRIB_gridType", "")
        if name == "lambert":
            return {
                "grid_mapping_name": "lambert_conformal_conic",
                "standard_parallel": [
                    da.attrs.get("GRIB_Latin1InDegrees"),
                    da.attrs.get("GRIB_Latin2InDegrees"),
                ],
                "longitude_of_central_meridian": da.attrs.get("GRIB_LoVInDegrees"),
                "latitude_of_projection_origin": da.attrs.get("GRIB_LaDInDegrees"),
                "semi_major_axis": 6371229.0,
                "semi_minor_axis": 6371229.0,
            }
        elif name == "polar_stereographic":
            return {
                "grid_mapping_name": "polar_stereographic",
                "straight_vertical_longitude_from_pole": da.attrs.get(
                    "GRIB_orientationOfTheGridInDegrees"
                ),
                "latitude_of_projection_origin": 90.0,
                "semi_major_axis": 6371229.0,
                "semi_minor_axis": 6371229.0,
            }
        elif name in ("regular_ll", "regular_gg"):
            return {"grid_mapping_name": "latitude_longitude"}
    return {}


def open_zarr(source: ZarrSource) -> xr.Dataset:
    """Open a ZarrSource as an xarray Dataset."""
    return xr.open_zarr(
        source.url,
        consolidated=source.consolidated,
        storage_options=source.storage_options or None,
        **source.open_kwargs,
    )

def open_zarr_catalog(
    entry: "ZarrCatalogEntry",
    **extra_kwargs,
) -> xr.Dataset:
    """
    Open a ``ZarrCatalogEntry`` as an ``xr.Dataset``.

    If the entry has a ``store_factory``, it is called with ``extra_kwargs``
    (e.g. ``date=``, ``variable=``, ``level=``).  If the factory returns an
    ``xr.Dataset`` it is handed back directly; otherwise its return value is
    treated as a zarr store and passed to ``xr.open_zarr``.

    Any remaining ``extra_kwargs`` that are not consumed by the factory are
    merged into the entry's ``open_kwargs`` and forwarded to ``xr.open_zarr``.
    """
    if entry.store_factory is not None:
        result = entry.store_factory(**extra_kwargs)
        if isinstance(result, xr.Dataset):
            return result
        # Factory returned a store object — open it
        return xr.open_zarr(
            result,
            consolidated=entry.consolidated,
            storage_options=entry.storage_options or None,
            **{**entry.open_kwargs, **extra_kwargs},
        )

    return xr.open_zarr(
        entry.url,
        consolidated=entry.consolidated,
        storage_options=entry.storage_options or None,
        **{**entry.open_kwargs, **extra_kwargs},
    )
