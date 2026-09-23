"""
NOTE: The Rapid Refresh Forecast System is under development and is rapidly changing
"""

HELP = r"""
Herbie(date, model='rrfs', ...)

fxx : int
product : {"prslev", "prslevnomads", "2dfld", "2dfldnomads", "subh"}
domain : {"conus", "alaska", "hawaii", "puerto rico", "na"}

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
            "prslevnomads": "pressure level fields, ensemble",
            "2dfld": "2D surface/post-processed fields",
            "2dfldnomads": "2D surface/post-processed fields, ensemble",
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

        if self.member is None:
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
        else:  # member > 1 is specified
            self.SOURCES = {
                "aws": (
                    f"https://noaa-rrfs-ops-pds.s3.amazonaws.com/"
                    f"rrfsens.{self.date:%Y%m%d/%H}/m{self.member:03d}/"
                    f"rrfs.t{self.date:%H}z.m{self.member:03d}.{self.product}.{resolution}{extra_subh}.f{self.fxx:03d}.{self.domain}.grib2"
                ),
                "nomads": (
                    f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/rrfs/v1.0/"
                    f"rrfsens.{self.date:%Y%m%d/%H}/m{self.member:03d}/"
                    f"rrfs.t{self.date:%H}z.m{self.member:03d}.{self.product}.{resolution}{extra_subh}.f{self.fxx:03d}.{self.domain}.grib2"
                ),
            }

        self.LOCALFILE = f"{self.get_remoteFileName}"
