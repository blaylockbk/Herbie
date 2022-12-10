
.. .. image:: _static/HerbieLogo2_tan_transparent.png

.. This drop-shadow glow on the logo helps when in Darkmode

.. raw :: html

   <img src="_static/Herbie_transparent_tan.svg" style="filter: drop-shadow(0px 0px 100px #ffffff28)">



===============================
Herbie: Retrieve NWP Model Data
===============================
**Herbie** is a python package that downloads recent and archived numerical weather prediction (NWP) model output from different cloud archive sources.  **Its most popular capability is to download HRRR model data.** NWP data in GRIB2 format can be read with xarray+cfgrib. Model data Herbie can retrieve includes the High Resolution Rapid Refresh (HRRR), Rapid Refresh (RAP), Global Forecast System (GFS), National Blend of Models (NBM), Rapid Refresh Forecast System - Prototype (RRFS), and  ECMWF open data forecast products (ECMWF).

.. toctree::
   :maxdepth: 1

   /user_guide/index
   /reference_guide/index

.. TODO: I'd like to have the cards here instead of the toctree, but the toctree is needed to show the links in the top banner.
.. .. card:: User Guide
..     :link: https://blaylockbk.github.io/Herbie/_build/html/user_guide/index.html

..     Information you need to know to use Herbie.

.. .. card:: Reference Guide
..     :link: https://blaylockbk.github.io/Herbie/_build/html/reference_guide/index.html

..     API reference for Herbie's classes and functions.



Installation
------------
The easiest way to install Herbie and its dependencies is with Conda.

.. code-block::bash

   conda install -c conda-forge herbie-data

More details at :ref:`🐍 Installation`.

Capabilities
------------

Create a Herbie object
^^^^^^^^^^^^^^^^^^^^^^
The most important piece of Herbie is the **Herbie class** which represents a single model output file. When you create a Herbie object, Herbie looks for model data at different sources until the requested file is found.

Herbie can discover data from the following models (click for example usage):

- `High Resolution Rapid Refresh (HRRR) <https://blaylockbk.github.io/Herbie/_build/html/user_guide/notebooks/data_hrrr.html>`_
- `High Resolution Rapid Refresh - Alaska (HRRRAK) <https://blaylockbk.github.io/Herbie/_build/html/user_guide/notebooks/data_hrrrak.html>`_
- `Rapid Refresh (RAP) <https://blaylockbk.github.io/Herbie/_build/html/user_guide/notebooks/data_rap.html>`_
- `Global Forecast System (GFS) <https://blaylockbk.github.io/Herbie/_build/html/user_guide/notebooks/data_gfs.html>`_
- `Global Forecast System - Wave (GFS-Wave) <https://blaylockbk.github.io/Herbie/_build/html/user_guide/notebooks/data_gfs.html#Get-data-from-the-GFS-wave-output>`_
- `ECMWF Open Data Forecast Products (ECMWF) <https://blaylockbk.github.io/Herbie/_build/html/user_guide/notebooks/data_ecmwf.html>`_
- `National Blend of Models (NMB) <https://blaylockbk.github.io/Herbie/_build/html/user_guide/notebooks/data_nbm.html>`_
- `Rapid Refresh Forecast System - Prototype (RRFS) <https://blaylockbk.github.io/Herbie/_build/html/user_guide/notebooks/data_rrfs.html>`_

This example shows how to create a Herbie object for the HRRR model ``sfc`` product and 6 hour forecast. The file was found an Amazon Web Services.

.. code-block:: python

   from herbie import Herbie
   H = Herbie('2021-07-01 12:00', model='hrrr', product='sfc', fxx=6)

.. code-block::

   OUT:
   ✅ Found ┊ model=hrrr ┊ product=sfc ┊ 2021-Jul-01 12:00 UTC F06 ┊ GRIB2 @ aws ┊ IDX @ aws


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

Download a subset
"""""""""""""""""
**Subsetting GRIB files by GRIB message** is also supported, provided that an index (.idx) file exists. For more information about subsetting, read :ref:`What is GRIB2? <GRIB2_FAQ>`.

Using the Herbie object we created above, we can retrieve all fields at 500 mb.

.. code-block:: python

   # Download all fields at 700 mb level
   H.download(":700 mb")


Read GRIB2 Data
^^^^^^^^^^^^^^^
Herbie can help you read these files with `xarray <http://xarray.pydata.org/en/stable/>`_ via `cfgrib <https://github.com/ecmwf/cfgrib>`_.

.. code-block:: python

   # Open 2-m Temperature field
   H.xarray('TMP:2 m')

.. image:: _static/screenshots/usage_4.png


Fast Herbie
^^^^^^^^^^^
Often, data from several GRIB2 files is needed (range of datetimes and/or forecast lead time). ``FastHerbie()`` use multithreading to help you efficiently create multiple Herbie objects, download many files, and open data in concatenated xarray DataSets for a range of model runs and forecast lead times.

In this example, we will get the F00-F03 forecasts for each of the runs initialized between 00z-06z on January 1, 2022 (a total of 28 Herbie objects).

.. code-block:: python

   from herbie import FastHerbie
   import pandas as pd

   # Create a range of dates
   DATES = pd.date_range('2022-01-01 00:00', '2022-01-01 06:00', freq='1H')

   # Create a range of forecast lead times
   fxx = range(0,4)

   # Make FastHerbie Object.
   FH = FastHerbie(DATES, model='hrrr', fxx=fxx)

At it's core, ``FastHerbie`` uses multithreading to make a list of Herbie objects. The list of Herbie objects is stored in the property

.. code-block:: python

   FH.objects

You can download those Herbie objects

.. code-block:: python

   # Full GRIB2 files
   FH.download()

   # Subset of GRIB2 files
   FH.download("TMP:2 m")

or read the data into an xarray DataSet

.. code-block:: python

   ds = FH.xarray("TMP:2 m")

.. image:: _static/screenshots/usage_FastHerbie_xarray.png

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
