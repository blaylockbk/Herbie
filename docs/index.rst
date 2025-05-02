
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
- ECMWF open data forecast products (ECMWF (IFS and AIFS))
- National Blend of Models (NBM)
- Rapid Refresh Forecast System - Prototype (RRFS)
- Real-Time/Un-Restricted Mesoscale Analysis (RTMA and URMA)
- and many others (see :ref:`Gallery`)

.. toctree::
   :maxdepth: 1

   /user_guide/index
   /gallery/index
   /grib_reference/index
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

.. tab-set::

    .. tab-item:: mamba

        .. code-block:: bash

            mamba install -c conda-forge herbie-data

    .. tab-item:: conda

        .. code-block:: bash

            conda install -c conda-forge herbie-data


    .. tab-item:: pip

        .. code-block:: bash

            pip install herbie-data

    .. tab-item:: uv

        Add Herbie to your uv project with the following command:

        .. code-block:: bash

            uv add herbie-data

        Or install Herbie as a tool for its CLI

        .. code-block:: uv

            uv install herbie-data

More details at :ref:`🐍 Installation`.


Capabilities
------------

Herbie helps you discover and use data from many different numerical weather models and sources.

.. figure:: _static/diagrams/mermaid-capabilities.png
   :class: img-fluid
   :width: 66%

Specifically, Herbie can do the following:

- Locate GRIB2 files in the cloud.
- Show the content of those files.
- Download data to your computer.
- Download *subsets*  of the data.
- Read the data with xarray.
- Help you use the data with xarray accessors (see :ref:`🗃️ Xarray Accessors`)
- Support for custom model templates with `Herbie plugins <https://github.com/blaylockbk/herbie-plugin-tutorial>`_.


Herbie Python
^^^^^^^^^^^^^

Using Herbie's Python API looks something like this...

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

Herbie CLI
^^^^^^^^^^

Herbie also has a command line interface (CLI) so you can use Herbie right in your terminal.

.. code-block:: bash

   # Get the URL for a HRRR surface file from today at 12Z
   herbie data -m hrrr --product sfc -d "2023-03-15 12:00" -f 0

   # Download GFS 0.25° forecast hour 24 temperature at 850mb
   herbie download -m gfs --product 0p25 -d 2023-03-15T00:00 -f 24 --subset ":TMP:850 mb:"

   # View all available variables in a RAP model run
   herbie inventory -m rap -d 2023031512 -f 0

   # Download multiple forecast hours for a date range
   herbie download -m hrrr -d 2023-03-15T00:00 2023-03-15T06:00 -f 1 3 6 --subset ":UGRD:10 m:"

   # Specify custom source priority (check only Google)
   herbie data -m hrrr -d 2023-03-15 -f 0 -p google

More details in the :ref:`User Guide`.

