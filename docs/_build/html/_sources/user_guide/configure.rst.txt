==============
🛠 Configure
==============

Some default settings are set in the ``config.toml`` file. This file is automatically created the first time you import a Herbie module and is located at ``${HOME}/.config/herbie/config.toml``. The configuration file is written in `TOML format <https://toml.io/en/>`_.

The default settings are 

.. code-block::

    [default]
    model = "hrrr"
    fxx = 0
    product = "sfc"
    priority = [ "aws", "nomads", "google", "azure", "pando", "pando2",]
    save_dir = "${CENTER}/data"
    overwrite = false
    verbose = true

Any of the default options can be overwritten when creating a new Herbie object.

model
    Model name as defined in the models template folder. CASE INSENSITIVE 
        
    Some examples:
    - ``'hrrr'`` HRRR contiguous United States model
    - ``'hrrrak'`` HRRR Alaska model (alias ``'alaska'``)
    - ``'rap'`` RAP model
    - ``'gfs'`` Global Forecast System (atmosphere)
    - ``'gfs_wave'`` Global Forecast System (wave)
    - ``'rrfs'`` Rapid Refresh Forecast System prototype
    - etc.
    
fxx
    Forecast lead time in hours. Available lead times depend on
    the model type and model version. Range is model and run 
    dependant.
    
product
    Output variable product file type. If not specified, will 
    use first product in model template file. CASE SENSITIVE.
    
    For example, the HRRR model has these products:
    - ``'sfc'`` surface fields
    - ``'prs'`` pressure fields
    - ``'nat'`` native fields
    - ``'subh'`` subhourly fields

member
    Some ensemble models (e.g. the future RRFS) will need to 
    specify an ensemble member.

priority
    List of data sources in the order of download priority. CASE INSENSITIVE. 
    
    For example:
    - ``'aws'`` Amazon Web Services (Big Data Program)
    - ``'nomads'`` NOAA NOMADS server
    - ``'google'`` Google Cloud Platform (Big Data Program)
    - ``'azure'`` Microsoft Azure (Big Data Program)
    - ``'pando'`` University of Utah Pando Archive (gateway 1)
    - ``'pando2'`` University of Utah Pando Archive (gateway 2)

save_dir
    Location to save GRIB2 files locally. You may use system environment variables like _${HOME}_, and _${TMPDIR}_

overwrite
    If true, look for GRIB2 file even if local copy exists.
    If false, use the local copy (still need to find the idx file).


Default Download Priority Rational
----------------------------------
The reason for this default is that I anticipate most often a user will request model output from the recent past or earlier rather than relying on Herbie for operational, real-time needs.

Much of the past data and near real-time data is archived at one of NOAA's Big Data partners. Amazon AWS in particular hosts many of these datasets. While, NOMADS is the official operational source of model output data and has the most recent model output available, NOMADS only retains data for a few days, they throttle the download speed, and will block users who violate their usage agreement and download too much data within an hour. For this 

To prevent being blocked by NOMADS, the default is to first look for data on AWS. If the data requested is within the last few hours and was not found on AWS, then Herbie will look for the data at NOMADS. If the data is still not found on NOMADS, the file may be on google, azure, or pando. 

If you _really_ want to download the real-time data from NOMADS first and not a Big Data Project partner, you may change the priority order in the herbie config file or set the priority argument when creating the Herbie object (e.g., ``priority=['nomads', ...]``).
