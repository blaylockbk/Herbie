from herbie.experimental.models import ModelTemplate


class HREFTemplate(ModelTemplate):
    """High Resolution Ensemble Forecast (HREF) Model Template."""

    MODEL_NAME = "HREF"
    MODEL_DESCRIPTION = "NOAA High Resolution Ensemble Forecast"
    MODEL_WEBSITES = {
        "nomads": "https://nomads.ncep.noaa.gov/",
    }

    PARAMS = {
        "product": {
            "default": "mean",
            "valid": ["mean", "pmmn", "lpmm", "avrg", "sprd", "prob", "eas"],
            "descriptions": {
                "mean": "Arithmetic mean of all members",
                "pmmn": "Probability matched mean (full domain)",
                "lpmm": "Localized probability matched mean",
                "avrg": "Averaging of mean and pmmn (precipitation only)",
                "sprd": "Spread of the ensemble",
                "prob": "Probabilistic output (percentage of members meeting threshold)",
                "eas": "Ensemble Agreement Scale probability",
            },
        },
        "domain": {
            "default": "conus",
            "valid": ["conus", "ak", "hi", "pr"],
            "descriptions": {
                "conus": "lower-48 US domain",
                "ak": "Alaska domain",
                "hi": "Hawaii domain",
                "pr": "Puerto Rico domain",
            },
        },
        "step": {
            "default": 0,
            "valid": range(0, 49),
        },
    }

    INDEX_SUFFIX = [".grib2.idx", ".idx"]

    def get_remote_urls(self) -> dict[str, str]:
        """Return all the URLs.

        Dict order defines priority.
        """
        date = self.date
        product = self.params.get("product")
        domain = self.params.get("domain")
        step = self.params.get("step")

        path = f"href.{date:%Y%m%d}/ensprod/href.t{date:%H}z.{domain}.{product}.f{step:02d}.grib2"

        return {
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/href/prod/{path}",
        }
