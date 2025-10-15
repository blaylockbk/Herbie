"""Herbie Helpers to get the latest model grid."""

import time

import pandas as pd

from herbie import Herbie, config


def HerbieLatest(
    model=config["default"].get("model"),
    priority=["aws", "nomads"],
    periods=4,
    **kwargs,
):
    r"""Find the latest model data.

    Parameters
    ----------
    model : str
        The name of the model.
    priority : list
        The sources to look for data.

        The default value `["aws", "nomads"]` was chosen because it is a
        reasonable priority order for many of the models available from
        the NODD program (NOAA models like HRRR, GFS, GEFS, etc.) The
        data for these models will be made available on NOMADS first,
        but I also know AWS gets the data pretty quick. So, check AWS
        first, then check NOMADS (because if you make too many downloads
        from NOMADS your IP address will get blocked.)
    periods : int
        The number of periods (initialization datetimes) to search through.
    **kwargs
        Any other input you want passed to the Herbie class.
    """
    if model.lower() in ["hrrr", "rap", "rrfs"]:
        freq = "1h"
    elif model.lower() in ["rtma_ru"]:
        freq = "15min"
    else:
        freq = "6h"

    if 'valid_date' in kwargs:
        valid_date = pd.to_datetime(kwargs.get('valid_date'))

        # Create a list of recent dates to try
        dates = pd.date_range(
                pd.Timestamp.utcnow().floor(freq).tz_localize(None),
                periods=periods,
                freq=f"-{freq}",
            )

        # Create a corresponding list of fxx values that give the correct
        # valid_date
        fxxs = [int((valid_date - date).total_seconds() / 3600.0)
                for date in dates]

        # series of dates/fxxs
        dates_fxxs = pd.Series(data=fxxs, index=dates)

        # Find first existing Herbie object with correct date/fxx combination
        for date, fxx in dates_fxxs.items():
            H = Herbie(date=date,
                       model=model,
                       priority=priority,
                       fxx=fxx,
                       **kwargs)
            if H.grib:
                return H

    else:
        # Create a list of recent dates to try
        dates = pd.date_range(
            pd.Timestamp.utcnow().floor(freq).tz_localize(None),
            periods=periods,
            freq=f"-{freq}",
        )
        print(dates)

        # Find first existing Herbie object
        for date in dates:
            H = Herbie(date=date,
                       model=model,
                       priority=priority,
                       **kwargs)
            if H.grib:
                return H

    raise TimeoutError(f"Herbie did not find data for the latest time: {H}")


def HerbieWait(
    run=pd.Timestamp("now", tz="utc").floor('1h').replace(tzinfo=None),
    model=config["default"].get("model"),
    priority=["aws", "nomads"],
    wait_for="5min",
    check_interval="15s",
    **kwargs,
):
    """Wait for the latest model grid to become available.

    Parameters
    ----------
    run : datetime or pandas.Timestamp
        The model run to search for.
        If not provided, the default value is the current UTC hour.
    model : str
        The name of the model.
    priority : list
        The sources to look for data.

        The default value `["aws", "nomads"]` was chosen because it is a
        reasonable priority order for many of the models available from
        the NODD program (NOAA models like HRRR, GFS, GEFS, etc.) The
        data for these models will be made available on NOMADS first,
        but I also know AWS gets the data pretty quick. So, check AWS
        first, then check NOMADS (because if you make too many downloads
        from NOMADS your IP address will get blocked.)
    wait_for : timedelta or Pandas-parsable Timedelta str
        Length of time Herbie will wait for data.
    check_every : int (seconds), timedelta, Pandas-parsable Timedelta str
        Frequency Herbie will look for data again, as a pandas-parsable
        timedelta string (e.g., '30s') or an int representing seconds.
    **kwargs
        Any other input you want passed to the Herbie class.
    """
    if isinstance(check_interval, str):
        check_interval = pd.Timedelta(check_interval).total_seconds()

    timer = pd.Timestamp("now")

    H = Herbie(run, model=model, priority=priority, **kwargs)

    # If H.grib does not exist, wait for it
    while H.grib is None:
        # Wait for the specified check interval
        time.sleep(check_interval)

        # Try again; break out of loop if successful
        H = Herbie(run, model=model, priority=priority, **kwargs)
        if H.grib is not None:
            break

        # Error out if timeout is exceeded
        if (pd.Timestamp("now") - timer) >= pd.Timedelta(wait_for):
            raise TimeoutError(f"Herbie did not find data in time: {H}")

    return Herbie(run, model=model, priority=priority, **kwargs)
