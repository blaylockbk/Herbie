## Added by Brian Blaylock
## July 26, 2021

class gfs:
    def template(self):
        self.DESCRIPTION = 'Global Forecast System'
        self.DETAILS = {
            'nomads product description': 'https://www.nco.ncep.noaa.gov/pmb/products/gfs',
            'google cloud platform': 'https://console.cloud.google.com/marketplace/product/noaa-public/gfs?q=search&referrer=search&project=python-232920',
            'azure document':'https://github.com/microsoft/AIforEarthDatasets#noaa-global-forecast-system-gfs',
        }
        self.PRODUCTS = {
            'pgrb2.0p25': 'common fields, 0.25 degree resolution',
            'pgrb2.0p50': 'common fields, 0.50 degree resolution',
            'pgrb2.1p00': 'common fields, 1.00 degree resolution',
            'pgrb2b.0p25': 'uncommon fields, 0.25 degree resolution',
            'pgrb2b.0p50': 'uncommon fields, 0.50 degree resolution',
            'pgrb2b.1p00': 'uncommon fields, 1.00 degree resolution',
            'pgrb2full.0p50': 'combined grids of 0.50 resolution',
        }
        self.SOURCES = {
            'aws': f'https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.{self.date:%Y%m%d/%H}/atmos/gfs.t{self.date:%H}z.{self.product}.f{self.fxx:03d}',
            'aws-old': f'https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.{self.date:%Y%m%d/%H}/gfs.t{self.date:%H}z.{self.product}.f{self.fxx:03d}',
            'nomads': f'https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.{self.date:%Y%m%d/%H}/atmos/gfs.t{self.date:%H}z.{self.product}.f{self.fxx:03d}',
            'google': f'https://storage.googleapis.com/global-forecast-system/gfs.{self.date:%Y%m%d/%H}/atmos/gfs.t{self.date:%H}z.{self.product}.f{self.fxx:03d}',
            'azure': f'https://noaagfs.blob.core.windows.net/gfs/gfs.{self.date:%Y%m%d/%H}/atmos/gfs.t{self.date:%H}z.{self.product}.f{self.fxx:03d}',
        }
        self.LOCALFILE = f"{self.get_remoteFileName}"