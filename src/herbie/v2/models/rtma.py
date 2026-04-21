"""RTMA and URMA model templates for Herbie v2."""

from __future__ import annotations

from herbie.v2._base import HerbieModel
from herbie.v2._sources import GribSource

_IDX = [".grb2.idx", ".idx", ".grib.idx"]


class RTMA(HerbieModel):
    """
    CONUS Real-Time Mesoscale Analysis (RTMA).

    High-resolution (2.5-km) hourly analysis of surface conditions
    over the CONUS.

    Parameters
    ----------
    date : str or datetime
        Analysis valid datetime (UTC).
    product : {'anl', 'err', 'ges', 'pcp'}, default 'anl'
        Product type:

        ``'anl'``  2D variational analysis.
        ``'err'``  Analysis forecast error.
        ``'ges'``  First-guess (short forecast).
        ``'pcp'``  Precipitation field.

        Aliases: ``analysis→anl``, ``error→err``, ``forecast→ges``,
        ``guess→ges``, ``precipitation→pcp``.

    References
    ----------
    * https://www.nco.ncep.noaa.gov/pmb/products/rtma/
    * https://registry.opendata.aws/noaa-rtma/
    """

    MODEL_NAME = "RTMA"
    MODEL_DESCRIPTION = "CONUS Real-Time Mesoscale Analysis"
    MODEL_WEBSITES = {
        "NOMADS": "https://www.nco.ncep.noaa.gov/pmb/products/rtma/",
        "AWS": "https://registry.opendata.aws/noaa-rtma/",
    }

    PARAMS = {
        "product": {
            "default": "anl",
            "valid": ["anl", "err", "ges", "pcp"],
            "aliases": {
                "analysis": "anl",
                "error": "err",
                "forecast": "ges",
                "guess": "ges",
                "precipitation": "pcp",
            },
            "descriptions": {
                "anl": "2D variational analysis",
                "err": "Analysis forecast error",
                "ges": "First-guess (short forecast)",
                "pcp": "Precipitation field",
            },
        },
    }

    def _build_sources(self) -> dict:
        d = self.date
        product = self.params["product"]

        if product != "pcp":
            path = f"rtma2p5.{d:%Y%m%d}/rtma2p5.t{d:%H}z.2dvar{product}_ndfd.grb2_wexp"
        else:
            path = f"rtma2p5.{d:%Y%m%d}/rtma2p5.{d:%Y%m%d%H}.{product}.184.grb2"

        return {
            "aws":    GribSource(f"https://noaa-rtma-pds.s3.amazonaws.com/{path}", _IDX),
            "nomads": GribSource(f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/rtma/prod/{path}", _IDX),
        }


class RTMA_AK(HerbieModel):
    """Alaska Real-Time Mesoscale Analysis."""

    MODEL_NAME = "RTMA_AK"
    MODEL_DESCRIPTION = "Alaska Real-Time Mesoscale Analysis"

    PARAMS = {
        "product": {
            "default": "anl",
            "valid": ["anl", "err", "ges"],
            "aliases": {"analysis": "anl", "error": "err", "forecast": "ges"},
        },
    }

    def _build_sources(self) -> dict:
        d = self.date
        product = self.params["product"]
        path = f"akrtma.{d:%Y%m%d}/akrtma.t{d:%H}z.2dvar{product}_ndfd_3p0.grb2"
        return {
            "aws":    GribSource(f"https://noaa-rtma-pds.s3.amazonaws.com/{path}", _IDX),
            "nomads": GribSource(f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/rtma/prod/{path}", _IDX),
        }


class URMA(HerbieModel):
    """
    CONUS Un-Restricted Mesoscale Analysis (URMA).

    Like RTMA but uses a longer data-assimilation window for improved
    accuracy.  Updated once per hour.

    Parameters
    ----------
    date : str or datetime
        Analysis valid datetime (UTC).
    product : {'anl', 'err', 'ges'}, default 'anl'
        Product type (same as RTMA, minus precipitation).
    domain : {'conus', 'alaska', 'hawaii', 'puertorico'}, default 'conus'
        Analysis domain.

    References
    ----------
    * https://www.nco.ncep.noaa.gov/pmb/products/rtma/
    * https://registry.opendata.aws/noaa-rtma/
    """

    MODEL_NAME = "URMA"
    MODEL_DESCRIPTION = "NOAA Un-Restricted Mesoscale Analysis"
    MODEL_WEBSITES = {
        "NOMADS": "https://www.nco.ncep.noaa.gov/pmb/products/rtma/",
        "AWS": "https://registry.opendata.aws/noaa-rtma/",
    }

    PARAMS = {
        "domain": {
            "default": "conus",
            "valid": ["conus", "alaska", "hawaii", "puertorico"],
            "descriptions": {
                "conus":       "Continental US (2.5-km)",
                "alaska":      "Alaska (3.0-km)",
                "hawaii":      "Hawaii (2.5-km)",
                "puertorico":  "Puerto Rico",
            },
        },
        "product": {
            "default": "anl",
            "valid": ["anl", "err", "ges"],
            "aliases": {"analysis": "anl", "error": "err", "forecast": "ges", "guess": "ges"},
        },
    }

    _PREFIX = {
        "conus":      "urma2p5",
        "alaska":     "akurma",
        "hawaii":     "hiurma",
        "puertorico": "prurma",
    }
    _SUFFIX = {
        "conus":      "_ndfd.grb2_wexp",
        "alaska":     "_ndfd_3p0.grb2",
        "hawaii":     "_ndfd_2p5.grb2",
        "puertorico": "_ndfd.grb2",
    }

    def _build_sources(self) -> dict:
        d = self.date
        domain = self.params["domain"]
        product = self.params["product"]

        prefix = self._PREFIX[domain]
        suffix = self._SUFFIX[domain]
        filename = f"{prefix}.t{d:%H}z.2dvar{product}{suffix}"
        path = f"{prefix}.{d:%Y%m%d}/{filename}"

        return {
            "aws":    GribSource(f"https://noaa-urma-pds.s3.amazonaws.com/{path}", _IDX),
            "nomads": GribSource(f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/urma/prod/{path}", _IDX),
        }
