"""
ECMWF open-data model templates for Herbie v2.

IFS  — Integrated Forecast System (deterministic + ensemble)
AIFS — Artificial Intelligence Integrated Forecast System

Data license: © ECMWF, CC BY 4.0
https://creativecommons.org/licenses/by/4.0/
"""

from __future__ import annotations

from datetime import datetime

from herbie.v2._base import HerbieModel
from herbie.v2._sources import EccodesGribSource


class IFS(HerbieModel):
    """
    ECMWF Integrated Forecast System (IFS) open data.

    The ECMWF open-data archive provides global NWP output at 0.25°
    resolution (0.4° before 2024-02-01).  Updated as new forecasts
    are published; not all lead times are available for all products.

    Parameters
    ----------
    date : str or datetime
        Model initialization datetime.  ECMWF runs at 00 and 12 UTC
        for ``oper``; 00, 06, 12, 18 UTC for ``scda``.
    fxx : int or str, default 0
        Forecast lead time in hours.

        * ``oper`` / ``wave`` — 0, 6, 12, …, 360 h
        * ``enfo`` / ``waef`` — 0, 6, 12, …, 360 h
        * ``scda`` / ``scwv`` — 0, 1, 2, …, 90 h (high-frequency)

    product : str, default 'oper'
        Forecast stream:

        ``'oper'``  Operational high-resolution, atmospheric fields.
        ``'enfo'``  Ensemble forecast, atmospheric fields.
        ``'wave'``  High-resolution wave forecast.
        ``'waef'``  Ensemble wave forecast.
        ``'scda'``  Short cut-off high-resolution (high-frequency).
        ``'scwv'``  Short cut-off wave (high-frequency).
        ``'mmsf'``  Multi-model seasonal forecast (ECMWF only).

        Aliases: ``operational→oper``, ``ensemble→enfo``.

    Examples
    --------
    >>> from herbie.v2 import IFS
    >>> H = IFS("2024-03-01", fxx=24, product="oper")
    >>> H.inventory("t:500")
    >>> ds = H.xarray("t:500")

    References
    ----------
    * https://confluence.ecmwf.int/display/DAC/ECMWF+open+data
    * https://creativecommons.org/licenses/by/4.0/
    """

    MODEL_NAME = "IFS"
    MODEL_DESCRIPTION = "ECMWF Open Data — Integrated Forecast System"
    MODEL_WEBSITES = {
        "ECMWF": "https://confluence.ecmwf.int/display/DAC/ECMWF+open+data%3A+real-time+forecasts",
    }

    PARAMS = {
        "product": {
            "default": "oper",
            "valid": ["oper", "enfo", "wave", "waef", "scda", "scwv", "mmsf"],
            "aliases": {
                "operational": "oper",
                "ensemble": "enfo",
                "high-frequency": "scda",
                "wave-ensemble": "waef",
                "wave-short-cutoff": "scwv",
                "seasonal": "mmsf",
            },
            "descriptions": {
                "oper": "Operational high-resolution forecast, atmospheric fields",
                "enfo": "Ensemble forecast, atmospheric fields",
                "wave": "High-resolution wave forecast",
                "waef": "Ensemble wave forecast",
                "scda": "Short cut-off high-resolution forecast (high-frequency)",
                "scwv": "Short cut-off wave forecast (high-frequency)",
                "mmsf": "Multi-model seasonal forecast (ECMWF model only)",
            },
        },

    }

    def _build_sources(self) -> dict:
        d = self.date
        fxx = self.fxx
        product = self.params["product"]

        # Resolution changed 2024-02-01
        resolution = "0p4-beta" if d < datetime(2024, 2, 1) else "0p25"

        # Product suffix
        product_suffix = "ef" if product in ("enfo", "waef") else "fc"

        # URL layout changed 2024-02-28 06Z
        if d < datetime(2024, 2, 28, 6):
            post_root = (
                f"{d:%Y%m%d/%Hz}/{resolution}/{product}"
                f"/{d:%Y%m%d%H%M%S}-{fxx}h-{product}-{product_suffix}.grib2"
            )
        else:
            post_root = (
                f"{d:%Y%m%d/%Hz}/ifs/{resolution}/{product}"
                f"/{d:%Y%m%d%H%M%S}-{fxx}h-{product}-{product_suffix}.grib2"
            )

        idx = [".index"]
        return {
            "google": EccodesGribSource(
                f"https://storage.googleapis.com/ecmwf-open-data/{post_root}", idx
            ),
            "aws": EccodesGribSource(
                f"https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com/{post_root}", idx
            ),
            "ecmwf": EccodesGribSource(
                f"https://data.ecmwf.int/forecasts/{post_root}", idx
            ),
            "azure": EccodesGribSource(
                f"https://ai4edataeuwest.blob.core.windows.net/ecmwf/{post_root}", idx
            ),
        }


