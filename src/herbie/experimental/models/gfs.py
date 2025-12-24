from datetime import datetime

from herbie.experimental.models import ModelTemplate


class GFSTemplate(ModelTemplate):
    """GFS Model Template."""

    MODEL_NAME = "GFS"
    MODEL_DESCRIPTION = "NOAA Global Forecast System"
    MODEL_WEBSITES = {
        "nomads": "https://www.nco.ncep.noaa.gov/pmb/products/gfs",
        "aws": "https://registry.opendata.aws/noaa-gfs-bdp-pds",
        "google": "https://console.cloud.google.com/marketplace/product/noaa-public/gfs",
        "azure": "https://microsoft.github.io/AIforEarthDataSets/data/noaa-gfs.html",
        "ncar_rda": "https://rda.ucar.edu/datasets/d084001/",
    }

    PARAMS = {
        "product": {
            "default": "pgrb2",
            "aliases": {"common": "pgrb2", "uncommon": "pgrb2b"},
            "valid": ["pgrb2", "pgrb2b"],
            "descriptions": {
                "pgrb2": "Common fields",
                "pgrb2b": "Uncommon fields",
            },
        },
        "resolution": {
            "default": 0.25,
            "valid": [0.25, 0.5, 1.0],
            "descriptions": {
                0.25: "0.25° resolution",
                0.5: "0.50° resolution",
                1.0: "1.00° resolution",
            },
        },
        "step": {
            "default": 0,
            "valid": range(0, 385),
        },
    }

    INDEX_SUFFIX = [".idx", ".grb2.inv"]

    
    def get_remote_urls(self) -> dict[str, str]:
        """Return all the URLs.

        Dict order defines priority.
        """
        date = self.date
        step = self.params.get("step")
        product = self.params.get("product")
        resolution = self.params.get("resolution")

        # Convert resolution to grib2 format (0.25 → 0p25)
        res_str = self._resolution_to_string(resolution)

        # GFS v16 layout change
        if date < datetime(2021, 3, 23):
            path = (
                f"gfs.{date:%Y%m%d/%H}/gfs.t{date:%H}z.{product}.{res_str}.f{step:03d}"
            )
        else:
            path = f"gfs.{date:%Y%m%d/%H}/atmos/gfs.t{date:%H}z.{product}.{res_str}.f{step:03d}"

        return {
            "aws": f"https://noaa-gfs-bdp-pds.s3.amazonaws.com/{path}",
            "google": f"https://storage.googleapis.com/global-forecast-system/{path}",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/{path}",
            "azure": f"https://noaagfs.blob.core.windows.net/gfs/{path}",
            "ncar_rda": (
                "https://data.rda.ucar.edu/d084001/"
                f"{date:%Y/%Y%m%d}/gfs.{res_str}.{date:%Y%m%d%H}.f{step:03d}.grib2"
            ),
        }
