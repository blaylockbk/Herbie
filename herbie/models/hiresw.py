## Added by Karl Schneider
## July 24, 2024

"""
A Herbie template for the HIRESW models.
"""
HELP = """
Herbie(date, model='hiresw', ...)

fxx : int
product : {"arw_2p5km", "fv3_2p5km", "arw_5km", ""fv3_5km}
domain : {"conus", "ak", "hi", "guam", "pr"}
member : int

2 members (1 and 2) available for ARW; Only 1 member (1) is available for FV3
"""

class hiresw:
    def template(self):
        self.DESCRIPTION = "High-Resolution Window (HIRESW) Forecast System"
        self.DETAILS = {
            "NOMADS product description": "https://www.nco.ncep.noaa.gov/pmb/products/hiresw/",
        }
        self.HELP = HELP
        self.PRODUCTS = {
            "arw_2p5km": "CONUS 2.5km ARW",
            "fv3_2p5km": "CONUS 2.5km FV3",
            "arw_5km": "CONUS 5km ARW",
            "fv3_5km": "CONUS 5km FV3",
        }
        self.DOMAINS = {
            "conus": "CONUS",
            "ak": "Alaska",
            "hi": "Hawaii",
            "guam": "Guam",
            "pr": "Puerto Rico",
        }
        
        # Set defaults
        if not hasattr(self, "domain"):
            self.domain = "conus"
        if not hasattr(self, "member"):
            self.member = 1
        
        # Format the member string correctly
        if self.member == 2:
            member = "mem2"
        else:
            member = ""
        
        self.SOURCES = {
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/hiresw/prod/hiresw.{self.date:%Y%m%d}/hiresw.t{self.date:%H}z.{self.product}.f{self.fxx:02d}.{self.domain}{member}.grib2",
        }
        self.EXPECT_IDX_FILE = "remote"
        self.LOCALFILE = f"{self.get_remoteFileName}"