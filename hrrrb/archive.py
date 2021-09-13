#!/usr/bin/env python3

## Brian Blaylock
## July 8, 2020

"""
👴🏻 The HRRR-B API is deprecated. Use the new Herbie API.

=======================================
Retrieve HRRR GRIB2 files from archives
=======================================

Download High-Resolution Rapid Refresh (HRRR) model GRIB2 files from
different archive sources. Support for subsetting GRIB2 files by fields
if the `.idx`` file exist.

Default HRRR Data Source Priority
---------------------------------
NOAA started pushing the HRRR data to the Google Cloud Platform and
Amazon Web Services at the end of 2020. The archives were also
backfilled to previous years as far back as July 30, 2014. This module
will download HRRR data from these sources in the following order (the
default download source priority can be changed).


1. NOMAS: NOAA Operational Model Archive and Distribution System
    - https://nomads.ncep.noaa.gov/
    - Available for today's and yesterday's runs
    - Original data source. All available data.
    - Includes ``.idx`` for all GRIB2 files.

2. Google: Google Cloud Platform Earth
    - https://console.cloud.google.com/storage/browser/high-resolution-rapid-refresh
    - Available from July 30, 2014 to Present.
    - Does not have ``.idx`` files before September 17, 2018.
    - Has all original data including nat, subh, prs, and sfc files
      for all forecast hours.

3. AWS: Amazon Web Services
    - https://noaa-hrrr-bdp-pds.s3.amazonaws.com/
    - Available from July 30, 2014 to Present.
    - Does not have ``.idx`` files.
    - Has all nat, subh, prs, and sfc files for all forecast hours.
    - Some data may be missing.

3. Pando: The University of Utah HRRR archive
    - http://hrrr.chpc.utah.edu/
    - Available from July 15, 2016 to Present.
    - A subset of prs and sfc files.
    - Contains a ``.idx`` file for *every* GRIB2 file for subsetting.

Main Functions
--------------
download_hrrr
    Download GRIB2 files to local disk.
xhrrr
    Download and read HRRR data as an xarray.Dataset with cfgrib engine.

"""

import configparser
import os
import re
import urllib.request
import warnings
from datetime import datetime, timedelta
from itertools import product
from pathlib import Path

import cfgrib
import numpy as np
import pandas as pd
import requests
import xarray as xr

from hrrrb.tools import get_crs, to_180

warnings.warn(
      "The hrrrb API is deprecated. Use the new Herbie API instead."
   )

#=======================================================================
# Specify default location to save HRRR GRIB2 files
#=======================================================================
config = configparser.ConfigParser()
_config_path = Path('~').expanduser() / '.config' / 'hrrrb' / 'config.cfg'

user_home_default = str(Path('~').expanduser() / 'data')

if not _config_path.exists():
    _config_path.parent.mkdir(parents=True)
    _config_path.touch()
    config.read(_config_path)
    config.add_section('download')
    config.set('download', 'default_save_dir', user_home_default)
    with open(_config_path, 'w') as configfile:
        config.write(configfile)
    print(f'⚙ Created config file [{_config_path}]',
          f'with default download directory set as [{user_home_default}]')

config.read(_config_path)
try:
    _default_save_dir = Path(config.get('download', 'default_save_dir'))
except:
    print(f'🦁🐯🐻 oh my! {_config_path} looks weird,',
          f'but I will add a new section')
    config.add_section('download')
    config.set('download', 'default_save_dir', user_home_default)
    with open(_config_path, 'w') as configfile:
        config.write(configfile)
    _default_save_dir = Path(config.get('download', 'default_save_dir'))

# Uncomment to just set save dir to the user's home directory
#_default_save_dir = Path('~').expanduser() / 'data'
#=======================================================================
#=======================================================================


