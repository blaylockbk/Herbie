"""
RRFS Ensemble Forecast System (REFS)
"""

import warnings

HELP = r"""
Herbie(date, model='refs', ...)

fxx : int
product : {"mean", "sprd", "pmmn", "lpmm", "avrg", "prob", "eas", "ffri"}
domain : {"conus", "alaska", "hawaii", "puerto rico", "na"}

If product="natlev", then domain should be "na"
"""


class refs:
    def template(self):
        self.DESCRIPTION = "Rapid Refresh Forecast System (RRFS)"
        self.DETAILS = {
            "aws product description": "https://registry.opendata.aws/noaa-rrfs-ops/",
        }
        self.HELP = HELP

        self.PRODUCTS = {
            # Below are ensemble products found in ensprod/
            "mean": "ensemble mean",
            "sprd": "ensemble products: ensemble spread",
            "pmmn": "ensemble products: probability-matched mean",
            "lpmm": "ensemble products: localized probability-matched mean",
            "avrg": "ensemble products: a combination of the pmmn and mean fields",
            "prob": "ensemble products: probabilistic output",
            "eas": "ensemble products: ensemble agreement scale probabilistic output",
            "ffri": "ensemble products: flash flood and recurrence interval exceedance probabilities (conus only)",
        }

        # Format the domain parameter (default to conus)
        domain_map = {"alaska": "ak", "hawaii": "hi", "puerto rico": "pr"}
        if self.product == "ffri":
            self.domain = "conus"
        else:
            self.domain = getattr(self, "domain", None) or "conus"
            self.domain = domain_map.get(self.domain, self.domain)

        if self.fxx==0:
            warnings.warn(
                            "REFS does not include fxx=0, using fxx=1 instead."
                        )
            self.fxx = 1

        self.SOURCES = {
            "aws": (
                f"https://noaa-rrfs-ops-pds.s3.amazonaws.com/"
                f"refs.{self.date:%Y%m%d/%H}/ensprod/"
                f"refs.t{self.date:%H}z.{self.product}.f{self.fxx:02d}.{self.domain}.grib2"
            ),
            "nomads": (
                f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/refs/v1.0/"
                f"refs.{self.date:%Y%m%d/%H}/ensprod/"
                f"refs.t{self.date:%H}z.{self.product}.f{self.fxx:02d}.{self.domain}.grib2"
            ),

        }

        self.LOCALFILE = f"{self.get_remoteFileName}"
