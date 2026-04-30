============
v2 (Preview)
============

.. warning::
   Herbie v2 is under active development. The API may change before the
   stable release. For production use, see the :ref:`User Guide` for the
   current stable API.

.. code-block:: python

   from herbie.v2 import HRRR

   H = HRRR("2025-01-01", step=6, product="sfc")
   H.inventory("TMP:2 m above ground")
   ds = H.xarray("TMP:2 m above ground")

.. toctree::
   :maxdepth: 1
   :caption: Herbie v2

   whats_new
   quickstart
   models
   migration
