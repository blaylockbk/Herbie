==========================
👷🏻‍♂️ Extending Herbie
==========================

Herbie download capability can be extended to include additional models. The requirements are:

- The model data must exists on an http server
- File names must be predictable (consistent naming with date, model name, forecast lead time, product, etc.)
- Subetting of a GRIB2 file requires an index or inventory file
- one of the below:
    1. Modifying Herbie source: A model template class must be created and added to ``herbie/models`` and imported in the ``herbie/models/__init__``
    2. Add custom template to home directory: A model template class must be created and added to ``~/.config/herbie/custom_template.py`` and create empty file ``~/.config/herbie/__init__.py``.

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

