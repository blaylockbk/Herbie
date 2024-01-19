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
    **kwargs
        Any other input you want passed to the Herbie class.
    """
    if model.lower() in ["hrrr", "rap"]:
        freq = "1H"
    else:
        freq = "6H"

    # Create a list of recent dates to try
    dates = pd.date_range(
        pd.Timestamp.utcnow().floor(freq).tz_localize(None),
        periods=4,
        freq=f"-{freq}",
    )

    # Find first existing Herbie object
    for date in dates:
        H = Herbie(date=date, model=model, priority=priority, **kwargs)
        if H.grib:
            return H

    raise TimeoutError(f"Herbie did not find data for the latest time: {H}")


def HerbieWait(
    model=config["default"].get("model"),
    priority=["aws", "nomads"],
    wait_for="5min",
    check_interval="15s",
    **kwargs,
):
    """Wait for the latest model grid to become available.

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
    wait_for : timedelta or Pandas-parsable Timedelta str
        Length of time Herbie will wait for data.
    check_every : int (seconds), timedelta, Pandas-parsable Timedelta str
        Frequency Herbie will look for data again, as a pandas-parsable
        timedelta string (e.g., '30s') or an int representing seconds.
    **kwargs
        Any other input you want passed to the Herbie class.
    """
    now = pd.Timestamp.utcnow().floor("1h").tz_localize(None)

    if isinstance(check_interval, str):
        check_interval = pd.Timedelta(check_interval).total_seconds()

    timer = pd.Timestamp("now")

    H = Herbie(now, model=model, priority=priority, **kwargs)

    while H.grib is None:
        now = pd.Timestamp.utcnow().floor("1h").tz_localize(None)
        H = Herbie(now, model=model, priority=priority, **kwargs)
        if H.grib:
            return H

        time.sleep(check_interval)

        if (pd.Timestamp("now") - timer) >= pd.Timedelta(wait_for):
            break

    raise TimeoutError(f"Herbie did not find data in time: {H}")
