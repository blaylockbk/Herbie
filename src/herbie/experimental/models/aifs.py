from datetime import datetime

from herbie.experimental.models import ModelTemplate


class AIFSTemplate(ModelTemplate):
    """ECMWF Artificial Intelligence Integrated Forecast System Template."""

    MODEL_NAME = "AIFS"
    MODEL_DESCRIPTION = (
        "ECMWF Open Data - Artificial Intelligence Integrated Forecast System"
    )
    MODEL_WEBSITES = {
        "ecmwf": "https://confluence.ecmwf.int/display/DAC/ECMWF+open+data%3A+real-time+forecasts+from+IFS+and+AIFS",
        "announcement": "https://www.ecmwf.int/en/about/media-centre/news/2025/ecmwfs-ai-forecasts-become-operational",
        "google": "https://storage.googleapis.com/ecmwf-open-data",
        "aws": "https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com",
        "azure": "https://ai4edataeuwest.blob.core.windows.net/ecmwf",
    }

    PARAMS = {
        "product": {
            "default": "oper",
            "valid": ["oper", "enfo", "experimental"],
            "descriptions": {
                "oper": "Operational high-resolution forecast, atmospheric fields",
                "enfo": "Ensemble forecast, atmospheric fields",
                "experimental": "Experimental high-resolution forecast, atmospheric fields",
            },
        },
        "step": {
            "default": 0,
            "valid": range(0, 241),  # Adjust range as needed for AIFS
        },
        "control": {
            "default": False,
            "valid": [True, False],
            "descriptions": {
                True: "Control forecast",
                False: "Perturbed forecast",
            },
        },
    }

    INDEX_SUFFIX = [".index"]
    INDEX_STYLE = "eccodes"  # 'wgrib2' or 'eccodes'

    def get_remote_urls(self) -> dict[str, str]:
        """Return all the URLs.

        Dict order defines priority.
        """
        date = self.date
        step = self.params.get("step")
        product = self.params.get("product")
        control = self.params.get("control", False)

        # Assign correct product suffix
        if control:
            product_suffix = "cf"
        else:
            if product == "enfo":
                product_suffix = "pf"
            else:
                product_suffix = "fc"

        # AIFS ensembles
        if product == "enfo":
            post_root = (
                f"{date:%Y%m%d/%Hz}/aifs-ens/0p25/{product}"
                f"/{date:%Y%m%d%H%M%S}-{step}h-{product}-{product_suffix}.grib2"
            )
        # Operational and experimental runs
        else:
            if date >= datetime(2025, 2, 25, 6):
                # ECMWF's AI forecasts become operational
                post_root = (
                    f"{date:%Y%m%d/%Hz}/aifs-single/0p25/{product}"
                    f"/{date:%Y%m%d%H%M%S}-{step}h-{product}-{product_suffix}.grib2"
                )
            elif date >= datetime(2025, 2, 9, 12):
                # Preparing for the operational phase of the AI forecast
                post_root = (
                    f"{date:%Y%m%d/%Hz}/aifs-single/0p25/experimental/{product}"
                    f"/{date:%Y%m%d%H%M%S}-{step}h-{product}-{product_suffix}.grib2"
                )
            else:
                post_root = (
                    f"{date:%Y%m%d/%Hz}/aifs/0p25/{product}"
                    f"/{date:%Y%m%d%H%M%S}-{step}h-{product}-{product_suffix}.grib2"
                )

        return {
            "google": f"https://storage.googleapis.com/ecmwf-open-data/{post_root}",
            "aws": f"https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com/{post_root}",
            "ecmwf": f"https://data.ecmwf.int/forecasts/{post_root}",
            "azure": f"https://ai4edataeuwest.blob.core.windows.net/ecmwf/{post_root}",
        }
