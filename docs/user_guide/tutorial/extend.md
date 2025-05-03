# 👷🏻‍♂️ Extending Herbie

A _model template_ in Herbie is a Python class that defines where Herbie looks for weather model datasets. Herbie comes with many [model templates](https://github.com/blaylockbk/Herbie/tree/main/src/herbie/models). When you import Herbie, it loads its model templates, and then Herbie looks for any templates from installed plugins.

Herbie can be extended to download additional types of model data from the internet. The requirements are:

- The NWP model data must exist on an http server.
- File names must be predictable (i.e., consistent naming with date, model name, forecast lead time, product, etc.)
- Subetting of a GRIB2 file requires an ASCII index or inventory file (preferably the wgrib2 style index file).

Pull requests are welcome to update extinsting templates or create new templates.

You can also create your own plugin with custom model templates. You might need your own model template when:

- You have local GRIB2 files (e.g., WRF/MPAS output) you'd like to access with Herbie.
- You have access to GRIB2 data on a private network.
- You want to override behavior of an existing model temple.
- You want to iterate on a new model template before contributing upstream.

**If creating a plugin is right for you, please follow the [Herbie Plugin Tutorial](https://github.com/blaylockbk/herbie-plugin-tutorial).**

## Parts of a Herbie Template Class

For an example of what a template class looks like, look at the heavily commented [HRRR template (herbie/models/hrrr.py)](https://github.com/blaylockbk/Herbie/blob/main/src/herbie/models/hrrr.py).

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

There are two types of custom template to Herbie:

1. **Public Template**: Add a template to the Herbie source code and make a pull request to extend the functionality to Herbie. A model template class must be created and added to `herbie/models` and imported in the `herbie/models/__init__`. Then make a pull request to make your new template available to others 🙂.

1. **Plugin Templates**: These are Python packages that, when installed, Herbie loads its templates. Please follow [Herbie Plugin Tutorial](https://github.com/blaylockbk/herbie-plugin-tutorial) for an example.
