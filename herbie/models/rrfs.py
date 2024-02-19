"""
NOTE: The Rapid Refresh Forecast System is under development and is rapidly changing
"""

HELP = r"""
Herbie(date, model='rrfs', ...)

fxx : int
product : {"prs", "nat", "testbed", "ififip"}
member : {"control", int}
domain : {"conus", "alaska", "hawaii", "puerto rico", None}

If product="natlev', then domain must be None
"""


class rrfs:
    def template(self):
        self.DESCRIPTION = "Rapid Refresh Forecast System (RRFS) Ensemble"
        self.DETAILS = {
            "aws product description": "https://registry.opendata.aws/noaa-rrfs/",
        }
        self.HELP = HELP

        self.PRODUCTS = {
            # Below are ensemble products found in ensprod/
            "prslev": "",
            "natlev": "",
            "testbed": "",
            "ififip": "",
        }

        # Format the member argument
        # member can be one of {'control', 'mem000#'}
        if isinstance(self.member, int):
            self.member = f"mem{self.member:04d}"

        # Format the product parameter
        if self.product == "prs":
            self.product = "prslev"
        elif self.product == "nat":
            self.product = "natlev"

        # Format the domain parameter
        if self.domain == "conus":
            self.domain = ".conus_3km"
        elif self.domain == "alaska":
            self.domain = ".ak"
        elif self.domain == "hawaii":
            self.domain = ".hi"
        elif self.domain == "puerto rico":
            self.domain = ".pr"
        elif self.domain is None:
            self.domain = ""

        self.SOURCES = {
            "aws": f"https://noaa-rrfs-pds.s3.amazonaws.com/rrfs_a/rrfs_a.{self.date:%Y%m%d/%H}/{self.member}/rrfs.t{self.date:%H}z.{self.product}.f{self.fxx:03d}{self.domain}.grib2",
        }
        self.LOCALFILE = f"{self.member}/{self.get_remoteFileName}"


class rrfs_old:
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
