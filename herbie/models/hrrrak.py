## Added by Brian Blaylock
## July 26, 2021

class hrrrak:
    def template(self):
        self.DESCRIPTION = 'High-Resolution Rapid Refresh - Alaska'
        self.DETAILS = {
            'nomads product description': 'https://www.nco.ncep.noaa.gov/pmb/products/hrrr',
        }
        self.PRODUCTS = {
            'prs': "3D pressure level fields; 3-km resolution",
            'sfc': "2D surface level fields; 3-km resolution",
            'nat': "Native level fields; 3-km resolution",
            'subh': "Subhourly grids; 3-km resolution"
        }
        self.SOURCES = {
            'nomads': f'https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod/hrrr.{self.date:%Y%m%d}/alaska/hrrr.t{self.date:%H}z.wrf{self.product}f{self.fxx:02d}.ak.grib2',
            'aws': f'https://noaa-hrrr-bdp-pds.s3.amazonaws.com/hrrr.{self.date:%Y%m%d}/alaska/hrrr.t{self.date:%H}z.wrf{self.product}f{self.fxx:02d}.ak.grib2',
            'google': f'https://storage.googleapis.com/high-resolution-rapid-refresh/hrrr.{self.date:%Y%m%d}/alaska/hrrr.t{self.date:%H}z.wrf{self.product}f{self.fxx:02d}.ak.grib2',
            'azure': f'https://noaahrrr.blob.core.windows.net/hrrr/hrrr.{self.date:%Y%m%d}/alaska/hrrr.t{self.date:%H}z.wrf{self.product}f{self.fxx:02d}.ak.grib2',
            'pando': f'https://pando-rgw01.chpc.utah.edu/{self.model}/{self.product}/{self.date:%Y%m%d}/{self.model}.t{self.date:%H}z.wrf{self.product}f{self.fxx:02d}.grib2',
            'pando2': f'https://pando-rgw02.chpc.utah.edu/{self.model}/{self.product}/{self.date:%Y%m%d}/{self.model}.t{self.date:%H}z.wrf{self.product}f{self.fxx:02d}.grib2',
        }
        self.LOCALFILE = f"{self.get_remoteFileName}"