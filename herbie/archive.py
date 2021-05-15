#!/usr/bin/env python3

## Brian Blaylock
## May 3, 2021

"""
=========================================================
Herbie: Download HRRR and RAP model output from the cloud
=========================================================

Herbie is your model output download assistant with a mind of his own!
Herbie might look small on the outside, but he has a big heart on the 
inside and will get you to the
`finish line <https://www.youtube.com/watch?v=4XWufUZ1mxQ&t=189s>`_ 🏁.

With Herbie's API, you can download High-Resolution Rapid Refresh (HRRR)
HRRR-Alaska, and Rapid Refresh (RAP) model GRIB2 files from different 
archive sources. Supports subsetting of GRIB2 files by individual GRIB
messages (i.e. variable and level) if the index (.idx) file exist.
Herbie looks for model output data from NOMADS, NOAA's Big Data Project 
partners (Amazon Web Services, Google Cloud Platform, and Microsoft 
Azure), and the CHPC Pando archive at the University of Utah.

.. note:: Updates since ``hrrrb``

    - Rename package to ``herbie``. "Herbie is your model output download assistant with a mind of its own."
    - Implement new **Herbie** class
    - Drop support for hrrrx (experimental HRRR no longer archived on Pando and ESRL is now developing RRFS)
    - Added ability to download and read RAP model GRIB2 files.
    - Less reliance on Pando, more on aws and google.
    - New method for searchString index file search. Uses same regex search patterns as old API.
    - Filename for GRIB2 subset includes all GRIB message numbers.
    - Moved default download source to config file setting.
    - Check local file copy on __init__. (Don't need to look for file on remote if we have local copy)
    - Option to remove grib2 file when reading xarray if didn't already exist locally (don't clutter local disk).
    - Attach index file DataFrame to object if it exists.
    - If full file exists locally, use remote idx file to cURL local file instead of remote. (Can't create idx file locally because wgrib2 not available on windows)
    - TODO: Rename 'searchString' to 'subset' (and rename subset function)
    - TODO: Add NCEI as a source for the RAP data?? URL is complex.
    - TODO: Create .idx file if wgrib2 is installed (linux only)

HRRR and RAP Data Sources
-------------------------
Real-time HRRR and RAP data is available from NOMADS. At the end of 
2020, NOAA started pushing the HRRR and RAP data to the Google Cloud 
Platform and Amazon Web Services as part of the NOAA Big Data Progam.
These archives were backfilled to previous years as far back as 
July 30, 2014. A archive used for research purposes also exists 
on the University of Utah CHPC Pando Archive System.

.. note::
    A paper about archiving model data in the cloud.

    Blaylock B., J. Horel and S. Liston, 2017: Cloud Archiving and Data
    Mining of High Resolution Rapid Refresh Model Output. Computers and
    Geosciences. 109, 43-50. https://doi.org/10.1016/j.cageo.2017.08.005

The Herbie module enables you to easily download HRRR and RAP data 
between these different data sources wherever the data you are 
interested in is available. The different download sources and the 
download priority order are listed below:

#. AWS: Amazon Web Services
    - https://noaa-hrrr-bdp-pds.s3.amazonaws.com/
    - Available from July 30, 2014 to Present.
    - Slight latency for real-time products.
    - Not all GRIB2 files have an .idx files.
    - Has all nat, subh, prs, and sfc files for all forecast hours.
    - Some data may be missing.

#. NOMADS: NOAA Operational Model Archive and Distribution System
    - https://nomads.ncep.noaa.gov/
    - Available for today's and yesterday's runs
    - Real-time data.
    - Original data source. All available data included.
    - Download limits.
    - Includes GRIB2 .idx for all GRIB2 files.

#. Google: Google Cloud Platform Earth
    - https://console.cloud.google.com/storage/browser/high-resolution-rapid-refresh
    - Available from July 30, 2014 to Present.
    - Slight latency for real-time products.
    - Does not have GRIB2 .idx files before September 17, 2018.
    - Has all original data including nat, subh, prs, and sfc files 
      for all forecast hours.

#. Azure: Microsoft Azure
    - https://github.com/microsoft/AIforEarthDataSets/blob/main/data/noaa-hrrr.md
    - Only recent HRRR and RAP data?
    - Subset of HRRR and RAP data?

#. Pando: The University of Utah HRRR archive
    - http://hrrr.chpc.utah.edu/
    - Research archive. Older files being removed.
    - A subset of prs and sfc files.
    - Contains .idx file for every GRIB2 file.

.. note:: **Default Download Priority Rational** 
    Most often, a user will request model output from a recent
    past or earlier run. Past data is archived at one of NOAA's Big 
    Data parters. NOMADS has the most recent model output available, 
    but they also throttle the download speed and will block users who
    violate their usage agreement and download too much data within
    an hour. To prevent being blocked by NOMADS, the default is to 
    first look for data on AWS. If the data requested is within the
    last few hours and was not found on AWS, then Herbie will look
    for the data at NOMADS. If you really want to download data 
    from NOMADS and not a Big Data Project partner, change the
    priority order so that NOMADS is first, (e.g.,
    ``priority=['nomads', ...]``).

"""
import os
from pathlib import Path
import warnings
from datetime import datetime, timedelta

