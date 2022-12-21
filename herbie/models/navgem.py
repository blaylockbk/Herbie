## Added by Brian Blaylock
## July 28, 2021
__all__ = ["navgem"]


class navgem:
    def template(self):
        self.DESCRIPTION = "Navy Global Environment Model"
        self.DETAILS = {
            "NRL description": "https://www.nrlmry.navy.mil/metoc/nogaps/navgem.html",
        }
        self.PRODUCTS = {
            "none": "",
        }
        self.SOURCES = {
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/fnmoc/prod/navgem.{self.date:%Y%m%d}/navgem_{self.date:%Y%m%d%H}f{self.fxx:03d}.grib2",
        }
        self.LOCALFILE = f"{self.get_remoteFileName}"


# ! DOES NOT WORK
class navgem_godae:
    """Not great implementation, just playing around..."""

    def template(self):
        self.DESCRIPTION = "Navy Global Environment Model"
        self.DETAILS = {
            "godae": "https://usgodae.org/",
        }
        self.PRODUCTS = {
            "GMET": "",
            "GLND": "",
            "GCOM": "",
        }
        self.SOURCES = {
            "g1": "https://usgodae.org/ftp/outgoing/fnmoc/models/navgem_0.5/2022/2022010306/US058GMET-GR1mdl.0018_0056_00600F0OF2022010306_0100_003500-000000air_temp",
            "godae": f"https://usgodae.org/ftp/outgoing/fnmoc/models/navgem_0.5/{self.date:%Y/%Y%m%d%H}/US058{self.product}-GR1mdl.0018_0056_{self.fxx:03d}00F0OF{self.date:%Y%m%d%H}_{self.level}{self.variable}",
        }
        self.LOCALFILE = f"{self.get_remoteFileName}"
