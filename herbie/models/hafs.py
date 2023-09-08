"""
A Herbie template for the HAFS model.
"""

# maybe use functool caching decorator here??
def get_name_mapping(DATE):
    """Get a mapping of the available hurricane names and storm id."""
    # read some file/files at NOMADS
    # parse it into a dict with name:label
    pass

class hafsa:
    def template(self):
        self.DESCRIPTION = "Hurricane Analysis and Forecast System (HAFS-A) with GFDL microphysics."
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

        # `self.name` is the hurricane storm identifier (e.g., 11e)
        # I want to get a list of labels for the requested datetime
        # and produce a maping of the stormIDs to the hurricane name
        # so that if name='jova' it will get the stormID name='11e'

        # TODO: If name is a regular hurricane name and not an ID label,
        # then get the ID from the name_mapping

        self.SOURCES = {
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/hafs/prod/{self.model}.{self.date:%Y%m%d/%H}/{self.name}.{self.date:%Y%m%d%H}.{self.model}.{self.product}.f{self.fxx:02d}.grb2"
        }
        self.EXPECT_IDX_FILE = "remote"
        self.LOCALFILE = f"{self.get_remoteFileName}"


class hafsb:
    def template(self):
        self.DESCRIPTION = "Hurricane Analysis and Forecast System (HAFS-B) Thompson microphysics and tc-pbl option."
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
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/hafs/prod/{self.model}.{self.date:%Y%m%d/%H}/{self.name}.{self.date:%Y%m%d%H}.{self.model}.{self.product}.f{self.fxx:02d}.grb2"
        }
        self.EXPECT_IDX_FILE = "remote"
        self.LOCALFILE = f"{self.get_remoteFileName}"
