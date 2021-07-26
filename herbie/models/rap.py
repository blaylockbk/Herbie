## Added by Brian Blaylock
## July 26, 2021

class rap:
    def template(self):
        self.DESCRIPTION = 'Rapid Refresh'
        self.DETAILS = {
            'nomads product description': 'https://www.nco.ncep.noaa.gov/pmb/products/rap',
        }
        self.PRODUCTS = {
            'wrfprs.': 'Full domain Pressure Levels; 13-km',
            'wrfnat.': 'Full domain Native Levels; 13-km',
            'awp130pgrb': 'CONUS Pressure levels; 13-km resolution',
            'awp252pgrb': 'CONUS Pressure levels; 20-km resolution',
            'awp236pgrb': 'CONUS Pressure levels; 40-km resolution',
            'awp130bgrb': 'CONUS Native levels; 13-km resolution',
            'awp252bgrb': 'CONUS Native levels; 20-km resolution',
            'awip32': 'NOAMHI - High-Resolution North American Master Grid; 32-km resolution',
            'awp242': 'Alaska Quadruple Resolution Pressure levels; 11-km resolution',
            'awp200': 'Puerto Rico Pressure levels; 16-km resolution',
            'awp243': 'Eastern North America Pressure levels, 0.4 degree resolution',
            'wrfmsl': 'WRFMSL; 13-km resolution',
        }
        self.SOURCES = {
            'nomads': f'https://nomads.ncep.noaa.gov/pub/data/nccf/com/rap/prod/rap.{self.date:%Y%m%d}/rap.t{self.date:%H}z.{self.product}f{self.fxx:02d}.grib2',
            'aws': f'https://noaa-rap-pds.s3.amazonaws.com/rap.{self.date:%Y%m%d}/rap.t{self.date:%H}z.{self.product}f{self.fxx:02d}.grib2',
            'google': f'https://storage.googleapis.com/rapid-refresh/rap.{self.date:%Y%m%d}/rap.t{self.date:%H}z.{self.product}f{self.fxx:02d}.grib2',
            'azure': f'https://noaarap.blob.core.windows.net/rap/rap.{self.date:%Y%m%d}/rap.t{self.date:%H}z.{self.product}f{self.fxx:02d}.grib2',
        }
        self.LOCALFILE = f"{self.get_remoteFileName}"