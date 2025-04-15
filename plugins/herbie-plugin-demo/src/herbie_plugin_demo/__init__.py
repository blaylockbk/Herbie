"""My custom Herbie model template."""


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


class plugin_model_2:
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
            "local_main": f"/path/to/your/model2/templated/with/{self.model}/gribfiles/{self.date:%Y%m%d%H}/the_file.t{self.date:%H}z.{self.product}.f{self.fxx:02d}.grib2",
            "local_alt": f"/alternative/path/to/your/model2/templated/with/{self.model}/gribfiles/{self.date:%Y%m%d%H}/the_file.t{self.date:%H}z.{self.product}.f{self.fxx:02d}.grib2",
        }
        self.LOCALFILE = f"{self.get_remoteFileName}"
