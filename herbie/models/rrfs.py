## Added by Brian Blaylock
## July 26, 2021

# NOTE: The Rapid Refresh Forecast System is rapidly changing


class rrfs:
    def template(self):
        self.DESCRIPTION = "Rapid Refresh Forecast System (RRFS) Ensemble"
        self.DETAILS = {
            "aws product description": "https://registry.opendata.aws/noaa-rrfs/",
        }
        self.PRODUCTS = {
            # Below are ensemble products found in ensprod/
            "mean": "ensemble mean",
            "avrg": "ensemble products: ???",
            "eas": "ensemble products: ???",
            "ffri": "ensemble products: ???",
            "lpmm": "ensemble products: ???",
            "pmmn": "ensemble products: ???",
            "prob": "ensemble products: ???",
            # Below are member products found in mem##/
            "testbed.conus": "surface grids (one for each member)",
            "na": "native grids (one for each member)",
        }
        self.SOURCES = {
            "aws": f"https://noaa-rrfs-pds.s3.amazonaws.com/rrfs.{self.date:%Y%m%d/%H}/ensprod/rrfsce.t{self.date:%H}z.conus.{self.product}.f{self.fxx:02d}.grib2",
            "aws-mem": f"https://noaa-rrfs-pds.s3.amazonaws.com/rrfs.{self.date:%Y%m%d/%H}/mem{self.member:02d}/rrfs.t{self.date:%H}z.mem{self.member:02d}.{self.product}f{self.fxx:03d}.grib2",
        }
        self.LOCALFILE = f"mem{self.member:02d}/{self.get_remoteFileName}"