# List of HRRR download source base URLs, in order of priority
base_url = dict(
    nomads = 'https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod',
    google = 'https://storage.googleapis.com/high-resolution-rapid-refresh',
    aws = 'https://noaa-hrrr-bdp-pds.s3.amazonaws.com',
    pando = 'https://pando-rgw01.chpc.utah.edu',
    pando2 = 'https://pando-rgw02.chpc.utah.edu',  # The 2nd rados gateway might work if the 1st didn't.
)

def _ping_pando(gateway=1):
    """Pinging the Pando server before downloading can prevent a bad handshake."""
    try:
        requests.head(f'https://pando-rgw0{gateway}.chpc.utah.edu/')
    except:
        print('bad handshake...am I able to move on?')
        pass

def _reporthook(a, b, c):
    """
    Report download progress in megabytes. Prints progress to screen.

    Parameters
    ----------
    a : Chunk number
    b : Maximum chunk size
    c : Total size of the download
    """
    chunk_progress = a * b / c * 100
    total_size_MB =  c / 1000000.
    print(f"\r🚛💨  Download Progress: {chunk_progress:.2f}% of {total_size_MB:.1f} MB\r", end='')

def _searchString_help(searchString):
    msg = [
        f"There is something wrong with [[  searchString='{searchString}'  ]]",
        "\nUse regular expression to search for lines in the .idx file",
        "Here are some examples you can use for `searchString`",
        "  ============================= ===============================================",
        "  ``searchString``              Messages that will be downloaded",
        "  ============================= ===============================================",
        "  ':TMP:2 m'                    Temperature at 2 m.",
        "  ':TMP:'                       Temperature fields at all levels.",
        "  ':UGRD:.* mb'                 U Wind at all pressure levels.",
        "  ':500 mb:'                    All variables on the 500 mb level.",
        "  ':APCP:'                      All accumulated precipitation fields.",
        "  ':APCP:surface:0-[1-9]*'      Accumulated precip since initialization time",
        "  ':APCP:surface:[1-9]*-[1-9]*' Accumulated precip over last hour",
        "  ':UGRD:10 m'                  U wind component at 10 meters.",
        "  ':(U|V)GRD:(10|80) m'         U and V wind component at 10 and 80 m.",
        "  ':(U|V)GRD:'                  U and V wind component at all levels.",
        "  ':.GRD:'                      (Same as above)",
        "  ':(TMP|DPT):'                 Temperature and Dew Point for all levels .",
        "  ':(TMP|DPT|RH):'              TMP, DPT, and Relative Humidity for all levels.",
        "  ':REFC:'                      Composite Reflectivity",
        "  ':surface:'                   All variables at the surface.",
        "  ============================= ===============================================",
        "\nIf you need help with regular expression, search the web",
        "  or look at this cheatsheet: https://www.petefreitag.com/cheatsheets/regex/."
        ]
    return '\n'.join(msg)

def _outFile_from_url(url, save_dir):
    """
    Define the filename for a grib2 file from its URL.

    Parameters
    ----------
    url : str
        A URL string for a grib2 file we want to download.
    save_dir : dir
        The directory path to save the file.
    """
    if 'pando' in url:
        outFile = '_'.join(url.split('/')[-2:])
    else:
        outFile = url.split('/')[-3][5:] + '_' + url.split('/')[-1]

    outFile = save_dir / outFile

    if not outFile.parent.is_dir():
        outFile.parent.mkdir(parents=True, exist_ok=True)
        print(f'👨🏻‍🏭 Created directory: [{outFile.parent}]')

    return outFile

