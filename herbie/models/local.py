## Added by Brian Blaylock
## September 30, 2021

"""
! Experimental
This is a special case template for GRIB2 model data that is stored on
your local machine rather than retrieving data from remote sources.

Index files are assumed to be in the same directory as the file with
".idx" appended to the file name. If you don't have these, you will need
to generate them with wgrib2 (required for xarray subsetting).

Only one item is allowed in the SOURCES dict, and the key is "local".

Since Herbie accepts kwargs and passes them to self, you can template
the local file path with any parameter, just remember to pass that
parameter to the Herbie class 😋

To ask Herbie to find files with the template below you would type

..code-block::
    python

    Herbie('2021-9-21', model="my_model", fxx=0, ...)

    Herbie('2021-9-21', model="my_second_model", fxx=0, ...)

"""


class my_model:
    def template(self):
        self.DESCRIPTION = "Local GRIB Files"
        self.DETAILS = {
            "local": "These GRIB2 files are from a locally-stored modeling experiments."
        }
        self.PRODUCTS = {
            # UPDATE THIS
            "prs": "3D pressure level fields",
        }
        self.SOURCES = {
            "local": f"/path/to/your/model/templated/with/{self.model}/gribfiles/{self.date:%Y%m%d%H}/nest{self.nest}/the_file.t{self.date:%H}z.{self.product}.f{self.fxx:02d}.grib2",
        }
        self.LOCALFILE = f"{self.get_remoteFileName}"


class my_second_model:
    def template(self):
        self.DESCRIPTION = "Local GRIB Files"
        self.DETAILS = {
            "local": "These GRIB2 files are from a locally-stored modeling experiments."
        }
        self.PRODUCTS = {
            # UPDATE THIS
            "prs": "3D pressure level fields",
        }
        self.SOURCES = {
            "local": f"/path/to/your/second/model/templated/with/{self.model}/gribfiles/{self.date:%Y%m%d%H}/nest{self.nest}/the_file.t{self.date:%H}z.{self.product}.f{self.fxx:02d}.grib2",
        }
        self.LOCALFILE = f"{self.get_remoteFileName}"
