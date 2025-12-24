"""Load GRIB2 data into xarray."""

# TODO: Add coordinate reference system attributes.

def load_grib2_into_xarray(local_file, backend_kwargs: dict = {}):
    """Load GRIB2 data into xarray."""
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

    Hxr = cfgrib.open_datasets(
        local_file,
        backend_kwargs=backend_kwargs,
        decode_timedelta=True,
    )

    if len(Hxr) == 1:
        return Hxr[0]
    else:
        return xr.DataTree.from_dict({f"node{i}": ds for i, ds in enumerate(Hxr)})
