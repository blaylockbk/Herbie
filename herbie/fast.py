## Brian Blaylock
## May 3, 2021

"""
============
Herbie Tools
============
"""
from datetime import datetime, timedelta

import logging
import cartopy.crs as ccrs
import metpy  # accessor needed to parse crs
import numpy as np
import pandas as pd
import xarray as xr

from herbie.core import Herbie, wgrib2_idx
from . import Path

# Multithreading :)
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed, wait

log = logging.getLogger(__name__)


"""
🧵🤹🏻‍♂️ Notice! Multithreading and Multiprocessing is use

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


def Herbie_latest(n=6, freq="1H", **kwargs):
    """Search for the most recent GRIB2 file (using multithreading).

    Parameters
    ----------
    n : int
        Number of attempts to try.
    freq : pandas-parsable timedelta string
        Time interval between each attempt.

    Examples
    --------
    When ``n=6``, and ``freq='1H'``, Herbie will look for the latest
    file within the last 6 hours (suitable for the HRRR model).

    When ``n=3``, and ``freq='6H'``, Herbie will look for the latest
    file within the last 18 hours (suitable for the GFS model).
    """
    current = pd.Timestamp.now("utc").tz_localize(None).floor(freq)
    DATES = pd.date_range(
        start=current - (pd.Timedelta(freq) * n),
        end=current,
        freq=freq,
    )
    FH = FastHerbie(DATES, **kwargs)
    return FH.file_exists[-1]


class FastHerbie:
    def __init__(self, DATES, fxx=[0], *, max_threads=50, **kwargs):
        """Create many Herbie objects with methods to download or read with xarray.

        Uses multithreading.

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
        self.DATES = _validate_DATES(DATES)
        self.fxx = _validate_fxx(fxx)

        kwargs.setdefault("verbose", False)

        ################
        # Multithreading
        self.tasks = len(DATES) * len(fxx)
        threads = min(self.tasks, max_threads)
        log.info(f"🧵 Working on {self.tasks} tasks with {threads} threads.")

        self.objects = []
        with ThreadPoolExecutor(threads) as exe:
            futures = [
                exe.submit(Herbie, date=DATE, fxx=f, **kwargs)
                for DATE in DATES
                for f in fxx
            ]

            # Return list of Herbie objects in order completed
            for future in as_completed(futures):
                if future.exception() is None:
                    self.objects.append(future.result())
                else:
                    log.error(f"Exception has occured : {future.exception()}")

        log.info(f"Number of Herbie objects: {len(self.objects)}")

        # Sort the list of Herbie objects by lead time then by date
        self.objects.sort(key=lambda H: H.fxx)
        self.objects.sort(key=lambda H: H.date)

        self.objects = self.objects

        # Which files exist?
        self.file_exists = [H for H in self.objects if H.grib is not None]
        self.file_not_exists = [H for H in self.objects if H.grib is None]

        if len(self.file_not_exists) > 0:
            log.warning(
                f"Could not find {len(self.file_not_exists)}/{len(self.file_exists)} GRIB files."
            )

    def __len__(self):
        return len(self.objects)

    def df(self):
        """Organize Herbie objects into a DataFrame.

        #? Why is this inefficient? Takes several seconds to display because the __str__ does a lot.
        """
        ds_list = [
            self.objects[x : x + len(self.fxx)]
            for x in range(0, len(self.objects), len(self.fxx))
        ]
        return pd.DataFrame(
            ds_list, index=self.DATES, columns=[f"F{i:02d}" for i in self.fxx]
        )

    def inventory(self, searchString=None):
        """Get combined inventory DataFrame.

        Useful for data discovery and checking your searchString before
        doing a download.
        """
        # NOTE: In my quick test, you don't gain much speed using multithreading here.
        dfs = []
        for i in self.file_exists:
            df = i.inventory(searchString)
            df = df.assign(FILE=i.grib)
            dfs.append(df)
        return pd.concat(dfs, ignore_index=True)

    def download(self, searchString=None, *, max_threads=20, **download_kwargs):
        r"""Download many Herbie objects

        Uses multithreading.

        Parameters
        ----------
        searchString : string
            Regular expression string to specify which GRIB messages to
            download.
        **download_kwargs :
            Any kwarg for Herbie's download method.

        Benchmark
        ---------
        Downloading 48 files with 1 variable (TMP:2 m)
            - 1 thread took 1 min 17 s
            - 2 threads took 36 s
            - 5 threads took 28 s
            - 10 threads took 25 s
            - 50 threads took 23 s
        """
        ###########################
        # Multithread the downloads
        threads = min(self.tasks, max_threads)
        log.info(f"🧵 Working on {self.tasks} tasks with {threads} threads.")

        outFiles = []
        with ThreadPoolExecutor(threads) as exe:
            futures = [
                exe.submit(H.download, searchString, **download_kwargs)
                for H in self.file_exists
            ]

            # Return list of Herbie objects in order completed
            for future in as_completed(futures):
                if future.exception() is None:
                    outFiles.append(future.result())
                else:
                    log.error(f"Exception has occured : {future.exception()}")

        return outFiles

    def xarray(
        self,
        searchString,
        *,
        max_threads=None,
        **xarray_kwargs,
    ):
        """Read many Herbie objects into an xarray Dataset

        # TODO: Sometimes the Jupyter Cell always crashes when I run this.
        # TODO: "fatal flex scanner internal error--end of buffer missed"

        Uses multithreading (or multiprocessing).
        This would likely benefit from multiprocessing instead.

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
        xarray_kwargs = dict(searchString=searchString, **xarray_kwargs)

        # NOTE: Multiprocessing does not seem to work because it looks
        # NOTE: like xarray objects are not pickleable.
        # NOTE: ``Reason: 'TypeError("cannot pickle '_thread.lock' object"``

        if max_threads:
            ###########################
            # Multithread the downloads
            # ! Only works sometimes
            # ! I get this error: "'EntryPoint' object has no attribute '_key'""

            threads = min(self.tasks, max_threads)
            log.info(f"🧵 Working on {self.tasks} tasks with {threads} threads.")

            with ThreadPoolExecutor(max_threads) as exe:
                futures = [
                    exe.submit(H.xarray, **xarray_kwargs) for H in self.file_exists
                ]

                # Return list of Herbie objects in order completed
                ds_list = [future.result() for future in as_completed(futures)]

        else:
            ds_list = [H.xarray(**xarray_kwargs) for H in self.file_exists]

        # Sort the DataSets, first by lead time (step), then by run time (time)
        ds_list.sort(key=lambda x: x.step.data.max())
        ds_list.sort(key=lambda x: x.time.data.max())

        # Reshape list with dimensions (len(DATES), len(fxx))
        ds_list = [
            ds_list[x : x + len(self.fxx)]
            for x in range(0, len(ds_list), len(self.fxx))
        ]

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

        return ds
