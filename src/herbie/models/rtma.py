## Added by Brian Blaylock
## January 3, 2023

"""
A Herbie template for the RTMA (Real-time Mesoscale Analysis).

Look at the urma.py file for the URMA analysis template

TODO: Precipitation products need help!

TODO: Clean up to look like URMA's template file.

TODO: Add all other domains.

"""


class rtma:
    def template(self):
        self.DESCRIPTION = "CONUS Real-Time Mesoscale Analysis (RTMA)"
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
            PATH = f"rtma2p5.{self.date:%Y%m%d}/rtma2p5.t{self.date:%H}z.2dvar{self.product}_ndfd.grb2_wexp"
            self.SOURCES = {
                "aws": f"https://noaa-rtma-pds.s3.amazonaws.com/{PATH}",
                "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/rtma/prod/{PATH}",
            }
        else:
            PATH = f"rtma2p5.{self.date:%Y%m%d}/rtma2p5.{self.date:%Y%m%d%H}.{self.product}.184.grb2"
            self.SOURCES = {
                "aws": f"https://noaa-rtma-pds.s3.amazonaws.com/{PATH}",
                "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/rtma/prod/{PATH}",
            }

        self.IDX_SUFFIX = [".grb2.idx", ".idx", ".grib.idx"]
        self.LOCALFILE = f"{self.get_remoteFileName}"


class rtma_ru:
    def template(self):
        self.DESCRIPTION = "CONUS Rapid Update Real-Time Mesoscale Analysis (RTMA)"
        self.DETAILS = {
            "NOMADS product description": "https://www.nco.ncep.noaa.gov/pmb/products/rtma/",
            "Amazon Open Data": "https://registry.opendata.aws/noaa-rtma/",
        }
        self.PRODUCTS = {
            "anl": "Analysis",
            "err": "Analysis Forecast Error",
            "ges": "Forecasts",
        }

        raise NotImplementedError(
            "The 'rtma_ru' template is incomplete. Please edit rtma.py and make a pull request."
        )

        PATH = f"rtma2p5_ru.{self.date:%Y%m%d}/rtma2p5_ru.t{self.t:04d}z.2dvar{self.product}_ndfd.grb2"
        self.SOURCES = {
            "aws": f"https://noaa-rtma-pds.s3.amazonaws.com/{PATH}",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/rtma/prod/{PATH}",
        }

        self.IDX_SUFFIX = [".grb2.idx", ".idx", ".grib.idx"]
        self.LOCALFILE = f"{self.get_remoteFileName}"


class rtma_ak:
    def template(self):
        self.DESCRIPTION = "Alaska Real-Time Mesoscale Analysis (RTMA)"
        self.DETAILS = {
            "NOMADS product description": "https://www.nco.ncep.noaa.gov/pmb/products/rtma/",
            "Amazon Open Data": "https://registry.opendata.aws/noaa-rtma/",
        }
        self.PRODUCTS = {
            "anl": "Analysis",
            "err": "Analysis Forecast Error",
            "ges": "Forecasts",
        }

        PATH = f"akrtma.{self.date:%Y%m%d}/akrtma.t{self.date:%H}z.2dvar{self.product}_ndfd_3p0.grb2"
        self.SOURCES = {
            "aws": f"https://noaa-rtma-pds.s3.amazonaws.com/{PATH}",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/rtma/prod/{PATH}",
        }

        self.IDX_SUFFIX = [".grb2.idx", ".idx", ".grib.idx"]
        self.LOCALFILE = f"{self.get_remoteFileName}"


class rtma_hi:
    def template(self):
        self.DESCRIPTION = "Hawaii Real-Time Mesoscale Analysis (RTMA)"
        self.DETAILS = {
            "NOMADS product description": "https://www.nco.ncep.noaa.gov/pmb/products/rtma/",
            "Amazon Open Data": "https://registry.opendata.aws/noaa-rtma/",
        }
        self.PRODUCTS = {
            "anl": "Analysis",
            "err": "Analysis Forecast Error",
            "ges": "Forecasts",
        }

        PATH = f"hirtma.{self.date:%Y%m%d}/hirtma.t{self.date:%H}z.2dvar{self.product}_ndfd.grb2"
        self.SOURCES = {
            "aws": f"https://noaa-rtma-pds.s3.amazonaws.com/{PATH}",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/rtma/prod/{PATH}",
        }

        self.IDX_SUFFIX = [".grb2.idx", ".idx", ".grib.idx"]
        self.LOCALFILE = f"{self.get_remoteFileName}"


class rtma_pr:
    def template(self):
        self.DESCRIPTION = "Puerto Rico Real-Time Mesoscale Analysis (RTMA)"
        self.DETAILS = {
            "NOMADS product description": "https://www.nco.ncep.noaa.gov/pmb/products/rtma/",
            "Amazon Open Data": "https://registry.opendata.aws/noaa-rtma/",
        }
        self.PRODUCTS = {
            "anl": "Analysis",
            "err": "Analysis Forecast Error",
            "ges": "Forecasts",
        }

        PATH = f"prrtma.{self.date:%Y%m%d}/prrtma.t{self.date:%H}z.2dvar{self.product}_ndfd.grb2"
        self.SOURCES = {
            "aws": f"https://noaa-rtma-pds.s3.amazonaws.com/{PATH}",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/rtma/prod/{PATH}",
        }

        self.IDX_SUFFIX = [".grb2.idx", ".idx", ".grib.idx"]
        self.LOCALFILE = f"{self.get_remoteFileName}"


class rtma_gu:
    def template(self):
        self.DESCRIPTION = "Guam Real-Time Mesoscale Analysis (RTMA)"
        self.DETAILS = {
            "NOMADS product description": "https://www.nco.ncep.noaa.gov/pmb/products/rtma/",
            "Amazon Open Data": "https://registry.opendata.aws/noaa-rtma/",
        }
        self.PRODUCTS = {
            "anl": "Analysis",
            "err": "Analysis Forecast Error",
            "ges": "Forecasts",
        }

        PATH = f"gurtma.{self.date:%Y%m%d}/gurtma.t{self.date:%H}z.2dvar{self.product}_ndfd.grb2"
        self.SOURCES = {
            "aws": f"https://noaa-rtma-pds.s3.amazonaws.com/{PATH}",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/rtma/prod/{PATH}",
        }

        self.IDX_SUFFIX = [".grb2.idx", ".idx", ".grib.idx"]
        self.LOCALFILE = f"{self.get_remoteFileName}"
