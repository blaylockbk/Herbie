## Brian Blaylock
## May 3, 2021

"""
============
Herbie Tools
============
"""
from datetime import datetime, timedelta

import cartopy.crs as ccrs
import metpy
import numpy as np
import pandas as pd
import xarray as xr

from herbie.archive import Herbie


def bulk_download(
    DATES,
    searchString=None,
    *,
    fxx=range(0, 1),
    model="hrrr",
    product="sfc",
    priority=None,
    verbose=True,
):
    """
    Bulk download GRIB2 files from file source to the local machine.

    Iterates over a list of datetimes (DATES) and forecast lead times (fxx).

    Parameters
    ----------
    DATES : list
        List of datetimes
    searchString : None or str
        If None, download the full file. If string, use regex to search
        index files for variables and levels of interest and only
        download the matched GRIB messages.
    fxx : int or list
        List of forecast lead times to download. Default only downloads model analysis.
    model : {'hrrr', 'hrrrak', 'rap'}
        Model to download.
    product : {'sfc', 'prs', 'nat', 'subh'}
        Variable products file to download. Not needed for RAP model.
    """
    if isinstance(DATES, (str, pd.Timestamp)) or hasattr(DATES, "strptime"):
        DATES = [DATES]
    if isinstance(fxx, int):
        fxx = [fxx]

    kw = dict(model=model, product=product)
    if priority is not None:
        kw["priority"] = priority

    # Locate the file sources
    print("👨🏻‍🔬 Check which requested files exists")
    grib_sources = [Herbie(d, fxx=f, **kw) for d in DATES for f in fxx]

    # Keep a list of successful and failed Herbie objects
    success = []
    failed = []

    loop_time = timedelta()
    n = len(grib_sources)

    print("\n🌧 Download requested data")
    for i, H in enumerate(grib_sources):
        try:
            timer = datetime.now()
            H.download(searchString=searchString)

            # ---------------------------------------------------------
            # Time keeping: *crude* method to estimate remaining time.
            # ---------------------------------------------------------
            loop_time += datetime.now() - timer
            mean_dt_per_loop = loop_time / (i + 1)
            remaining_loops = n - i - 1
            est_rem_time = mean_dt_per_loop * remaining_loops

            success.append(H)
        except Exception as e:
            print(f"WARNING: {e}")
            failed.append(H)
        if verbose:
            print(
                f"🚛💨 Download Progress: [{i+1}/{n} completed] >> Est. Time Remaining {str(est_rem_time):16}\n"
            )
        # ---------------------------------------------------------

    requested = len(grib_sources)
    completed = sum([i.grib is None for i in grib_sources])
    print(f"🍦 Done! Downloaded [{completed}/{requested}] files. Timer={loop_time}")

    return dict(success=success, failed=failed)


def xr_concat_sameRun(DATE, searchString, fxx=range(0, 18), **kwargs):
    """
    Load and concatenate xarray objects by forecast lead time for the same run.

    Parameters
    ----------
    DATE : pandas-parsable datetime
        A datetime that represents the model initialization time.
    searchString : str
        Variable fields to load. This really only works if the search
        string returns data on the same hyper cube.
    fxx : list of int
        List of forecast lead times, in hours, to concat together.
    """
    Hs_to_cat = [Herbie(DATE, fxx=f, **kwargs).xarray(searchString) for f in fxx]
    return xr.concat(Hs_to_cat, dim="f")


def xr_concat_sameLead(DATES, searchString, fxx=0, DATE_is_valid_time=True, **kwargs):
    """
    Load and concatenate xarray objects by model initialization date for the same lead time.

    Parameters
    ----------
    DATES : list of pandas-parsable datetime
        Datetime that represents the model valid time.
    searchString : str
        Variable fields to load. This really only works if the search
        string returns data on the same hyper cube.
    fxx : int
        The forecast lead time, in hours.
    """
    Hs_to_cat = [
        Herbie(DATE, fxx=fxx, DATE_is_valid_time=DATE_is_valid_time, **kwargs).xarray(
            searchString
        )
        for DATE in DATES
    ]
    return xr.concat(Hs_to_cat, dim="t")


# TODO: Probably should implement this as an accessor instead of a "tool".
def nearest_points(ds, points, names=None, verbose=True):
    """
    Get the nearest latitude/longitude points from a xarray Dataset.

    This is **much** faster than my old "pluck_points" method. For
    matchign 1,948 points,
    - `nearest_points` completed in 7.5 seconds.
    - `pluck_points` completed in 2 minutes.

    Info
    ----
    - Stack Overflow: https://stackoverflow.com/questions/58758480/xarray-select-nearest-lat-lon-with-multi-dimension-coordinates
    - MetPy Details: https://unidata.github.io/MetPy/latest/tutorials/xarray_tutorial.html?highlight=assign_y_x


    Parameters
    ----------
    ds : a friendly xarray Dataset
    points : tuple (lon, lat) or list of tuples
        The longitude and latitude (lon, lat) coordinate pair (as a tuple)
        for the points you want to pluck from the gridded Dataset.
        A list of tuples may be given to return the values from multiple points.
    names : list
        A list of names for each point location (i.e., station name).
        None will not append any names. names should be the same
        length as points.
    """
    # Check if MetPy has already parsed the CF metadata grid projection.
    # Do that if it hasn't been done yet.
    if "metpy_crs" not in ds:
        ds = ds.metpy.parse_cf()

    # Apply the MetPy method `assign_y_x` to the dataset
    # https://unidata.github.io/MetPy/latest/api/generated/metpy.xarray.html?highlight=assign_y_x#metpy.xarray.MetPyDataArrayAccessor.assign_y_x
    ds = ds.metpy.assign_y_x()

    # Convert the requested [(lon,lat), (lon,lat)] points to map projection.
    # Accept a list of point tuples, or Shapely Points object.
    # We want to index the dataset at a single point.
    # We can do this by transforming a lat/lon point to the grid location
    crs = ds.metpy_crs.item().to_cartopy()
    # lat/lon input must be a numpy array, not a list or polygon
    if isinstance(points, tuple):
        # If a tuple is give, turn into a one-item list.
        points = np.array([points])
    if not isinstance(points, np.ndarray):
        # Points must be a 2D numpy array
        points = np.array(points)
    lons = points[:, 0]
    lats = points[:, 1]
    transformed_data = crs.transform_points(ccrs.PlateCarree(), lons, lats)
    xs = transformed_data[:, 0]
    ys = transformed_data[:, 1]

    # Select the nearest points from the projection coordinates.
    # TODO: Is there a better way?
    # There doesn't seem to be a way to get just the points like this
    # ds = ds.sel(x=xs, y=ys, method='nearest')
    # because it gives a 2D array, and not a point-by-point index.
    # Instead, I have too loop the ds.sel method
    new_ds = xr.concat(
        [ds.sel(x=xi, y=yi, method="nearest") for xi, yi in zip(xs, ys)], dim="point"
    )

    # Add list of names as a coordinate
    if names is not None:
        # Assign the point dimension as the names.
        assert len(points) == len(names), "`points` and `names` must be same length."
        new_ds["point"] = names

    return new_ds


# TODO: I like the idea in Salem to mask data by a geographic region
# TODO: Maybe can use that in Herbie. https://github.com/fmaussion/salem
