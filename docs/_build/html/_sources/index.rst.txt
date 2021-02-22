.. HRRR-B documentation master file, created by
   sphinx-quickstart on Thu Oct  1 20:01:05 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. image:: _static/HRRR-B_logo.png

.. note::
   This is a work in progress

.. toctree::
   :maxdepth: 1

   /user_guide/index
   /reference_guide/index

====================
HRRR-B Documentation
====================

The `High-Resolution Rapid Refresh <https://rapidrefresh.noaa.gov/hrrr/>`_ model is NOAA's hourly, 3-km numerical weather prediction model. 

HRRR-B, or "Herbie," is a python package for downloading recent and archived High Resolution Rapid Refresh (HRRR) model forecasts and opening HRRR data as an ``xarray.Dataset`` with `cfgrib <https://github.com/ecmwf/cfgrib>`_. I created most of this during my PhD and decided to organize what I created into a more coherent package. It will continue to evolve at my own leisure.
.. figure:: _static/Herbie3.png
   :class: img-fluid
   :width: 50%
   :align: right


The HRRR is the foundation for the upcoming Rapid-Refresh Forecast System. Read some of the `HRRR's achievements <https://research.noaa.gov/article/ArtMID/587/ArticleID/2702/The-amazing-research-resume-of-High-Resolution-Rapid-Refresh-Model>`_


Install
-------
This package requires **Python 3.7+** (doesn't work in 3.6 and earlier because I use relative imports)

Install ``hrrrb`` in a conda environment. You may use this minimum `environment.yml
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
Download archived HRRR data from multiple sources:

- `NOAA NOMADS Server <https://nomads.ncep.noaa.gov/>`_
- `Amazon Web Services <https://registry.opendata.aws/noaa-hrrr-pds/>`_
- `Google Cloud Platform <https://console.cloud.google.com/marketplace/product/noaa-public/hrrr>`_
- `University of Utah Pando Archive <http://hrrr.chpc.utah.edu/>`_

Subset by GRIB2 field
^^^^^^^^^^^^^^^^^^^^^
Instead of downloading full GRIB2 files, you may download a select GRIB2 fields or variables from a file. This is enabled by the cURL command which allows you to download a range of bytes from a file. The index ``.idx`` files tells you the beginning byte for each field. HRRR-B search those ``.idx`` files for variables you want and performs the cURL command for each field.

Other useful tools
^^^^^^^^^^^^^^^^^^
Some other useful tools in development include plucking out points from the HRRR grid. Other useful tools can be found in my `Carpenter Workshop <https://github.com/blaylockbk/Carpenter_Workshop>`_



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
