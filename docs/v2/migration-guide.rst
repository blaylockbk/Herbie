Migration Guide
===============

Herbie v2 introduces several architectural improvements and API changes.
Most workflows remain similar, but a few key parameters and patterns have changed.

This guide highlights the most common changes and how to update existing code.

----

Key API Changes
---------------

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * - Change
     - v1
     - v2
   * - Forecast lead time parameter
     - ``fxx``
     - ``step``
   * - Default data directory
     - ``~/data/`` or user specified
     - ``~/herbie-data/``
   * - DataFrame library
     - Pandas
     - Polars
   * - Model access
     - ``Herbie(model='hrrr')``
     - ``Herbie.HRRR()``
   * - Notebook display
     - Plain text repr
     - Rich HTML display
   * - Inventory filtering
     - Search string
     - Search string *or* Polars expressions
   * - Multi-hypercube datasets
     - Flattened
     - ``xarray.DataTree``

----

Common Workflows
----------------

Create a Herbie Object
~~~~~~~~~~~~~~~~~~~~~~

.. grid:: 2

   .. grid-item-card:: v1

      Specify model with ``model=`` argument

      .. code-block:: python

         from herbie import Herbie

         H = Herbie(
             "2025-01-01",
             model="hrrr",
             fxx=12
         )

   .. grid-item-card:: v2

      Import and use a Herbie model class

      .. code-block:: python

         from herbie.v2 import HRRR

         H = HRRR(
             "2025-01-01",
             step=12
         )

      Or, use model class via the Herbie namespace. You can still use ``datetime`` to specify the desired date:

      .. code-block:: python

         from herbie.v2 import Herbie
         from datetime import datetime

         H = Herbie.HRRR(
            datetime(2025, 1, 1),
            step=12
         )

----

Forecast Lead Time
------------------


.. grid:: 2

   .. grid-item-card:: v1

      .. code-block:: python

         H = Herbie(
            "2025-01-01",
            model="hrrr",
            fxx=6
         )

   .. grid-item-card:: v2

      The ``fxx`` parameter has been renamed to ``step``.

      .. code-block:: python

         H = HRRR(
            "2025-01-01",
            step=6
         )

      You can also use a ``timedelta``:

      .. code-block:: python

         from datetime import timedelta

         H = HRRR(
            "2025-01-01",
            step=timedelta(hours=6)
         )

----

Inventory
---------


.. grid:: 2

   .. grid-item-card:: v1

      .. code-block:: python

         H.inventory("TMP:2 m")

      .. code-block:: python

         H.inventory(r"TMP:/d+ mb")

   .. grid-item-card:: v2

      Inventories are now **Polars DataFrames**, which support fast expression-based filtering.

      Same regex search strings work from v1, but you may also use Polars expressions to filter the inventory enabling more flexible filtering.

      .. code-block:: python

         inv = H.inventory()

         inv.filter(
             pl.col("variable") == "TMP"
         )

         inv.filter(
             [
               pl.col("variable") == "TMP",
               pl.col("level").str.ends_with("mb"),
             ]

         )

      The dataframe also includes the source path to the index file, which make the new FastHerbie features possible.

----

Download Fields
---------------

.. grid:: 2

   .. grid-item-card:: v1

      .. code-block:: python

         H.download("TMP:2 m")

   .. grid-item-card:: v2

      .. code-block:: python

         H.download("TMP:2 m")

      The basic workflow is unchanged, but...

      - Downloads each subset group in **parallel threads**
      - Displays **Rich progress bars**
      - Preserves the **remote file path structure**

----

Load Data with xarray
---------------------

.. grid:: 2

   .. grid-item-card:: v1

      .. code-block:: python

         ds = H.xarray("TMP:2 m")

   .. grid-item-card:: v2

      .. code-block:: python

         ds = H.xarray("TMP:2 m")

      If multiple hypercubes are present, v2 returns an **xarray DataTree** rather than flattening them.

----

Checking Data Availability
--------------------------

.. grid:: 2

   .. grid-item-card:: v1

      Source checking was mostly implicit. File existence was checked when the Herbie object was created.

   .. grid-item-card:: v2

      Herbie only checks for file existence when you ask to retrieve data (i.e., using the inventory, download, or xarray methods). You may also explicitly resolve sources to inspect them yourself:

      .. code-block:: python

         # Default resolution
         # Look for first available file
         H.resolve()

         # Check existence at a specific source
         H.resolve("google")

         # Check all sources
         H.resolve("all")

----

FastHerbie Changes
------------------



.. grid:: 2

   .. grid-item-card:: v1

      Focused primarily on downloading many files quickly.

   .. grid-item-card:: v2

      ``FastHerbie`` has been completely redesigned.

      Now enables **building custom GRIB files from multiple model runs**.

      Example use cases:

      - Combine all ``TMP:2 m`` forecasts for a day
      - Combine all ``GRD:10 m`` forecasts initialized at one cycle

      This allows users to generate **custom GRIB datasets tailored to
      their workflow**.

----

Configuration
-------------

Herbie v2 introduces a **configuration file** that lets you set preferences
without modifying Python code:

- Default data directory
- Preferred sources
- Authentication settings

----

Notebook Experience
-------------------

When displayed in a Jupyter notebook, a Herbie object now shows a
**rich HTML summary** that includes:

- Model configuration
- Forecast step
- Available sources
- Data availability

This makes exploratory analysis much easier.

----

Summary
-------

Most workflows require **minimal code changes**, but the following updates
are recommended:

1. Replace ``fxx`` with ``step``
2. Import models from ``herbie.v2``
3. Update inventory workflows to use **Polars expressions**
4. Be aware that multi-hypercube datasets now return **DataTree objects**

These changes provide faster performance, improved data handling, better
extensibility, and a more modern Python API.
