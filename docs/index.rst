.. image:: _static/HerbieLogo2_tan_transparent.png


====================
Herbie Documentation
====================
**Herbie** is a python package that downloads recent and archived GRIB2 numerical weather prediction model output. 

.. toctree::
   :maxdepth: 1

   /user_guide/index
   /reference_guide/index


Capabilities
------------

Download Model Data
^^^^^^^^^^^^^^^^^^^
Herbie downloads full or partial GRIB2 files from different models. Supported models include:
- High Resolution Rapid Refresh (HRRR)
- High Resolution Rapid Refresh - Alaska (HRRRAK)
- Rapid Refresh (RAP)
- Global Forecast System (GFS)
- Global Forecast System - Wave (GFS-Wave)
- Rapid Refresh Forecast System - Prototype (RRFS)
- National Blend of Models (NMB)

**Subsetting by GRIB message** is also supported, provided that an index (.idx) file exists. GRIB files contain "messages" which define a grid of data for a particular variable. Data for a variable grid are stacked on top of each other. Instead of downloading full GRIB2 files, you may download a selections from a GRIB2 file based on GRIB message. This is enabled by the cURL command which allows you to download a range of bytes from a file. GRIB index files list the beginning byte for each GRIB field. Herbie searches these index file for the variables you want and performs the cURL command for each field. The returned data is a valid GRIB2 file that contains the whole grid for just the requested variable.

Read GRIB2 Data
^^^^^^^^^^^^^^^
Herbie can help you read these files with `xarray <http://xarray.pydata.org/en/stable/>`_ via `cfgrib <https://github.com/ecmwf/cfgrib>`_.

Plot Fields
^^^^^^^^^^^
🏗 Under construction. I want to make some useful xarray accessors for plotting the GRIB2 fields.

Data Sources 
------------
Thanks to the `NOAA Big Data Program <https://www.noaa.gov/information-technology/big-data>`_ weather data is more easily accessible than ever before. Common data sources include
- `NOAA NOMADS Server <https://nomads.ncep.noaa.gov/>`_ (most recent data, but not archived)
- `Amazon Web Services <https://registry.opendata.aws/noaa-hrrr-pds/>`_
- `Google Cloud Platform <https://console.cloud.google.com/marketplace/product/noaa-public/hrrr>`_
- `Microsoft Azure <https://github.com/microsoft/AIforEarthDataSets/blob/main/data/noaa-hrrr.md>`_
- `University of Utah Pando Archive <http://hrrr.chpc.utah.edu/>`_

Install
-------
Herbie requires **Python 3.8+**

Install with pip

.. code:: bash

   pip install hrrrb

   # or

   pip install git+https://github.com/blaylockbk/HRRR_archive_download.git

To install within a conda environment file, you may use this minimum `environment.yml
<https://github.com/blaylockbk/HRRR_archive_download/blob/master/environment.yml>`_ file 
and create the environment with the following...

.. code:: bash

   # Create the environment
   conda env create -f environment.yml

   # Update the environment
   conda env update -f environment.yml

   # Activate the environment
   conda activate hrrrb

History
-------
During my PhD at the University of Utah, I created, at the time, the only publicly-accessible archive of HRRR data. In the later half of 2020, this data was made available through the `NOAA Big Data Program <https://www.noaa.gov/information-technology/big-data>`_. The Herbie package organizes and expands my original download scripts into a more coherent package with the extended ability to download more than just the HRRR and RAP model data and from different data sources. It will continue to evolve at my own leisure.

I originally released this package under the name "HRRR-B" because it only dealt with the HRRR data set and the "B" is for my initial. Since then, I have added the ability to download RAP, GFS, NBM, RRFS, and potentially more models in the future. Thus, it was re-branded with the name "Herbie" named after some favorite childhood movies. For now, it is still called "hrrrb" on PyPI because "herbie" is already taken. Maybe someday, with some time and an enticing reason, I'll add additional download capabilities. 

While Herbie can download numerical weather prediction model output, my `goes-2-go <https://github.com/blaylockbk/goes2go/tree/master/goes2go>`_ package can help you download GOES ABI and GLM data.


.. figure:: _static/Herbie3.png
   :class: img-fluid
   :width: 66%


Other useful tools
------------------
Brian's Python Add-ons
^^^^^^^^^^^^^^^^^^^^^^
These are still in development and require my `Carpenter Workshop <https://github.com/blaylockbk/Carpenter_Workshop>`_ package to plot the data on a Cartopy map or pluck points nearest specific latitudes and longitudes.

GRIB2 Tools
^^^^^^^^^^^
Yes, GRIB is notoriously difficult to work with, and has a steep learning curve for those unfamiliar with the format or meteorological data. 

There are two command-line tools for looking at GRIB file contents.

1. *wgrib2* is a product of NOAA and can be installed via conda-forge in your environment (linux only).
2. *grib_ls* is a product of ECMWF and is a dependency of cfgrib. This utility is included when you install cfgrib in your environment.

For a sample GRIB2 file with precipitation data, below is the output using both tools

.. code-block:: bash

   $ wgrib2 subset_20201214_hrrr.t00z.wrfsfcf12.grib2
   1:0:d=2020121400:APCP:surface:0-12 hour acc fcst:
   2:887244:d=2020121400:APCP:surface:11-12 hour acc fcst:

.. code-block:: bash


   $ grib_ls subset_20201214_hrrr.t00z.wrfsfcf12.grib2 
   subset_20201214_hrrr.t00z.wrfsfcf12.grib2
   edition      centre       date         dataType     gridType     typeOfLevel  level        stepRange    shortName    packingType  
   2            kwbc         20201214     fc           lambert      surface      0            0-12         tp           grid_complex_spatial_differencing 
   2            kwbc         20201214     fc           lambert      surface      0            11-12        tp           grid_complex_spatial_differencing 
   2 of 2 messages in subset_20201214_hrrr.t00z.wrfsfcf12.grib2

   2 of 2 total messages in 1 files

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
