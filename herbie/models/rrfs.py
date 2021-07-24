class rrfs:
    def template(self):
        self.DESCRIPTION = 'Rapid Refresh Forecast System (RRFS) Ensemble'
        self.DETAILS = 'https://registry.opendata.aws/noaa-rrfs/'
        self.PRODUCTS = {
            'temp': '',
        }
        self.SOURCES = {
            'aws' : f'https://noaa-rrfs-pds.s3.amazonaws.com/rrfs.{self.date:%Y%m%d/%H}/mem{self.member:02d}/rrfs.t{self.date:%H}z.conusf{self.fxx:03d}.grib2',
        }