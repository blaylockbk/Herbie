## Added by Brian Blaylock
## July 27, 2021


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
            "ak": "Alaska; 13-km resolution",
            "co": "CONUS 13-km resolution",
            "gu": "Guam 13-km resolution",
            "hi": "Hawaii 13-km resolution",
            "pr": "Puerto Rico 13-km resolution",
        }
        self.SOURCES = {
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/blend/prod/blend.{self.date:%Y%m%d/%H}/core/blend.t{self.date:%H}z.core.f{self.fxx:03d}.{self.product}.grib2",
            "aws": f"https://noaa-nbm-grib2-pds.s3.amazonaws.com/blend.{self.date:%Y%m%d/%H}/core/blend.t{self.date:%H}z.core.f{self.fxx:03d}.{self.product}.grib2",
        }
        self.LOCALFILE = f"{self.get_remoteFileName}"
