## Added by Brian Blaylock
## September 30, 2021

"""

.. warning ::
    This is an experimental feature.

This is a special case template for GRIB2 model data that is stored on
your local machine rather than retrieving data from remote sources.
For example, you may have output from some WRF simulations you did.

.. attention ::
    Rather than editing this file, this class should be copied to a
    private template file at ``~/.config/herbie/custom_template.py``.
    Don't forget to create the file ``~/.config/herbie/__init__.py``.

Index files are assumed to be in the same directory as the file with
".idx" appended to the file name. If you don't have these inventory
files then they can be generated on-the-fly if you have wgrib2 installed
in your PATH or conda environment.

The keys in the SOURCES dictionary should start with "local".

Since Herbie accepts kwargs and passes them to self, you can template
the local file path with any parameter, just remember to pass that
parameter to the Herbie class 😋

To ask Herbie to find files with the template below you would type

.. code-block:: python

    Herbie('2021-9-21', model="model1", fxx=0, ...)

    Herbie('2021-9-21', model="model2", fxx=0, ...)

"""


class model1:
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
            "local_main": f"/path/to/your/model1/templated/with/{self.model}/gribfiles/{self.date:%Y%m%d%H}/nest{self.nest}/the_file.t{self.date:%H}z.{self.product}.f{self.fxx:02d}.grib2",
            "local_alt": f"/alternative/path/to/your/model1/templated/with/{self.model}/gribfiles/{self.date:%Y%m%d%H}/nest{self.nest}/the_file.t{self.date:%H}z.{self.product}.f{self.fxx:02d}.grib2",
        }
        self.LOCALFILE = f"{self.get_remoteFileName}"


class model2:
    def template(self):
        self.DESCRIPTION = "Local GRIB Files for model2"
        self.DETAILS = {
            "local": "These GRIB2 files are from a locally-stored modeling experiments."
        }
        self.PRODUCTS = {
            # UPDATE THIS
            "prs": "3D pressure level fields",
            "sfc": "Surface level fields",
        }
        self.SOURCES = {
            "local_main": f"/path/to/your/model2/templated/with/{self.model}/gribfiles/{self.date:%Y%m%d%H}/nest{self.nest}/the_file.t{self.date:%H}z.{self.product}.f{self.fxx:02d}.grib2",
            "local_alt": f"/alternative/path/to/your/model2/templated/with/{self.model}/gribfiles/{self.date:%Y%m%d%H}/nest{self.nest}/the_file.t{self.date:%H}z.{self.product}.f{self.fxx:02d}.grib2",
        }
        self.LOCALFILE = f"{self.get_remoteFileName}"
