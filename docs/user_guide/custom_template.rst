==========================
👷🏻‍♂️ Extending Herbie
==========================

Herbie can be extended to download additional types of model data from the internet. The requirements are:

- The model data must exists on an http server.
- File names must be predictable (i.e., consistent naming with date, model name, forecast lead time, product, etc.)
- Subetting of a GRIB2 file requires an index or inventory file

Parts of a Herbie Template Class
--------------------------------

As an example of what a template class looks like, look at the heavily-commented `hrrr.py template <https://github.com/blaylockbk/Herbie/blob/master/herbie/models/hrrr.py>`_.


The model class template function must include the properties

- ``DESCRIPTION`` String.
- ``DETAILS`` Dictionary.
- ``PRODUCTS`` Dictionary.
- ``SOURCES`` Dictionary.
- ``LOCALFILE`` Usually set to ``f"{self.get_remoteFileName}"``, but not always, if you need to save the file as something else.

The following are optional

- ``IDX_SUFFIX`` List of strings. Default is ``[".grib2.idx"]``.
- ``IDX_STYLE`` String. Default is ``"wgrib2"``. Options: ``"wgrib2"`` or ``"eccodes"``


Types of Herbie Template Class
------------------------------

There are two ways to add a custom template to Herbie:

1. **Public Template**: Add a template to the Herbie source code and make a pull request to extend the functionality to Herbie. A model template class must be created and added to ``herbie/models`` and imported in the ``herbie/models/__init__``. Then make a pull request to make your new template available to others 🙂.

2. **Private Template**: To include a template private to yourself, you can add a custom template to your home config directory. You would want to make a private class for locally stored model data or some special handling of public URLs. First, create the file ``~/.config/herbie/custom_template.py`` and write a template Class. Second, create the empty file ``~/.config/herbie/__init__.py``.

.. note::
    **Special Case for local model data:** If you have model data stored locally, such as from a WRF simulation, and you have an index file accompanying each GRIB2 file, you can use Herbie to subset the data and open with xarray. Follow the `local.py <https://github.com/blaylockbk/Herbie/blob/master/herbie/models/local.py>`_ template to create a custom class using the Private template method described. 
