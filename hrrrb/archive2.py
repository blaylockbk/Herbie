#!/usr/bin/env python3

## Brian Blaylock
## May 3, 2021

"""
=======================================
Retrieve HRRR GRIB2 files from archives
=======================================

Updates:
- 

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

import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from itertools import product
import warnings
import configparser

import urllib.request
import requests
import cfgrib
import numpy as np
import pandas as pd
import xarray as xr

from hrrrb.tools import to_180, get_crs

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

class GET_HRRR:
    
    def __init__(self, date, fxx=0, model='hrrr', field='sfc',
                 priority=['nomads', 'aws', 'google', 'pando', 'pando2']):
        date = pd.to_datetime(date)
        self.date = date
        self.fxx = fxx
        self.model = model
        self.field = field
        self.priority = priority
        
        self._validate()
                
        self.url = None
        self.idx = None
        
        for source in priority:
            print(f"Looking at {source}:", end=' ')
            
            if source in ['pando', 'pando2']:
                self._ping_pando()
            
            url = self.get_url(source)
            
            if self.url is None and self._check_grib(url):
                print(f'Found grib.', end=' ')
                self.url = url
                self.url_source = source
            if self.idx is None and self._check_idx(url):
                print(f'Found idx.')
                self.idx = url+'.idx'
                self.idx_source = source
            print()
            if all([self.url is not None, self.idx is not None]):
                break
    
    def __repr__(self):
        """Representation in Notebook"""
        return f"{self.model} model {self.field} fields run at {self.date:%H:%M UTC %d %b %Y} for F{self.fxx:02d}. "

    def __str__(self):
        """When class object is printed"""
        msg = [
            f'{self.model=}',
            f'{self.field=}',
            f'{self.fxx=}',
            f'{self.date=}',
        ]
        return '\n'.join(msg)
        
    def _validate(self):
        _models = ['hrrr', 'hrrrak', 'rap']
        _fields = ['prs', 'sfc', 'nat', 'subh']
        assert self.fxx in range(48), "Forecast lead time `fxx` is too large"
        assert self.model in _models, f"`model` must be one of {_models}"
        assert self.field in _fields, f"`field must be one of {_fields}"
    
    def _ping_pando(self):
        """Pinging the Pando server before downloading can prevent a bad handshake."""
        try:
            requests.head('https://pando-rgw01.chpc.utah.edu/')
        except:
            print('🤝🏻⛔ Bad handshake with pando? Am I able to move on?')
            pass
    
    def _check_grib(self, url):
        """grib2 file must exist and be of valid length"""
        head = requests.head(url)
        check_exists = head.ok
        if check_exists:
            check_content = int(head.raw.info()['Content-Length']) > 1_000_000
        else:
            cehck_content = False
        return check_exists and check_content
    
    def _check_idx(self, url):
        """does the .idx file exist?"""
        if not url.endswith('.idx'):
            url += '.idx'
        head = requests.head(url)
        check_exists = head.ok
        return check_exists
    
    def get_url(self, source):
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
        elif source.startswith('pando'):
            if source[-1] == '2':
                gateway = 2
            else:
                gateway = 1
            if self.model == 'rap':
                base = None
                path = None
            else:
                base = f'https://pando-rgw0{gateway}.chpc.utah.edu/'
                path = f"{self.model}/{self.field}/{self.date:%Y%m%d}/{self.model}.t{self.date:%H}z.wrf{self.field}f{self.fxx:02d}.grib2"
        
        url = base+path
        
        return url
    
    def read_idx(self, searchString=None):
        """read the index file"""
        import numpy as np

        r = requests.get(self.idx)
        if r.ok:
            read_idx = r.text.split('\n')
            df = pd.DataFrame([i.split(':') for i in read_idx[:-1]], 
                              columns=['grib_message', 'start_byte', 'reference_time', 'variable', 'level', 'forecast_time', 'none'])

            df['grib_message'] = df['grib_message'].astype(int)
            df['reference_time'] = pd.to_datetime(df.reference_time, format='d=%Y%m%d%H')
            df['valid_time'] = df['reference_time'] + pd.to_timedelta(f"{self.fxx}H")
            df['start_byte'] = df['start_byte'].astype(int)
            df['end_byte'] = df['start_byte'].shift(-1, fill_value='')
            df['range'] = df.start_byte.astype(str) + '-' + df.end_byte.astype(str)
            df = df.drop(columns='none')
            df = df.set_index('grib_message')
            df = df.reindex(columns=['start_byte', 'end_byte', 'range', 'reference_time', 'valid_time', 'variable', 'level', 'forecast_time'])
            df.attrs = dict(source=self.idx_source, description='Index (.idx) file for the GRIB2 file.', model=self.model, field=self.field, lead_time=self.fxx, datetime=self.date)
            if searchString not in [None, ':']:
                logic = df['variable'].str.cat(df['level'], ':').str.cat(df['forecast_time'], ':').str.contains(searchString)
                df = df.loc[logic]
            return df
            
        else:
            raise ValueError('Index File Does not Exist')
    
    def download(self, searchString=None, source=None, *,
                 save_dir=_default_save_dir, 
                 overwrite=False, verbose=True):
        """
        Download file from source.
        """
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

        def subset(searchString, outFile):
            """Download a subset via a searchString"""
            outFile = outFile.with_suffix('.grib2.subset')
            df = self.read_idx(searchString)
            for i, (msg, row) in enumerate(df.iterrows()):
                print(i, msg, row.range, row.variable, row.level)
                
                if i == 0:
                    # If we are working on the first item, overwrite the existing file.
                    curl = f'curl -s --range {row.range} {self.url} > {outFile}'
                else:
                    # If we are working on not the first item, append the existing file.
                    curl = f'curl -s --range {row.range} {self.url} >> {outFile}'
                os.system(curl)
            print(outFile)
            
        
        if source is not None:
            # Force download from a specified source and not from first in priority
            self.url = self.get_url(source)
            
        # Make save_dir if path doesn't exist
        if not hasattr(save_dir, 'exists'): 
            save_dir = Path(save_dir).resolve()
        save_dir = save_dir / self.model
                
        outFile = save_dir / f"{self.date:%Y%m%d}" / f"{self.date:%Y%m%d}_{self.url.split('/')[-1]}"
        if not outFile.parent.is_dir():
                outFile.parent.mkdir(parents=True, exist_ok=True)
                print(f'👨🏻‍🏭 Created directory: [{outFile.parent}]')
        
        if searchString in [None, ':']:
            # Download the full file
            if not overwrite and outFile.exists():
                if verbose: print(f'🌉 Already have file for --> {outFile}')
            else:
                urllib.request.urlretrieve(self.url, outFile, _reporthook)
                if verbose: print(f'✅ Success! Downloaded from [{self.url_source}] {self.url} --> {outFile}')
        else:
            df = subset(searchString, outFile)
            return df


###############################################################################
###############################################################################

def download_hrrr(DATES, searchString=None, fxx=range(0,1), model='hrrr', field='sfc'):
    
    ## Add a timer
    
    print(DATES, searchString, fxx, model, field)
    m = [GET_HRRR(d, fxx=f, model=model, field=field) for d in DATES for f in fxx]
    [i.download(searchString=searchString) for i in m]
    return m
    