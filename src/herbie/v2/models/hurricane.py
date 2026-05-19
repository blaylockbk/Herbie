"""
HAFS, HIRESW, and NAVGEM model templates for Herbie v2.

HAFSA / HAFSB  — Hurricane Analysis and Forecast System
HIRESW         — High-Resolution Window Forecast System
NavgemNOMADS   — Navy Global Environment Model (recent, from NOMADS)
NavgemGODAE    — NAVGEM / NOGAPS historical archive (GODAE server)
"""

from __future__ import annotations

import functools
import re

import requests

from herbie.v2._base import HerbieModel
from herbie.v2._sources import GribSource


# ---------------------------------------------------------------------------
# Storm lookup helper (shared by HAFSA and HAFSB)
# ---------------------------------------------------------------------------


class _StormLookup:
    """Lazily fetch active storm IDs and names from the NOMADS HAFS directory."""

    @functools.cached_property
    def id_to_name(self) -> dict[str, str]:
        try:
            url = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/hafs/prod/inphfsa/"
            text = requests.get(url, timeout=8).text
            storms: dict[str, str] = {}
            for msg in set(re.findall(r"message\d+", text)):
                parts = re.split(
                    r"\s+", requests.get(url + msg, timeout=5).text, maxsplit=3
                )
                if len(parts) >= 3:
                    storms[parts[1].lower()] = parts[2].lower()
            return storms
        except Exception:
            return {}

    @functools.cached_property
    def name_to_id(self) -> dict[str, str]:
        return {v: k for k, v in self.id_to_name.items()}


_STORMS = _StormLookup()


# ---------------------------------------------------------------------------
# HAFSA
# ---------------------------------------------------------------------------


class HAFSA(HerbieModel):
    """
    NOAA Hurricane Analysis and Forecast System — configuration A (HAFS-A).

    Coupled atmosphere–ocean–wave model for tropical cyclone prediction.
    Products are organized by storm and initialization time.

    Parameters
    ----------
    date : str or datetime
        Model initialization datetime (UTC).
    step : int, default 0
        Forecast lead time in hours (0–126).
    storm : str
        Storm identifier.  Either the 8-character ATCF storm ID
        (e.g. ``'al052023'``) or the storm name (e.g. ``'idalia'``).
        Names are resolved to IDs by querying the NOMADS directory.
    product : str, default 'storm.atm'
        Output domain and field type:

        ``'storm.atm'``    Storm-following domain, atmospheric fields.
        ``'storm.sat'``    Storm-following domain, satellite-sim fields.
        ``'parent.atm'``   Parent domain, atmospheric fields.
        ``'parent.sat'``   Parent domain, satellite-sim fields.
        ``'parent.swath'`` Parent domain, max-wind swath.
        ``'ww3'``          WAVEWATCH III wave output.

    References
    ----------
    * https://wpo.noaa.gov/the-hurricane-analysis-and-forecast-system-hafs/
    * https://nomads.ncep.noaa.gov/pub/data/nccf/com/hafs/prod/
    """

    MODEL_NAME = "HAFSA"
    MODEL_DESCRIPTION = "Hurricane Analysis and Forecast System — A"
    MODEL_WEBSITES = {
        "WPO": "https://wpo.noaa.gov/the-hurricane-analysis-and-forecast-system-hafs/",
        "HFIP": "https://hfip.org/hafs",
    }

    PARAMS = {
        "storm": {
            "default": None,
            # Valid values are dynamic; validation is done in _build_sources
        },
        "product": {
            "default": "storm.atm",
            "valid": [
                "storm.atm",
                "storm.sat",
                "parent.atm",
                "parent.sat",
                "parent.swath",
                "ww3",
            ],
            "descriptions": {
                "storm.atm": "Storm-following domain, atmospheric fields",
                "storm.sat": "Storm-following domain, satellite-sim fields",
                "parent.atm": "Parent domain, atmospheric fields",
                "parent.sat": "Parent domain, satellite-sim fields",
                "parent.swath": "Parent domain, max-wind swath",
                "ww3": "WaveWatch III wave output",
            },
        },
    }

    _FLAVOR = "a"

    def _resolve_storm(self, storm: str | None) -> str:
        if storm is None:
            raise ValueError(
                "HAFSA requires a 'storm' parameter.\n"
                "Pass the ATCF storm ID (e.g. storm='al052023') or the storm "
                "name (e.g. storm='idalia')."
            )
        # Name → ID lookup (only if the value looks like a pure name)
        if storm.isalpha():
            resolved = _STORMS.name_to_id.get(storm.lower())
            if resolved is None:
                available = list(_STORMS.name_to_id.keys())
                raise ValueError(
                    f"Storm name {storm!r} not found. "
                    f"Available active storms: {available}"
                )
            return resolved
        return storm.lower()

    def _build_sources(self) -> dict:
        d = self.date
        step = self.step
        product = self.params.get("product", "storm.atm")
        storm = self._resolve_storm(self.params.get("storm"))
        flavor = self._FLAVOR

        path = (
            f"hfs{flavor}.{d:%Y%m%d/%H}/"
            f"{storm}.{d:%Y%m%d%H}.hfs{flavor}.{product}.f{step:03d}.grb2"
        )
        idx = [".grb2.idx", ".idx"]
        return {
            "nomads": GribSource(
                f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/hafs/prod/{path}",
                idx,
            ),
        }