def _download_hrrr_subset(url, searchString, *,
                          df_row_urls=None,
                          save_dir=_default_save_dir,
                          dryrun=False, verbose=True):
    """
    Download a subset of GRIB fields from a HRRR file located at a URL.

    There must be an index (.idx) file available for the file.

    A USER, YOU SHOULD NOT USE THIS FUNCTION DIRECTLY. Instead, use the
    ``download_hrrr`` function and specify the search string to get a
    subset of a GRIB2 file.

    Parameters
    ----------
    url : string
        The URL for the HRRR file you are trying to download. There must be an
        index file for the GRIB2 file. For example, if
        ``url='https://pando-rgw01.chpc.utah.edu/hrrr/sfc/20200624/hrrr.t01z.wrfsfcf17.grib2'``,
        then ``https://pando-rgw01.chpc.utah.edu/hrrr/sfc/20200624/hrrr.t01z.wrfsfcf17.grib2.idx``
        must also exist.
    searchString : str
        The string you are looking for in each line of the index file.
        Refer to the _searchString_help for examples.
    df_row_urls : None or list
        THIS VARIABLE IS RESERVED FOR INPUT FROM THE ``download_hrrr``
        FUNCTION for the case when there isn't an .idx file from the
        requested source, the .idx might be available at a different URL.
        This is a list of those other URLs (supplied by the download_hrrr function's loop)
    save_dir : string
        Directory path to save the file, default ``~/data/``.
    dryrun : bool
        If True, do not perform download, but print out what the function will
        attempt to do.
    verbose : bool
        If True, print lots of details (default)

    Returns
    -------
    The path and name of the new file.
    """
    # Ping Pando first. This *might* prevent a "bad handshake" error.
    if 'pando-rgw01' in url: _ping_pando(1)
    elif 'pando-rgw02' in url: _ping_pando(2)

    # Make a request for the .idx file for the above URL
    idx = url + '.idx'
    r = requests.get(idx)

    # Check that the file exists. If there isn't an index, you will get a 404 error.
    if not r.ok:
        print(f'❌ .idx file does not exist at {idx}')
        if df_row_urls is not None:
            # Check the other sources provided
            for alt_url in df_row_urls[1:]:
                if alt_url != url:  # don't check the url twice
                    idx = alt_url + '.idx'
                    r = requests.get(idx)
                    if r.ok:
                        print(f'✔ I found a .idx file at {idx}')
                        continue
                    else:
                        print(f'❌ .idx file does not exist at {idx}')

    if not r.ok:
        notice = [
            '',
            f'❌ SORRY! Status Code: {r.status_code} {r.reason}',
            f'❌ It does not look like an index file exists: {idx}',
            f'❌ Please change your request or download the full grib2 file with `download_hrrr`.'
        ]
        raise Exception('\n'.join(notice))

    # Read the text lines of the request
    lines = r.text.split('\n')

    # Search expression
    try:
        expr = re.compile(searchString)
    except Exception as e:
        print('re.compile error:', e)
        raise Exception(_searchString_help(searchString))

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
        print(_searchString_help(searchString))
        return None

    # What should we name the file we save this data to?
    # Let's name it something like `subset_20200624_hrrr.t01z.wrfsfcf17.grib2`
    runDate = list(byte_ranges.items())[0][1].split(':')[2][2:-2]
    outFile = '_'.join(['subset', runDate, url.split('/')[-1]])
    outFile = save_dir / outFile

    for i, (byteRange, line) in enumerate(byte_ranges.items()):

        if i == 0:
            # If we are working on the first item, overwrite the existing file.
            curl = f'curl -s --range {byteRange} {url} > {outFile}'
        else:
            # If we are working on not the first item, append the existing file.
            curl = f'curl -s --range {byteRange} {url} >> {outFile}'

        num, byte, date, var, level, forecast, *_ = line.split(':')

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

###############################################################################
###############################################################################

