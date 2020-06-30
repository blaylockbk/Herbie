#!/usr/bin/env python3

## Brian Blaylock
## June 26, 2020

"""
=========================
Download HRRR GRIB2 files
=========================

Can download HRRR files from the University of Utah HRRR archive on Pando
or from the NOMADS server.

reporthook
     Prints download progress when downloading full files.
searchString_help
    Prints examples for the `searchString` argument when there is an error.
download_HRRR_subset
    Download parts of a HRRR file.
download_HRRR
    Main function for downloading many HRRR files.
get_crs
    Get cartopy projection object from xarray.Dataset
get_HRRR
    Read HRRR data as an xarray Dataset with cfgrib engine.
"""

import os
import re
from datetime import datetime, timedelta

import numpy as np
import urllib.request  # Used to download the file
import requests        # Used to check if a URL exists
import warnings
import cartopy.crs as ccrs
import cfgrib
import xarray as xr

def reporthook(a, b, c):
    """
    Report download progress in megabytes (prints progress to screen).
    
    Parameters
    ----------
    a : Chunk number
    b : Maximum chunk size
    c : Total size of the download
    """
    chunk_progress = a * b / c * 100
    total_size_MB =  c / 1000000.
    print(f"\r Download Progress: {chunk_progress:.2f}% of {total_size_MB:.1f} MB\r", end='')

def searchString_help(searchString):
    msg = [
        f"There is something wrong with [[  searchString='{searchString}'  ]]",
        "\nHere are some examples you can use for `searchString`",
        "    ================ ===============================================",
        "    ``searchString`` Messages that will be downloaded",
        "    ================ ===============================================",
        "    ':TMP:2 m'       Temperature at 2 m.",
        "    ':TMP:'          Temperature fields at all levels.",
        "    ':500 mb:'       All variables on the 500 mb level.",
        "    ':APCP:'         All accumulated precipitation fields.",
        "    ':UGRD:10 m'     U wind component at 10 meters.",
        "    ':(U|V)GRD:'     U and V wind component at all levels.",
        "    ':.GRD:'         (Same as above)",
        "    ':(TMP|DPT):'    Temperature and Dew Point for all levels .",
        "    ':(TMP|DPT|RH):' TMP, DPT, and Relative Humidity for all levels.",
        "    ':REFC:'         Composite Reflectivity",
        "    ':surface:'      All variables at the surface.",
        "    '((U|V)GRD:10 m|TMP:2 m|APCP)' 10-m wind, 2-m temp, and precip.",
        "    ================ ===============================================",
        "\n  If you need help with regular expression, search the web",
        "  or look at this cheatsheet: https://www.petefreitag.com/cheatsheets/regex/",
        "PLEASE FIX THE `searchString`"
        ]
    return '\n'.join(msg)

