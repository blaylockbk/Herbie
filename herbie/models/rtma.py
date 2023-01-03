## Added by Brian Blaylock
## January 3, 2023

"""
A Herbie template for the RTMA (Real-time Mesoscale Analysis).

TODO: Extend template for URMA
"""
__all__ = ["rtma", "rtma_ak"]


class rtma:
    def template(self):
        self.DESCRIPTION = "CONUS Real-Time Mesoscale Analysis (RTMA)"
        self.DETAILS = {
            "NOMADS product description": "https://www.nco.ncep.noaa.gov/pmb/products/rtma/",
            "Amazon Open Data": "https://registry.opendata.aws/noaa-rtma/",
        }
        self.PRODUCTS = {
            "anl": "",
            "err": "",
            "ges": "",
            "pcp": "Precipitation Field",
        }

        if self.product != "pcp":
            self.SOURCES = {
                "aws": f"https://noaa-rtma-pds.s3.amazonaws.com/rtma2p5.{self.date:%Y%m%d}/rtma2p5.t{self.date:%H}z.2dvar{self.product}_ndfd.grb2_wexp",
                "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/rtma/prod/rtma2p5.{self.date:%Y%m%d}/rtma2p5.t{self.date:%H}z.2dvar{self.product}_ndfd.grb2_wexp",
            }
        else:
            self.SOURCES = {
                "aws": f"https://noaa-rtma-pds.s3.amazonaws.com/rtma2p5.{self.date:%Y%m%d}/rtma2p5.{self.date:%Y%m%d%H}.{self.product}.184.grb2",
                "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/rtma/prod/rtma2p5.{self.date:%Y%m%d}/rtma2p5.{self.date:%Y%m%d%H}.{self.product}.184.grb2",
            }

        self.EXPECT_IDX_FILE = None
        self.LOCALFILE = f"{self.get_remoteFileName}"

class rtma_ak:
    def template(self):
        self.DESCRIPTION = "Alaska Real-Time Mesoscale Analysis (RTMA)"
        self.DETAILS = {
            "NOMADS product description": "https://www.nco.ncep.noaa.gov/pmb/products/rtma/",
            "Amazon Open Data": "https://registry.opendata.aws/noaa-rtma/",
        }
        self.PRODUCTS = {
            "anl": "",
            "err": "",
            "ges": "",
        }

        self.SOURCES = {
            "aws": f"https://noaa-rtma-pds.s3.amazonaws.com/akrtma.{self.date:%Y%m%d}/akrtma.t{self.date:%H}z.2dvar{self.product}_ndfd_3p0.grb2",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/rtma/prod/akrtma.{self.date:%Y%m%d}/akrtma.t{self.date:%H}z.2dvar{self.product}_ndfd_3p0.grb2",
        }

        self.EXPECT_IDX_FILE = None
        self.LOCALFILE = f"{self.get_remoteFileName}"
