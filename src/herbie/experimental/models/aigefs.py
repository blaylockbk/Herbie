from herbie.experimental.models import ModelTemplate


class AIGEFSTemplate(ModelTemplate):
    """AI Global Ensemble Forecast System Template."""

    MODEL_NAME = "AIGEFS"
    MODEL_DESCRIPTION = "AI Global Ensemble Forecast System (AIGEFS)"
    MODEL_WEBSITES = {
        "nomads": "https://www.nco.ncep.noaa.gov/pmb/products/aigefs/",
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
            "default": 0,
            "aliases": {
                "control": 0,
            },
            "valid": list(range(0, 31)) + ["spr", "avg"],
            "descriptions": {
                "spr": "Ensemble spread",
                "avg": "Ensemble average",
            },
        },
        "step": {
            "default": 0,
            "valid": range(0, 385),  # Adjust range as needed for AIGEFS
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

        # Convert member to string format
        if isinstance(member, int):
            member_str = f"mem{member:03d}"
        else:
            member_str = member  # "spr" or "avg"

        filedir = f"aigefs.{date:%Y%m%d/%H}"

        if member_str in ["spr", "avg"]:
            filepath = (
                f"{filedir}/ensstat/products/atmos/grib2/"
                f"aigefs.t{date:%H}z.{product}.{member_str}.f{step:03d}.grib2"
            )
        else:
            filepath = (
                f"{filedir}/{member_str}/model/atmos/grib2/"
                f"aigefs.t{date:%H}z.{product}.f{step:03d}.grib2"
            )

        return {
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/aigefs/prod/{filepath}",
        }
