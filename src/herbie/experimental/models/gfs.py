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

    # Resolution → product mapping
    RESOLUTION_PRODUCTS = {
        0.25: "pgrb2.0p25",
        0.5: "pgrb2.0p50",
        1.0: "pgrb2.1p00",
    }

    VALID_PRODUCTS = {
        "pgrb2.0p25": "Common fields, 0.25° resolution",
        "pgrb2.0p50": "Common fields, 0.50° resolution",
        "pgrb2.1p00": "Common fields, 1.00° resolution",
        "pgrb2b.0p25": "Uncommon fields, 0.25° resolution",
        "pgrb2b.0p50": "Uncommon fields, 0.50° resolution",
        "pgrb2b.1p00": "Uncommon fields, 1.00° resolution",
        "pgrb2full.0p50": "Combined grids, 0.50° resolution",
        "sfluxgrb": "Surface flux fields",
        "goesimpgrb2.0p25": "GOES imager proxy fields",
    }

    DEFAULT_RESOLUTION = 0.25
    DEFAULT_PRODUCT = None  # inferred from resolution

    INDEX_SUFFIX = [".idx", ".grb2.inv"]

    def _resolve_product(self) -> str:
        """Determine product from resolution or explicit product."""
        if "product" in self.params:
            return self.params["product"]

        resolution = self.params.get("resolution", self.DEFAULT_RESOLUTION)

        try:
            return self.RESOLUTION_PRODUCTS[float(resolution)]
        except (KeyError, ValueError):
            raise ValueError(
                f"Invalid resolution '{resolution}'. "
                f"Must be one of {list(self.RESOLUTION_PRODUCTS)}"
            )

    def _validate_params(self) -> None:
        """Validate parameters."""
        product = self._resolve_product()
        if product not in self.VALID_PRODUCTS:
            raise ValueError(
                f"Invalid product '{product}'. Must be one of {list(self.VALID_PRODUCTS)}"
            )

        step = self.params.get("step", self.DEFAULT_STEP)
        if not isinstance(step, int) or step < 0 or step > 384:
            raise ValueError("Invalid forecast hour. Step must be between 0 and 384.")

    def get_remote_urls(self) -> dict[str, str]:
        """Return all the URLs.

        Dict order defines priority.
        """
        date = self.date
        step = self.params.get("step", self.DEFAULT_STEP)
        product = self._resolve_product()

        # GFS v16 layout change
        if date < datetime(2021, 3, 23):
            path = f"gfs.{date:%Y%m%d/%H}/gfs.t{date:%H}z.{product}.f{step:03d}"
        else:
            path = f"gfs.{date:%Y%m%d/%H}/atmos/gfs.t{date:%H}z.{product}.f{step:03d}"

        # Special case
        if product == "sfluxgrb":
            path = path.replace("sfluxgrb.", "sfluxgrb")

        return {
            "aws": f"https://noaa-gfs-bdp-pds.s3.amazonaws.com/{path}",
            "google": f"https://storage.googleapis.com/global-forecast-system/{path}",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/{path}",
            "azure": f"https://noaagfs.blob.core.windows.net/gfs/{path}",
            "ncar_rda": (
                "https://data.rda.ucar.edu/d084001/"
                f"{date:%Y/%Y%m%d}/gfs.0p25.{date:%Y%m%d%H}.f{step:03d}.grib2"
            ),
        }