def download_HRRR_subset(url, searchString, SAVEDIR='./',
                         dryrun=False, verbose=True):
    """
    Download a subset of GRIB fields from a HRRR file.
    
    This assumes there is an index (.idx) file available for the file.
    
    Parameters
    ----------
    url : string
        The URL for the HRRR file you are trying to download. There must be an 
        index file for the GRIB2 file. For example, if 
        ``url='https://pando-rgw01.chpc.utah.edu/hrrr/sfc/20200624/hrrr.t01z.wrfsfcf17.grib2'``,
        then ``https://pando-rgw01.chpc.utah.edu/hrrr/sfc/20200624/hrrr.t01z.wrfsfcf17.grib2.idx``
        must also exist on the server.
    searchString : str
        The string you are looking for in each line of the index file. 
        Take a look at the 
        .idx file at https://pando-rgw01.chpc.utah.edu/hrrr/sfc/20200624/hrrr.t01z.wrfsfcf17.grib2.idx
        to get familiar with what is in each line.
        Also look at this webpage: http://hrrr.chpc.utah.edu/HRRR_archive/hrrr_sfc_table_f00-f01.html
        for additional details.**You should focus on the variable and level 
        field for your searches**.
        
        You may use regular expression syntax to customize your search. 
        Check out this regulare expression cheatsheet:
        https://link.medium.com/7rxduD2e06
        
        Here are a few examples that can help you get started
        
        ================ ===============================================
        ``searchString`` Messages that will be downloaded
        ================ ===============================================
        ':TMP:2 m'       Temperature at 2 m.
        ':TMP:'          Temperature fields at all levels.
        ':500 mb:'       All variables on the 500 mb level.
        ':APCP:'         All accumulated precipitation fields.
        ':UGRD:10 m'    U wind component at 10 meters.
        ':(U|V)GRD:'     U and V wind component at all levels.
        ':.GRD:'         (Same as above)
        ':(TMP|DPT):'    Temperature and Dew Point for all levels .
        ':(TMP|DPT|RH):' TMP, DPT, and Relative Humidity for all levels.
        ':REFC:'         Composite Reflectivity
        ':surface:'      All variables at the surface.
        ================ ===============================================    
        
    SAVEDIR : string
        Directory path to save the file, default is the current directory.
    dryrun : bool
        If True, do not actually download, but print out what the function will
        attempt to do.
    verbose : bool
        If True, print lots of details (default)
    
    Returns
    -------
    The path and name of the new file.
    """
    # Ping Pando first. This *might* prevent a "bad handshake" error.
    if 'pando' in url:
        try:
            requests.head('https://pando-rgw01.chpc.utah.edu/')
        except:
            print('bad handshake...am I able to on?')
            pass
    
    # Make SAVEDIR if path doesn't exist
    if not os.path.exists(SAVEDIR):
        os.makedirs(SAVEDIR)
        print(f'Created directory: {SAVEDIR}')

    
    # Make a request for the .idx file for the above URL
    idx = url + '.idx'
    r = requests.get(idx)

    # Check that the file exists. If there isn't an index, you will get a 404 error.
    if not r.ok: 
        print('❌ SORRY! Status Code:', r.status_code, r.reason)
        print(f'❌ It does not look like the index file exists: {idx}')

    # Read the text lines of the request
    lines = r.text.split('\n')
    
    # Search expression
    try:
        expr = re.compile(searchString)
    except Exception as e: 
        print('re.compile error:', e)
        raise Exception(searchString_help(searchString))

    # Store the byte ranges in a dictionary
    #     {byte-range-as-string: line}
    byte_ranges = {}
    for n, line in enumerate(lines, start=1):
        # n is the line number (starting from 1) so that when we call for 
        # `lines[n]` it will give us the next line. (Clear as mud??)

        # Use the compiled regular expression to search the line
        if expr.search(line):   
            # aka, if the line contains the string we are looking for...

            # Get the beginning byte in the line we found
            parts = line.split(':')
            rangestart = int(parts[1])

            # Get the beginning byte in the next line...
            if n+1 < len(lines):
                # ...if there is a next line
                parts = lines[n].split(':')
                rangeend = int(parts[1])
            else:
                # ...if there isn't a next line, then go to the end of the file.
                rangeend = ''

            # Store the byte-range string in our dictionary, 
            # and keep the line information too so we can refer back to it.
            byte_ranges[f'{rangestart}-{rangeend}'] = line
    
    if len(byte_ranges) == 0:
        # Loop didn't find the searchString in the index file.
        print(f'❌ WARNING: Sorry, I did not find [{searchString}] in the index file {idx}')
        print(searchString_help(searchString))
        return None
    
    # What should we name the file we save this data to?
    # Let's name it something like `subset_20200624_hrrr.t01z.wrfsfcf17.grib2`
    runDate = list(byte_ranges.items())[0][1].split(':')[2][2:-2]
    outFile = '_'.join(['subset', runDate, url.split('/')[-1]])
    outFile = os.path.join(SAVEDIR, outFile)
    
    for i, (byteRange, line) in enumerate(byte_ranges.items()):
        
        if i == 0:
            # If we are working on the first item, overwrite the existing file.
            curl = f'curl -s --range {byteRange} {url} > {outFile}'
        else:
            # If we are working on not the first item, append the existing file.
            curl = f'curl -s --range {byteRange} {url} >> {outFile}'
            
        num, byte, date, var, level, forecast, _ = line.split(':')
        
        if dryrun:
            if verbose: print(f'    🐫 Dry Run: Found GRIB line [{num:>3}]: variable={var}, level={level}, forecast={forecast}')
            #print(f'    🐫 Dry Run: `{curl}`')
        else:
            if verbose: print(f'  Downloading GRIB line [{num:>3}]: variable={var}, level={level}, forecast={forecast}')    
            os.system(curl)
    
    if dryrun:
        if verbose: print(f'🌵 Dry Run: Success! Searched for [{searchString}] and found [{len(byte_ranges)}] GRIB fields. Would save as {outFile}')
    else:
        if verbose: print(f'✅ Success! Searched for [{searchString}] and got [{len(byte_ranges)}] GRIB fields and saved as {outFile}')
    
        return outFile
    