import urllib.request
import requests
import cfgrib
import pandas as pd

# NOTE: These values are set in the config file at 
# ~/.config/herbie/config.cfg and are read in from the __init__ file.
from . import _default_save_dir
from . import _default_priority

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

class Herbie:
    """Find model output file location based on source priority."""

    def __init__(self, DATE, fxx=0, *, 
                 model='hrrr', field='sfc',
                 priority=_default_priority,
                 save_dir=_default_save_dir,
                 DATE_is_valid_time=False,
                 overwrite=False,
                 verbose=True):
        """
        Specify model output and find GRIB2 file at one of the sources.
        
        Parameters
        ----------
        DATE : pandas-parsable datetime
            Model initialization datetime if 
            ``DATE_is_valid_time=False`` (default) or forecast valid 
            datetime if ``DATE_is_valid_time=True``.
        fxx : int
            Forecast lead time in hours. Available lead times depend on
            the model type and model version. Range from 0 to 15, 18, 
            36, or 48 (model and run dependant).
        model : {'hrrr', 'hrrrak', 'rap'}
            Model type. 
            - ``'hrrr'`` HRRR contiguous United States model
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
        save_dir : str or pathlib.Path
            Location to save GRIB2 files locally. Default save directory
            is set in ``~/.config/herbie/config.cfg``.
        DATE_is_valid_time : bool
            If True, DATE represents the valid time.
            If False (default), DATE represents the initialization time.
        Overwrite : bool
            If True, look for GRIB2 files even if local copy exists.
            If False (default), use the local copy (still need to find 
            the idx file).
        """

        self.date = pd.to_datetime(DATE)
        self.fxx = fxx
        self.model = model.lower()
        self.field = field.lower()
        self.priority = priority
        self.save_dir = Path(save_dir).resolve()
        
        if DATE_is_valid_time:
            # The user-supplied DATE represents the forecast valid 
            # time. Adjust self.date by forecast lead time so it 
            # represents the model initialization datetime.
            self.date = self.date - timedelta(hours=self.fxx)

        self._validate()

        # self.grib is the first existing GRIB2 file discovered.
        # self.idx is the first existing index file discovered.
        self.grib = None
        self.grib_source = None
        self.idx = None
        self.idx_source = None
        
        # But first, check if the GRIB2 file exists locally.
        local_copy = self.get_localPath()
        if local_copy.exists() and not overwrite:
            self.grib = local_copy
            self.grib_source = 'local'
            # NOTE: We will still get the idx files from a remote.
        
        for source in self.priority:            
            if 'pando' in source:
                # Sometimes pando returns a bad handshake. Pinging
                # pando first can help prevent that.
                self._ping_pando()
            
            # Get the file URL for the source and determine if the 
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
                # Exit loop early if we found both GRIB2 and idx file.
                break

        if verbose: 
            if any([self.grib is not None, self.idx is not None]):
                print(f'🏋🏻‍♂️ Found',
                      f'\033[32m{self.date:%Y-%b-%d %H:%M UTC} F{self.fxx:02d}\033[m',
                      f'{self.model.upper()} {self.field}',
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
        msg = (f"{self.model.upper()} model {self.field} fields",
               f"run at \033[32m{self.date:%Y-%b-%d %H:%M UTC}",
               f"F{self.fxx:02d}\033[m")
        return ' '.join(msg)

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
        _fields = {'prs', 'sfc', 'nat', 'subh'}  # Only for HRRR and HRRR-AK
        
        assert self.date < datetime.utcnow(), "🔮 Date cannot be in the future."
        
        if self.model.lower() == 'alaska':
            self.model = 'hrrrak'

        assert self.fxx in range(49), "Forecast lead time `fxx` is too large"
        assert self.model in _models, f"`model` must be one of {_models}"
        if self.model in ['hrrr', 'hrrrak']:
            assert self.field in _fields, f"`field must be one of {_fields}"
        else:
            # field is not needed for RAP model.
            self.field = ''
        
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
        # Big Data Program Path Template
        BDP_path_template = {
            'rap': f'rap.{self.date:%Y%m%d}/rap.t{self.date:%H}z.awip32f{self.fxx:02d}.grib2',
            'hrrr': f"hrrr.{self.date:%Y%m%d}/conus/hrrr.t{self.date:%H}z.wrf{self.field}f{self.fxx:02d}.grib2",
            'hrrrak': f"hrrr.{self.date:%Y%m%d}/alaska/hrrr.t{self.date:%H}z.wrf{self.field}f{self.fxx:02d}.ak.grib2"
        }

        # Big Data Program Sources (and NOMADS)
        if source == 'nomads':
            if self.model == 'rap':
                base = f'https://nomads.ncep.noaa.gov/pub/data/nccf/com/rap/prod/'
                path = BDP_path_template[self.model]
            else:
                base = 'https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod/'
                path = BDP_path_template[self.model]
        elif source == 'aws':
            if self.model == 'rap':
                base = 'https://noaa-rap-pds.s3.amazonaws.com/'
                path = BDP_path_template[self.model]
            else:
                base = 'https://noaa-hrrr-bdp-pds.s3.amazonaws.com/'
                path = BDP_path_template[self.model]
        elif source == 'google':
            if self.model == 'rap':
                base = 'https://storage.googleapis.com/rapid-refresh/'
                path = BDP_path_template[self.model]
            else:
                base = 'https://storage.googleapis.com/high-resolution-rapid-refresh/'
                path = BDP_path_template[self.model]
        elif source == 'azure':
            if self.model == 'rap':
                base = 'https://noaarap.blob.core.windows.net/rap'
                path = BDP_path_template[self.model]
            else:
                base = 'https://noaahrrr.blob.core.windows.net/hrrr/'
                path = BDP_path_template[self.model]
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

    @property
    def get_remoteFileName(self):
        """Predict Remote File Name"""
        return self.get_url('nomads').split('/')[-1]  # predict name based on nomads source

    @property
    def get_localFileName(self):
        """Predict Local File Name"""
        return f"{self.date:%Y%m%d}_{self.get_remoteFileName}"

    def get_localPath(self, searchString=None):
        """Get path to local file"""
        outFile = self.save_dir / self.model / f"{self.date:%Y%m%d}" / self.get_localFileName
        if searchString is not None:
            # Reassign the index DataFrame with the requested searchString
            self.idx_df = self.read_idx(searchString)

            # Get a list of all GRIB message numbers. We will use this
            # in the output file name as a unique identifier.
            all_grib_msg = '-'.join([f"{i:g}" for i in self.idx_df.index])

            # Append the filename to distinguish it from the full file.
            outFile = outFile.with_suffix(f'.grib2.subset_{all_grib_msg}')
        
        return outFile

    def read_idx(self, searchString=None):
        """
        Inspect the GRIB2 file contents by reading the index file.
        
        Parameters
        ----------
        searchString : str
            Filter dataframe by a searchString regular expression.
            Searches for strings in the index file lines, specifically
            the variable, level, and forecast_time columns.
            Execute ``_searchString_help()`` for examples of a good
            searchString.

            .. include:: ~/searchString_help.rst
        
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
        df['grib_message'] = df['grib_message'].astype(float)  # float because RAP idx files have some decimal grib message numbers
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
                 save_dir=None, 
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
            the first location the GRIB2 file was found from the 
            priority lists when this class was initialized. Else, you 
            may specify the source to force downloading it from a 
            different location.

            .. include:: ~/searchString_help.rst

        save_dir : str or pathlib.Path
            Location to save the model output files.
            If None, uses the default or path specified in __init__.
            Else, changes the path files are saved.
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
            grib_source = self.grib
            if hasattr(grib_source, 'as_posix') and grib_source.exists():
                # The GRIB source is local. Curl the local file
                # See https://stackoverflow.com/a/21023161/2383070
                grib_source = f"file://{str(self.grib)}"
            print(f'📇 Download subset: {self.__repr__()}{" ":60s}\n cURL from {grib_source}')

            # Download subsets of the file by byte range with cURL.
            for i, (grbmsg, row) in enumerate(self.idx_df.iterrows()):
                print(f"{i+1:>4g}: GRIB_message={grbmsg:<3g} \033[34m{row.variable}:{row.level}:{row.forecast_time}\033[m")
                if i == 0:
                    # If we are working on the first item, overwrite the existing file...
                    curl = f'curl -s --range {row.range} {grib_source} > {outFile}'
                else:
                    # ...all other messages are appended to the subset file.
                    curl = f'curl -s --range {row.range} {grib_source} >> {outFile}'
                os.system(curl)

            self.local_grib_subset = outFile
        
        # If the file exists in the localPath and we don't want to 
        # overwrite, then we don't need to download it.
        outFile = self.get_localPath(searchString=searchString)
        if outFile.exists() and not overwrite:
            if verbose: print(f'🌉 Already have local copy --> {outFile}')
            if searchString in [None, ':']:
                self.local_grib = outFile
            else:
                self.local_grib_subset = outFile
            return

        # Attach the index file to the object (how much overhead is this?)
        self.idx_df = self.read_idx(searchString)

        # This overwrites the save_dir specified in __init__
        if save_dir is not None:
            self.save_dir = save_dir
        if not hasattr(self.save_dir, 'exists'): 
            self.save_dir = Path(self.save_dir).resolve()

        # Check that data exists
        if self.grib is None:
            msg = f'🦨 GRIB2 file not found: {self.model=} {self.date=} {self.fxx=}'
            if errors == 'warn':
                warnings.warn(msg)
                return # Can't download anything without a GRIB file URL.
            elif errors == 'raise':
                raise ValueError(msg)
        if self.idx is None and searchString is not None:
            msg = f'🦨 Index file not found; cannot download subset: {self.model=} {self.date=} {self.fxx=}'
            if errors == 'warn':
                warnings.warn(msg+' I will download the full file because I cannot subset.')
            elif errors == 'raise':
                raise ValueError(msg)

        if source is not None:
            # Force download from a specified source and not from first in priority
            self.grib = self.get_url(source)
            
        # Create directory if it doesn't exist
        if not outFile.parent.is_dir():
            outFile.parent.mkdir(parents=True, exist_ok=True)
            print(f'👨🏻‍🏭 Created directory: [{outFile.parent}]')
        
        if searchString in [None, ':'] or self.idx is None:
            # Download the full file from remote source
            urllib.request.urlretrieve(self.grib, outFile, _reporthook)
            if verbose: print(f'✅ Success! Downloaded {self.model.upper()} from \033[38;5;202m{self.grib_source:20s}\033[m\n\tsrc: {self.grib}\n\tdst: {outFile}')
            self.local_grib = outFile
        else:
            # Download a subset of the file
            subset(searchString, outFile)

    def xarray(self, searchString, backend_kwargs={}, remove_grib=True, **download_kwargs):
        """
        Open GRIB2 data as xarray DataSet
        
        Parameters
        ----------
        searchString : str
            Variables to read into xarray Dataset
        remove_grib : bool
            If True, grib file will be removed ONLY IF it didn't exist
            before we downloaded it.
        """

        download_kwargs = {**dict(overwrite=False), **download_kwargs}

        # Download file if local file does not exists
        local_file = self.get_localPath(searchString=searchString)
        
        # Only remove grib if it didn't exists before we download it
        remove_grib = not local_file.exists() and remove_grib

        if not local_file.exists() or download_kwargs['overwrite']:
            self.download(searchString=searchString, **download_kwargs)

        # Backend kwargs for cfgrib
        backend_kwargs.setdefault('indexpath', '')
        backend_kwargs.setdefault('read_keys', ['parameterName', 'parameterUnits', 'stepRange'])
        backend_kwargs.setdefault('errors', 'raise')

        # Use cfgrib.open_datasets, just in case there are multiple "hypercubes"
        # for what we requested.
        Hxr = cfgrib.open_datasets(self.get_localPath(searchString=searchString),
                                 backend_kwargs=backend_kwargs)

        for h in Hxr:
            h.attrs['model'] = self.model
            h.attrs['remote_grib'] = self.grib
            h.attrs['local_grib'] = self.get_localPath(searchString=searchString)

        if remove_grib:
            # Load the data to memory before removing the file
            Hxr = [ds.load() for ds in Hxr]
            # Only remove grib if it didn't exists before
            local_file.unlink()  # Removes file

        if len(Hxr) == 1:
            return Hxr[0]
        else:
            return Hxr
        
