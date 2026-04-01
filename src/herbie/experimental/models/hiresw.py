from herbie.experimental.models import ModelTemplate


class HIRESWTemplate(ModelTemplate):
    """High-Resolution Window (HIRESW) Forecast System Model Template."""

    MODEL_NAME = "HIRESW"
    MODEL_DESCRIPTION = "NOAA High-Resolution Window Forecast System"
    MODEL_WEBSITES = {
        "nomads": "https://www.nco.ncep.noaa.gov/pmb/products/hiresw/",
    }

    PARAMS = {
        "product": {
            "default": "arw_2p5km",
            "valid": ["arw_2p5km", "fv3_2p5km", "arw_5km", "fv3_5km"],
            "descriptions": {
                "arw_2p5km": "CONUS 2.5km ARW",
                "fv3_2p5km": "CONUS 2.5km FV3",
                "arw_5km": "CONUS 5km ARW",
                "fv3_5km": "CONUS 5km FV3",
            },
        },
        "domain": {
            "default": "conus",
            "valid": ["conus", "ak", "hi", "guam", "pr"],
            "descriptions": {
                "conus": "CONUS",
                "ak": "Alaska",
                "hi": "Hawaii",
                "guam": "Guam",
                "pr": "Puerto Rico",
            },
        },
        "member": {
            "default": 1,
            "valid": [1, 2],
        },
        "step": {
            "default": 0,
            "valid": range(0, 49),
        },
    }

    INDEX_SUFFIX = [".idx", ".grib2.idx"]

    def get_remote_urls(self) -> dict[str, str]:
        """Return all the URLs.

        Dict order defines priority.
        """
        date = self.date
        product = self.params.get("product")
        domain = self.params.get("domain")
        member = self.params.get("member")
        step = self.params.get("step")

        # Format member string
        member_str = f"mem{member}" if member == 2 else ""

        path = f"hiresw.{date:%Y%m%d}/hiresw.t{date:%H}z.{product}.f{step:02d}.{domain}{member_str}.grib2"

        return {
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/hiresw/prod/{path}",
        }