class AIFS(HerbieModel):
    """
    ECMWF Artificial Intelligence Integrated Forecast System (AIFS).

    Machine-learning global weather model trained on ERA5 and operational
    ECMWF analyses.  Became operational on 2025-02-25 at 0.25° resolution.

    Parameters
    ----------
    date : str or datetime
        Model initialization datetime (00 or 12 UTC).
    fxx : int or str, default 0
        Forecast lead time in hours (0–240).
    product : {'oper', 'enfo'}, default 'oper'
        Forecast stream:

        ``'oper'``  Deterministic high-resolution forecast.
        ``'enfo'``  50-member ensemble forecast.

    References
    ----------
    * https://www.ecmwf.int/en/about/media-centre/news/2025/ecmwfs-ai-forecasts-become-operational
    * https://confluence.ecmwf.int/display/DAC/ECMWF+open+data
    """

    MODEL_NAME = "AIFS"
    MODEL_DESCRIPTION = "ECMWF Open Data — AI Integrated Forecast System"
    MODEL_WEBSITES = {
        "ECMWF": "https://confluence.ecmwf.int/display/DAC/ECMWF+open+data%3A+real-time+forecasts",
        "Announcement": "https://www.ecmwf.int/en/about/media-centre/news/2025/ecmwfs-ai-forecasts-become-operational",
    }

    PARAMS = {
        "product": {
            "default": "oper",
            "valid": ["oper", "enfo"],
            "descriptions": {
                "oper": "Deterministic high-resolution forecast",
                "enfo": "50-member ensemble forecast",
            },
        },

    }

    def _build_sources(self) -> dict:
        d = self.date
        fxx = self.fxx
        product = self.params["product"]

        product_suffix = "pf" if product == "enfo" else "fc"

        # Layout history
        if d >= datetime(2025, 2, 25, 6):
            # Operational phase (current)
            post_root = (
                f"{d:%Y%m%d/%Hz}/aifs-single/0p25/{product}"
                f"/{d:%Y%m%d%H%M%S}-{fxx}h-{product}-{product_suffix}.grib2"
            )
        elif d >= datetime(2025, 2, 9, 12):
            # Pre-operational
            post_root = (
                f"{d:%Y%m%d/%Hz}/aifs-single/0p25/experimental/{product}"
                f"/{d:%Y%m%d%H%M%S}-{fxx}h-{product}-{product_suffix}.grib2"
            )
        elif product == "enfo":
            post_root = (
                f"{d:%Y%m%d/%Hz}/aifs-ens/0p25/{product}"
                f"/{d:%Y%m%d%H%M%S}-{fxx}h-{product}-{product_suffix}.grib2"
            )
        else:
            post_root = (
                f"{d:%Y%m%d/%Hz}/aifs/0p25/{product}"
                f"/{d:%Y%m%d%H%M%S}-{fxx}h-{product}-{product_suffix}.grib2"
            )

        idx = [".index"]
        return {
            "google": EccodesGribSource(
                f"https://storage.googleapis.com/ecmwf-open-data/{post_root}", idx
            ),
            "aws": EccodesGribSource(
                f"https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com/{post_root}", idx
            ),
            "ecmwf": EccodesGribSource(
                f"https://data.ecmwf.int/forecasts/{post_root}", idx
            ),
            "azure": EccodesGribSource(
                f"https://ai4edataeuwest.blob.core.windows.net/ecmwf/{post_root}", idx
            ),
        }
