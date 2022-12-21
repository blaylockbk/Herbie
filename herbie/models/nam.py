## Added by Brian Blaylock
## August 10, 2022

"""
A Herbie template for the NAM model.
"""


class nam:
    def template(self):
        self.DESCRIPTION = "North America Mesoscale - CONUS"
        self.DETAILS = {
            "NOMADS product description": "https://www.nco.ncep.noaa.gov/pmb/products/nam/",
        }
        self.PRODUCTS = {
            # TODO: Can add to this list. Look here: https://www.nco.ncep.noaa.gov/pmb/products/nam/
            "conusnest.hiresf": "CONUS 5 km",
            "firewxnest.hiresf": "Fire Weather 1.33 km CONUS/1.5 km Alaska",
            "alaskanest.hiresf": "Alaska 6 km",
            "hawaiinest.hiresf": "Hawaii 6 km",
            "priconest.hiresf": "Puerto Rico 3 km",
            "afwaca": "Central America/Caribbean",
        }
        self.SOURCES = {
            "aws": f"https://noaa-nam-pds.s3.amazonaws.com/nam.{self.date:%Y%m%d}/nam.t{self.date:%H}z.{self.product}{self.fxx:02d}.tm00.grib2",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/nam/prod/nam.{self.date:%Y%m%d}/nam.t{self.date:%H}z.{self.product}{self.fxx:02d}.tm00.grib2",
        }
        self.EXPECT_IDX_FILE = "remote"
        self.LOCALFILE = f"{self.get_remoteFileName}"
