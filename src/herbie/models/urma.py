## Added by Brian Blaylock
## May 22, 2023

"""
A Herbie template for the URMA (Un-Restricted Mesoscale Analysis).

Look at the rtma.py file for the RTMA analysis template

TODO: Precipitation products need help!

NOTE: Hawaii and Puerto Rico GRIB files are not returned as a grid and
the data needs to be reshaped. I don't know what the right shape is.

NOTE: URMA is not archived very long on AWS

"""


class urma:
    def template(self):
        self.DESCRIPTION = "CONUS Un-Restricted Mesoscale Analysis (URMA)"
        self.DETAILS = {
            "NOMADS product description": "https://www.nco.ncep.noaa.gov/pmb/products/rtma/",
            "Amazon Open Data": "https://registry.opendata.aws/noaa-rtma/",
        }
        self.PRODUCTS = {
            "anl": "Analysis",
            "err": "Analysis Forecast Error",
            "ges": "Forecasts",
            "pcp": "Precipitation Field",
        }

        if self.product != "pcp":
            PATH = f"urma2p5.{self.date:%Y%m%d}/urma2p5.t{self.date:%H}z.2dvar{self.product}_ndfd.grb2_wexp"
            self.SOURCES = {
                "aws": f"https://noaa-urma-pds.s3.amazonaws.com/{PATH}",
                "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/urma/prod/{PATH}",
            }
        else:
            raise NotImplementedError(
                "The URMA model template needs some work. Please edit open a pull request. https://github.com/blaylockbk/Herbie/blob/main/herbie/models/urma.py"
            )

        self.IDX_SUFFIX = [".grb2.idx", ".idx", ".grib.idx"]
        self.LOCALFILE = f"{self.get_remoteFileName}"


class urma_ak:
    def template(self):
        self.DESCRIPTION = "Alaska Un-Restricted Mesoscale Analysis (URMA)"
        self.DETAILS = {
            "NOMADS product description": "https://www.nco.ncep.noaa.gov/pmb/products/rtma/",
            "Amazon Open Data": "https://registry.opendata.aws/noaa-rtma/",
        }
        self.PRODUCTS = {
            "anl": "Analysis",
            "err": "Analysis Forecast Error",
            "ges": "Forecasts",
        }

        PATH = f"akurma.{self.date:%Y%m%d}/akurma.t{self.date:%H}z.2dvar{self.product}_ndfd_3p0.grb2"
        self.SOURCES = {
            "aws": f"https://noaa-urma-pds.s3.amazonaws.com/{PATH}",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/urma/prod/{PATH}",
        }

        self.IDX_SUFFIX = [".grb2.idx", ".idx", ".grib.idx"]
        self.LOCALFILE = f"{self.get_remoteFileName}"


class urma_hi:
    def template(self):
        self.DESCRIPTION = "Hawaii Un-Restricted Mesoscale Analysis (URMA)"
        self.DETAILS = {
            "NOMADS product description": "https://www.nco.ncep.noaa.gov/pmb/products/rtma/",
            "Amazon Open Data": "https://registry.opendata.aws/noaa-rtma/",
        }
        self.PRODUCTS = {
            "anl": "Analysis",
            "err": "Analysis Forecast Error",
            "ges": "Forecasts",
        }

        PATH = f"hiurma.{self.date:%Y%m%d}/hiurma.t{self.date:%H}z.2dvar{self.product}_ndfd.grb2"
        self.SOURCES = {
            "aws": f"https://noaa-urma-pds.s3.amazonaws.com/{PATH}",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/urma/prod/{PATH}",
        }

        self.IDX_SUFFIX = [".grb2.idx", ".idx", ".grib.idx"]
        self.LOCALFILE = f"{self.get_remoteFileName}"


class urma_pr:
    def template(self):
        self.DESCRIPTION = "Puerto Rico Un-Restricted Mesoscale Analysis (URMA)"
        self.DETAILS = {
            "NOMADS product description": "https://www.nco.ncep.noaa.gov/pmb/products/rtma/",
            "Amazon Open Data": "https://registry.opendata.aws/noaa-rtma/",
        }
        self.PRODUCTS = {
            "anl": "Analysis",
            "err": "Analysis Forecast Error",
            "ges": "Forecasts",
        }

        PATH = f"prurma.{self.date:%Y%m%d}/prurma.t{self.date:%H}z.2dvar{self.product}_ndfd.grb2"
        self.SOURCES = {
            "aws": f"https://noaa-urma-pds.s3.amazonaws.com/{PATH}",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/urma/prod/{PATH}",
        }

        self.IDX_SUFFIX = [".grb2.idx", ".idx", ".grib.idx"]
        self.LOCALFILE = f"{self.get_remoteFileName}"