def download_HRRR(DATES, searchString=None, fxx=range(0, 1), *,
                  model='hrrr', field='sfc',
                  SAVEDIR='./', dryrun=False, verbose=True):
    """
    Downloads full HRRR grib2 files for a list of dates and forecasts.
    
    Files are downloaded from the University of Utah HRRR archive (Pando) 
    or NOAA Operational Model Archive and Distribution System (NOMADS). This
    function will automatically change the download source for each datetime
    requested.
    
    Parameters
    ----------
    DATES : datetime or list of datetimes
        A datetime or list of datetimes that represent the model 
        initialization time for which you want to download.
    searchString : str
        The string that describes the variables you want to download
        from the file. This is used as the `searchString` in
        ``download_hrrr_subset`` to looking for sepecific byte ranges
        from the file to download. 
        
        Default is None, meaning to not search for variables, but to
        download the full file. ':' is an alias for None, becuase
        it is equivalent to identifying every line in the .idx file.
        Read the details below for more help on defining a suitable 
        ``searchString``.
        
        Take a look at the .idx file at 
        https://pando-rgw01.chpc.utah.edu/hrrr/sfc/20200624/hrrr.t01z.wrfsfcf17.grib2.idx
        to get familiar with what an index file is.
        Also look at this webpage: http://hrrr.chpc.utah.edu/HRRR_archive/hrrr_sfc_table_f00-f01.html
        for additional details.**You should focus on the variable and level 
        field for your searches**.
        
        You may use regular expression syntax to customize your search. 
        Check out this regulare expression cheatsheet:
        https://link.medium.com/7rxduD2e06
        
        Here are a few examples that can help you get started
        
        ================ ===============================================
        ``searchString`` Messages that will be downloaded
        ================ ===============================================
        ':TMP:2 m'       Temperature at 2 m.
        ':TMP:'          Temperature fields at all levels.
        ':500 mb:'       All variables on the 500 mb level.
        ':APCP:'         All accumulated precipitation fields.
        ':UGRD:10 m'    U wind component at 10 meters.
        ':(U|V)GRD:'     U and V wind component at all levels.
        ':.GRD:'         (Same as above)
        ':(TMP|DPT):'    Temperature and Dew Point for all levels .
        ':(TMP|DPT|RH):' TMP, DPT, and Relative Humidity for all levels.
        ':REFC:'         Composite Reflectivity
        ':surface:'      All variables at the surface.
        ''
        ================ =============================================== 
        
    fxx : int or list of ints
        Forecast lead time or list of forecast lead times to download.
        Default only grabs analysis hour (f00), but you might want all
        the forecasts hours, in that case, you could set ``fxx=range(0,19)``.
    model : {'hrrr', 'hrrrak', 'hrrrX'}
        The model type you want to download.
        - 'hrrr' HRRR Contiguous United States (operational)
        - 'hrrrak' HRRR Alaska. You can also use 'alaska' as an alias.
        - 'hrrrX' HRRR *experimental*
    field : {'prs', 'sfc', 'nat', 'subh'}
        Variable fields you wish to download. 
        - 'sfc' surface fields
        - 'prs' pressure fields
        - 'nat' native fields      ('nat' files are not available on Pando)
        - 'subh' subhourly fields  ('subh' files are not available on Pando)
    SAVEDIR : str
        Directory path to save the downloaded HRRR files.
    dryrun : bool
        If True, instead of downloading the files, it will print out the
        files that could be downloaded. This is set to False by default.
    verbose :bool
        If True, print lots of information (default).
        If False, only print some info about download progress.

    Returns
    -------
    The file name for the HRRR files we downloaded and the URL it was from.
    (i.e. `20170101_hrrr.t00z.wrfsfcf00.grib2`)
    """
    
    #**************************************************************************
    ## Check function input
    #**************************************************************************
    
    # Force the `field` input string to be lower case.
    field = field.lower()

    # Ping Pando first. This *might* prevent a "bad handshake" error.
    try:
        requests.head('https://pando-rgw01.chpc.utah.edu/')
    except Exception as e:
        print(f'Ran into an error: {e}')
        print('bad handshake...am I able to on?')
        pass

    # `DATES` and `fxx` should be a list-like object, but if it doesn't have
    # length, (like if the user requests a single date or forecast hour),
    # then turn it item into a list-like object.
    if not hasattr(DATES, '__len__'): DATES = np.array([DATES])
    if not hasattr(fxx, '__len__'): fxx = [fxx]

    assert all([i < datetime.utcnow() for i in DATES]), "🦨 Whoops! One or more of your DATES is in the future."

    ## Set the download SOURCE for each of the DATES
    ## ---------------------------------------------
    # HRRR data is available on NOMADS for today's and yesterday's runs.
    # I will set the download source to get HRRR data from pando if the
    # datetime is for older than yesterday, and set to nomads for datetimes
    # of yesterday or today.
    yesterday = datetime.utcnow() - timedelta(days=1)
    yesterday = datetime(yesterday.year, yesterday.month, yesterday.day)   
    SOURCE = ['pando' if i < yesterday else 'nomads' for i in DATES]

    # The user may set `model='alaska'` as an alias for 'hrrrak'.
    if model.lower() == 'alaska': model = 'hrrrak'

    # The model type and field available depends on the download SOURCE.
    available = {'pando':{'models':{}, 'fields':{}}, 'nomads':{'models':{}, 'fields':{}}}
    available['pando']['models'] = {'hrrr', 'hrrrak', 'hrrrX'}
    available['pando']['fields'] = {'sfc', 'prs'}
    available['nomads']['models'] = {'hrrr', 'hrrrak'}
    available['nomads']['fields'] = {'sfc', 'prs', 'nat', 'subh'}

    # Make SAVEDIR if path doesn't exist
    if not os.path.exists(SAVEDIR):
        os.makedirs(SAVEDIR)
        print(f'Created directory: {SAVEDIR}')

    #**************************************************************************
    # Build the URL path for every file we want
    #**************************************************************************
    # An example URL for a file from Pando is 
    # https://pando-rgw01.chpc.utah.edu/hrrr/sfc/20200624/hrrr.t01z.wrfsfcf17.grib2
    # 
    # An example URL for a file from NOMADS is
    # https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod/hrrr.20200624/conus/hrrr.t00z.wrfsfcf09.grib2
    URL_list = []
    for source, DATE in zip(SOURCE, DATES):
        if source == 'pando':
            base = f'https://pando-rgw01.chpc.utah.edu/{model}/{field}'
            URL_list += [f'{base}/{DATE:%Y%m%d}/{model}.t{DATE:%H}z.wrf{field}f{f:02d}.grib2' for f in fxx]
            
            if model not in available[source]['models']:
                warnings.warn(f"model='{model}' is not available from [{source}]. Only {available[source]['models']}")
            if field not in available[source]['fields']:
                warnings.warn(f"field='{field}' is not available from [{source}]. Only {available[source]['fields']}")

        elif source == 'nomads':
            base = 'https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod'
            if model == 'hrrr':
                URL_list += [f'{base}/hrrr.{DATE:%Y%m%d}/conus/hrrr.t{DATE:%H}z.wrf{field}f{f:02d}.grib2' for f in fxx]
            elif model == 'hrrrak':
                URL_list += [f'{base}/hrrr.{DATE:%Y%m%d}/alaska/hrrr.t{DATE:%H}z.wrf{field}f{f:02d}.ak.grib2' for f in fxx]
                
            if model not in available[source]['models']:
                warnings.warn(f"model='{model}' is not available from [{source}]. Only {available[source]['models']}")
            if field not in available[source]['fields']:
                warnings.warn(f"field='{field}' is not available from [{source}]. Only {available[source]['fields']}")
        
    #**************************************************************************
    # Ok, so we have a URL and filename for each requested forecast hour.
    # Now we need to check if each of those files exist, and if it does,
    # we will download that file to the SAVEDIR location.
    
    n = len(URL_list)
    if dryrun:
        print(f'🌵 Info: Dry Run {n} GRIB2 files\n')
    else:
        print(f'💡 Info: Downloading {n} GRIB2 files\n')
    
    # For keeping track of total time spent downloading data
    loop_time = timedelta()
    
    all_files = []
    for i, file_URL in enumerate(URL_list):
        timer = datetime.now()
        
        # Time keeping: *crude* method to estimate remaining time.
        mean_dt_per_loop = loop_time/(i+1)
        est_rem_time = mean_dt_per_loop * (n-i+1)
        
        if not verbose: 
            # Still show a little indicator of what is downloading.    
            print(f"\r Download Progress: ({i+1}/{n}) files {file_URL} (Est. Time Remaining {str(est_rem_time):16})\r", end='')
        
        # We want to prepend the filename with the run date, YYYYMMDD
        if 'pando' in file_URL:
            outFile = '_'.join(file_URL.split('/')[-2:])
            outFile = os.path.join(SAVEDIR, outFile)
        elif 'nomads' in file_URL:
            outFile = file_URL.split('/')[-3][5:] + '_' + file_URL.split('/')[-1]
            outFile = os.path.join(SAVEDIR, outFile)
        
        # Check if the URL returns a status code of 200 (meaning the URL is ok)
        # Also check that the Content-Length is >1000000 bytes (if it's smaller,
        # the file on the server might be incomplete)
        head = requests.head(file_URL)
        
        check_exists = head.ok
        check_content = int(head.raw.info()['Content-Length']) > 1000000
        
        if verbose: print(f"\nDownload Progress: ({i+1}/{n}) files {file_URL} (Est. Time Remaining {str(est_rem_time):16})")
        if check_exists and check_content:
            # Download the file
            if searchString in [None, ':']:
                if dryrun:
                    if verbose: print(f'🌵 Dry Run Success! Would have downloaded {file_URL} as {outFile}')
                    all_files.append(None)
                else:
                    # Download the full file.
                    urllib.request.urlretrieve(file_URL, outFile, reporthook)
                    all_files.append(outFile)
                    if verbose: print(f'✅ Success! Downloaded {file_URL} as {outFile}')
            else:
                # Download a subset of the full file based on the seachString.
                if verbose: print(f"Download subset from [{source}]:")
                thisfile = download_HRRR_subset(file_URL, 
                                                searchString, 
                                                SAVEDIR=SAVEDIR, 
                                                dryrun=dryrun, 
                                                verbose=verbose)
                all_files.append(thisfile)
        else:
            # The URL request is bad. If status code == 404, the URL does not exist.
            print()
            print(f'❌ WARNING: Status code {head.status_code}: {head.reason}. Content-Length: {int(head.raw.info()["Content-Length"]):,} bytes')
            print(f'❌ Could not download {head.url}')
    
        loop_time += datetime.now() - timer
        
    print(f"\nFinished 🍦  (Time spent downloading: {loop_time})")
    
    if len(all_files) == 1:
        return all_files[0], URL_list[0]  # return a string, not list
    else:
        return np.array(all_files), np.array(URL_list)  # return the list of file names and URLs
    
