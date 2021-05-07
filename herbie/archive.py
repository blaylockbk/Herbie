#!/usr/bin/env python3

## Brian Blaylock
## May 3, 2021

"""
=========================================================
Herbie: Download HRRR and RAP Model Output from the cloud
=========================================================

Herbie is your model output download assistant with a mind of his own!
Herbie might look small on the outside, but he has a big heart on the 
inside and will get you to the 
`finish line <https://www.youtube.com/watch?v=4XWufUZ1mxQ&t=189s>`_ 🏁.

With Herbie's help you can download High-Resolution Rapid Refresh (HRRR)
HRRR-Alaska, and Rapid Refresh (RAP) model GRIB2 files from different 
archive sources. Supports subsetting of GRIB2 files by individual GRIB
messages (i.e. variable and level) if the index (.idx) file exist.
Herbie looks for model output data from NOMADS, NOAA's Big Data Project 
partners (Amazon Web Services, Google Cloud Platform, and Microsoft 
Azure), and the CHPC Pando archive at the University of Utah.

.. note:: Updates since ``hrrrb``
    - Rename package to ``herbie``. "Herbie is your model output download assistant with a mind of its own."
    - Implement new **ModelOuputSource** class
    - Drop support for hrrrx (no longer archived on Pando and ESRL is developing RRFS)
    - Added RAP model
    - Less reliance on Pando, more on aws and google.
    - New method for searchString index file search.
    - Subset file name retain GRIB message numbers included
    - TODO: check local file copy on class init

HRRR and RAP Data Sources
-------------------------
Real-time HRRR and RAP data is available from NOMADS. At the end of 
2020, NOAA started pushing the HRRR and RAP data to the Google Cloud 
Platform and Amazon Web Services as part of the NOAA Big Data Progam.
These archives were backfilled to previous years as far back as 
July 30, 2014. A limited archive used for research purposes also exists 
on the University of Utah CHPC Pando Archive System. 

This module enable you to easily download HRRR and RAP data between
these different data sources wherever the data you are interested in
is available. The default download source priority and some attributes
of the data sources is listed below:

1. NOMADS: NOAA Operational Model Archive and Distribution System
    - https://nomads.ncep.noaa.gov/
    - Available for today's and yesterday's runs
    - Real-time data.
    - Original data source. All available data included.
    - Download limits.
    - Includes GRIB2 .idx for all GRIB2 files.

2. AWS: Amazon Web Services
    - https://noaa-hrrr-bdp-pds.s3.amazonaws.com/
    - Available from July 30, 2014 to Present.
    - Slight latency for real-time products.
    - Not all GRIB2 files have an .idx files.
    - Has all nat, subh, prs, and sfc files for all forecast hours.
    - Some data may be missing.

3. Google: Google Cloud Platform Earth
    - https://console.cloud.google.com/storage/browser/high-resolution-rapid-refresh
    - Available from July 30, 2014 to Present.
    - Slight latency for real-time products.
    - Does not have GRIB2 .idx files before September 17, 2018.
    - Has all original data including nat, subh, prs, and sfc files 
      for all forecast hours.

4. Azure: Microsoft Azure
    - https://github.com/microsoft/AIforEarthDataSets/blob/main/data/noaa-hrrr.md
    - Only recent HRRR and RAP data?
    - Subset of HRRR and RAP data?

5. Pando: The University of Utah HRRR archive
    - http://hrrr.chpc.utah.edu/
    - Research archive. Older files being removed.
    - A subset of prs and sfc files.
    - Contains .idx file for every GRIB2 file.

"""
import os
from pathlib import Path
import warnings
from datetime import datetime, timedelta

import urllib.request
import requests
import cfgrib
import numpy as np
import pandas as pd
import xarray as xr

# NOTE: The `_default_save_dir` is defined in __init__.py and set in 
# the config file at ~/.config/herbie/config.cfg.
from . import _default_save_dir

