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
    VALID_PRODUCTS = {
        "sfc": "2D surface level fields; 3-km resolution",
        "prs": "3D pressure level fields; 3-km resolution",
        "nat": "Native level fields; 3-km resolution",
        "subh": "Subhourly grids; 3-km resolution",
    }
    DEFAULT_PRODUCT = "prs"
    INDEX_SUFFIX = [".idx", ".grib2.idx"]  # Try .idx first, then .grib2.idx

    def _validate_params(self) -> None:
        """Validate parameters."""
        product = self.params.get("product", self.DEFAULT_PRODUCT)
        if product not in self.VALID_PRODUCTS.keys():
            raise ValueError(
                f"Invalid product '{product}'. Must be one of {self.VALID_PRODUCTS}"
            )

        step = self.params.get("step", self.DEFAULT_STEP)
        if not isinstance(step, int) or step < 0 or step > 48:
            raise ValueError(f"Invalid forecast hour '{step}'. Must be 0-48")

    def get_remote_urls(self) -> dict[str, str]:
        """Return all the URLs.

        Note: Dict order defines default priority order.
        """
        date = self.date
        step = self.params.get("step", self.DEFAULT_STEP)
        product = self.params.get("product", self.DEFAULT_PRODUCT)

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