def get_crs(ds):
    """
    Get the cartopy coordinate reference system from a cfgrib's xarray Dataset
    
    Parameters
    ----------
    ds : xarray.Dataset
        An xarray.Dataset from a GRIB2 file opened by the cfgrib engine.
    """
    # Base projection on the attributes from the 1st variable in the Dataset
    attrs = ds[list(ds)[0]].attrs  
    if attrs['GRIB_gridType'] == 'lambert':
        lc_HRRR_kwargs = {
            'globe': ccrs.Globe(ellipse='sphere'),
            'central_latitude': attrs['GRIB_LaDInDegrees'],
            'central_longitude': attrs['GRIB_LoVInDegrees'],
            'standard_parallels': (attrs['GRIB_Latin1InDegrees'],\
                                   attrs['GRIB_Latin2InDegrees'])}
        lc = ccrs.LambertConformal(**lc_HRRR_kwargs)
        return lc
    else:
        warnings.warn('GRIB_gridType is not "lambert".')
        return None

def get_HRRR(DATE, searchString, *, fxx=0, DATE_is_valid_time=False, 
            remove_grib2=True, add_crs=True, **download_kwargs):
    """
    Download HRRR data and return as an xarray Dataset (or Datasets)
    
    Only request one `DATE` and `fxx` (forecast lead time).
    
    Parameters
    ----------
    DATE : datetime
        A single datetime object.
    searchString: string
        A string representing a field or fields from the GRIB2 file.
        See more details in ``download_hrrr`` docstring.
        
        Some examples:
        
        ================ ===============================================
        ``searchString`` Messages that will be downloaded
        ================ ===============================================
        ':TMP:2 m'       Temperature at 2 m.
        ':TMP:'          Temperature fields at all levels.
        ':500 mb:'       All variables on the 500 mb level.
        ':APCP:'         All accumulated precipitation fields.
        ':UGRD:10 m'    U wind component at 10 meters.
        ':(U|V)GRD:'     U and V wind component at all levels.
        ':.GRD:'         (Same as above)
        ':(TMP|DPT):'    Temperature and Dew Point for all levels .
        ':(TMP|DPT|RH):' TMP, DPT, and Relative Humidity for all levels.
        ':REFC:'         Composite Reflectivity
        ':surface:'      All variables at the surface.
        ================ =============================================== 
        
    fxx : int
        Forecast lead time. Default will get the analysis, F00.
    DATE_is_valid_time: bool
        False - (default) The DATE argument represents the model 
                initialization datetime.
        True  - The DATE argument represents the model valid time.
                This is handy when you want a specific forecast leadtime
                that is valid at a certian date.
    remove_grib2 : bool
        True  - (default) Delete the GRIB2 file after reading into a Dataset.
                This requires a copy to memory, so it might slow things down.
        False - Keep the GRIB2 file downloaded.
                This might be a better option performance-wise, because it
                does not need to copy the data but keeps the file on disk.
                You would be responsible for removing files when you don't
                need them.
    add_crs : bool
        True  - (default) Append the Cartopy coordinate reference system (crs) 
                projection as an attribute to the Dataset.
    **download_kwargs :
        Any other key word argument accepted by ``download_HRRR`.
        {model, field, SAVEDIR, dryrun, verbose}
    """
    inputs = locals()

    assert not hasattr(DATE, '__len__'), "`DATE` must be a single datetime, not a list."
    assert not hasattr(fxx, '__len__'), "`fxx` must be a single integer, not a list."
        
    if DATE_is_valid_time:
        # Change DATE to the model run initialization DATE so that when we take
        # into account the forecast lead time offset, the the returned data 
        # be valid for the DATE the user requested.
        DATE = DATE - timedelta(hours=fxx)
    
    # Download the GRIB2 file
    grib2file, url = download_HRRR(DATE, searchString, fxx=fxx, **download_kwargs)
    
    # Some extra backend kwargs for cfgrib
    backend_kwargs = {'indexpath':'',
                      'read_keys': ['parameterName', 'parameterUnits'],
                      'errors': 'raise'}
    
    # Use cfgrib.open_datasets, just in case there are multiple "hypercubes"
    # for what we requested.
    H = cfgrib.open_datasets(grib2file, backend_kwargs=backend_kwargs)

    # Create a cartopy projection object
    if add_crs: 
        crs = get_crs(H[0])

    for ds in H:
        ds.attrs['get_HRRR inputs'] = inputs
        ds.attrs['url'] = url
        if add_crs:
            # Add the crs projection info as a Dataset attribute
            ds.attrs['crs'] = crs
            # ...and add attrs for each variable for ease of access.
            for var in list(ds):

                    ds[var].attrs['crs'] = crs
    if remove_grib2:
        H = [ds.copy(deep=True) for ds in H]
        os.remove(grib2file)
    
    if len(H) == 1:
        H = H[0]
    else:
        warnings.warn('⚠ ALERT! Could not load grib2 data into a single xarray Dataset. You might consider refining your `searchString` if you are getting data you do not need.')
    
    return H
    