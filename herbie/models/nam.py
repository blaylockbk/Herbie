## Added by Brian Blaylock
## August 10, 2022
## Last Updated July 24, 2024

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
            "awphys": "NAM 218 AWIPS Grid - CONUS; 12-km Resolution; full complement of pressure level fields and some surface-based fields",
            "awip12": "NAM 218 AWIPS Grid - CONUS; 12-km Resolution; 12-km Resolution; full complement of surface-based fields",
            "goes218": "NAM 218 AWIPS Grid - CONUS; 12-km Resolution; GOES Simulated Brightness Temp",
            "bgrdsf": "NAM 190 grid - CONUS; 12-km Resolution; Staggered B-grid on rotated latitude/longitude grid",
            "bgrd3d": "NAM 190 grid - CONUS; 12-km Resolution; Staggered B-grid on rotated lat/lon grid using the 60 NAM hybrid levels",
            "awip32": "NAM 221 AWIPS Grid; 32-km Resolution; High Resolution North American Master Grid",
        }
        self.SOURCES = {
            "aws": f"https://noaa-nam-pds.s3.amazonaws.com/nam.{self.date:%Y%m%d}/nam.t{self.date:%H}z.{self.product}{self.fxx:02d}.tm00.grib2",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/nam/prod/nam.{self.date:%Y%m%d}/nam.t{self.date:%H}z.{self.product}{self.fxx:02d}.tm00.grib2",
        }
        self.EXPECT_IDX_FILE = "remote"
        self.LOCALFILE = f"{self.get_remoteFileName}"