def download_hrrr(DATES, searchString=None, *,
                  fxx=range(0, 1),
                  model='hrrr',
                  field='sfc',
                  save_dir=_default_save_dir,
                  download_source_priority=None,
                  overwrite=False,
                  dryrun=False, verbose=True):
    """
    Download full or partial HRRR grib2 files for a list of dates and forecasts.

    Attempts to download grib2 files from three different sources in the
    following order:

    1. NOAA Operational Model Archive and Distribution System ('nomads').
    2. Google Cloud Platform ('google')
    3. University of Utah HRRR archive ('pando')
    4. Amazon Web Services ('aws')

    Parameters
    ----------
    DATES : datetime or list of datetimes
        A datetime or list of datetimes that represent the model
        initialization time for which you want to download. May also
        use a date as a string if it can be parsed by Pandas.
    searchString : str
        A regular expression string that describes the variables you
        want to download from the file. This is used as the
        `searchString` in ``_download_hrrr_subset`` to looking for
        specific byte ranges from the file to download.

        Default is None, meaning to not search for all variables and
        **downloads the full GRIB2 file**. Furthermore, ``':'`` is an
        alias for None because it is equivalent to identifying every
        line in the .idx file.

        Take a look at the .idx file at
        https://pando-rgw01.chpc.utah.edu/hrrr/sfc/20200624/hrrr.t01z.wrfsfcf17.grib2.idx
        for an example of what an index file looks like.

        Also look at this webpage: http://hrrr.chpc.utah.edu/HRRR_archive/hrrr_sfc_table_f00-f01.html
        for additional details. **You should focus your searches on the
        *variable* and *level* to key in on specific fields**.

        You may use regular expression syntax to customize your search.
        Check out this regular expression cheatsheet:
        https://link.medium.com/7rxduD2e06

        Here are a few examples that can help you get started

        ============================= ===============================================
        ``searchString``              Messages that will be downloaded
        ============================= ===============================================
        ':TMP:2 m'                    Temperature at 2 m.
        ':TMP:'                       Temperature fields at all levels.
        ':UGRD:.* mb'                 U Wind at all pressure levels.
        ':500 mb:'                    All variables on the 500 mb level.
        ':APCP:'                      All accumulated precipitation fields.
        ':APCP:surface:0-[1-9]*'      Accumulated precip since initialization time
        ':APCP:surface:[1-9]*-[1-9]*' Accumulated precip over last hour
        ':UGRD:10 m'                  U wind component at 10 meters.
        ':(U|V)GRD:'                  U and V wind component at all levels.
        ':.GRD:'                      (Same as above)
        ':(TMP|DPT):'                 Temperature and Dew Point for all levels .
        ':(TMP|DPT|RH):'              TMP, DPT, and Relative Humidity for all levels.
        ':REFC:'                      Composite Reflectivity
        ':surface:'                   All variables at the surface.
        ''
        ============================= ===============================================

    fxx : int or list of int
        Forecast lead time or list of forecast lead times to download.
        Default only grabs analysis hour (f00). If you want all forecasts
        hours, you can set ``fxx=range(0,19)``.
    model : {'hrrr', 'hrrrak', 'hrrrX'}
        The model type you want to download.
        - `'hrrr'` HRRR Contiguous United States (operational)
        - `'hrrrak'` HRRR Alaska. You can also use 'alaska' as an alias.
        - `'hrrrX'` *experimental* HRRR (experimental version run at ESRL)
           is only available from the Pando archive.
        - `'rap'` Rapid Refresh model. **This is not fully tested or implemented**,
           but you can get the GRIB2 grids and subset the file by .idx with
           searchString. `field` is not required as all levels are in the same file.
    field : {'prs', 'sfc', 'nat', 'subh'}
        Variable fields you wish to download. Only 'sfc' and 'prs' are
        available on Pando, but 'nat' and 'subh' are attainable from
        other sources.
        - 'sfc' surface fields
        - 'prs' pressure fields
        - 'nat' native fields
        - 'subh' subhourly fields
    save_dir : pathlib.Path
        Directory path to save the downloaded HRRR files.
    download_source_priority : None or list
        If None, the default order is the order specified by
        ``base_url``. You may, however, specify a different
        priority by supplying a list of keys in the ``base_url``.
        For example, to download from 'google' before checking 'pando',
        you may do ``download_source_priority=['google', 'pando', 'nomads']``.
        This also makes is possible to exclude a source.
    overwrite : bool
        Only applicable if ``searchString=None``. Will check if the
        file exists, and if ``overwrite=False``, will not redownload
        the file.
    dryrun : bool
        If True, instead of downloading the files, it will print out the
        files that would be downloaded. This is set to False by default.
    verbose :bool
        If True, print lots of information (default).
        If False, only print some info about download progress.

    Returns
    -------
    The file name for the HRRR files we downloaded and the URL it was from.
    For example: ``('20170101_hrrr.t00z.wrfsfcf00.grib2', 'https://pando-rgw01...')``
    """

    #*******************************************************************
    ## Check function input
    #*******************************************************************

    # The user may set `model='alaska'` as an alias for 'hrrrak'.
    if model.lower() == 'alaska': model = 'hrrrak'

    # Force the `field` input string to be lower case.
    field = field.lower()

    # `DATES` and `fxx` should be a list-like object, but if they have no
    # length, (like if the user requests a single date or forecast hour),
    # then turn the item into a list-like object.
    if not hasattr(fxx, '__len__'): fxx = [fxx]
    if isinstance(download_source_priority, str): download_source_priority = [download_source_priority]
    if isinstance(DATES, str): DATES = pd.to_datetime(DATES)
    if not hasattr(DATES, '__len__'): DATES = np.array([DATES])
    DATES = pd.to_datetime(DATES)

    if not all([i < datetime.utcnow() for i in DATES]):
        warnings.warn("🦨 Whoops! One or more of your DATES is in the future.")

    # Make save_dir if path doesn't exist
    if not hasattr(save_dir, 'exists'):
        save_dir = Path(save_dir).resolve()

    save_dir = save_dir / model
    if not save_dir.is_dir():
        save_dir.mkdir(parents=True, exist_ok=True)
        print(f'👨🏻‍🏭 Created directory: [{save_dir}]')

    if download_source_priority is None:
        source_priority = base_url
    else:
        # If desired, reorder download_source_priority
        source_priority = {}
        for i in download_source_priority:
            i = i.lower()
            if i in base_url:
                source_priority[i] = base_url[i]
            else:
                print(f'  ♟ Skipping `{i}` as a potential source '
                      f'because it is not a valid source name. Must be '
                      f'one of {list(base_url)}.')

    # Ping Pando first. This *might* prevent a "bad handshake" error
    # when a file downloaded from Pando.
    if 'pando' in source_priority: _ping_pando(1)
    elif 'pando2' in source_priority: _ping_pando(2)

    #**************************************************************************
    # Build the URL path for every file we want
    #**************************************************************************
    # HRRR Full URL Examples
    # ----------------------
    # NOMADS
    #   https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod/hrrr.20200624/conus/hrrr.t00z.wrfsfcf09.grib2
    # Pando
    #   https://pando-rgw01.chpc.utah.edu/hrrr/sfc/20200624/hrrr.t01z.wrfsfcf17.grib2
    # Google
    #   https://storage.googleapis.com/high-resolution-rapid-refresh/hrrr.20200101/conus/hrrr.t00z.wrfnatf04.grib2
    # Amazon AWS
    #   https://noaa-hrrr-bdp-pds.s3.amazonaws.com/hrrr.20140917/conus/hrrr.t00z.wrfsubhf1015.grib2
    #
    # RAP Full URL Examples
    # ----------------------
    # NOMADS
    #   https://nomads.ncep.noaa.gov/pub/data/nccf/com/rap/prod/rap.20210407/rap.t00z.awip32f00.grib2
    # Amazon AWS
    #   https://noaa-rap-pds.s3.amazonaws.com/rap.20210407/rap.t00z.awip32f03.grib2
    # Google
    #   https://storage.googleapis.com/rapid-refresh/rap.20210222/rap.t00z.awip32f01.grib2

    # Create a list of URLs for each files from each download source
    URL_list = {}
    for source, source_url in source_priority.items():
        URL_list[source] = []

        for DATE, f in product(DATES, fxx):
            if source.startswith('pando'):
                # Pando URL is unique
                URL_list[source].append(f"{source_url}/{model}/{field}/{DATE:%Y%m%d}/{model}.t{DATE:%H}z.wrf{field}f{f:02d}.grib2")
            else:
                # NOMADS, Google, and AWS URL are the same after their base_url
                if model == 'hrrr':
                    URL_list[source].append(f"{source_url}/hrrr.{DATE:%Y%m%d}/conus/hrrr.t{DATE:%H}z.wrf{field}f{f:02d}.grib2")
                elif model == 'hrrrak':
                    URL_list[source].append(f"{source_url}/hrrr.{DATE:%Y%m%d}/alaska/hrrr.t{DATE:%H}z.wrf{field}f{f:02d}.ak.grib2")
                elif model == 'rap':
                    ## Rapid Refresh Model is a special case
                    if source == 'aws':
                        URL_list[source].append(f'https://noaa-rap-pds.s3.amazonaws.com/rap.{DATE:%Y%m%d}/rap.t{DATE:%H}z.awip32f{f:02d}.grib2')
                    elif source == 'nomads':
                        URL_list[source].append(f'https://nomads.ncep.noaa.gov/pub/data/nccf/com/rap/prod/rap.{DATE:%Y%m%d}/rap.t{DATE:%H}z.awip32f{f:02d}.grib2')
                    elif source == 'google':
                        URL_list[source].append(f'https://storage.googleapis.com/rapid-refresh/rap.{DATE:%Y%m%d}/rap.t{DATE:%H}z.awip32f{f:02d}.grib2')
                else:
                    URL_list[source].append(f'https://pando-rgw01.chpc.utah.edu/hrrrX/nonehere_placeholder_{source}') # Experimental HRRR (hrrrX) only exists on Pando. This is a placeholder.

    # A pandas.DataFrame to keep track of the URLs. We will iterate over each row.
    URL_df = pd.DataFrame(URL_list)

    #return URL_df

    #*******************************************************************
    # Download Files that exist
    #*******************************************************************
    # Attempt download from sources in order of source priority.

    n = len(URL_df)

    if dryrun:
        print(f'🌵 Info: Dry Run [{n}] GRIB2 files\n')
    else:
        print(f'💡 Info: Downloading [{n}] GRIB2 files\n')

    # Keep track of total time spent in the download loop.
    loop_time = timedelta()

    # We want to return lists of the filenames we retrive and the URLs
    all_files = []
    all_urls = []

    for (index, row), DATE in zip(URL_df.iterrows(), DATES):
        #print(index, row, DATE)
        #---------------------------------------------------------
        # Time keeping: *crude* method to estimate remaining time.
        #---------------------------------------------------------
        timer = datetime.now()
        #---------------------------------------------------------

        # We will set this to True when we have downloaded a file from a source
        # For example, this will prevents us from downloading a file from
        # google if we already got the file from pando.
        one_exists = False

        for source, url in row.items():
            # Check if the URL exists and the filesize is large enough to be a file.
            head = requests.head(url)
            check_exists = head.ok
            check_content = int(head.raw.info()['Content-Length']) > 1_000_000

            if check_exists and check_content:
                # Yippie! a grib2 file exists
                one_exists = True

                # Define the filename we want to save the data as
                outFile = _outFile_from_url(url, save_dir / f'{DATE:%Y%m%d}')

                # Download the data
                #------------------
                if searchString in [None, ':']:
                    if dryrun:
                        if not overwrite and outFile.exists():
                            if verbose: print(f'🌵 Dry Run! Already have file for --> {outFile}')
                            all_files.append(None)
                        else:
                            if verbose: print(f'🌵 Dry Run! Would get from [{source}] {url} --> {outFile}')
                            all_files.append(None)
                    else:
                        # Download the full file.
                        if not overwrite and outFile.exists():
                            if verbose: print(f'🌉 Already have file for --> {outFile}')
                            all_files.append(outFile)
                        else:
                            urllib.request.urlretrieve(url, outFile, _reporthook)
                            all_files.append(outFile)
                            if verbose: print(f'✅ Success! Downloaded from [{source}] {url} --> {outFile}')
                else:
                    # Download a subset of the full file based on the searchString.
                    if verbose: print(f"Download subset from [{source}]:")
                    thisfile = _download_hrrr_subset(url, searchString,
                                                    df_row_urls=row,
                                                    save_dir=outFile.parent,
                                                    dryrun=dryrun,
                                                    verbose=verbose)
                    all_files.append(thisfile)
                all_urls.append(url)
                break # because we downloaded a file and don't need it from another source

        if not one_exists:
            # The URL request is bad or file size is small and the file is not
            # available from any of the sources.
            print()
            print(f'❌ WARNING: Status code {head.status_code}: {head.reason}. Content-Length: {int(head.raw.info()["Content-Length"]):,} bytes')
            print(f"❌ Could not download file for [{model}] [{field}]. Tried to get the following:")
            for i, url in enumerate(row, start=1):
                print(f'    {i}: {url}')
            print('')

        #---------------------------------------------------------
        # Time keeping: *crude* method to estimate remaining time.
        #---------------------------------------------------------
        loop_time += datetime.now() - timer
        mean_dt_per_loop = loop_time/(index+1)
        remaining_loops = n-index-1
        est_rem_time = mean_dt_per_loop * remaining_loops
        if verbose: print(f"🚛💨 Download Progress: [{index+1}/{n} completed] >> Est. Time Remaining {str(est_rem_time):16}\n")
        #---------------------------------------------------------

    print(f"\n🍦 Finished 🍦  Time spent on download: {loop_time}")

    if len(all_files) == 1:
        return all_files[0], all_urls[0]  # return only the one time, not list
    else:
        return np.array(all_files), np.array(all_urls)  # return the list of file names and URLs

