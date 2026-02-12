from herbie.experimental.models import ModelTemplate


class RAPTemplate(ModelTemplate):
    """Rapid Refresh (RAP) Model Template."""

    MODEL_NAME = "RAP"
    MODEL_DESCRIPTION = "NOAA Rapid Refresh - CONUS"
    MODEL_WEBSITES = {
        "nomads": "https://www.nco.ncep.noaa.gov/pmb/products/rap",
    }

    PARAMS = {
        "product": {
            "default": "awp130pgrb",
            "valid": [
                "awp130pgrb",
                "awp252pgrb",
                "awp236pgrb",
                "awp130bgrb",
                "awp252bgrb",
                "wrfprs",
                "wrfnat",
                "awip32",
                "awp242",
                "awp200",
                "awp243",
                "wrfmsl",
            ],
            "descriptions": {
                "awp130pgrb": "CONUS Pressure levels; 13-km resolution",
                "awp252pgrb": "CONUS Pressure levels; 20-km resolution",
                "awp236pgrb": "CONUS Pressure levels; 40-km resolution",
                "awp130bgrb": "CONUS Native levels; 13-km resolution",
                "awp252bgrb": "CONUS Native levels; 20-km resolution",
                "wrfprs": "Full domain Pressure Levels; 13-km",
                "wrfnat": "Full domain Native Levels; 13-km",
                "awip32": "NOAMHI - High-Resolution North American Master Grid; 32-km",
                "awp242": "Alaska Quadruple Resolution Pressure levels; 11-km",
                "awp200": "Puerto Rico Pressure levels; 16-km",
                "awp243": "Eastern North America Pressure levels; 0.4 degree",
                "wrfmsl": "WRFMSL; 13-km resolution",
            },
        },
        "step": {
            "default": 0,
            "valid": range(0, 22),
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

        path = f"rap.{date:%Y%m%d}/rap.t{date:%H}z.{product}f{step:02d}.grib2"

        return {
            "aws": f"https://noaa-rap-pds.s3.amazonaws.com/{path}",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/rap/prod/{path}",
            "google": f"https://storage.googleapis.com/rapid-refresh/{path}",
            "azure": f"https://noaarap.blob.core.windows.net/rap/{path}",
        }


class RAPHistoricalTemplate(ModelTemplate):
    """Rapid Refresh (RAP) Historical - NCEI Model Template."""

    MODEL_NAME = "RAP_HISTORICAL"
    MODEL_DESCRIPTION = "NOAA Rapid Refresh - NCEI Historical"
    MODEL_WEBSITES = {
        "ncei": "https://www.ncei.noaa.gov/products/weather-climate-models/rapid-refresh-update",
    }

    PARAMS = {
        "product": {
            "default": "analysis",
            "valid": ["analysis", "forecast"],
            "descriptions": {
                "analysis": "RAP Analysis",
                "forecast": "RAP Forecast",
            },
        },
        "step": {
            "default": 0,
            "valid": range(0, 22),
        },
    }

    INDEX_SUFFIX = [".inv", ".grb2.inv", ".grib.inv"]

    def get_remote_urls(self) -> dict[str, str]:
        """Return all the URLs.

        Dict order defines priority.
        """
        date = self.date
        product = self.params.get("product")
        step = self.params.get("step")

        return {
            "rap_130": f"https://www.ncei.noaa.gov/data/rapid-refresh/access/historical/{product}/{date:%Y%m/%Y%m%d}/rap_130_{date:%Y%m%d_%H%M}_{step:03d}.grb2",
            "rap_252": f"https://www.ncei.noaa.gov/data/rapid-refresh/access/historical/{product}/{date:%Y%m/%Y%m%d}/rap_252_{date:%Y%m%d_%H%M}_{step:03d}.grb2",
            "ruc_252": f"https://www.ncei.noaa.gov/data/rapid-refresh/access/historical/{product}/{date:%Y%m/%Y%m%d}/ruc2_252_{date:%Y%m%d_%H%M}_{step:03d}.grb",
            "ruc_anl_252": f"https://www.ncei.noaa.gov/data/rapid-refresh/access/historical/{product}/{date:%Y%m/%Y%m%d}/ruc2anl_252_{date:%Y%m%d_%H%M}_{step:03d}.grb",
            "ruc_236": f"https://www.ncei.noaa.gov/data/rapid-refresh/access/historical/{product}/{date:%Y%m/%Y%m%d}/ruc2_236_{date:%Y%m%d_%H%M}_{step:03d}.grb",
            "ruc_211": f"https://www.ncei.noaa.gov/data/rapid-refresh/access/historical/{product}/{date:%Y%m/%Y%m%d}/ruc_211_{date:%Y%m%d_%H%M}_{step:03d}.grb",
        }


class RAPNCEITemplate(ModelTemplate):
    """Rapid Refresh (RAP) NCEI Model Template."""

    MODEL_NAME = "RAP_NCEI"
    MODEL_DESCRIPTION = "NOAA Rapid Refresh 13 km - NCEI"
    MODEL_WEBSITES = {
        "ncei": "https://www.ncei.noaa.gov/products/weather-climate-models/rapid-refresh-update",
    }

    PARAMS = {
        "product": {
            "default": "rap-130-13km",
            "valid": ["rap-130-13km", "rap-252-20km"],
            "descriptions": {
                "rap-130-13km": "RAP 13 km",
                "rap-252-20km": "RAP 20 km",
            },
        },
        "step": {
            "default": 0,
            "valid": range(0, 22),
        },
    }

    INDEX_SUFFIX = [".grb2.idx", ".idx"]

    def get_remote_urls(self) -> dict[str, str]:
        """Return all the URLs.

        Dict order defines priority.
        """
        date = self.date
        product = self.params.get("product")
        step = self.params.get("step")

        path = f"{product}/{date:%Y%m/%Y%m%d}/rap_{date:%Y%m%d_%H%M}_{step:03d}.grb2"

        return {
            "ncei": f"https://www.ncei.noaa.gov/data/rapid-refresh/access/{path}",
        }
