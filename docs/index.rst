
.. .. image:: _static/HerbieLogo2_tan_transparent.png

.. This drop-shadow glow on the logo helps when in Darkmode
   style="filter: drop-shadow(0px 0px 100px #ffffff28)"

.. raw :: html

   <img src="_static/logo_new/Herbie-logo.png" style="background-color:transparent;">



===============================================================
Herbie: Download Weather Forecast Model Data in Python
===============================================================

**Access HRRR, GFS, RAP, GEFS, ECMWF and 15+ Weather Models**


**Herbie** is a Python package that makes downloading and working with numerical weather prediction (NWP) model data simple and fast. Whether you're a researcher, meteorologist, data scientist, or weather enthusiast, Herbie provides easy access to forecast data from NOAA, ECMWF, and other sources.

.. code-block:: python

   from herbie import Herbie

   # Download HRRR 2-meter temperature
   H = Herbie('2021-01-01 12:00', model='hrrr')
   ds = H.xarray("TMP:2 m")


.. toctree::
   :maxdepth: 1
   :hidden:

   /user_guide/index
   /gallery/index
   /grib_reference/index
   /api_reference/index

.. grid:: 2
    :gutter: 3

    .. grid-item-card:: 📘 User Guide
        :link: user_guide/index
        :link-type: doc

        Learn how to use Herbie with tutorials and examples

    .. grid-item-card:: 🖼️ Model Gallery
        :link: gallery/index
        :link-type: doc

        Browse examples for each supported weather model

    .. grid-item-card:: 🔧 API Reference
        :link: api_reference/index
        :link-type: doc

        Complete reference for all classes and functions

    .. grid-item-card:: 💬 Community Support
        :link: https://github.com/blaylockbk/Herbie/discussions

        Ask questions and share ideas on GitHub Discussions

**Key Features:**

- 🌐 **Access 15+ weather models** including HRRR, GFS, RAP, GEFS, ECMWF, and more
- ⚡ **Smart downloads** - Get full GRIB2 files or subset by variable to save time and bandwidth
- 📊 **Built-in data reading** - Load data directly into xarray for analysis
- 🗺️ **Visualization aids** - Includes Cartopy integration for mapping
- 🔄 **Multiple data sources** - Automatically search multiple archive sources (AWS, Google Cloud, NOMADS, Azure)
- 🛠️ **CLI and Python API** - Use from command line or in your Python scripts

----

Supported Weather Models
------------------------

Herbie provides access to a wide range of numerical weather prediction models:

**US Models (NOAA):**

- **High-Resolution Rapid Refresh (HRRR)** - 3km resolution short-range forecasts
- **Rapid Refresh (RAP)** - 13km resolution regional forecasts
- **Global Forecast System (GFS)** - Global medium-range forecasts
- **Global Ensemble Forecast System (GEFS)** - Global ensemble predictions
- **National Blend of Models (NBM)** - Statistically blended forecasts
- **Rapid Refresh Forecast System (RRFS)** - Next-generation RAP/HRRR *(prototype)*
- **Real-Time/Un-Restricted Mesoscale Analysis (RTMA/URMA)** - Gridded observations
- **Hurricane Analysis and Forecast System (HAFS)** - Tropical cyclone forecasts
- **Climate Forecast System (CFS)** - Seasonal predictions

**Other Models:**

- **ECMWF Open Data** - IFS and AIFS global forecast models
- **NAVGEM** - US Navy global environmental model
- **HRDPS** - Canadian high-resolution forecasts

**And many more!** See the :ref:`Gallery` for complete model coverage.

.. tip::
   Much of this data is made available through the `NOAA Open Data Dissemination <https://www.noaa.gov/information-technology/open-data-dissemination>`_ (NODD) program, making weather data more accessible than ever before.



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

**Requirements:**

- Python 3.10 or higher
- xarray and cfgrib for reading GRIB2 data
- wgrib2 (optional, for advanced subsetting)

For detailed installation instructions, see :ref:`🐍 Installation`.


What Can Herbie Do?
-------------------

Herbie streamlines the entire workflow of accessing weather model data:

.. figure:: _static/diagrams/mermaid-capabilities.png
   :class: img-fluid
   :width: 75%
   :align: center

**Features:**

- 🔍 Search model output from different data sources
- ⬇️ Download full or subset GRIB2 files
- 📖 Read data with xarray and index files with Panda (see :ref:`🗃️ Xarray Accessors`)
- 🗺️ Built-in Cartopy aids for mapping
- 🎯 Extract data at specific points
- 🔌 Extensible with [custom model templates](https://github.com/blaylockbk/herbie-plugin-tutorial)

----

Using Herbie
------------

Herbie Python API
^^^^^^^^^^^^^^^^^

The Python API provides full programmatic access to all features:

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

**Learn more:** :ref:`User Guide`

Herbie Command Line Interface
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use Herbie directly from your terminal:


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

----

.. note::
   **Project maintained by Brian Blaylock**

   Check out Brian's other Python packages for atmospheric science:

   - `GOES-2-go <https://github.com/blaylockbk/goes2go>`_ - Download GOES satellite data
   - `SynopticPy <https://github.com/blaylockbk/SynopticPy>`_ - Access mesonet observations
   - `Carpenter Workshop <https://github.com/blaylockbk/Carpenter_Workshop>`_ - Meteorological analysis tools
