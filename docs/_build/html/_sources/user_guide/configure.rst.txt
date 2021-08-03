==============
🛠 Configure
==============

Some default settings are set in the ``config.toml`` file. This file is automatically created the first time you import a Herbie module and is located at ``${HOME}/.config/herbie/config.toml``. The configuration file is written in `TOML format <https://toml.io/en/>`_.

The default settings are 

.. code-block::

    [default]
    save_dir = "${HOME}/data"
    priority = [ "aws", "nomads", "google", "azure", "pando", "pando2",]

save_dir
    Default location downloaded files are saved. May use environment variables to specify directory paths. Can overwrite when creating a Herbie object.

priority
    Default data source search order, listed in order of priority. Can overwrite when creating a Herbie object.


Default Download Priority Rational
----------------------------------
The reason for this default is that I anticipate most often a user will request model output from the recent past or earlier rather than relying on Herbie for operational, real-time needs.

Much of the past data and near real-time data is archived at one of NOAA's Big Data partners. Amazon AWS in particular hosts many of these datasets. While, NOMADS is the official operational source of model output data and has the most recent model output available, NOMADS only retains data for a few days, they throttle the download speed, and will block users who violate their usage agreement and download too much data within an hour. For this 

To prevent being blocked by NOMADS, the default is to first look for data on AWS. If the data requested is within the last few hours and was not found on AWS, then Herbie will look for the data at NOMADS. If the data is still not found on NOMADS, the file may be on google, azure, or pando. 

If you _really_ want to download the real-time data from NOMADS first and not a Big Data Project partner, you may change the priority order in the herbie config file or set the priority argument when creating the Herbie object (e.g., ``priority=['nomads', ...]``).
