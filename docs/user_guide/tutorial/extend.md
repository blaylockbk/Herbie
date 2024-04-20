# 👷🏻‍♂️ Extending Herbie

Herbie can be extended to download additional types of model data from the internet. **_Pull requests are welcome._** The requirements are:

- The NWP model data must exist on an http server.
- File names must be predictable (i.e., consistent naming with date, model name, forecast lead time, product, etc.)
- Subetting of a GRIB2 file requires an ASCII index or inventory file (preferablly the wgrib2 style index file).

## Parts of a Herbie Template Class

For an example of what a template class looks like, look at the heavily commented [HRRR template (herbie/models/hrrr.py)](https://github.com/blaylockbk/Herbie/blob/main/herbie/models/hrrr.py).

The model class template function must include the properties

- `DESCRIPTION`: String.
- `DETAILS`: Dictionary.
- `PRODUCTS`: Dictionary.
- `SOURCES`: Dictionary.
- `LOCALFILE`: Usually set to `f"{self.get_remoteFileName}"`, but not always, if you need to save the file as something else.

The following are optional

- `IDX_SUFFIX` : List of strings. The default is `[".grib2.idx"]`.
- `IDX_STYLE`: String. Default is `"wgrib2"`. Options: `"wgrib2"` or `"eccodes"`

After creating/editing a model template class, remember to include it in the `herbie/models/__init__.py` file.

## Types of Herbie Template Class

There are two ways to add a custom template to Herbie:

1. **Public Template**: Add a template to the Herbie source code and make a pull request to extend the functionality to Herbie. A model template class must be created and added to `herbie/models` and imported in the `herbie/models/__init__`. Then make a pull request to make your new template available to others 🙂.

2. **Private Template**: To include a template private to yourself, you can add a custom template to the Herbie config directory. You would want to make a private class for locally stored model data or some special handling of public URLs. First, create/edit the file `~/.config/herbie/custom_template.py` and write a template Class. Second, create the empty file `~/.config/herbie/__init__.py`. Herbie will attempt to load these model templates.

> **Special Case for local model data:** If you have model data stored locally, such as from a WRF simulation, and you have an index file accompanying each GRIB2 file, you can use Herbie to subset the data and open it with xarray. Follow the [local.py](https://github.com/blaylockbk/Herbie/blob/main/herbie/models/local.py) template to create a custom class using the Private template method described.
