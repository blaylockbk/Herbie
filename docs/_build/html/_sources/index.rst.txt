.. image:: _static/HerbieLogo2_tan_transparent.png


===============================
Herbie: Retrieve NWP Model Data
===============================
**Herbie** is a python package that downloads recent and archived numerical weather prediction (NWP) model output from different cloud archive sources. NWP data in GRIB2 format can be read with xarray+cfgrib. Model data Herbie can retrieve includes the High Resolution Rapid Refresh (HRRR), Rapid Refresh (RAP), Global Forecast System (GFS), National Blend of Models (NBM), Rapid Refresh Forecast System - Prototype (RRFS), and  ECMWF open data forecast products (ECMWF).

.. toctree::
   :maxdepth: 1

   /user_guide/index
   /reference_guide/index

Install
-------
Herbie requires **Python 3.8+**

Install with pip

.. code:: bash

   pip install herbie-data

   # or

   pip install git+https://github.com/blaylockbk/Herbie.git

To install within a conda environment file, you may use this minimum `environment.yml
<https://github.com/blaylockbk/Herbie/blob/main/environment.yml>`_ file
and create the environment with the following...

.. code:: bash

   # Create the environment
   conda env create -f environment.yml

   # Update the environment
   conda env update -f environment.yml

   # Activate the environment
   conda activate herbie

Capabilities
------------

Create a Herbie object
^^^^^^^^^^^^^^^^^^^^^^
Herbie looks for model data at different sources until the requested file is found.

Herbie can discover data from the following models (click for example usage):

- `High Resolution Rapid Refresh (HRRR) <https://blaylockbk.github.io/Herbie/_build/html/user_guide/notebooks/data_hrrr.html>`_
- `High Resolution Rapid Refresh - Alaska (HRRRAK) <https://blaylockbk.github.io/Herbie/_build/html/user_guide/notebooks/data_hrrrak.html>`_
- `Rapid Refresh (RAP) <https://blaylockbk.github.io/Herbie/_build/html/user_guide/notebooks/data_rap.html>`_
- `Global Forecast System (GFS) <https://blaylockbk.github.io/Herbie/_build/html/user_guide/notebooks/data_gfs.html>`_
- `Global Forecast System - Wave (GFS-Wave) <https://blaylockbk.github.io/Herbie/_build/html/user_guide/notebooks/data_gfs.html#Get-data-from-the-GFS-wave-output>`_
- `ECMWF Open Data Forecast Products (ECMWF) <https://blaylockbk.github.io/Herbie/_build/html/user_guide/notebooks/data_ecmwf.html>`_
- `National Blend of Models (NMB) <https://blaylockbk.github.io/Herbie/_build/html/user_guide/notebooks/data_nbm.html>`_
- `Rapid Refresh Forecast System - Prototype (RRFS) <https://blaylockbk.github.io/Herbie/_build/html/user_guide/notebooks/data_rrfs.html>`_

This Herbie object is for the HRRR model sfc product and 6 hour forecast. The file was found an Amazon Web Services.

.. code-block:: python

   from herbie.archive import Herbie
   H = Herbie('2021-01-01 12:00', model='hrrr', product='sfc', fxx=6)

.. image:: _static/screenshots/usage_1.png

Data Sources
""""""""""""
Thanks to the `NOAA Big Data Program <https://www.noaa.gov/information-technology/big-data>`_ weather data is more easily accessible than ever before. Common data sources include

- `NOAA NOMADS Server <https://nomads.ncep.noaa.gov/>`_ (most recent data, but not archived)
- `Amazon Web Services <https://registry.opendata.aws/noaa-hrrr-pds/>`_
- `Google Cloud Platform <https://console.cloud.google.com/marketplace/product/noaa-public/hrrr>`_
- `Microsoft Azure <https://github.com/microsoft/AIforEarthDataSets/blob/main/data/noaa-hrrr.md>`_
- `University of Utah Pando Archive <http://hrrr.chpc.utah.edu/>`_
- `ECMWF Open Data <https://www.ecmwf.int/en/forecasts/datasets/open-data>`_

Download Model Data
^^^^^^^^^^^^^^^^^^^

Using the Herbie object we created above, this downloads the full GRIB2 file to your local machine.

.. code-block:: python

   H.download()

.. image:: _static/screenshots/usage_2.png

Download a subset
"""""""""""""""""
**Subsetting GRIB files by GRIB message** is also supported, provided that an index (.idx) file exists. For more information about subsetting, read :ref:`What is GRIB2? <GRIB2_FAQ>`.

Using the Herbie object we created above, we can retrieve all fields at 500 mb.

.. code-block:: python

   # Download all fields at 500 mb level
   H.download(':500 mb')

.. image:: _static/screenshots/usage_3.png

Read GRIB2 Data
^^^^^^^^^^^^^^^
Herbie can help you read these files with `xarray <http://xarray.pydata.org/en/stable/>`_ via `cfgrib <https://github.com/ecmwf/cfgrib>`_.

.. code-block:: python

   # Open 2-m Temperature field
   H.xarray('TMP:2 m')

.. image:: _static/screenshots/usage_4.png

Fast Herbie
^^^^^^^^^^^
Often, data from several GRIB2 files is needed (range of datetimes and/or forecast lead time). "Fast Herbie" tools use multithreading to help you efficiently create multiple Herbie objects, download many files, and open data in xarray DataSets for a range of model runs and forecast lead times.

.. code-block:: python

   from herbie.tools import fast_Herbie, fast_Herbie_download, fast_Herbie_xarray
   import pandas as pd

   # Get the F00-F06 forecasts for each of the runs initialized
   # between 00z-06z on January 1, 2022 (a total of 42 Herbie objects)
   DATES = pd.date_range('2022-01-01 00:00', '2022-01-01 06:00', freq='1H')
   fxx = range(0,7)

   # Create list of Herbie objects for all dates and lead times requested.
   HH = fast_Herbie(DATES=DATES, fxx=fxx)

   # Download many GRIB2 files; subset the files for 2-m temperature
   d = fast_Herbie_download(DATES=DATES, fxx=fxx, searchString='TMP:2 m')

   # Load many files into xarray; subset for 10-m u and v wind.
   ds = fast_Herbie_xarray(DATES=DATES, fxx=fxx, searchString='(?:U|V)GRD:10 m')

.. image:: _static/screenshots/usage_5.png

Xarray Herbie Accessors
^^^^^^^^^^^^^^^^^^^^^^^

.. note::
   🏗 Some of these features are under construction.

Herbie comes with custom xarray DataSet accessors.

- ``ds.herbie.crs`` returns the cartopy coordinate reference system.
- ``ds.herbie.polygon`` returns the model domain boundary as a polygon.
- ``ds.herbie.nearest_points()`` extracts the data nearest certain lat/lon points.
- ``ds.herbie.plot()`` creates a map plot.

These tools use my `Carpenter Workshop <https://github.com/blaylockbk/Carpenter_Workshop>`_.


Other Tools
-----------
**🛰 GOES ABI and GLM** data can be downloaded from AWS with my `goes-2-go <https://github.com/blaylockbk/goes2go>`_ package. This package was also originally developed during grad school and has been updated.

**🌡 Synoptic API (MesoWest)** data can be retrieved with my `SynopticPy <https://github.com/blaylockbk/SynopticPy>`_ package, also originally developed during grad school and has been updated.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