class HAFSB(HAFSA):
    """
    NOAA Hurricane Analysis and Forecast System — configuration B (HAFS-B).

    Identical interface to ``HAFSA``; uses a different physics configuration.

    Parameters
    ----------
    date, step, storm, product
        Same as ``HAFSA``.
    """

    MODEL_NAME = "HAFSB"
    MODEL_DESCRIPTION = "Hurricane Analysis and Forecast System — B"
    _FLAVOR = "b"


# ---------------------------------------------------------------------------
# HIRESW
# ---------------------------------------------------------------------------


class HIRESW(HerbieModel):
    """
    NOAA High-Resolution Window (HIRESW) Forecast System.

    Multiple ~2.5-km or 5-km domains using ARW or FV3 dynamic cores.
    Available for CONUS, Alaska, Hawaii, Puerto Rico, and Guam.

    Parameters
    ----------
    date : str or datetime
        Model initialization datetime (UTC).
        Runs at 00 and 12 UTC.
    step : int, default 0
        Forecast lead time in hours (0–48).
    product : str, default 'arw_2p5km'
        Dynamical core and resolution:

        ``'arw_2p5km'``  CONUS ARW 2.5-km.
        ``'fv3_2p5km'``  CONUS FV3 2.5-km.
        ``'arw_5km'``    CONUS ARW 5-km.
        ``'fv3_5km'``    CONUS FV3 5-km.

    domain : str, default 'conus'
        Geographic domain: ``'conus'``, ``'ak'``, ``'hi'``, ``'guam'``, ``'pr'``.
    member : int, default 1
        Member number (1 or 2; only 2 members for ARW).

    References
    ----------
    * https://www.nco.ncep.noaa.gov/pmb/products/hiresw/
    """

    MODEL_NAME = "HIRESW"
    MODEL_DESCRIPTION = "NOAA High-Resolution Window Forecast System"
    MODEL_WEBSITES = {
        "NOMADS": "https://www.nco.ncep.noaa.gov/pmb/products/hiresw/",
    }

    PARAMS = {
        "product": {
            "default": "arw_2p5km",
            "valid": ["arw_2p5km", "fv3_2p5km", "arw_5km", "fv3_5km"],
            "descriptions": {
                "arw_2p5km": "CONUS ARW 2.5-km",
                "fv3_2p5km": "CONUS FV3 2.5-km",
                "arw_5km": "CONUS ARW 5-km",
                "fv3_5km": "CONUS FV3 5-km",
            },
        },
        "domain": {
            "default": "conus",
            "valid": ["conus", "ak", "hi", "guam", "pr"],
            "aliases": {
                "alaska": "ak",
                "hawaii": "hi",
                "puertorico": "pr",
            },
        },
        "member": {
            "default": 1,
            "valid": [1, 2],
        },
    }

    def _build_sources(self) -> dict:
        d = self.date
        step = self.step
        product = self.params["product"]
        domain = self.params["domain"]
        member = self.params["member"]

        member_sfx = "mem2" if member == 2 else ""
        path = (
            f"hiresw.{d:%Y%m%d}/"
            f"hiresw.t{d:%H}z.{product}.f{step:02d}.{domain}{member_sfx}.grib2"
        )
        idx = [".idx", ".grib2.idx"]
        return {
            "nomads": GribSource(
                f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/hiresw/prod/{path}",
                idx,
            ),
        }


