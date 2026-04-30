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


# ---------------------------------------------------------------------------
# NAVGEM (recent — NOMADS)
# ---------------------------------------------------------------------------


class NavgemNOMADS(HerbieModel):
    """
    Navy Global Environment Model (NAVGEM) — recent data from NOMADS.

    Approximately last two days available.

    Parameters
    ----------
    date : str or datetime
        Model initialization datetime (UTC).
    step : int, default 0
        Forecast lead time in hours (0–168).

    References
    ----------
    * https://www.nrlmry.navy.mil/metoc/nogaps/navgem.html
    """

    MODEL_NAME = "NavgemNOMADS"
    MODEL_DESCRIPTION = "Navy Global Environment Model — NOMADS (recent)"
    MODEL_WEBSITES = {
        "NOMADS": "https://nomads.ncep.noaa.gov/pub/data/nccf/com/fnmoc/prod/",
    }

    PARAMS = {}

    def _build_sources(self) -> dict:
        d = self.date
        step = self.step
        path = f"navgem.{d:%Y%m%d}/navgem_{d:%Y%m%d%H}f{step:03d}.grib2"
        return {
            "nomads": GribSource(
                f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/fnmoc/prod/{path}",
                [".idx"],
            ),
        }


# ---------------------------------------------------------------------------
# NAVGEM / NOGAPS historical — GODAE server
# ---------------------------------------------------------------------------


class NavgemGODAE(HerbieModel):
    """
    NAVGEM (2013–2024) and NOGAPS (2004–2013) historical archive on GODAE.

    Uses GRIB1 for NOGAPS and GRIB2 for NAVGEM.  Variable selection uses
    wgrib2-style shorthand that is mapped to GODAE filename components.

    Parameters
    ----------
    date : str or datetime
        Model initialization datetime (UTC).
    step : int, default 0
        Forecast lead time in hours.
    variable : str
        Field to retrieve, in wgrib2-style format: ``'VARNAME:LEVEL'``.
        Examples: ``'TMP:500 mb'``, ``'UGRD:10 m'``, ``'HGT:surface'``.
    product : {'GMET', 'GLND', 'GOCN'}, default 'GMET'
        Product category.

    References
    ----------
    * https://usgodae.org/
    * https://usgodae.org/docs/layout/mdllayout.pns.html
    """

    MODEL_NAME = "NavgemGODAE"
    MODEL_DESCRIPTION = "NAVGEM / NOGAPS Historical — GODAE Archive"
    MODEL_WEBSITES = {
        "GODAE": "https://usgodae.org/",
        "Filename guide": "https://usgodae.org/docs/layout/mdllayout.pns.html",
    }

    PARAMS = {
        "product": {
            "default": "GMET",
            "valid": ["GMET", "GLND", "GOCN", "GCOM"],
            "descriptions": {
                "GMET": "Meteorological fields",
                "GLND": "Land / terrain fields",
                "GOCN": "Ocean fields",
                "GCOM": "Composition fields",
            },
        },
        "variable": {
            "default": "TMP:500 mb",
        },
    }

    # wgrib2 variable name → GODAE filename variable component
    _VAR_MAP = {
        "TMP": "air_temp",
        "DEPR": "dwpt_dprs",
        "ABSV": "abs_vort",
        "RH": "rltv_hum",
        "PRES": "pres",
        "UGRD": "wnd_ucmp",
        "VGRD": "wnd_vcmp",
        "HGT": "geop_ht",
        "VAPP": "vpr_pres",
        "VVEL": "wnd_vert_vel",
        "CAPE": "cape",
        "VIS": "visib",
        "PWAT": "prcp_h20",
        "PRATE": "rain_rate",
        "SHTFL": "snsb_heat_flux",
        "SNOD": "snw_dpth",
        "NSWRS": "sol_rad",
        "UFLX": "wnd_strs_ucmp",
        "VFLX": "wnd_strs_vcmp",
        "PRMSL": "pres_msl",
    }

    def _parse_variable(self) -> tuple[str, str]:
        """Return (godae_variable, godae_level) from the wgrib2-style variable string."""
        raw = self.params.get("variable", "TMP:500 mb")
        if ":" in raw:
            var, lev = raw.split(":", 1)
        else:
            var, lev = raw, "surface"

        godae_var = self._VAR_MAP.get(var.upper(), var.lower())

        if var.upper() == "HGT" and lev == "surface":
            return "terr_ht", "0001_000000-000000"

        if var.upper() in {"MSLMA", "PRMSL"}:
            return godae_var, "0102_000000-000000"

        lev = lev.strip()
        if lev.endswith("mb"):
            mb = int(lev.replace("mb", "").strip())
            return godae_var, f"0100_{mb:06d}-000000"
        if lev == "2 m":
            return godae_var, "0105_000020-000000"
        if lev == "10 m":
            return godae_var, "0105_000100-000000"
        if lev in {"surface", "sfc"}:
            return godae_var, "0001_000000-000000"
        if lev == "tropopause":
            return godae_var, "0007_000000-000000"

        return godae_var, "0001_000000-000000"

    def _build_sources(self) -> dict:
        d = self.date
        step = self.step
        product = self.params["product"]
        godae_var, godae_level = self._parse_variable()

        navgem_url = (
            f"https://usgodae.org/ftp/outgoing/fnmoc/models/navgem_0.5/"
            f"{d:%Y/%Y%m%d%H}/"
            f"US058{product}-GR1mdl.0018_0056_{step:03d}00F0RL"
            f"{d:%Y%m%d%H}_{godae_level}{godae_var}"
        )
        navgem_gr2 = (
            navgem_url.replace("GR1mdl", "GR2mdl").replace("0018_0056", "0018_0056")
            + ".gr2"
        )
        nogaps_url = (
            f"https://usgodae.org/ftp/outgoing/fnmoc/models/nogaps/"
            f"{d:%Y/%Y%m%d%H}/"
            f"US058{product}-GR1mdl.0058_0240_{step:03d}00F0RL"
            f"{d:%Y%m%d%H}_{godae_level}{godae_var}"
        )

        return {
            "navgem": GribSource(navgem_url, [".idx"]),
            "navgem_grib2": GribSource(navgem_gr2, [".idx"]),
            "nogaps": GribSource(nogaps_url, [".idx"]),
        }
