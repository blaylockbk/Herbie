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
Herbie can download full or partial GRIB2 files from different models, including the following:

- High Resolution Rapid Refresh (HRRR)
- High Resolution Rapid Refresh - Alaska (HRRRAK)
- Rapid Refresh (RAP)
- Global Forecast System (GFS)
- Global Forecast System - Wave (GFS-Wave)
- Rapid Refresh Forecast System - Prototype (RRFS)
- National Blend of Models (NMB)

**Subsetting these files by GRIB message** is also supported, provided that an index (.idx) file exists. For more information about subsetting, read :ref:`What is GRIB2? <GRIB2_FAQ>`

Data Sources 
""""""""""""
Thanks to the `NOAA Big Data Program <https://www.noaa.gov/information-technology/big-data>`_ weather data is more easily accessible than ever before. Common data sources include

- `NOAA NOMADS Server <https://nomads.ncep.noaa.gov/>`_ (most recent data, but not archived)
- `Amazon Web Services <https://registry.opendata.aws/noaa-hrrr-pds/>`_
- `Google Cloud Platform <https://console.cloud.google.com/marketplace/product/noaa-public/hrrr>`_
- `Microsoft Azure <https://github.com/microsoft/AIforEarthDataSets/blob/main/data/noaa-hrrr.md>`_
- `University of Utah Pando Archive <http://hrrr.chpc.utah.edu/>`_


Read GRIB2 Data
^^^^^^^^^^^^^^^
Herbie can help you read these files with `xarray <http://xarray.pydata.org/en/stable/>`_ via `cfgrib <https://github.com/ecmwf/cfgrib>`_.

Plot Fields
^^^^^^^^^^^
🏗 Under construction. I want to make some useful xarray accessors for plotting the GRIB2 fields. This will use tools I am developing in my `Carpenter Workshop <https://github.com/blaylockbk/Carpenter_Workshop>`_ package to plot the data on a Cartopy map or pluck points nearest specific latitudes and longitudes.


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
**👨🏻‍🎓 During my PhD at the University of Utah**, I created, at the time, the only publicly-accessible archive of HRRR data. In the later half of 2020, this data was made available through the `NOAA Big Data Program <https://www.noaa.gov/information-technology/big-data>`_. The Herbie package organizes and expands my original download scripts into a more coherent package with the extended ability to download more than just the HRRR and RAP model data and from different data sources. It will continue to evolve at my own leisure.

**🌹 What's in a name?** I originally released this package under the name "HRRR-B" because it only dealt with the HRRR data set and the "B" is for my initial. Since then, I have added the ability to download RAP, GFS, NBM, RRFS, and potentially more models in the future. Also, there is an archive of HRRR data in Zarr format, and Herbie could potentially be used to download that format. Thus, it was re-branded with the name "Herbie," named after a favorite childhood movie. For now, it is still called "hrrrb" on PyPI because "herbie" is already taken.

.. figure:: _static/Herbie3.png
   :class: img-fluid
   :width: 66%

**🛰 GOES ABI and GLM data** can be downloaded from AWS with my `goes-2-go <https://github.com/blaylockbk/goes2go/tree/master/goes2go>`_ package. This package was also originally developed during grad school and has been updated.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
