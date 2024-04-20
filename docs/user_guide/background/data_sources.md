# ☁ Data Sources

Thanks to the [NOAA Open Data Dissemination (NODD) Program](https://www.noaa.gov/nodd/about), meteorological data is made more easily accessible than ever before. Herbie enables you to discover and download NWP model output from different data sources. Because NWP data can be hosted on different remote servers with different availalbility, Herbie will look at different sources to find where a file you request exists. This is important when working with real-time versus archived data. For instance, model output on NOAMDS is only available for 2-14 days, depending on the model.

Herbie sets a default "priority" that tells Herbie the order to search different sources for a file. The available data sources are defined for each model by the [model template file](https://github.com/blaylockbk/Herbie/tree/master/herbie/models) and additional sources can be added. The default search order is `aws`, `nomads`, `google`, `azure`, `pando`, `pando2`.

For example, the following are the most popular data sources:

1. AWS: Amazon Web Services
    - Herbie source string, `"aws"`.
    - Website: <https://registry.opendata.aws/>
    - NODD Program
    - Slight latency for real-time products.

2. NOMADS: NOAA Operational Model Archive and Distribution System
    - Herbie source string, `"nomads"`.
    - Website: <https://nomads.ncep.noaa.gov/>
    - Original data source for NCEP models.
    - Lowest latency.
    - Limited archive period.
    - 🚨 ***Download limits.***

3. Google: Google Cloud Platform Earth
    - Herbie source string, `"google"`.
    - Website: <https://cloud.google.com/datasets>
    - NODD Program
    - Slight latency for real-time products.

4. Azure: Microsoft Azure
    - Herbie source string, `"azure"`.
    - Website: <https://github.com/microsoft/AIforEarthDataSets/>
    - NODD Program
    - ECMWF Open Data Program

5. Pando: The University of Utah HRRR archive
    - Herbie source string, `"pando"` and `"pando2"`.
    - Website: <http://hrrr.chpc.utah.edu/>
    - Research archive. 
    - Older files are being removed.

6. ECMWF Open Data
    - Herbie source string, `"ecmwf"`
    - Website: <https://confluence.ecmwf.int/display/UDOC/ECMWF+Open+Data+-+Real+Time>
    - ECMWF Open Data Program
