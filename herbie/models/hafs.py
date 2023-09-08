"""
A Herbie template for the HAFS model.
"""


class hafsa:
    def template(self):
        self.DESCRIPTION = "Hurricane Analysis and Forecast System"
        self.DETAILS = {
            "Homepage": "https://wpo.noaa.gov/the-hurricane-analysis-and-forecast-system-hafs/",
            "Hurricane Forecast Improvement Program": "https://hfip.org/hafs",
        }
        self.PRODUCTS = {
            "parent.atm": "?",
            "parent.sat": "?",
            "parent.swath": "?",
            "storm.atm": "?",
            "ww3": "?",
        }
        self.SOURCES = {
           "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/hafs/prod/{self.model}.{self.date:%Y%m%d/%H}/{self.label}.{self.date:%Y%m%d%H}.{self.model}.{self.product}.f{self.fxx:02d}.grb2
        }
        self.EXPECT_IDX_FILE = "remote"
        self.LOCALFILE = f"{self.get_remoteFileName}"


class hafsb:
    def template(self):
        self.DESCRIPTION = "Hurricane Analysis and Forecast System"
        self.DETAILS = {
            "Homepage": "https://wpo.noaa.gov/the-hurricane-analysis-and-forecast-system-hafs/",
            "Hurricane Forecast Improvement Program": "https://hfip.org/hafs",
        }
        self.PRODUCTS = {
            "parent.atm": "?",
            "parent.sat": "?",
            "parent.swath": "?",
            "storm.atm": "?",
            "ww3": "?",
        }
        self.SOURCES = {
           "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/hafs/prod/{self.model}.{self.date:%Y%m%d/%H}/{self.label}.{self.date:%Y%m%d%H}.{self.model}.{self.product}.f{self.fxx:02d}.grb2
        }
        self.EXPECT_IDX_FILE = "remote"
        self.LOCALFILE = f"{self.get_remoteFileName}"
