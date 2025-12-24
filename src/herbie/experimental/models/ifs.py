"""ECMWF Integrated Forecast System (IFS) Model Template.

See the media release: https://www.ecmwf.int/en/about/media-centre/news/2022/ecmwf-makes-wide-range-data-openly-available

Copyright: © 2022 European Centre for Medium-Range Weather Forecasts (ECMWF)
License: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)
Disclaimer: ECMWF does not accept any liability whatsoever for any error or omission in the data.

Update 2024-02-29: ECMWF changed from 0.4° to 0.25° resolution
https://www.ecmwf.int/en/about/media-centre/news/2024/ecmwf-releases-much-larger-open-dataset
"""

from datetime import datetime

from herbie.experimental.models import ModelTemplate


class IFSTemplate(ModelTemplate):
    """ECMWF Integrated Forecast System Template."""

    MODEL_NAME = "IFS"
    MODEL_DESCRIPTION = "ECMWF Open Data - Integrated Forecast System"
    MODEL_WEBSITES = {
        "ecmwf": "https://confluence.ecmwf.int/display/DAC/ECMWF+open+data%3A+real-time+forecasts+from+IFS+and+AIFS",
    }

    PARAMS = {
        "product": {
            "default": "oper",
            "aliases": {
                "operational": "oper",
                "ensemble": "enfo",
                "wave": "wave",
                "wave-ensemble": "waef",
                "short-cutoff": "scda",
                "high-frequency": "scda",
                "wave-short-cutoff": "scwv",
                "seasonal": "mmsf",
            },
            "valid": ["oper", "enfo", "wave", "waef", "scda", "scwv", "mmsf"],
            "descriptions": {
                "oper": "Operational high-resolution forecast, atmospheric fields",
                "enfo": "Ensemble forecast, atmospheric fields",
                "wave": "Wave forecasts",
                "waef": "Ensemble forecast, ocean wave fields",
                "scda": "Short cut-off high-resolution forecast, atmospheric fields (high-frequency)",
                "scwv": "Short cut-off high-resolution forecast, ocean wave fields (high-frequency)",
                "mmsf": "Multi-model seasonal forecasts from ECMWF model",
            },
        },
        "step": {
            "default": 0,
            "valid": range(0, 361),
        },
    }

    INDEX_SUFFIX = [".index"]

    def _normalize_params(self, kwargs: dict) -> dict:
        """Normalize parameters, handling resolution default based on date."""
        normalized = super()._normalize_params(kwargs)

        # Handle resolution default based on date
        if "resolution" not in normalized:
            if self.date < datetime(2024, 2, 1):
                normalized["resolution"] = "0p4-beta"
            else:
                normalized["resolution"] = "0p25"

        return normalized

    def get_remote_urls(self) -> dict[str, str]:
        """Return all the URLs.

        Dict order defines priority.
        """
        date = self.date
        step = self.params.get("step")
        product = self.params.get("product")
        resolution = self.params.get("resolution")

        # Determine product suffix based on product type
        if product in ["enfo", "waef"]:
            product_suffix = "ef"
        else:
            product_suffix = "fc"

        # Build path based on date (layout changed on 2024-02-28)
        if date < datetime(2024, 2, 28, 6):
            post_root = (
                f"{date:%Y%m%d/%Hz}/{resolution}/{product}"
                f"/{date:%Y%m%d%H%M%S}-{step:03d}h-{product}-{product_suffix}.grib2"
            )
        else:
            post_root = (
                f"{date:%Y%m%d/%Hz}/ifs/{resolution}/{product}"
                f"/{date:%Y%m%d%H%M%S}-{step:03d}h-{product}-{product_suffix}.grib2"
            )

        return {
            "google": f"https://storage.googleapis.com/ecmwf-open-data/{post_root}",
            "aws": f"https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com/{post_root}",
            "ecmwf": f"https://data.ecmwf.int/forecasts/{post_root}",
            "azure": f"https://ai4edataeuwest.blob.core.windows.net/ecmwf/{post_root}",
            "azure-scda": f"https://ai4edataeuwest.blob.core.windows.net/ecmwf/{post_root.replace('oper', 'scda')}",
            "azure-waef": f"https://ai4edataeuwest.blob.core.windows.net/ecmwf/{post_root.replace('wave', 'waef')}",
        }
