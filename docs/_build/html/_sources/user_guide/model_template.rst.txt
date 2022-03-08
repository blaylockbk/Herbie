==========================
👷🏻‍♂️ Extending Herbie
==========================

Herbie download capability can be extended to include additional models. The requirements are:

- The model data must exists on an http server
- File names must be predictable (consistent naming with date, model name, forecast lead time, product, etc.)
- Subetting of a GRIB2 file requires an index or inventory file
- A model template class must be created and added to ``herbie/models``

As an example, look at the heavily-commented `hrrr.py template <https://github.com/blaylockbk/Herbie/blob/master/herbie/models/hrrr.py>`_.

The model class template function must include the properties

- ``DESCRIPTION`` String.
- ``DETAILS`` Dictionary.
- ``PRODUCTS`` Dictionary.
- ``SOURCES`` Dictionary.
- ``LOCALFILE`` Usually set to ``f"{self.get_remoteFileName}"``, but not always.

The following are optional

- ``IDX_SUFFIX`` List of strings. Default is [".grib2.idx"].
- ``IDX_STYLE`` String. Default is "wgrib2". Options: "wgrib2" or "eccodes"


HRRR in Zarr format
-------------------
The HRRR model is available in `Zarr format on AWS <https://hrrrzarr.s3.amazonaws.com/index.html>`_. Herbie doesn't download this type of data yet, but might in the future.

For more information about HRRR-Zarr, read the `documentation <https://mesowest.utah.edu/html/hrrr/>`_.
