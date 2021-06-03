.. image:: _static/Herbie_Logo.png

.. toctree::
   :maxdepth: 1

   /user_guide/index
   /reference_guide/index

====================
Herbie Documentation
====================

**Herbie** is a python package that downloads recent and archived output from the High Resolution Rapid Refresh (HRRR) and Rapid Refresh (RAP) models from various sources. It also enables you to download subsets of the GRIB2 by variable and open the data with `xarray <http://xarray.pydata.org/en/stable/>`_ via `cfgrib <https://github.com/ecmwf/cfgrib>`_. I created most of this during my PhD and have since organized it into this more coherent package. The package was original named **HRRR-B**, but since then the package has been expanded to access more than just the HRRR data from one source and it will continue to evolve at my own leisure. It is now called Herbie, named after some favorite childhood movies.

The `HRRR <https://rapidrefresh.noaa.gov/hrrr/>`_ model is NOAA's hourly, 3-km numerical weather prediction model nested within the `RAP <https://rapidrefresh.noaa.gov/>`_ model and is a `valuable numerical weather prediction resource <https://research.noaa.gov/article/ArtMID/587/ArticleID/2702/The-amazing-research-resume-of-High-Resolution-Rapid-Refresh-Model>`_. The RAP and HRRR model development are the foundation for the upcoming Rapid-Refresh Forecast System (`RRFS <https://gsl.noaa.gov/focus-areas/unified_forecast_system/rrfs>`_). 


.. figure:: _static/Herbie3.png
   :class: img-fluid
   :width: 66%


Install
-------
This package requires **Python 3.8+**

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

Capabilities
------------

Download Data
^^^^^^^^^^^^^
Download recent and archived HRRR and RAP data from multiple sources made possible by `NOAA's big data program <https://www.noaa.gov/information-technology/big-data>`_:

- `NOAA NOMADS Server <https://nomads.ncep.noaa.gov/>`_
- `Amazon Web Services <https://registry.opendata.aws/noaa-hrrr-pds/>`_
- `Google Cloud Platform <https://console.cloud.google.com/marketplace/product/noaa-public/hrrr>`_
- `Microsoft Azure <https://github.com/microsoft/AIforEarthDataSets/blob/main/data/noaa-hrrr.md>`_
- `University of Utah Pando Archive <http://hrrr.chpc.utah.edu/>`_

Subset by GRIB2 variable
^^^^^^^^^^^^^^^^^^^^^^^^
GRIB files contain "messages" which define a grid of data for a particular variable. Data for a variable grid are stacked on top of each other. Instead of downloading full GRIB2 files, you may download a selections from a GRIB2 file based on GRIB message. This is enabled by the cURL command which allows you to download a range of bytes from a file. The index **.idx** files tells you the beginning byte for each GRIB field. Herbie searches an **.idx** file for the variables you want and performs the cURL command for each field. The returned data is a valid GRIB2 file that contains the whole grid for just the requested variable.

Other useful tools
^^^^^^^^^^^^^^^^^^
**Brian's Python Add-ons**
These are still in development and require my `Carpenter Workshop <https://github.com/blaylockbk/Carpenter_Workshop>`_ package to plot the data on a Cartopy map or pluck points nearest specific latitudes and longitudes.

**GRIB2 Tools**
There are two command-line tools for looking at GRIB file contents.

1. *wgrib2* is a product of NOAA and can be installed via conda-forge in your environment (linux only).
2. *grib_ls* ia a product of ECMWF and is a dependency of cfgrib. This utility is included when you install cfgrib in your environment.

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
