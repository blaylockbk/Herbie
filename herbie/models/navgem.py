## Added by Brian Blaylock
## July 28, 2021


class navgem_nomads:
    """NAVGEM on NOMADS."""

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


class navgem_godae:
    """
    NAVGEM on GODAE.

    Not great implementation.

    TODO: Study the file naming convention
    https://usgodae.org/docs/layout/mdllayout.pns.html

    For example:
    https://usgodae.org/ftp/outgoing/fnmoc/models/navgem_0.5/2023/2023011218/US058GMET-GR1mdl.0018_0056_00000F0OF2023011218_0100_010132-000000air_temp
    """

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
            # "g1": "https://usgodae.org/ftp/outgoing/fnmoc/models/navgem_0.5/2022/2022010306/US058GMET-GR1mdl.0018_0056_00600F0OF2022010306_0100_003500-000000air_temp",
            "godae": f"https://usgodae.org/ftp/outgoing/fnmoc/models/navgem_0.5/{self.date:%Y/%Y%m%d%H}/US058{self.product}-GR1mdl.0018_0056_{self.fxx:03d}00F0OF{self.date:%Y%m%d%H}_{self.level}{self.variable}",
        }
        self.LOCALFILE = f"{self.get_remoteFileName}"
