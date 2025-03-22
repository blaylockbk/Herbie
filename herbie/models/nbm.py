## Added by Brian Blaylock
## July 27, 2021

import warnings


class nbm:
    def template(self):
        self.DESCRIPTION = "National Blend of Models"
        self.DETAILS = {
            "NOMADS product description": "https://www.nco.ncep.noaa.gov/pmb/products/blend/",
            "AWS Registry": "https://registry.opendata.aws/noaa-nbm/",
            "NWS National Blend of Models Home": "https://www.weather.gov/mdl/nbm_home",
            "MDL NBM Page": "https://vlab.noaa.gov/web/mdl/nbm",
        }
        self.PRODUCTS = {
            "co": "CONUS 13-km resolution",
            "ak": "Alaska; 13-km resolution",
            "gu": "Guam 13-km resolution",
            "hi": "Hawaii 13-km resolution",
            "pr": "Puerto Rico 13-km resolution",
        }

        # fxx=0 are not provided for NBM, so default to 1 if not given
        if self.fxx == 0 or self.fxx is None:
            self.fxx = 1
            warnings.warn(
                "fxx=0 is not provided for NBM, so changing to fxx=1. "
                "Set fxx to remove this warning."
            )

        self.SOURCES = {
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/blend/prod/blend.{self.date:%Y%m%d/%H}/core/blend.t{self.date:%H}z.core.f{self.fxx:03d}.{self.product}.grib2",
            "aws": f"https://noaa-nbm-grib2-pds.s3.amazonaws.com/blend.{self.date:%Y%m%d/%H}/core/blend.t{self.date:%H}z.core.f{self.fxx:03d}.{self.product}.grib2",
        }
        self.LOCALFILE = f"{self.get_remoteFileName}"


class nbmqmd:
    def template(self):
        self.DESCRIPTION = "National Blend of Models - QMD"
        self.DETAILS = {
            "NOMADS product description": "https://www.nco.ncep.noaa.gov/pmb/products/blend/",
            "AWS Registry": "https://registry.opendata.aws/noaa-nbm/",
            "NWS National Blend of Models Home": "https://www.weather.gov/mdl/nbm_home",
            "MDL NBM Page": "https://vlab.noaa.gov/web/mdl/nbm",
        }
        self.PRODUCTS = {
            "co": "CONUS 13-km resolution",
            "ak": "Alaska; 13-km resolution",
            "gu": "Guam 13-km resolution",
            "hi": "Hawaii 13-km resolution",
            "pr": "Puerto Rico 13-km resolution",
        }

        # fxx=0 are not provided for NBM, so default to 1 if not given
        if self.fxx == 0 or self.fxx is None:
            self.fxx = 1
            warnings.warn(
                "fxx=0 is not provided for NBM, so changing to fxx=1. "
                "Set fxx to remove this warning."
            )

        self.SOURCES = {
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/blend/prod/blend.{self.date:%Y%m%d/%H}/qmd/blend.t{self.date:%H}z.qmd.f{self.fxx:03d}.{self.product}.grib2",
            "aws": f"https://noaa-nbm-grib2-pds.s3.amazonaws.com/blend.{self.date:%Y%m%d/%H}/qmd/blend.t{self.date:%H}z.qmd.f{self.fxx:03d}.{self.product}.grib2",
        }
        self.LOCALFILE = f"{self.get_remoteFileName}"
