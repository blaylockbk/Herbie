"""
NOTE: The Rapid Refresh Forecast System is under development and is rapidly changing
"""

HELP = r"""
Herbie(date, model='rrfs', ...)

fxx : int
product : {"prs", "2dfld", "testbed", "ififip", "subh"}
domain : {"conus", "alaska", "hawaii", "puerto rico", "na"}

If product="natlev", then domain should be "na"
"""


class rrfs:
    def template(self):
        self.DESCRIPTION = "Rapid Refresh Forecast System (RRFS)"
        self.DETAILS = {
            "aws product description": "https://registry.opendata.aws/noaa-rrfs-ops/",
        }
        self.HELP = HELP

        self.PRODUCTS = {
            "prslev": "pressure level fields",
            "natlev": "native level fields",
            "2dfld": "2D surface/post-processed fields",
            "testbed": "testbed fields",
            "ififip": "icing/freezing fields",
            "subh": "Subhourly grids (available with 2D fields only)"
        }

        # Format the product parameter
        if self.product == "prs":
            self.product = "prslev"
        elif self.product == "2d":
            self.product = "2dfld"

        # subhourly on RRFS is only 2D at this time.
        # It requires both 2dfld and subh.
        extra_subh = ""
        if self.product == "subh":
            self.product = "2dfld"
            extra_subh = ".subh"

        # Format the domain parameter (default to conus)
        domain_map = {"alaska": "ak", "hawaii": "hi", "puerto rico": "pr"}
        if self.product == "natlev":
            self.domain = "na"
        else:
            self.domain = getattr(self, "domain", None) or "conus"
            self.domain = domain_map.get(self.domain, self.domain)

        # Resolution depends on the domain
        if self.domain in ("hi", "pr"):
            resolution = "2p5km"
        elif self.domain in ("na"):
            resolution = "13km"
        else:
            resolution = "3km"


        # Ensemble member (int) vs deterministic (None/other)
        self.member = getattr(self, "member", None)

        self.SOURCES = {
            "aws": (
                f"https://noaa-rrfs-ops-pds.s3.amazonaws.com/"
                f"rrfs.{self.date:%Y%m%d/%H}/"
                f"rrfs.t{self.date:%H}z.{self.product}.{resolution}{extra_subh}.f{self.fxx:03d}.{self.domain}.grib2"
            ),
            "nomads": (
                f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/rrfs/v1.0/"
                f"rrfs.{self.date:%Y%m%d/%H}/"
                f"rrfs.t{self.date:%H}z.{self.product}.{resolution}{extra_subh}.f{self.fxx:03d}.{self.domain}.grib2"
            ),

        }

        self.LOCALFILE = f"{self.get_remoteFileName}"

# prototype version -
class rrfs_old:
    def template(self):
        self.DESCRIPTION = "Rapid Refresh Forecast System (RRFS) (prototype)"
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
