## Added by Brian Blaylock
## July 26, 2021

class gfs_wave:
    def template(self):
        self.DESCRIPTION = 'Global Forecast System - Wave Products'
        self.DETAILS = {
            'nomads product description': 'https://www.nco.ncep.noaa.gov/pmb/products/gfs/#GFSwave',
        }
        self.PRODUCTS = {
            'arctic.9km': 'Arctic; 9-km resolution',
            'atlocn.0p16': 'North Atlantic 0.16 deg resolution',
            'epacif.0p16': 'Eastern Pacific; .16 deg resolution',
            'global.0p16': 'Global; 0.16 deg resolution',
            'global.0p25': 'Global; 0.25 deg resolution',
            'gsouth.0p25': 'Global South; 0.25 deg resolution',
            'wcoast.0p16': 'West Coast; 0.16 deg resolution',

        }
        self.SOURCES = {
            'nomads': f'https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.{self.date:%Y%m%d/%H}/wave/gridded/gfswave.t{self.date:%H}z.{self.product}.f{self.fxx:03d}.grib2',
            'aws': f'https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.{self.date:%Y%m%d/%H}/wave/gridded/gfswave.t{self.date:%H}z.{self.product}.f{self.fxx:03d}.grib2',
            'google': f'https://storage.googleapis.com/global-forecast-system/gfs.{self.date:%Y%m%d/%H}/wave/gridded/gfswave.t{self.date:%H}z.{self.product}.f{self.fxx:03d}.grib2',
            'azure': f'https://noaahrrr.blob.core.windows.net/gfs/gfs.{self.date:%Y%m%d/%H}/wave/gridded/gfswave.t{self.date:%H}z.{self.product}.f{self.fxx:03d}.grib2',
        }
        self.LOCALFILE = f"{self.get_remoteFileName}"