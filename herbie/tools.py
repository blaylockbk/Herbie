## Brian Blaylock
## May 3, 2021

"""
============
Herbie Tools
============
"""
from datetime import datetime, timedelta
import pandas as pd
import xarray as xr

from herbie.archive import Herbie

def bulk_download(DATES, searchString=None, *, fxx=range(0,1), 
                  model='hrrr', field='sfc', priority=None,
                  verbose=True):
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
    field : {'sfc', 'prs', 'nat', 'subh'}
        Variable fields file to download. Not needed for RAP model.
    """   
    if isinstance(DATES, (str, pd.Timestamp)) or hasattr(DATES, 'strptime'):
        DATES = [DATES]
    if isinstance(fxx, int):
        fxx = [fxx]

    kw = dict(model=model, field=field)
    if priority is not None:
        kw['priority'] = priority
    
    # Locate the file sources
    print("👨🏻‍🔬 Check which requested files exists")
    grib_sources = [Herbie(d, fxx=f, **kw) \
                    for d in DATES \
                    for f in fxx]
    
    loop_time = timedelta()
    n = len(grib_sources)

    print("\n🌧 Download requested data")
    for i, g in enumerate(grib_sources):
        timer = datetime.now()
        g.download(searchString=searchString)
       
        #---------------------------------------------------------
        # Time keeping: *crude* method to estimate remaining time.
        #---------------------------------------------------------
        loop_time += datetime.now() - timer
        mean_dt_per_loop = loop_time/(i+1)
        remaining_loops = n-i-1
        est_rem_time = mean_dt_per_loop * remaining_loops
        if verbose: print(f"🚛💨 Download Progress: [{i+1}/{n} completed] >> Est. Time Remaining {str(est_rem_time):16}\n")
        #---------------------------------------------------------

    requested = len(grib_sources)
    completed = sum([i.grib is None for i in grib_sources])
    print(f"🍦 Done! Downloaded [{completed}/{requested}] files. Timer={loop_time}")
    
    return grib_sources

def xr_concat_sameRun(DATE, searchString, fxx=range(0,18)):
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
    Hs_to_cat = [Herbie(DATE, fxx=f).xarray(searchString) for f in fxx]
    return xr.concat(Hs_to_cat, dim='f')

def xr_concat_sameLead(DATES, searchString, fxx=0, DATE_is_valid_time=True):
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
    Hs_to_cat = [Herbie(DATE, fxx=fxx, DATE_is_valid_time=DATE_is_valid_time).xarray(searchString) for DATE in DATES]
    return xr.concat(Hs_to_cat, dim='t')
