===============
☁ Data Sources
===============

Thanks to the NOAA Big Data Project, more meteorological data is more easily accessible than ever before. Herbie enables you to download NWP model output from different data sources, wherever the data you are interested in is available. Because NWP data can be hosted on different remote servers, Herbie will look at different sources to find where a file exists. This is important when working with real-time versus archived data. For instance, model output on NOAMDS is only there for 2-14 days, depending on the model. 

Herbie sets a default "download priority" that tells Herbie where to first look for a file you request. The data source is defined for each model by the `model template file <https://github.com/blaylockbk/Herbie/tree/master/herbie/models>`_ and additional sources can be added. The default search order is `aws`, `nomads`, `google`, `azure`, `pando`, `pando2`.

1. [AWS: Amazon Web Services](https://noaa-hrrr-bdp-pds.s3.amazonaws.com/)
    - Herbie string, `'aws'`.
    - NOAA Big Data Program
    - Slight latency for real-time products.

1. [NOMADS: NOAA Operational Model Archive and Distribution System](https://nomads.ncep.noaa.gov/)
    - Herbie string, `'nomads'`.
    - Available for today's and yesterday's runs
    - Real-time data.
    - Original data source. All available data included.
    - Download limits.

1. [Google: Google Cloud Platform Earth](https://console.cloud.google.com/storage/browser/high-resolution-rapid-refresh)
    - Herbie string, `'google'`.
    - NOAA Big Data Program
    - Slight latency for real-time products.

1. [Azure: Microsoft Azure](https://github.com/microsoft/AIforEarthDataSets/blob/main/data/noaa-hrrr.md)
    - Herbie string, `'azure'`.
    - NOAA Big Data Program
    - Only recent HRRR and RAP data?
    - Subset of HRRR and RAP data?

1. [Pando: The University of Utah HRRR archive](http://hrrr.chpc.utah.edu/)
    - Herbie string, `'pando'` and `'pando2'`.
    - Research archive. Older files being removed.


Default Download Priority Rational
----------------------------------
The reason for this default is that I anticipate most often a user will request model output from the recent past or earlier rather than relying on Herbie for operational, real-time needs.

Much of the past data and near real-time data is archived at one of NOAA's Big Data partners. Amazon AWS in particular hosts many of these datasets. While, NOMADS is the official operational source of model output data and has the most recent model output available, NOMADS only retains data for a few days, they throttle the download speed, and will block users who violate their usage agreement and download too much data within an hour. For this 

To prevent being blocked by NOMADS, the default is to first look for data on AWS. If the data requested is within the last few hours and was not found on AWS, then Herbie will look for the data at NOMADS. If the data is still not found on NOMADS, the file may be on google, azure, or pando. 

If you _really_ want to download the real-time data from NOMADS first and not a Big Data Project partner, you may change the priority order in the herbie config file or set the priority argument when creating the Herbie object (e.g., ``priority=['nomads', ...]``).

.. note::

    ✒ I wrote a paper about archiving HRRR model data in the cloud.
    
    Blaylock B., J. Horel and S. Liston, 2017: Cloud Archiving and Data
    Mining of High Resolution Rapid Refresh Model Output. Computers and
    Geosciences. 109, 43-50. https://doi.org/10.1016/j.cageo.2017.08.005

