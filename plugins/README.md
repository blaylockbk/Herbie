# Herbie Model Template Plugins

This describes how to make a custom Herbie model template and install it as a plugin.

Let's make a plugin called `herbie-plugin-demo`. (I used `uv init --package herbie )

I used uv to create my plugin package.

```bash
uv init --package herbie-plugin-demo --python 3.11
```

The directory tree looks like this...
```
herbie-plugin-demo/
├── pyproject.toml
├── README.md
└── src
    └── herbie_plugin_demo
        └── __init__.py
```

Next, add entry points to the `pyproject.toml` file.

```toml
# pyproject.toml
[project]
name = "herbie-plugin-demo"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
authors = [
    { name = "Your Name", email = "your.email@here.com" },
]
requires-python = ">=3.11"
dependencies = []

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project.entry-points."herbie.plugins"]
my_custom_models = "herbie_plugin_demo"
```

Edit the `src/herbie_plugin_demo/__init__.py` with a Herbie model template.

> The class names should be all lowercase. (Herbie turns all user input to lowercase).

```python
# src/herbie_plugin_demo/__init__.py
class plugin_model_1:
    def template(self):
        self.DESCRIPTION = "Local GRIB Files for model1"
        self.DETAILS = {
            "local": "These GRIB2 files are from a locally-stored modeling experiments."
        }
        self.PRODUCTS = {
            # UPDATE THIS
            "prs": "3D pressure level fields",
            "sfc": "Surface level fields",
        }
        self.SOURCES = {
            "local_main": f"/path/to/your/model1/templated/with/{self.model}/gribfiles/{self.date:%Y%m%d%H}/the_file.t{self.date:%H}z.{self.product}.f{self.fxx:02d}.grib2",
            "local_alt": f"/alternative/path/to/your/model1/templated/with/{self.model}/gribfiles/{self.date:%Y%m%d%H}/the_file.t{self.date:%H}z.{self.product}.f{self.fxx:02d}.grib2",
        }
        self.LOCALFILE = f"{self.get_remoteFileName}"
```

Now install the plugin package.

```bash
pip install -e .
```

Once installed, you can then import Herbie and access those custom model templates.

```python
from herbie import Herbie

# The following is printed...
# added plugin 'plugin_model_1' to globals

# Then you can use your custom model template
H = Herbie("2025-01-01", model="plugin_model_1")
```
