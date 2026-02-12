from herbie.experimental.models import ModelTemplate


class HGEFSTemplate(ModelTemplate):
    """Hybrid Global Ensemble Forecast System Template."""

    MODEL_NAME = "HGEFS"
    MODEL_DESCRIPTION = "Hybrid Global Ensemble Forecast System (HGEFS)"
    MODEL_WEBSITES = {
        "nomads": "https://www.nco.ncep.noaa.gov/pmb/products/hgefs/",
        "announcement": "https://www.noaa.gov/news-release/noaa-deploys-new-generation-of-ai-driven-global-weather-models",
    }

    PARAMS = {
        "product": {
            "default": "pres",
            "aliases": {
                "surface": "sfc",
                "pressure": "pres",
            },
            "valid": ["pres", "sfc"],
            "descriptions": {
                "pres": "Pressure fields, 0.25 degree resolution",
                "sfc": "Surface fields, 0.25 degree resolution",
            },
        },
        "member": {
            "default": "spr",
            "valid": ["spr", "avg"],
            "descriptions": {
                "spr": "Ensemble spread",
                "avg": "Ensemble average",
            },
        },
        "step": {
            "default": 0,
            "valid": range(0, 385),  # Adjust range as needed for HGEFS
        },
    }

    INDEX_SUFFIX = [".grib2.idx"]

    def get_remote_urls(self) -> dict[str, str]:
        """Return all the URLs.

        Dict order defines priority.
        """
        date = self.date
        step = self.params.get("step")
        product = self.params.get("product")
        member = self.params.get("member")

        filepath = (
            f"hgefs.{date:%Y%m%d/%H}/ensstat/products/atmos/grib2/"
            f"hgefs.t{date:%H}z.{product}.{member}.f{step:03d}.grib2"
        )

        return {
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/hgefs/prod/{filepath}",
        }
