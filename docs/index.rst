.. Herbie documentation master file, created by
   sphinx-quickstart on Thu Oct  1 20:01:05 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. image:: _static/Herbie_Logo.png

.. toctree::
   :maxdepth: 1

   /user_guide/index
   /reference_guide/index

====================
Herbie Documentation
====================

Herbie is a python package that downloads recent and archived High Resolution Rapid Refresh (HRRR) model and Rapid Refresh (RAP) model output from various sources. It also enables you to download subsets of the GRIB2 by variable and open the data as an ``xarray.Dataset`` with `cfgrib <https://github.com/ecmwf/cfgrib>`_. I created most of this during my PhD and decided to organize what I created into a more coherent package. The main package was originally called HRRR-B, but the package has been expanded to read more than just the HRRR data set and will continue to evolve at my own leisure.


The `HRRR <https://rapidrefresh.noaa.gov/hrrr/>`_ model is NOAA's hourly, 3-km numerical weather prediction model nested within the `RAP <https://rapidrefresh.noaa.gov/>`_ model. Read some of the `HRRR's achievements <https://research.noaa.gov/article/ArtMID/587/ArticleID/2702/The-amazing-research-resume-of-High-Resolution-Rapid-Refresh-Model>`_. The HRRR is the foundation for the upcoming Rapid-Refresh Forecast System (`RRFS <https://gsl.noaa.gov/focus-areas/unified_forecast_system/rrfs>`_). 


.. figure:: _static/Herbie3.png
   :class: img-fluid
   :width: 66%


Install
-------
This package requires **Python 3.7+**

Install with pip

.. code:: bash

   pip install hrrrb

   # or

   pip install git+https://github.com/blaylockbk/HRRR_archive_download.git

To install with in a conda environment file, you may use this minimum `environment.yml
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
These are still in development and require my `Carpenter Workshop <https://github.com/blaylockbk/Carpenter_Workshop>`_ package to plot the data on a Cartopy map or pluck points nearest specific latitudes and longitudes.



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
