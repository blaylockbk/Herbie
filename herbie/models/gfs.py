class gfs:
    def template(self):
        self.DESCRIPTION = 'Global Forecast System'
        self.DETAILS = 'https://www.nco.ncep.noaa.gov/pmb/products/gfs/'
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
            'nomads': f'https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.{self.date:%Y%m%d/%H}/atmos/gfs.t{self.date:%H}z.{self.product}.f{self.fxx:03d}.grib2',
            'aws': f'https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.{self.date:%Y%m%d/%H}/atmos/gfs.t{self.date:%H}z.{self.product}.f{self.fxx:03d}.grib2',
            'google': f'https://storage.googleapis.com/global-forecast-system/gfs.{self.date:%Y%m%d/%H}/atmos/gfs.t{self.date:%H}z.{self.product}.f{self.fxx:03d}.grib2',
            'azure': f'https://noaahrrr.blob.core.windows.net/gfs/gfs.{self.date:%Y%m%d/%H}/atmos/gfs.t{self.date:%H}z.{self.product}.f{self.fxx:03d}.grib2',
        }