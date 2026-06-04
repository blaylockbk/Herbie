============
v2 (Preview)
============

.. warning::
   Herbie v2 is under active development. The API may change before the
   stable release. For production use, see the :ref:`User Guide` for the
   current stable API.

.. tab-set::


    .. tab-item:: uv

        Add Herbie to your uv project with the following command:

        .. code-block:: bash

            uv add herbie-data[v2,zarr]

    .. tab-item:: pip

        .. code-block:: bash

            pip install herbie-data[v2,zarr]

    .. tab-item:: mamba

        .. code-block:: bash

            mamba install -c conda-forge herbie-data

    .. tab-item:: conda

        .. code-block:: bash

            conda install -c conda-forge herbie-data

For optional features, if you are on Linux, make sure wgrib2 is installed and in your path. You can install wgrib2 from conda-forge with mamba/conda, or really easy with pixi

.. code-block:: bash

    pip global install wgrib2

.. code-block:: python

   from herbie.v2 import HRRR

   H = HRRR("2025-01-01", step=6, product="sfc")
   H.inventory("TMP:2 m above ground")
   ds = H.xarray("TMP:2 m above ground")

.. toctree::
   :maxdepth: 1
   :caption: Herbie v2

   whats-new
   migration-guide

.. toctree::
   :maxdepth: 1
   :caption: Examples

   example_status.ipynb
   example_step.ipynb
   example_datatree.ipynb
   example_fast.ipynb
   example_zarr.ipynb

.. toctree::
   :maxdepth: 1
   :caption: Gallery

   ./models/*



