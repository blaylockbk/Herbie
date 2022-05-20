## Brian Blaylock
## May 3, 2021

"""
============
Herbie Tools
============
"""
from datetime import datetime, timedelta

import logging
import os
import cartopy.crs as ccrs
import metpy  # accessor needed to parse crs
import numpy as np
import pandas as pd
import xarray as xr

from herbie.archive import Herbie, wgrib2_idx_to_str
from . import Path

# Multithreading :)
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed, wait

log = logging.getLogger(__name__)


"""
🧵 Notice! Multithreading is use

This is my first implementation of multithreading to create, download,
and read many Herbie objects. This drastically reduces the time it takes
to create a Herbie object (which is just looking for if and where a
GRIB2 file exists on the internet) and to download a file.
"""


def _validate_fxx(fxx):
    """Fast Herbie requires fxx as a list-like"""
    if isinstance(fxx, int):
        fxx = [fxx]

    if not isinstance(fxx, (list, range)):
        raise ValueError(f"fxx must be an int, list, or range. Gave {fxx}")

    return fxx


def _validate_DATES(DATES):
    """Fast Herbie requires DATES as a list-like"""
    if isinstance(DATES, str):
        DATES = [pd.to_datetime(DATES)]
    elif not hasattr(DATES, "__len__"):
        DATES = [pd.to_datetime(DATES)]

    if not isinstance(DATES, (list, pd.DatetimeIndex)):
        raise ValueError(
            f"DATES must be a pandas-parsable datetime string or a list. Gave {DATES}"
        )

    return DATES


def fast_Herbie(DATES, fxx=[0], *, max_threads=50, **kwargs):
    """
    Create many Herbie objects with Multithreading.

    .. note::
        Currently, Herbie objects looped by run datetime (date)
        and forecast lead time (fxx).

    Parameters
    ----------
    DATES : pandas-parsable datetime string or list of datetimes
    fxx : int or list of forecast lead times
    max_threads : int
        Maximum number of threads to use.
    kwargs :
        Remaining keywords for Herbie object
        (e.g., model, product, priority, verbose, etc.)

    Benchmark
    ---------
    Creating 48 Herbie objects
        - 1 thread took 16 s
        - 2 threads took 8 s
        - 5 threads took 3.3 s
        - 10 threads took 1.7 s
        - 50 threads took 0.5 s
    """
    DATES = _validate_DATES(DATES)
    fxx = _validate_fxx(fxx)

    kwargs.setdefault("verbose", False)

    ################
    # Multithreading
    tasks = len(DATES) * len(fxx)
    threads = min(tasks, max_threads)
    log.info(f"🧵 Working on {tasks} tasks with {threads} threads.")

    with ThreadPoolExecutor(threads) as exe:
        futures = [
            exe.submit(Herbie, date=DATE, fxx=f, **kwargs)
            for DATE in DATES
            for f in fxx
        ]

        # Return list of Herbie objects in order completed
        H_list = [future.result() for future in as_completed(futures)]

        # Return list of Herbie objects in order submitted
        # futures, _ = wait(futures)
        # H_list = [future.result() for future in futures]

    log.info(f"Number of Herbie objects: {len(H_list)}")

    # Sort the list of Herbie objects by lead time then by date
    H_list.sort(key=lambda H: H.fxx)
    H_list.sort(key=lambda H: H.date)

    return H_list


def fast_Herbie_download(
    DATES,
    *,
    searchString=None,
    fxx=[0],
    max_threads=20,
    download_kw={},
    **kwargs,
):
    """
    Use multithreading to download many Herbie objects

    Benchmark
    ---------
    Downloading 48 files with 1 variable (TMP:2 m)
        - 1 thread took 1 min 17 s
        - 2 threads took 36 s
        - 5 threads took 28 s
        - 10 threads took 25 s
        - 50 threads took 23 s
    """
    DATES = _validate_DATES(DATES)
    fxx = _validate_fxx(fxx)

    kwargs.setdefault("verbose", False)

    Hs = fast_Herbie(DATES, fxx=fxx, max_threads=max_threads, **kwargs)

    passed = [H for H in Hs if H.grib is not None]
    failed = [H for H in Hs if H.grib is None]

    ###########################
    # Multithread the downloads
    tasks = len(DATES) * len(fxx)
    threads = min(tasks, max_threads)
    log.info(f"🧵 Working on {tasks} tasks with {threads} threads.")

    with ThreadPoolExecutor(max_threads) as exe:
        futures = [exe.submit(H.download, searchString, **download_kw) for H in passed]

        # Return list of Herbie objects in order completed
        _ = [future.result() for future in as_completed(futures)]

    if len(failed):
        log.warning(
            f"Herbie only download {len(passed)}/{len(Hs)} files. ({len(failed)} had no GRIB2 file)."
        )

    return dict(passed=passed, failed=failed)


