"""
NAVGEM model templates for Herbie v2.

NavgemNOMADS   — Navy Global Environment Model (recent, from NOMADS)
NavgemGODAE    — NAVGEM / NOGAPS historical archive (GODAE server)
"""

from __future__ import annotations

from herbie.v2._base import HerbieModel
from herbie.v2._sources import GribSource

# ---------------------------------------------------------------------------
# NAVGEM (recent — NOMADS)
# ---------------------------------------------------------------------------


class NAVGEM(HerbieModel):
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


class NAVGEM_GODAE(HerbieModel):
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
