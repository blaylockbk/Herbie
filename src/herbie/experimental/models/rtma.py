"""RTMA (Real-Time Mesoscale Analysis) Model Templates.

Refactored for the new ModelTemplate base class.
Author: Brian Blaylock (original), Refactored: January 2025
"""

from herbie.experimental.models import ModelTemplate


class RTMATemplate(ModelTemplate):
    """CONUS Real-Time Mesoscale Analysis (RTMA)."""

    MODEL_NAME = "RTMA"
    MODEL_DESCRIPTION = "CONUS Real-Time Mesoscale Analysis"
    MODEL_WEBSITES = {
        "nomads": "https://www.nco.ncep.noaa.gov/pmb/products/rtma/",
        "aws": "https://registry.opendata.aws/noaa-rtma/",
    }

    PARAMS = {
        "product": {
            "default": "anl",
            "valid": ["anl", "err", "ges", "pcp"],
            "aliases": {
                "analysis": "anl",
                "error": "err",
                "forecast": "ges",
                "guess": "ges",
                "precipitation": "pcp",
            },
            "descriptions": {
                "anl": "Analysis",
                "err": "Analysis Forecast Error",
                "ges": "Forecasts (First Guess)",
                "pcp": "Precipitation Field",
            },
        },
    }

    INDEX_SUFFIX = [".grb2.idx", ".idx", ".grib.idx"]

    def get_remote_urls(self) -> dict[str, str]:
        """Return all the URLs.

        Note: Dict order defines default priority order.
        """
        date = self.date
        product = self.params.get("product")

        if product != "pcp":
            path = f"rtma2p5.{date:%Y%m%d}/rtma2p5.t{date:%H}z.2dvar{product}_ndfd.grb2_wexp"
        else:
            path = f"rtma2p5.{date:%Y%m%d}/rtma2p5.{date:%Y%m%d%H}.{product}.184.grb2"

        return {
            "aws": f"https://noaa-rtma-pds.s3.amazonaws.com/{path}",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/rtma/prod/{path}",
        }
