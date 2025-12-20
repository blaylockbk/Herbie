from herbie.experimental.models import ModelTemplate


class HRRRTemplate(ModelTemplate):
    """HRRR Model Template."""

    MODEL_NAME = "HRRR"
    MODEL_DESCRIPTION = "High-Resolution Rapid Refresh - CONUS"
    MODEL_WEBSITES = {
        "gsl": "https://rapidrefresh.noaa.gov/hrrr/",
        "nomads": "https://www.nco.ncep.noaa.gov/pmb/products/hrrr/",
        "utah": "http://hrrr.chpc.utah.edu/",
    }

    PARAMS = {
        "product": {
            "default": "prs",
            "valid": ["sfc", "prs", "nat", "subh"],
            "aliases": {
                "native": "nat",
                "pressure": "prs",
                "surface": "sfc",
                "subhourly": "subh",
            },
            "descriptions": {
                "sfc": "2D surface level fields; 3-km resolution",
                "prs": "3D pressure level fields; 3-km resolution",
                "nat": "Native level fields; 3-km resolution",
                "subh": "Subhourly fields; 3-km resolution",
            },
        },
        "step": {"default": 0, "valid": range(0, 49)},
    }

    INDEX_SUFFIX = [".idx", ".grib2.idx"]  # Try .idx first, then .grib2.idx

    def get_remote_urls(self) -> dict[str, str]:
        """Return all the URLs.

        Note: Dict order defines default priority order.
        """
        date = self.date
        step = self.params.get("step")
        product = self.params.get("product")

        path = (
            f"hrrr.{date:%Y%m%d}/conus/hrrr.t{date:%H}z.wrf{product}f{step:02d}.grib2"
        )
        path2 = f"hrrr/{product}/{date:%Y%m%d}/hrrr.t{date:%H}z.wrf{product}f{step:02d}.grib2"

        return {
            "aws": f"https://noaa-hrrr-bdp-pds.s3.amazonaws.com/{path}",
            "google": f"https://storage.googleapis.com/high-resolution-rapid-refresh/{path}",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod/{path}",
            "azure": f"https://noaahrrr.blob.core.windows.net/hrrr/{path}",
            "pando": f"https://pando-rgw01.chpc.utah.edu/{path2}",
            "pando2": f"https://pando-rgw02.chpc.utah.edu/{path2}",
        }
