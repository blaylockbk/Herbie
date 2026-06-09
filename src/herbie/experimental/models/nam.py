from herbie.experimental.models import ModelTemplate


class NAMTemplate(ModelTemplate):
    """North America Mesoscale (NAM) Model Template."""

    MODEL_NAME = "NAM"
    MODEL_DESCRIPTION = "NOAA North America Mesoscale - CONUS"
    MODEL_WEBSITES = {
        "nomads": "https://www.nco.ncep.noaa.gov/pmb/products/nam/",
    }

    PARAMS = {
        "product": {
            "default": "conusnest.hiresf",
            "valid": [
                "conusnest.hiresf",
                "firewxnest.hiresf",
                "alaskanest.hiresf",
                "hawaiinest.hiresf",
                "priconest.hiresf",
                "afwaca",
                "awphys",
                "awip12",
                "goes218",
                "bgrdsf",
                "bgrd3d",
                "awip32",
            ],
            "descriptions": {
                "conusnest.hiresf": "CONUS 5 km",
                "firewxnest.hiresf": "Fire Weather 1.33 km CONUS/1.5 km Alaska",
                "alaskanest.hiresf": "Alaska 6 km",
                "hawaiinest.hiresf": "Hawaii 6 km",
                "priconest.hiresf": "Puerto Rico 3 km",
                "afwaca": "Central America/Caribbean",
                "awphys": "NAM 218 AWIPS Grid - CONUS 12-km; pressure level fields",
                "awip12": "NAM 218 AWIPS Grid - CONUS 12-km; surface fields",
                "goes218": "NAM 218 AWIPS Grid - CONUS 12-km; GOES Simulated Brightness Temp",
                "bgrdsf": "NAM 190 grid - CONUS 12-km",
                "bgrd3d": "NAM 190 grid - CONUS 12-km; 60 hybrid levels",
                "awip32": "NAM 221 AWIPS Grid; 32-km resolution",
            },
        },
        "step": {
            "default": 0,
            "valid": range(0, 61),
        },
    }

    INDEX_SUFFIX = [".idx", ".grib2.idx"]

    def get_remote_urls(self) -> dict[str, str]:
        """Return all the URLs.

        Dict order defines priority.
        """
        date = self.date
        product = self.params.get("product")
        step = self.params.get("step")

        path = f"nam.{date:%Y%m%d}/nam.t{date:%H}z.{product}{step:02d}.tm00.grib2"

        return {
            "aws": f"https://noaa-nam-pds.s3.amazonaws.com/{path}",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/nam/prod/{path}",
        }