#=======================================================================
#=======================================================================

def xhrrr(DATE, searchString, fxx=0, *,
          DATE_is_valid_time=False,
          remove_grib2=True,
          add_crs=True,
          backend_kwargs={},
          **download_kwargs):
    """
    Download HRRR data and return as an xarray Dataset (or Datasets)

    You may only request one `DATE` and one `fxx` (forecast lead time).

    .. note::
        See https://github.com/ecmwf/cfgrib/issues/187 for why there is
        a problem with reading multiple accumulated precipitation
        fields when searchString=':APCP:'.

    Parameters
    ----------
    DATE : datetime
        A single datetime object.
    searchString: string
        A string representing a field or fields from the GRIB2 file.
        See more details in ``download_hrrr`` docstring.

        Some examples:

        ============================= ===============================================
        ``searchString``              Messages that will be downloaded
        ============================= ===============================================
        ':TMP:2 m'                    Temperature at 2 m.
        ':TMP:'                       Temperature fields at all levels.
        ':UGRD:.* mb'                 U Wind at all pressure levels.
        ':500 mb:'                    All variables on the 500 mb level.
        ':APCP:'                      All accumulated precipitation fields.
        ':APCP:surface:0-[1-9]*'      Accumulated precip since initialization time
        ':APCP:surface:[1-9]*-[1-9]*' Accumulated precip over last hour
        ':UGRD:10 m'                  U wind component at 10 meters.
        ':(U|V)GRD:'                  U and V wind component at all levels.
        ':.GRD:'                      (Same as above)
        ':(TMP|DPT):'                 Temperature and Dew Point for all levels .
        ':(TMP|DPT|RH):'              TMP, DPT, and Relative Humidity for all levels.
        ':REFC:'                      Composite Reflectivity
        ':surface:'                   All variables at the surface.
        ============================= ===============================================

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
        True  - (default) Add the Cartopy coordinate reference system (crs)
                projection as an attribute to the Dataset.
    **download_kwargs :
        Any other key word argument accepted by ``download_hrrr``.
            - model : {'hrrr', 'hrrrak', 'hrrrX'}
            - field : {'sfc', 'prs', 'nat', 'subh'}
            - save_dir : pathlib.Path
            - download_source_priority : a list of download sources
            - dryrun : bool
            - verbose : bool
    """
    # Convert DATE input to a pandas datetime (Pandas can parse some strings as dates.)
    DATE = pd.to_datetime(DATE)

    inputs = locals()

    assert not hasattr(DATE, '__len__'), "`DATE` must be a single datetime, not a list."
    assert not hasattr(fxx, '__len__'), "`fxx` must be a single integer, not a list."

    if DATE_is_valid_time:
        # Change DATE to the model run initialization DATE so that when we take
        # into account the forecast lead time offset, the the returned data
        # be valid for the DATE the user requested.
        DATE = DATE - timedelta(hours=fxx)

    # Download the GRIB2 file
    grib2file, url = download_hrrr(DATE, searchString, fxx=fxx, **download_kwargs)

    # Some extra backend kwargs for cfgrib
    backend_kwargs.setdefault('indexpath', '')
    backend_kwargs.setdefault('read_keys', ['parameterName', 'parameterUnits', 'stepRange'])
    backend_kwargs.setdefault('errors', 'raise')

    # Use cfgrib.open_datasets, just in case there are multiple "hypercubes"
    # for what we requested.
    H = cfgrib.open_datasets(grib2file, backend_kwargs=backend_kwargs)

    # Create a cartopy projection object
    if add_crs:
        crs = get_crs(H[0])

    for ds in H:
        ds.attrs['history'] = inputs
        ds.attrs['url'] = url

        # CF 1.8 map projection information for the HRRR model
        # http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#_lambert_conformal

        ##
        ## I'm not sure why, but when I assign an attribute for the main Dataset
        ## with a cartopy.crs and then copy it (for the remove_grib2 case),
        ## the cartopy.crs is reset to the default proj4_params.
        ## This isn't an issue when I set cartopy.crs as an attribute for
        ## a variable (DataArray).
        ## For this reason, I will return the 'crs' as an attribute for
        ## each variable's DataArray. Later, I will add the 'crs' as
        ## a Dataset attribute for convenience.
        ##

        ds.attrs['grid_mapping_name'] = 'lambert_conformal_conic'
        ds.attrs['standard_parallel'] = (38.5, 38.5)
        ds.attrs['longitude_of_central_meridian'] = 262.5
        ds.attrs['latitude_of_projection_origin'] = 38.5

        # This is redundant, but I want every variable to also have the
        # map projection information...
        for var in list(ds):
            ds[var].attrs['grid_mapping_name'] = 'lambert_conformal_conic'
            ds[var].attrs['standard_parallel'] = (38.5, 38.5)
            ds[var].attrs['longitude_of_central_meridian'] = 262.5
            ds[var].attrs['latitude_of_projection_origin'] = 38.5
            if add_crs:
                ds[var].attrs['crs'] = crs

    if remove_grib2:
        # Load the data to memory before removing the file
        H = [ds.load() for ds in H]
        # Ok, now we can remove the grib2 file
        os.remove(grib2file)

    if len(H) == 1:
        H = H[0]
        # Add the cartopy map projection object as an attribute, for convenience.
        H.attrs['crs'] = crs
    else:
        warnings.warn('⚠ ALERT! Could not load grib2 data into a single '
                      'xarray Dataset. You might consider refining your '
                      '`searchString` if you are getting data you do not need.')
        # Add the cartopy map projection object as an attribute, for convenience.
        for i in H:
            i.attrs['crs'] = crs

    return H
