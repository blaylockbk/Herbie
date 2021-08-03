===============
☁ Data Sources
===============

Thanks to the NOAA Big Data Project, more meteorological data is more easily accessible than ever before. Herbie enables you to download NWP model output from different data sources, wherever the data you are interested in is available. Because NWP data can be hosted on different remote servers, Herbie will look at different sources to find where a file exists. This is important when working with real-time versus archived data. For instance, model output on NOAMDS is only there for 2-14 days, depending on the model. 

Herbie sets a default "priority" that tells Herbie the order to search different sources for a file. The available data sources is defined for each model by the `model template file <https://github.com/blaylockbk/Herbie/tree/master/herbie/models>`_ and additional sources can be added. The default search order is `aws`, `nomads`, `google`, `azure`, `pando`, `pando2`.

For example, the following are the most popular data sources:

1. `AWS: Amazon Web Services <https://noaa-hrrr-bdp-pds.s3.amazonaws.com/>`_
    - Herbie string, `'aws'`.
    - NOAA Big Data Program
    - Slight latency for real-time products.

1. `NOMADS: NOAA Operational Model Archive and Distribution System <https://nomads.ncep.noaa.gov/>`_
    - Herbie string, `'nomads'`.
    - Available for today's and yesterday's runs
    - Real-time data.
    - Original data source. All available data included.
    - Download limits.

1. `Google: Google Cloud Platform Earth <https://console.cloud.google.com/storage/browser/high-resolution-rapid-refresh>`_
    - Herbie string, `'google'`.
    - NOAA Big Data Program
    - Slight latency for real-time products.

1. `Azure: Microsoft Azure <https://github.com/microsoft/AIforEarthDataSets/blob/main/data/noaa-hrrr.md>`_
    - Herbie string, `'azure'`.
    - NOAA Big Data Program
    - Only recent HRRR and RAP data?
    - Subset of HRRR and RAP data?

1. `Pando: The University of Utah HRRR archive <http://hrrr.chpc.utah.edu/>`_
    - Herbie string, `'pando'` and `'pando2'`.
    - Research archive. Older files being removed.

