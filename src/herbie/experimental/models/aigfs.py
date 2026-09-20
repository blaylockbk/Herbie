from herbie.experimental.models import ModelTemplate


class AIGFSTemplate(ModelTemplate):
    """AI-GFS Model Template."""

    MODEL_NAME = "AIGFS"
    MODEL_DESCRIPTION = "NOAA AI Global Forecast System"
    MODEL_WEBSITES = {
        "nomads": "https://www.nco.ncep.noaa.gov/pmb/products/aigfs",
        "announcement": "https://www.noaa.gov/news-release/noaa-deploys-new-generation-of-ai-driven-global-weather-models",
    }

    PARAMS = {
        "product": {
            "default": "sfc",
            "aliases": {
                "surface": "sfc",
                "pressure": "pres",
            },
            "valid": ["sfc", "pres"],
            "descriptions": {
                "sfc": "Surface fields, 0.25 degree resolution",
                "pres": "Pressure fields, 0.25 degree resolution",
            },
        },
        "step": {
            "default": 0,
        },
    }

    INDEX_SUFFIX = [".grib2.idx", ".idx"]

    def get_remote_urls(self) -> dict[str, str]:
        """Return all the URLs.

        Dict order defines priority.
        """
        date = self.date
        step = self.params.get("step")
        product = self.params.get("product")

        path = (
            f"aigfs.{date:%Y%m%d/%H}/model/atmos/grib2/"
            f"aigfs.t{date:%H}z.{product}.f{step:03d}.grib2"
        )

        return {
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/aigfs/prod/{path}",
        }
