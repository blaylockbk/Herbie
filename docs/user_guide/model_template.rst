======================
👷🏻‍♂️ Extending Herbie
======================

Herbie download capability can be extended to include additional models. The requirements are:

- The model data must exists on an http server
- File names must be predictable (consistent naming with date, model name, forecast lead time, product, etc.)
- Subetting of a GRIB2 file requires an index or inventory file
- A model template class must be created and added to ``herbie/models``

As an example, look at the heavily commented `hrrr.py template <https://github.com/blaylockbk/Herbie/blob/master/herbie/models/hrrr.py>`_.

The model class template function must include the properties

- ``DESCRIPTION``
- ``DETAILS``
- ``PRODUCTS``
- ``SOURCES``
- ``LOCALFILE``