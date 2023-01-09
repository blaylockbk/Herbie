# MIT License
# (c) 2023 Andreas Motl <andreas.motl@panodata.org>
# https://github.com/earthobservations
import logging

import fsspec
import numpy as np
import platformdirs
import s3fs
import xarray as xr

logger = logging.getLogger(__name__)


CACHE_BASEDIR = platformdirs.user_cache_path("herbie").joinpath("index-download")


def open_era5_zarr(parameter, year, month, datestart, dateend) -> xr.Dataset:
    """
    Load "ERA5 forecasts reanalysis" data from ECMWF, using Zarr.
    The ERA5 HRES atmospheric data has a resolution of 31km, 0.28125 degrees [1].

    The implementation is derived from ironArray's "Slicing Datasets and Creating
    Views" documentation [2]. For processing data more efficiently, downloaded data
    is cached locally, using fsspec's "filecache" filesystem [3].

    [1] https://confluence.ecmwf.int/display/CKB/ERA5%3A+data+documentation#heading-Spatialgrid
    [2] https://ironarray.io/docs/html/tutorials/03.Slicing_Datasets_and_Creating_Views.html
    [3] https://filesystem-spec.readthedocs.io/en/latest/features.html#caching-files-locally
    """
    location = f"era5-pds/zarr/{year}/{month:02d}/data/{parameter}.zarr/"
    logger.info(f"Loading NWP data from {location}")
    logger.info(f"Using local cache at {CACHE_BASEDIR}")

    # ERA5 is on AWS S3, it can be accessed anonymously.
    fs = s3fs.S3FileSystem(anon=True)

    # Add local cache, using fsspec fame.
    fs = fsspec.filesystem("filecache", cache_storage=str(CACHE_BASEDIR), fs=fs)

    # Access resource in Zarr format.
    # Possible engines: ['scipy', 'cfgrib', 'gini', 'store', 'zarr']
    s3map = s3fs.S3Map(location, s3=fs)
    ds = xr.open_dataset(s3map, engine="zarr")

    # The name of the `time` coordinate differs between datasets.
    time_field_candidates = ["time0", "time1"]
    for candidate in time_field_candidates:
        if candidate in ds.coords:
            time_field = candidate

    # Select subset of data based on time range.
    indexers = {time_field: slice(np.datetime64(datestart), np.datetime64(dateend))}
    ds = ds.sel(indexers=indexers)

    # Rearrange coordinates data from longitude 0 to 360 degrees (long3) to -180 to 180 degrees (long1).
    ds = ds.assign(lon=ds["lon"] - 180)

    return ds