def _searchString_help():
    """Help/Error Message for `searchString`"""
    msg = [
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

class ModelOutputSource:
    """
    Custom class to find model output file location based on source priority.

    .. note:: **Default Download Priority Rational** 
        Most often, a user will request model output from the recent
        past or earlier. Past data is archived at one of NOAA's Big Data
        parters. NOMADS has the most recent model output available, but
        they also throttle the download speed and will block users who
        violate their usage agreement and download too much data within
        an hour. To prevent being blocked by NOMADS, the default is to 
        first look for data on AWS. If the data requested is within the
        last few hours and was not found on AWS, then Herbie will look
        for the data at NOMADS. If you really want to download data 
        from NOMADS and not a Big Data Project partner, change the
        priority order so that NOMADS is first, (e.g.,
        ``priority=['nomads', ...]``).
    """
    _default_priority = ['aws', 'nomads', 'google', 'azure', 'pando', 'pando2']

    def __init__(self, DATE, fxx=0, *, 
                 model='hrrr', field='sfc',
                 priority=_default_priority,
                 verbose=True):
        """
        Specify model output and find grib2 file at one of the sources.
        
        Parameters
        ----------
        DATE : pandas-parsable datetime
            Initialization date.
        fxx : int
            Forecast lead time in hours. 
            Available lead times depend on the HRRR version and
            range from 0 to 15, 18, 36, or 48.
        model : {'hrrr', 'hrrrak', 'rap'}
            Model type. 
            - ``'hrrr'`` operational HRRR contiguous United States model.
            - ``'hrrrak'`` HRRR Alaska model (alias ``'alaska'``)
            - ``'rap'`` RAP model
        field : {'sfc', 'prs', 'nat', 'subh'}
            Output variable field file type. In the HRRR model, the
            different field files have certain variables at levels. 
            Not required for the RAP model as all variables are in the 
            same file.
            - ``'sfc'`` surface fields
            - ``'prs'`` pressure fields
            - ``'nat'`` native fields
            - ``'subh'`` subhourly fields
        priority : list or str
            List of model sources to get the data in the order of 
            download priority. The available data sources and default
            priority order are listed below.
            - ``'aws'`` Amazon Web Services (Big Data Program)
            - ``'nomads'`` NOAA's NOMADS server
            - ``'google'`` Google Cloud Platform (Big Data Program)
            - ``'azure'`` Microsoft Azure (Big Data Program)
            - ``'pando'`` University of Utah Pando Archive (gateway 1)
            - ``'pando2'`` University of Utah Pando Archive (gateway 2)
        """

        self.date = DATE
        self.fxx = fxx
        self.model = model.lower()
        self.field = field.lower()
        self.priority = priority
        
        self._validate()

        # url is the first existing source URL for the desired model output.
        # idx is the first existing index file for the desired model output.
        # These are initially set to None, but will look for files in the
        # for loop.
        self.grib = None
        self.idx = None
        self.grib_source = None
        self.idx_source = None
        
        for source in self.priority:            
            if source in ['pando', 'pando2']:
                # Sometimes pando returns a bad handshake. Pinging
                # pando first can help prevent that.
                self._ping_pando()
            
            # First get the file URL for the source and determine if the 
            # GRIB2 file and the index file exist. If found, store the
            # URL for the GRIB2 file and the .idx file.
            url = self.get_url(source)
            
            found_grib = False
            found_idx = False
            if self.grib is None and self._check_grib(url):
                found_grib = True
                self.grib = url
                self.grib_source = source
            if self.idx is None and self._check_idx(url):
                found_idx = True
                self.idx = url+'.idx'
                self.idx_source = source
            
            if verbose:
                msg = (f"Looked in [{source:^10s}] for {self.model.upper()} "
                    f"{self.date:%H:%M UTC %d %b %Y} F{self.fxx:02d} "
                    f"--> ({found_grib=}) ({found_idx=}) {' ':5s}")
                if verbose: print(msg, end='\r', flush=True)
            
            if all([self.grib is not None, self.idx is not None]):
                break
        if verbose: 
            if any([self.grib is not None, self.idx is not None]):
                print(f'🏋🏻‍♂️ Found',
                      f'\033[32m{self.date:%Y-%b-%d %H:%M UTC} F{self.fxx:02d}\033[m',
                      f'{self.model.upper()}',
                      f'GRIB2 file from \033[38;5;202m{self.grib_source}\033[m and',
                      f'index file from \033[38;5;202m{self.idx_source}\033[m.',
                      f'{" ":100s}')
            else:
                print(f'💔 Did not find a GRIB2 or Index File for',
                      f'\033[32m{self.date:%Y-%b-%d %H:%M UTC} F{self.fxx:02d}\033[m',
                      f'{self.model.upper()}',
                      f'{" ":100s}')

    def __repr__(self):
        """Representation in Notebook"""
        return f"{self.model.upper()} model {self.field} fields run at \033[32m{self.date:%Y-%b-%d %H:%M UTC} F{self.fxx:02d}\033[m"

    def __str__(self):
        """When class object is printed"""
        msg = [
            f'{self.model=}',
            f'{self.field=}',
            f'{self.fxx=}',
            f'{self.date=}',
            f'{self.priority=}',
        ]
        return '\n'.join(msg)
        
    def _validate(self):
        """Validate the class input arguments"""
        _models = {'hrrr', 'hrrrak', 'rap'}
        _fields = {'prs', 'sfc', 'nat', 'subh'}
        
        self.date = pd.to_datetime(self.date)
        
        if self.model == 'alaska':
            self.model == 'hrrrak'
        
        assert self.fxx in range(49), "Forecast lead time `fxx` is too large"
        assert self.model in _models, f"`model` must be one of {_models}"
        assert self.field in _fields, f"`field must be one of {_fields}"
        
        if isinstance(self.priority, str):
            self.priority = [self.priority]
        
        self.priority = [i.lower() for i in self.priority]

        # Don't look for data from NOMADS if requested date is earlier
        # than yesterday. NOMADS doesn't keep data that old.
        if 'nomads' in self.priority:
            yesterday = datetime.utcnow() - timedelta(hours=24)
            yesterday = pd.to_datetime(f"{yesterday:%Y-%m-%d}")
            if self.date < yesterday:
                self.priority.remove('nomads')
    
    def _ping_pando(self):
        """Pinging the Pando server before downloading can prevent a bad handshake."""
        try:
            requests.head('https://pando-rgw01.chpc.utah.edu/')
        except:
            print('🤝🏻⛔ Bad handshake with pando? Am I able to move on?')
            pass
    
    def _check_grib(self, url):
        """Check that the GRIB2 URL exist and is of useful length."""
        head = requests.head(url)
        check_exists = head.ok
        if check_exists:
            check_content = int(head.raw.info()['Content-Length']) > 1_000_000
            return check_exists and check_content
        else:
            return False
    
    def _check_idx(self, url):
        """Check if an index file exist for the GRIB2 URL."""
        if not url.endswith('.idx'):
            url += '.idx'
        return requests.head(url).ok
    
    def get_url(self, source):
        """
        Build the URL for the GRIB2 file for the requested file and data source.
        
        Parameters
        ----------
        source : {'aws', 'nomads', 'google', 'azure', 'pando', 'pando2'}
            The data download source for the RAP and HRRR models. 
            - ``'aws'`` Amazon Web Services (Big Data Program)
            - ``'nomads'`` NOAA's NOMADS server
            - ``'google'`` Google Cloud Platform (Big Data Program)
            - ``'azure'`` Microsoft Azure (Big Data Program)
            - ``'pando'`` University of Utah Pando Archive (gateway 1)
            - ``'pando2'`` University of Utah Pando Archive (gateway 2)
        """
        if source == 'nomads':
            if self.model == 'rap':
                base = 'https://nomads.ncep.noaa.gov/pub/data/nccf/com/rap/prod/'
                path = f'rap.{self.date:%Y%m%d}/rap.t{self.date:%H}z.awip32f{self.fxx:02d}.grib2'
            else:
                base = 'https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod/'
                if self.model == 'hrrr':
                    path = f"hrrr.{self.date:%Y%m%d}/conus/hrrr.t{self.date:%H}z.wrf{self.field}f{self.fxx:02d}.grib2"
                elif self.model == 'hrrrak':
                    path = f"hrrr.{self.date:%Y%m%d}/alaska/hrrr.t{self.date:%H}z.wrf{self.field}f{self.fxx:02d}.ak.grib2"
        elif source == 'aws':
            if self.model == 'rap':
                base = 'https://noaa-rap-pds.s3.amazonaws.com/'
                path = f'rap.{self.date:%Y%m%d}/rap.t{self.date:%H}z.awip32f{self.fxx:02d}.grib2'
            else:
                base = 'https://noaa-hrrr-bdp-pds.s3.amazonaws.com/'
                if self.model == 'hrrr':
                    path = f"hrrr.{self.date:%Y%m%d}/conus/hrrr.t{self.date:%H}z.wrf{self.field}f{self.fxx:02d}.grib2"
                elif self.model == 'hrrrak':
                    path = f"hrrr.{self.date:%Y%m%d}/alaska/hrrr.t{self.date:%H}z.wrf{self.field}f{self.fxx:02d}.ak.grib2"
        elif source == 'google':
            if self.model == 'rap':
                base = 'https://storage.googleapis.com/rapid-refresh/'
                path = f'rap.{self.date:%Y%m%d}/rap.t{self.date:%H}z.awip32f{self.fxx:02d}.grib2'
            else:
                base = 'https://storage.googleapis.com/high-resolution-rapid-refresh/'
                if self.model == 'hrrr':
                    path = f"hrrr.{self.date:%Y%m%d}/conus/hrrr.t{self.date:%H}z.wrf{self.field}f{self.fxx:02d}.grib2"
                elif self.model == 'hrrrak':
                    path = f"hrrr.{self.date:%Y%m%d}/alaska/hrrr.t{self.date:%H}z.wrf{self.field}f{self.fxx:02d}.ak.grib2"
        elif source == 'azure':
            if self.model == 'rap':
                base = 'https://noaarap.blob.core.windows.net/rap'
                path = f'rap.{self.date:%Y%m%d}/rap.t{self.date:%H}z.awip32f{self.fxx:02d}.grib2'
            else:
                base = 'https://noaahrrr.blob.core.windows.net/hrrr/'
                if self.model == 'hrrr':
                    path = f"hrrr.{self.date:%Y%m%d}/conus/hrrr.t{self.date:%H}z.wrf{self.field}f{self.fxx:02d}.grib2"
                elif self.model == 'hrrrak':
                    path = f"hrrr.{self.date:%Y%m%d}/alaska/hrrr.t{self.date:%H}z.wrf{self.field}f{self.fxx:02d}.ak.grib2"
        elif source.startswith('pando'):
            if source[-1] == '2':
                gateway = 2
            else:
                gateway = 1
            if self.model == 'rap':
                return None  # No RAP data on Pando
            else:
                base = f'https://pando-rgw0{gateway}.chpc.utah.edu/'
                path = f"{self.model}/{self.field}/{self.date:%Y%m%d}/{self.model}.t{self.date:%H}z.wrf{self.field}f{self.fxx:02d}.grib2"
               
        return base+path
    
    def read_idx(self, searchString=None):
        """
        Inspect the GRIB2 file contents by reading the index file.
        
        Parameters
        ----------
        searchString : str
            Filter dataframe by a searchString regular expression.
            Searches for strings in the index file lines, specifically
            the variable, level, and forecast_time columns.
            Execute ``_searchString_help()` for examples of a good
            searchString.
        
        Returns
        -------
        A Pandas DataFrame of the index file.
        """
        assert self.idx is not None, f"No index file for {self.grib}."
        
        # Open the idx file
        r = requests.get(self.idx)
        assert r.ok, f"Index file does not exist: {self.idx}"   

        read_idx = r.text.split('\n')[:-1]  # last line is empty
        df = pd.DataFrame([i.split(':') for i in read_idx], 
                            columns=['grib_message', 'start_byte', 
                                     'reference_time', 'variable', 
                                     'level', 'forecast_time', 'none'])

        # Format the DataFrame
        df['grib_message'] = df['grib_message'].astype(int)
        df['reference_time'] = pd.to_datetime(df.reference_time, format='d=%Y%m%d%H')
        df['valid_time'] = df['reference_time'] + pd.to_timedelta(f"{self.fxx}H")
        df['start_byte'] = df['start_byte'].astype(int)
        df['end_byte'] = df['start_byte'].shift(-1, fill_value='')
        df['range'] = df.start_byte.astype(str) + '-' + df.end_byte.astype(str)
        df = df.drop(columns='none')
        df = df.set_index('grib_message')
        df = df.reindex(columns=['start_byte', 'end_byte', 'range', 
                                 'reference_time', 'valid_time', 
                                 'variable', 'level', 'forecast_time'])
        df.attrs = dict(
            source=self.idx_source, 
            description='Index (.idx) file for the GRIB2 file.', 
            model=self.model, 
            field=self.field, 
            lead_time=self.fxx, 
            datetime=self.date
        )

        # Filter DataFrame by searchString
        if searchString not in [None, ':']:
            columns_to_search = df[['variable', 'level', 'forecast_time']].apply(lambda x: ':'.join(x), axis=1)
            logic = columns_to_search.str.contains(searchString)
            if logic.sum() == 0:
                print(f"No GRIB messages found. There might be something wrong with {searchString=}")
                print(_searchString_help(searchString))
            df = df.loc[logic]
        return df
    
    def download(self, searchString=None, source=None, *,
                 save_dir=_default_save_dir, 
                 overwrite=False, verbose=True,
                 errors='warn'):
        """
        Download file from source.

        Parameters
        ----------
        searchString : str
            If None, download the full file. Else, use regex to subset
            the file by specific variables and levels.
        source : {'nomads', 'aws', 'google', 'azure', 'pando', 'pando2'}
            If None, download GRIB2 file from self.grib2 which is
            the first place the GRIB2 file was found when this class
            was initialized. Else, you may specify the source to force
            downloading it from a different location.
        save_dir : str or pathlib.Path
            Location to save the model output files.
        overwrite : bool
            If True, overwrite existing files. Default will skip
            downloading if the full file exists. Not applicable when
            when searchString is not None because file subsets might 
            be unique.
        errors : {'warn', 'raise'}
            When an error occurs, send a warning or raise a value error.
        """
        def _reporthook(a, b, c):
            """
            Print download progress in megabytes.

            Parameters
            ----------
            a : Chunk number
            b : Maximum chunk size
            c : Total size of the download
            """
            chunk_progress = a * b / c * 100
            total_size_MB =  c / 1000000.
            print(f"\r🚛💨  Download Progress: {chunk_progress:.2f}% of {total_size_MB:.1f} MB\r", end='')

        def subset(searchString, outFile):
            """Download a subset specified by the regex searchString"""
            print(f'📇 Download subset: {self.__repr__()}{" ":60s}')
            
            df = self.read_idx(searchString)
            
            # Get a list of all GRIB message numbers. We will use this
            # in the output file name as a unique identifier.
            all_grib_msg = '-'.join(df.index.astype(str))

            # Append the filename to distinguish it from the full file.
            outFile = outFile.with_suffix(F'.grib2.subset_{all_grib_msg}')
            
            if not overwrite and outFile.exists():
                if verbose: print(f'🌉 Already have local copy --> {outFile}')
                self.local_grib_subset = outFile
            else:
                # Download subsets of the file by byte range with cURL.
                for i, (grbmsg, row) in enumerate(df.iterrows()):
                    print(f"{i+1:>4g}: GRIB_message={grbmsg:<3g} \033[34m{row.variable}:{row.level}:{row.forecast_time}\033[m")
                    if i == 0:
                        # If we are working on the first item, overwrite the existing file...
                        curl = f'curl -s --range {row.range} {self.grib} > {outFile}'
                    else:
                        # ...all other messages are appended to the subset file.
                        curl = f'curl -s --range {row.range} {self.grib} >> {outFile}'
                    os.system(curl)

                self.local_grib_subset = outFile
        
        # Check that data exists
        if self.grib is None:
            msg = f'🦨 GRIB2 file not found: {self.model=} {self.date=} {self.fxx=}'
            if errors == 'warn':
                warnings.warn(msg)
                return # Can't download anything without a GRIB file URL.
            elif errors == 'raise':
                raise ValueError(msg)
        if self.idx is None and searchString is not None:
            msg = f'🦨 Index file not found: {self.model=} {self.date=} {self.fxx=}'
            if errors == 'warn':
                warnings.warn(msg+' I will download the full file because I cannot subset.')
            elif errors == 'raise':
                raise ValueError(msg)

        if source is not None:
            # Force download from a specified source and not from first in priority
            self.grib = self.get_url(source)
            
        # Make save_dir if path doesn't exist
        if not hasattr(save_dir, 'exists'): 
            save_dir = Path(save_dir).resolve()
        save_dir = save_dir / self.model
                
        outFile = save_dir / f"{self.date:%Y%m%d}" / f"{self.date:%Y%m%d}_{self.grib.split('/')[-1]}"
        if not outFile.parent.is_dir():
                outFile.parent.mkdir(parents=True, exist_ok=True)
                print(f'👨🏻‍🏭 Created directory: [{outFile.parent}]')
        
        if searchString in [None, ':'] or self.idx is None:
            # Download the full file
            if not overwrite and outFile.exists():
                if verbose: print(f'🌉 Already have local copy --> {outFile}')
                self.local_grib = outFile
            else:
                urllib.request.urlretrieve(self.grib, outFile, _reporthook)
                if verbose: print(f'✅ Success! Downloaded from [{self.grib_source}] {self.grib} --> {outFile}')
                self.local_grib = outFile
        else:
            subset(searchString, outFile)

    def to_xarray(self, searchString, remove_grib=True):
        """
        FUTURE WORK
        
        Download data and read as xarray
        
        Parameters
        ----------
        searchString : str
            Variables to read into xarray Dataset
        remove_grib : bool
            Remove GRIB2 file after it is read in.
        """
        print('nothing here yet')
        pass

###############################################################################
###############################################################################

def download(DATES, searchString=None, *, fxx=range(0,1), 
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
        List of forecast lead times to download.
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
    grib_sources = [ModelOutputSource(d, fxx=f, **kw) \
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

def xget(DATE, searchString, fxx=0, *, 
         is_valid_time=False,
         remove_grib=True, backend_kwargs={}, **download_kwargs):
    r"""
    Download subset of model output and open with xarray/cfgrib.

    Parameters
    ----------
    DATE : datetime
        Model initialization datetime (if is_valid_time is False).
        Model valid datetime (if is_valid_time is True).
    searchString : str
    fxx : int
    remove_grib : bool
        remove file after downloading it
    backend_kwargs : dict
    **download_kwargs
    """
    print('nothing here yet')
    pass