def fast_Herbie_xarray(
    DATES,
    *,
    searchString=None,
    fxx=[0],
    max_threads=5,
    xarray_kw={},
    **kwargs,
):
    """
    Use multithreading to download many Herbie objects

    Parameters
    ----------
    max_threads : int
        Control the maximum number of threads to use.
        If you use too many threads, you may run into memory limits.

    Benchmark
    ---------
    Opening 48 files with 1 variable (TMP:2 m)
        - 1 thread took 1 min 45 s
        - 2 threads took 55 s
        - 5 threads took 39 s
        - 10 threads took 39 s
        - 50 threads took 37 s
    """
    DATES = _validate_DATES(DATES)
    fxx = _validate_fxx(fxx)

    kwargs.setdefault("verbose", False)

    Hs = fast_Herbie(DATES, fxx=fxx, max_threads=max_threads, **kwargs)

    passed = [H for H in Hs if H.grib is not None]
    failed = [H for H in Hs if H.grib is None]

    ###########################
    # Multithread the downloads
    tasks = len(DATES) * len(fxx)
    threads = min(tasks, max_threads)
    log.info(f"🧵 Working on {tasks} tasks with {threads} threads.")

    with ThreadPoolExecutor(max_threads) as exe:
        futures = [exe.submit(H.xarray, searchString, **xarray_kw) for H in passed]

        # Return list of Herbie objects in order completed
        ds_list = [future.result() for future in as_completed(futures)]

    # Sort the DataSets, first by lead time (step), then by run time (time)
    ds_list.sort(key=lambda x: x.step.data.max())
    ds_list.sort(key=lambda x: x.time.data.max())

    # Reshape list with dimensions (len(DATES), len(fxx))
    ds_list = [ds_list[x : x + len(fxx)] for x in range(0, len(ds_list), len(fxx))]

    # Concat DataSets
    try:
        ds = xr.combine_nested(
            ds_list,
            concat_dim=["time", "step"],
            combine_attrs="drop_conflicts",
        )
    except:
        # TODO: I'm not sure why some cases doesn't like the combine_attrs argument
        ds = xr.combine_nested(
            ds_list,
            concat_dim=["time", "step"],
        )

    ds["gribfile_projection"] = ds.gribfile_projection[0][0]
    ds = ds.squeeze()

    if len(failed):
        log.warning(
            f"Herbie only retrieved {len(passed)}/{len(Hs)} files. ({len(failed)} had no GRIB2 file)."
        )

    return ds


########################################################################
########################################################################


def create_index_files(path, overwrite=False):
    """Create an index file for all GRIB2 files in a directory.

    # TODO: use Path().expand()

    Parameters
    ----------
    path : str or pathlib.Path
        Path to directory or file.
    overwrite : bool
        Overwrite index file if it exists.
    """
    path = Path(path)
    files = []
    if path.is_dir():
        # List all GRIB2 files in the directory
        files = list(path.rglob("*.grib2*"))
    elif path.is_file():
        # The path is a single file
        files = [path]

    if not files:
        raise ValueError(f"No grib2 files were found in {path}")

    for f in files:
        f_idx = Path(str(f) + ".idx")
        if not f_idx.exists() or overwrite:
            # Create an index using wgrib2's simple inventory option
            # if it doesn't already exist or if overwrite is True.
            index_data = wgrib2_idx_to_str(Path(f))
            with open(f_idx, "w+") as out_idx:
                out_idx.write(index_data)


########################################################################
########################################################################
# ! Old


def bulk_download(DATES, searchString=None, *, fxx=range(0, 1), verbose=True, **kwargs):
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
    log.warning("`bulk_download` is depreciated. Use `fast_Herbie_download` instead")

    if isinstance(DATES, (str, pd.Timestamp)) or hasattr(DATES, "strptime"):
        DATES = [DATES]
    if isinstance(fxx, int):
        fxx = [fxx]

    # Locate the file sources
    print("👨🏻‍🔬 Check which requested files exists")
    grib_sources = fast_Herbie(DATES, fxx, **kwargs)

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
    completed = sum([i.grib is not None for i in grib_sources])
    print(f"🍦 Done! Downloaded [{completed}/{requested}] files. Timer={loop_time}")

    return dict(success=success, failed=failed)


def xr_concat_sameRun(DATE, searchString, fxx=range(0, 18), verbose=False, **kwargs):
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
    log.warning("`xr_concat_sameRun` is depreciated. Use `fast_Herbie_xarray` instead")
    Hs = fast_Herbie(DATE, fxx, **kwargs)

    Hs_to_cat = [H.xarray(searchString, verbose=verbose) for H in Hs]
    return xr.concat(Hs_to_cat, dim="f")


def xr_concat_sameLead(DATES, searchString, fxx=0, verbose=False, **kwargs):
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
    log.warning("`xr_concat_sameLead` is depreciated. Use `fast_Herbie_xarray` instead")
    Hs = fast_Herbie(DATES, fxx, **kwargs)
    Hs_to_cat = [H.xarray(searchString, verbose=verbose) for H in Hs]
    return xr.concat(Hs_to_cat, dim="t")


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
    log.warning(
        "Depreciated:  `nearest_points` is now a herbie accessor. Use `ds.herbie.nearest_points()`"
    )

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
