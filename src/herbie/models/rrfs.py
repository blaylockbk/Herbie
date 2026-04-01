"""
NOTE: The Rapid Refresh Forecast System is under development and is rapidly changing
"""

HELP = r"""
Herbie(date, model='rrfs', ...)

fxx : int
product : {"prs", "nat", "testbed", "ififip"}
member : {None, int}
    None for deterministic run, int (1-5) for ensemble members
domain : {"conus", "alaska", "hawaii", "puerto rico", "na"}

If product="natlev", then domain should be "na"
"""


class rrfs:
    def template(self):
        self.DESCRIPTION = "Rapid Refresh Forecast System (RRFS)"
        self.DETAILS = {
            "aws product description": "https://registry.opendata.aws/noaa-rrfs/",
        }
        self.HELP = HELP

        self.PRODUCTS = {
            "prslev": "pressure level fields",
            "natlev": "native level fields",
            "testbed": "testbed fields",
            "ififip": "icing/freezing fields",
        }

        # Format the product parameter
        if self.product == "prs":
            self.product = "prslev"
        elif self.product == "nat":
            self.product = "natlev"

        # Format the domain parameter (default to conus)
        domain_map = {"alaska": "ak", "hawaii": "hi", "puerto rico": "pr"}
        if self.product == "natlev":
            self.domain = "na"
        else:
            self.domain = getattr(self, "domain", None) or "conus"
            self.domain = domain_map.get(self.domain, self.domain)

        # Resolution depends on the domain
        resolution = "2p5km" if self.domain in ("hi", "pr") else "3km"

        # Ensemble member (int) vs deterministic (None/other)
        self.member = getattr(self, "member", None)

        if isinstance(self.member, int):
            member_str = f"m{self.member:03d}"
            # Ensemble members are only available for the "na" domain
            self.SOURCES = {
                "aws": (
                    f"https://noaa-rrfs-pds.s3.amazonaws.com/"
                    f"rrfs_a/rrfsens.{self.date:%Y%m%d/%H}/{member_str}/"
                    f"rrfs.t{self.date:%H}z.{member_str}.nbmfld.{resolution}.f{self.fxx:03d}.na.grib2"
                ),
            }
        else:
            self.SOURCES = {
                "aws": (
                    f"https://noaa-rrfs-pds.s3.amazonaws.com/"
                    f"rrfs_a/rrfs.{self.date:%Y%m%d/%H}/"
                    f"rrfs.t{self.date:%H}z.{self.product}.{resolution}.f{self.fxx:03d}.{self.domain}.grib2"
                ),
            }

        self.LOCALFILE = f"{self.get_remoteFileName}"


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
