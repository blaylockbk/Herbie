================
Extending Herbie
================

Additional models can be added to extend Herbie's download ability. The requirements are:

- Model data must exists on an http server.
- File names must be predictable (consistent naming with date, model name, forecast lead time, product, etc.).
- Subetting of a GRIB2 file requires an index file.
- A model template class must be created and added to ``herbie/models``. 

As an example, look at the heavily commented `hrrr.py template <https://github.com/blaylockbk/HRRR_archive_download/blob/master/herbie/models/hrrr.py>`_

The model class template function must include the properties

- ``DESCRIPTION``
- ``DETAILS``
- ``PRODUCTS``
- ``SOURCES``
- ``LOCALFILE``