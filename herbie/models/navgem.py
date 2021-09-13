## Added by Brian Blaylock
## July 28, 2021

class navgem:
    def template(self):
        self.DESCRIPTION = 'Navy Global Environment Model'
        self.DETAILS = {
            'NRL description': 'https://www.nrlmry.navy.mil/metoc/nogaps/navgem.html',
        }
        self.PRODUCTS = {
            'none': '',
        }
        self.SOURCES = {
            'nomads': f'https://nomads.ncep.noaa.gov/pub/data/nccf/com/fnmoc/prod/navgem.{self.date:%Y%m%d}/navgem_{self.date:%Y%m%d%H}f{self.fxx:03d}.grib2',
        }
        self.LOCALFILE = f"{self.get_remoteFileName}"
