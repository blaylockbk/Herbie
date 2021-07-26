# ☁ Data Sources

Herbie enables you to easily download HRRR and RAP data between these different data sources wherever the data you are interested in is available. The different download sources are listed below in the order of the default download priority.

## Default Download Priority Rational 
I anticipate that most often, a user will request model output from the recent past or earlier run rather than relying on this or operational, real-time needs. 

Past data and near real-time data is archived at one of NOAA's Big Data partners. NOMADS is the official operational source of model output data and has the most recent model output available. However, they throttle the download speed and will block users who violate their usage agreement and download too much data within an hour. 

To prevent being blocked by NOMADS, the default is to first look for data on AWS. If the data requested is within the last few hours and was not found on AWS, then Herbie will look for the data at NOMADS. If the requested data is older than yester, Herbie will not look for the data at NOMADS. If you really want to download in real-time from NOMADS first and not a Big Data Project partner, change the priority order so that NOMADS is first, (e.g., ``priority=['nomads', ...]``).

## HRRR and RAP Data Sources
Real-time HRRR and RAP data is available from NOMADS. At the end of 
2020, NOAA started pushing the HRRR and RAP data to the Google Cloud 
Platform and Amazon Web Services as part of the NOAA Big Data Progam.
These archives were backfilled to previous years as far back as 
July 30, 2014. A archive used for research purposes also exists 
on the University of Utah CHPC Pando Archive System.

> A paper about archiving model data in the cloud.
> 
> Blaylock B., J. Horel and S. Liston, 2017: Cloud Archiving and Data
> Mining of High Resolution Rapid Refresh Model Output. Computers and
> Geosciences. 109, 43-50. https://doi.org/10.1016/j.cageo.2017.08.005

1. [AWS: Amazon Web Services](https://noaa-hrrr-bdp-pds.s3.amazonaws.com/)
    - Herbie string, `'aws'`.
    - NOAA Big Data Program
    - Available from July 30, 2014 to Present.
    - Slight latency for real-time products.
    - Not all GRIB2 files have an .idx files.
    - Has all nat, subh, prs, and sfc files for all forecast hours.
    - Some data may be missing.

1. [NOMADS: NOAA Operational Model Archive and Distribution System](https://nomads.ncep.noaa.gov/)
    - Herbie string, `'nomads'`.
    - Available for today's and yesterday's runs
    - Real-time data.
    - Original data source. All available data included.
    - Download limits.
    - Includes GRIB2 .idx for all GRIB2 files.

1. [Google: Google Cloud Platform Earth](https://console.cloud.google.com/storage/browser/high-resolution-rapid-refresh)
    - Herbie string, `'google'`.
    - NOAA Big Data Program
    - Available from July 30, 2014 to Present.
    - Slight latency for real-time products.
    - Does not have GRIB2 .idx files before September 17, 2018.
    - Has all original data including nat, subh, prs, and sfc files 
      for all forecast hours.

1. [Azure: Microsoft Azure](https://github.com/microsoft/AIforEarthDataSets/blob/main/data/noaa-hrrr.md)
    - Herbie string, `'azure'`.
    - NOAA Big Data Program
    - Only recent HRRR and RAP data?
    - Subset of HRRR and RAP data?

1. [Pando: The University of Utah HRRR archive](http://hrrr.chpc.utah.edu/)
    - Herbie string, `'pando'` and `'pando2'`.
    - Research archive. Older files being removed.
    - A subset of prs and sfc files.
    - Contains .idx file for every GRIB2 file.

