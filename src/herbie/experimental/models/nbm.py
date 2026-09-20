from herbie.experimental.models import ModelTemplate


class NBMTemplate(ModelTemplate):
    """National Blend of Models (NBM) Model Template."""

    MODEL_NAME = "NBM"
    MODEL_DESCRIPTION = "NOAA National Blend of Models"
    MODEL_WEBSITES = {
        "nomads": "https://www.nco.ncep.noaa.gov/pmb/products/blend/",
        "aws": "https://registry.opendata.aws/noaa-nbm/",
        "nws": "https://www.weather.gov/mdl/nbm_home",
    }

    PARAMS = {
        "product": {
            "default": "co",
            "valid": ["co", "ak", "gu", "hi", "pr"],
            "descriptions": {
                "co": "CONUS 13-km resolution",
                "ak": "Alaska; 13-km resolution",
                "gu": "Guam 13-km resolution",
                "hi": "Hawaii 13-km resolution",
                "pr": "Puerto Rico 13-km resolution",
            },
        },
        "step": {
            "default": 1,  # fxx=0 not provided for NBM
            "valid": range(1, 215),
        },
    }

    INDEX_SUFFIX = [".idx", ".grib2.idx"]

    def get_remote_urls(self) -> dict[str, str]:
        """Return all the URLs.

        Dict order defines priority.
        """
        date = self.date
        product = self.params.get("product")
        step = self.params.get("step", 1)

        path = f"blend.{date:%Y%m%d/%H}/core/blend.t{date:%H}z.core.f{step:03d}.{product}.grib2"

        return {
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/blend/prod/{path}",
            "aws": f"https://noaa-nbm-grib2-pds.s3.amazonaws.com/{path}",
        }


class NBMQMDTemplate(ModelTemplate):
    """National Blend of Models - QMD (Quantitative Meteorological Diagnostic) Model Template."""

    MODEL_NAME = "NBMQMD"
    MODEL_DESCRIPTION = "NOAA National Blend of Models - QMD"
    MODEL_WEBSITES = {
        "nomads": "https://www.nco.ncep.noaa.gov/pmb/products/blend/",
        "aws": "https://registry.opendata.aws/noaa-nbm/",
        "nws": "https://www.weather.gov/mdl/nbm_home",
    }

    PARAMS = {
        "product": {
            "default": "co",
            "valid": ["co", "ak", "gu", "hi", "pr"],
            "descriptions": {
                "co": "CONUS 13-km resolution",
                "ak": "Alaska; 13-km resolution",
                "gu": "Guam 13-km resolution",
                "hi": "Hawaii 13-km resolution",
                "pr": "Puerto Rico 13-km resolution",
            },
        },
        "step": {
            "default": 1,  # fxx=0 not provided for NBM
            "valid": range(1, 215),
        },
    }

    INDEX_SUFFIX = [".idx", ".grib2.idx"]

    def get_remote_urls(self) -> dict[str, str]:
        """Return all the URLs.

        Dict order defines priority.
        """
        date = self.date
        product = self.params.get("product")
        step = self.params.get("step", 1)

        path = f"blend.{date:%Y%m%d/%H}/qmd/blend.t{date:%H}z.qmd.f{step:03d}.{product}.grib2"

        return {
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/blend/prod/{path}",
            "aws": f"https://noaa-nbm-grib2-pds.s3.amazonaws.com/{path}",
        }
