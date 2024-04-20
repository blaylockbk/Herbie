
.. .. image:: _static/HerbieLogo2_tan_transparent.png

.. This drop-shadow glow on the logo helps when in Darkmode
   style="filter: drop-shadow(0px 0px 100px #ffffff28)"

.. raw :: html

   <img src="_static/logo_new/Herbie-logo.png" style="background-color:transparent;">



===============================
Herbie: Retrieve NWP Model Data
===============================

**Herbie** is a python package that downloads recent and archived numerical weather prediction (NWP) model output from different cloud archive sources. NWP data is distributed in GRIB2 format and can be read with xarray+cfgrib.

Some models Herbie can retrieve data from include:

- High-Resolution Rapid Refresh (HRRR)
- Rapid Refresh (RAP)
- Global Forecast System (GFS)
- ECMWF open data forecast products (IFS and AIFS)
- National Blend of Models (NBM)
- Rapid Refresh Forecast System - Prototype (RRFS)
- Real-Time/Un-Restricted Mesoscale Analysis (RTMA/URMA)
- and many others (see :ref:`🗺 Model Tutorials`)

.. toctree::
   :maxdepth: 1

   /user_guide/index
   /api_reference/index

.. TODO: I'd like to have the cards here instead of the toctree, but the toctree is needed to show the links in the top banner.
.. .. card:: User Guide
..     :link: https://herbie.readthedocs.io/user_guide/index.html

..     Information you need to know to use Herbie.

.. .. card:: Reference Guide
..     :link: https://herbie.readthedocs.io/reference_guide/index.html

..     API reference for Herbie's classes and functions.



Installation
------------
The easiest way to install Herbie and its dependencies is with Conda.

.. code-block:: bash

   conda install -c conda-forge herbie-data

More details at :ref:`🐍 Installation`.

Capabilities
------------

Herbie helps you discover and use data from many different numerical weather models and sources.

.. figure:: _static/diagrams/mermaid-capabilities.png
   :class: img-fluid
   :width: 66%

Specifically, Herbie can

- Locate GRIB2 files in the cloud.
- Explore the content of those files.
- Download data to your computer.
- Download *subsets*  of the data.
- Read the data with xarray.
- Useful xarray accessors (see :ref:`🗃️ Xarray Accessors`)

Using Herbie looks something like this...

.. code-block:: python

   from herbie import Herbie

   # Create Herbie object for the HRRR model 6-hr surface forecast product
   H = Herbie(
     '2021-01-01 12:00',
     model='hrrr',
     product='sfc',
     fxx=6
   )

   # Look at the GRIB2 file contents
   H.inventory()

   # Download the full GRIB2 file
   H.download()

   # Download a subset of the file, like all fields at 500 mb
   H.download(":500 mb")

   # Read a subset of the file with xarray, like 2-m temperature.
   H.xarray("TMP:2 m")


More details in the :ref:`User Guide`.

